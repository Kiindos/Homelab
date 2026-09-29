#!/usr/bin/env python3
"""Veille de sécurité : versions en service comparées aux dernières publiées, failles connues.

Chaque nuit (VEILLE_HEURE, heure de Paris), ou à la demande (fichier <données>/lancer) :

1. inventaire des conteneurs en service, relevé par chaque machine (métrique homelab_conteneur_info) ;
2. failles des images (Trivy) : la liste des paquets (SBOM) est calculée une seule fois par empreinte d'image, puis
   comparée chaque nuit à la base de failles du jour, sans retélécharger l'image ;
3. nouvelle construction de la même version sur le registre (en-tête du manifeste seulement) ;
4. dernière version publiée et avis de sécurité du projet (API GitHub, requêtes conditionnelles) ;
5. services hors conteneurs : version lue sur le service (ex. coffre OpenBao) ou relevée par une autre machine
   (OPNsense, métrique homelab_opnsense_info).

Résultats : métriques Prometheus (http://veille:9800/metrics) pour les alertes et le tableau Grafana « Veille de
sécurité » ; rapport complet dans <sortie>/veille.json. Aucune donnée n'est envoyée ailleurs que vers les registres
d'images et GitHub (lecture publique).
"""

import datetime
import http.server
import json
import os
import re
import ssl
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

CONFIG = os.environ.get("VEILLE_CONFIG", "/etc/veille/veille.json")
DONNEES = os.environ.get("VEILLE_DONNEES", "/donnees")
SORTIE = os.environ.get("VEILLE_SORTIE", DONNEES)
PORT = int(os.environ.get("VEILLE_PORT", "9800"))
HEURE = os.environ.get("VEILLE_HEURE", "04:40")
FICHIER_JETON = os.environ.get("VEILLE_JETON_GITHUB", "/run/secrets/github")
CA = os.environ.get("VEILLE_CA", "")
TRIVY_CACHE = os.path.join(DONNEES, "trivy")
SBOM = os.path.join(DONNEES, "sbom")
DECLENCHEUR = os.path.join(DONNEES, "lancer")
GRAVITES = ("CRITICAL", "HIGH", "MEDIUM", "LOW", "UNKNOWN")
GRAVITES_AVIS = {"critical": "critique", "high": "haute", "medium": "moyenne", "low": "faible"}
ACCEPT_MANIFESTE = ", ".join([
    "application/vnd.oci.image.index.v1+json",
    "application/vnd.docker.distribution.manifest.list.v2+json",
    "application/vnd.oci.image.manifest.v1+json",
    "application/vnd.docker.distribution.manifest.v2+json",
])

metriques = {"texte": "", "verrou": threading.Lock()}


def journal(evenement, **champs):
    print(json.dumps({"heure": datetime.datetime.now().isoformat(timespec="seconds"), "evenement": evenement,
                      **champs}, ensure_ascii=False), flush=True)


# --- Versions ----------------------------------------------------------------------------------------------


def version(texte, motif=r"(\d+(?:\.\d+)+)"):
    """« v4.53.10-ls270 » → (4, 53, 10) ; None si aucune version lisible."""
    trouve = re.search(motif, texte or "")
    return tuple(int(x) for x in re.findall(r"\d+", trouve.group(1))) if trouve else None


def comparer(a, b):
    longueur = max(len(a), len(b))
    a, b = a + (0,) * (longueur - len(a)), b + (0,) * (longueur - len(b))
    return (a > b) - (a < b)


def dans_intervalle(v, intervalle):
    """Intervalle d'un avis GitHub : « < 2.7.0 », « >= 3.0.0, < 3.2.3 », « <= 1.4 », « = 1.0.0 »."""
    if not intervalle:
        return False
    for condition in intervalle.split(","):
        trouve = re.match(r"\s*(<=|>=|<|>|=)?\s*v?([\w.\-+]+)", condition)
        borne = version(trouve.group(2)) if trouve else None
        if borne is None:
            return False
        resultat = comparer(v, borne)
        if not {"<": resultat < 0, "<=": resultat <= 0, ">": resultat > 0, ">=": resultat >= 0,
                "=": resultat == 0, None: resultat == 0}[trouve.group(1)]:
            return False
    return True


def affecte(v, intervalle, corriges):
    """Version touchée par un avis ? Les intervalles publiés sont souvent incomplets (borne basse seule, une borne par
    branche) : on se fie d'abord aux versions corrigées de la même branche, puis à l'intervalle.

    - correctif publié pour la même version mineure (ex. 3.2.x) : touchée si plus ancienne que lui ;
    - correctifs de la même version majeure seulement : non touchée si plus récente que tous, sinon l'intervalle ;
    - correctifs seulement pour des versions majeures plus anciennes : non touchée (branche plus récente) ;
    - aucun correctif publié : l'intervalle, s'il a une borne haute ; sinon avis ignoré (impossible à trancher).
    """
    conditions = [c.strip() for c in (intervalle or "").split(",") if c.strip()]
    corrigees = [c for c in (version(x) for x in (corriges or "").split(",")) if c]
    if corrigees:
        meme_mineure = [c for c in corrigees if c[:2] == v[:2]]
        if meme_mineure:
            return comparer(v, min(meme_mineure)) < 0
        meme_majeure = [c for c in corrigees if c[0] == v[0]]
        if meme_majeure and all(comparer(v, c) > 0 for c in meme_majeure):
            return False
        if not meme_majeure and all(c[0] < v[0] for c in corrigees):
            return False
        return dans_intervalle(v, intervalle)
    if not any(re.match(r"(<|<=|=)\s*v?\d", c) for c in conditions):
        return False
    return dans_intervalle(v, intervalle)


def texte_version(v):
    return ".".join(str(x) for x in v) if v else ""


# --- Accès réseau ------------------------------------------------------------------------------------------


def contexte_tls():
    return ssl.create_default_context(cafile=CA) if CA and os.path.exists(CA) else ssl.create_default_context()


def ouvrir(url, methode="GET", entetes=None, delai=30):
    requete = urllib.request.Request(url, method=methode, headers={"User-Agent": "homelab-veille", **(entetes or {})})
    return urllib.request.urlopen(requete, timeout=delai, context=contexte_tls())


def lire_json(url, entetes=None):
    with ouvrir(url, entetes=entetes) as reponse:
        return json.load(reponse)


def prometheus(config, promql):
    url = config["prometheus"] + "/api/v1/query?" + urllib.parse.urlencode({"query": promql})
    return [(r["metric"], float(r["value"][1])) for r in lire_json(url)["data"]["result"]]


class GitHub:
    """API GitHub en lecture publique, avec cache et requêtes conditionnelles (une réponse 304 ne compte pas dans
    la limite de 60 requêtes par heure sans jeton)."""

    def __init__(self):
        self.chemin = os.path.join(DONNEES, "github.json")
        try:
            with open(self.chemin, encoding="utf-8") as fichier:
                self.cache = json.load(fichier)
        except (OSError, ValueError):
            self.cache = {}
        self.jeton = ""
        if os.path.exists(FICHIER_JETON):
            with open(FICHIER_JETON, encoding="utf-8") as fichier:
                self.jeton = fichier.read().strip()
        self.limite_atteinte = False
        self.memo = {}

    def lire(self, chemin):
        url = "https://api.github.com/" + chemin
        if url not in self.memo:
            self.memo[url] = self._lire(url)
        return self.memo[url]

    def _lire(self, url):
        entree = self.cache.get(url, {})
        if self.limite_atteinte:
            return entree.get("donnees")
        entetes = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
        if self.jeton:
            entetes["Authorization"] = f"Bearer {self.jeton}"
        if entree.get("etag"):
            entetes["If-None-Match"] = entree["etag"]
        try:
            with ouvrir(url, entetes=entetes) as reponse:
                self.cache[url] = {"etag": reponse.headers.get("ETag", ""), "donnees": json.load(reponse)}
        except urllib.error.HTTPError as erreur:
            if erreur.code == 304:
                return entree.get("donnees")
            if erreur.code in (403, 429):
                self.limite_atteinte = True
                journal("github-limite", url=url)
            elif erreur.code != 404:
                journal("github-erreur", url=url, code=erreur.code)
            return entree.get("donnees")
        except (urllib.error.URLError, TimeoutError, ValueError) as erreur:
            journal("github-erreur", url=url, erreur=str(erreur))
            return entree.get("donnees")
        return self.cache[url]["donnees"]

    def enregistrer(self):
        temporaire = self.chemin + ".tmp"
        with open(temporaire, "w", encoding="utf-8") as fichier:
            json.dump(self.cache, fichier)
        os.replace(temporaire, self.chemin)


def registre(image):
    """« nginx » → (registry-1.docker.io, library/nginx) ; « ghcr.io/a/b » → (ghcr.io, a/b)."""
    premier, _, reste = image.partition("/")
    if reste and ("." in premier or ":" in premier or premier == "localhost"):
        return ("registry-1.docker.io" if premier == "docker.io" else premier), reste
    return "registry-1.docker.io", (image if "/" in image else "library/" + image)


def empreinte_registre(image, etiquette):
    """Empreinte actuelle d'une étiquette sur le registre (requête HEAD : ne compte pas comme un téléchargement)."""
    hote, depot = registre(image)
    url = f"https://{hote}/v2/{depot}/manifests/{etiquette}"
    entetes = {"Accept": ACCEPT_MANIFESTE}
    for _ in range(2):
        try:
            with ouvrir(url, methode="HEAD", entetes=entetes, delai=20) as reponse:
                return reponse.headers.get("Docker-Content-Digest")
        except urllib.error.HTTPError as erreur:
            defi = erreur.headers.get("WWW-Authenticate", "")
            if erreur.code != 401 or not defi.startswith("Bearer") or "Authorization" in entetes:
                return None
            champs = dict(re.findall(r'(\w+)="([^"]*)"', defi))
            parametres = {k: v for k, v in champs.items() if k in ("service", "scope")}
            try:
                jeton = lire_json(champs["realm"] + "?" + urllib.parse.urlencode(parametres))
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
                return None
            entetes["Authorization"] = "Bearer " + (jeton.get("token") or jeton.get("access_token", ""))
        except (urllib.error.URLError, TimeoutError):
            return None
    return None


# --- Trivy -------------------------------------------------------------------------------------------------


def trivy(*arguments, delai=1800):
    return subprocess.run(["trivy", "--cache-dir", TRIVY_CACHE, "--quiet", *arguments],
                          capture_output=True, text=True, timeout=delai, check=False)


def failles_image(image, empreinte):
    """Failles de l'image en service (par empreinte) ; None si l'analyse est impossible (image locale…)."""
    if not empreinte:
        return None
    fichier = os.path.join(SBOM, empreinte.replace(":", "_") + ".json")
    if not os.path.exists(fichier):
        resultat = trivy("image", "--image-src", "remote", "--platform", "linux/amd64", "--format", "cyclonedx",
                         "--output", fichier + ".tmp", f"{image}@{empreinte}")
        if resultat.returncode != 0:
            journal("sbom-echec", image=image, erreur=resultat.stderr.strip()[-300:])
            return None
        os.replace(fichier + ".tmp", fichier)
        journal("sbom", image=image, empreinte=empreinte[:19])
    resultat = trivy("sbom", "--skip-db-update", "--scanners", "vuln", "--format", "json", fichier)
    if resultat.returncode != 0:
        journal("analyse-echec", image=image, erreur=resultat.stderr.strip()[-300:])
        return None
    failles = {}
    for bloc in json.loads(resultat.stdout).get("Results") or []:
        for faille in bloc.get("Vulnerabilities") or []:
            cle = (faille["VulnerabilityID"], faille.get("PkgName", ""))
            failles[cle] = {"id": faille["VulnerabilityID"], "paquet": faille.get("PkgName", ""),
                            "installe": faille.get("InstalledVersion", ""), "corrige": faille.get("FixedVersion", ""),
                            "gravite": faille.get("Severity", "UNKNOWN"), "titre": (faille.get("Title") or "")[:160]}
    return list(failles.values())


# --- Collecte ----------------------------------------------------------------------------------------------


def source_de(config, image):
    for motif, source in config.get("sources", {}).items():
        if image == motif or image.endswith("/" + motif):
            return source
    return {}


def derniere_publiee(github, source):
    """Dernière version publiée du projet (releases, ou étiquettes si le projet n'en publie pas)."""
    if not source.get("github"):
        return None
    motif = source.get("version_depot", r"(\d+(?:\.\d+)+)")
    if source.get("etiquettes"):
        liste = github.lire(f"repos/{source['github']}/tags?per_page=50") or []
        versions = [version(e["name"], motif) for e in liste
                    if not re.search(r"(alpha|beta|rc|dev)", e["name"], re.IGNORECASE)]
        return max((v for v in versions if v), default=None, key=lambda v: v + (0,) * (8 - len(v)))
    publication = github.lire(f"repos/{source['github']}/releases/latest") or {}
    return version(publication.get("tag_name"), motif)


def avis_applicables(github, source, courante):
    depot = source.get("avis", source.get("github"))
    if not depot or not courante:
        return []
    paquet = source.get("paquet_avis")
    retenus = []
    for avis in github.lire(f"repos/{depot}/security-advisories?state=published&per_page=100") or []:
        for cible in avis.get("vulnerabilities") or []:
            nom = (cible.get("package") or {}).get("name") or ""
            if paquet and not re.search(paquet, nom):
                continue
            if affecte(courante, cible.get("vulnerable_version_range"), cible.get("patched_versions")):
                retenus.append({"id": avis.get("cve_id") or avis["ghsa_id"], "ghsa": avis["ghsa_id"],
                                "gravite": GRAVITES_AVIS.get(avis.get("severity"), "inconnue"),
                                "corrige": cible.get("patched_versions") or "", "resume": avis.get("summary", "")[:160],
                                "publie": (avis.get("published_at") or "")[:10]})
                break
    return retenus


def version_en_ligne(service):
    """Version lue sur le service lui-même (ex. /v1/sys/health du coffre)."""
    try:
        donnees = lire_json(service["url_version"])
        return str(donnees.get(service.get("champ", "version"), ""))
    except (urllib.error.URLError, TimeoutError, ValueError) as erreur:
        journal("version-illisible", service=service.get("nom"), erreur=str(erreur))
        return ""


def cycle(config):
    debut = time.time()
    journal("debut")
    os.makedirs(SBOM, exist_ok=True)
    maj_base = trivy("image", "--download-db-only", delai=900)
    if maj_base.returncode != 0:
        journal("base-echec", erreur=maj_base.stderr.strip()[-300:])
    github = GitHub()

    conteneurs = [m for m, _ in prometheus(config, "homelab_conteneur_info")]
    images = {}
    for c in conteneurs:
        cle = (c["image"], c["version"], c.get("empreinte", ""))
        images.setdefault(cle, []).append(c)

    rapport_images, services = [], []
    for (image, etiquette, empreinte), instances in sorted(images.items()):
        source = source_de(config, image)
        nom = source.get("nom") or image.rsplit("/", 1)[-1]
        locale = bool(source.get("image_locale"))
        empreinte = "" if locale else empreinte
        failles = failles_image(image, empreinte)
        actuelle_registre = empreinte_registre(image, etiquette) if empreinte else None
        reconstruction = bool(actuelle_registre and empreinte and actuelle_registre != empreinte)
        machines = sorted({c["instance"] for c in instances})
        rapport_images.append({"image": image, "version": etiquette, "empreinte": empreinte, "service": nom,
                               "machines": machines, "reconstruction": reconstruction, "failles": failles})
        # Version lue sur le service (étiquette flottante, ex. « 12.1 ») : voir la liste « services » de la config.
        if source.get("github") and not source.get("url_version"):
            for machine in machines:
                services.append({"machine": machine, "service": nom, "image": image, "etiquette": etiquette,
                                 "courante": version(etiquette, source.get("version_image", r"(\d+(?:\.\d+)+)")),
                                 "source": source, "expose": bool(source.get("expose"))})

    for service in config.get("services", []):
        texte = version_en_ligne(service) if service.get("url_version") else ""
        services.append({"machine": service["machine"], "service": service["nom"], "image": "",
                         "etiquette": texte, "courante": version(texte), "source": service,
                         "expose": bool(service.get("expose"))})

    # OPNsense : version installée relevée par l'hyperviseur (clé d'API limitée au tableau de bord).
    opnsense = config.get("opnsense")
    if opnsense:
        for m, _ in prometheus(config, "homelab_opnsense_info"):
            services.append({"machine": opnsense.get("machine", "fw01"), "service": "OPNsense", "image": "",
                             "etiquette": m.get("version", ""), "courante": version(m.get("version", "")),
                             "source": opnsense, "expose": True, "systeme": True})

    for s in services:
        s["derniere"] = derniere_publiee(github, s["source"])
        s["avis"] = avis_applicables(github, s["source"], s["courante"])
        if not s["courante"] or not s["derniere"]:
            s["statut"] = "inconnu"
        else:
            s["statut"] = "version_disponible" if comparer(s["derniere"], s["courante"]) > 0 else "a_jour"
    github.enregistrer()

    actions = []
    for s in services:
        for avis in s["avis"]:
            actions.append({"machine": s["machine"], "service": s["service"], "action": "avis",
                            "detail": f"{avis['id']} ({avis['gravite']}) : {avis['resume'][:90]} — corrigé en "
                                      f"{avis['corrige'] or '?'}"})
        if s.get("systeme") and s["statut"] == "version_disponible":
            actions.append({"machine": s["machine"], "service": s["service"], "action": "systeme",
                            "detail": f"{s['etiquette']} → {texte_version(s['derniere'])}"})
    for img in rapport_images:
        graves = [f for f in img["failles"] or [] if f["gravite"] in ("CRITICAL", "HIGH") and f["corrige"]]
        if graves and img["reconstruction"]:
            for machine in img["machines"]:
                actions.append({"machine": machine, "service": img["service"], "action": "reconstruction",
                                "detail": f"{len(graves)} faille(s) critique(s) ou haute(s) corrigeable(s) ; nouvelle "
                                          f"construction de {img['version']} disponible (mise à jour du parc)"})
        elif any(f["gravite"] == "CRITICAL" for f in graves):
            plus_recente = next((s for s in services if s["image"] == img["image"]
                                 and s["statut"] == "version_disponible"), None)
            if plus_recente:
                for machine in img["machines"]:
                    actions.append({"machine": machine, "service": img["service"], "action": "version",
                                    "detail": f"faille(s) critique(s) corrigeable(s) dans {img['version']} ; version "
                                              f"{texte_version(plus_recente['derniere'])} publiée (changement dans le code)"})

    publier(services, rapport_images, actions, debut, github.limite_atteinte)
    journal("fin", duree=int(time.time() - debut), images=len(rapport_images), services=len(services),
            actions=len(actions))


# --- Publication -------------------------------------------------------------------------------------------


def etiquettes(**champs):
    def echapper(valeur):
        return str(valeur).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")
    return "{" + ",".join(f'{cle}="{echapper(val)}"' for cle, val in champs.items()) + "}"


def publier(services, images, actions, debut, limite):
    maintenant = time.time()
    lignes = [
        "# HELP homelab_veille_service_info Version en service et dernière publiée, par service et machine.",
        "# TYPE homelab_veille_service_info gauge",
    ]
    for s in services:
        lignes.append("homelab_veille_service_info" + etiquettes(
            machine=s["machine"], service=s["service"], image=s["image"], version=s["etiquette"],
            derniere=texte_version(s["derniere"]), statut=s["statut"], expose="oui" if s["expose"] else "non") + " 1")
        for avis in s["avis"]:
            lignes.append("homelab_veille_avis_info" + etiquettes(
                machine=s["machine"], service=s["service"], id=avis["id"], gravite=avis["gravite"],
                version=s["etiquette"], corrige=avis["corrige"], resume=avis["resume"]) + " 1")
    lignes.append("# HELP homelab_veille_failles Failles connues des images en service (Trivy), par gravité.")
    lignes.append("# TYPE homelab_veille_failles gauge")
    for img in images:
        cles = dict(service=img["service"], image=img["image"], version=img["version"],
                    machines=",".join(img["machines"]))
        lignes.append("homelab_veille_reconstruction" + etiquettes(**cles) + f" {int(img['reconstruction'])}")
        if img["empreinte"]:  # image construite sur place : pas d'analyse possible, pas d'alerte
            lignes.append("homelab_veille_analyse_ok" + etiquettes(**cles) + f" {int(img['failles'] is not None)}")
        for gravite in GRAVITES:
            for corrigeable in ("oui", "non"):
                nombre = sum(1 for f in img["failles"] or [] if f["gravite"] == gravite
                             and bool(f["corrige"]) == (corrigeable == "oui"))
                lignes.append("homelab_veille_failles" + etiquettes(**cles, gravite=gravite, corrigeable=corrigeable)
                              + f" {nombre}")
        for f in img["failles"] or []:
            if f["gravite"] in ("CRITICAL", "HIGH") and f["corrige"]:
                lignes.append("homelab_veille_faille_info" + etiquettes(
                    service=img["service"], image=img["image"], version=img["version"], id=f["id"],
                    paquet=f["paquet"], installe=f["installe"], corrige=f["corrige"], gravite=f["gravite"],
                    titre=f["titre"]) + " 1")
    lignes.append("# HELP homelab_veille_action Action de sécurité à mener (alerte VeilleActionSecurite).")
    lignes.append("# TYPE homelab_veille_action gauge")
    for a in actions:
        lignes.append("homelab_veille_action" + etiquettes(**a) + " 1")
    lignes += [
        f"homelab_veille_github_limite {int(limite)}",
        f"homelab_veille_duree_secondes {int(maintenant - debut)}",
        f"homelab_veille_derniere_reussite_timestamp {int(maintenant)}",
    ]
    with metriques["verrou"]:
        metriques["texte"] = "\n".join(lignes) + "\n"
    rapport = {"genere": datetime.datetime.now().isoformat(timespec="seconds"), "services": [
        {**{k: v for k, v in s.items() if k not in ("source", "courante", "derniere")},
         "derniere": texte_version(s["derniere"])} for s in services], "images": images, "actions": actions}
    for chemin, contenu in ((os.path.join(SORTIE, "veille.json"), rapport),
                            (os.path.join(DONNEES, "metriques.txt"), metriques["texte"])):
        temporaire = chemin + ".tmp"
        with open(temporaire, "w", encoding="utf-8") as fichier:
            if isinstance(contenu, str):
                fichier.write(contenu)
            else:
                json.dump(contenu, fichier, ensure_ascii=False, indent=1)
        os.replace(temporaire, chemin)


class Serveur(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (nom imposé par http.server)
        if self.path != "/metrics":
            self.send_error(404)
            return
        with metriques["verrou"]:
            corps = metriques["texte"].encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; version=0.0.4; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def log_message(self, *_):
        pass


# --- Boucle ------------------------------------------------------------------------------------------------


def prochaine_execution(apres):
    heures, minutes = (int(x) for x in HEURE.split(":"))
    cible = apres.replace(hour=heures, minute=minutes, second=0, microsecond=0)
    return cible if cible > apres else cible + datetime.timedelta(days=1)


def main():
    for dossier in (TRIVY_CACHE, SBOM, os.environ.get("TMPDIR", "/tmp")):
        os.makedirs(dossier, exist_ok=True)
    try:  # métriques de la veille précédente, en attendant la prochaine
        with open(os.path.join(DONNEES, "metriques.txt"), encoding="utf-8") as fichier:
            metriques["texte"] = fichier.read()
    except OSError:
        pass
    serveur = http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Serveur)
    threading.Thread(target=serveur.serve_forever, daemon=True).start()
    derniere = re.search(r"homelab_veille_derniere_reussite_timestamp (\d+)", metriques["texte"])
    prochaine = prochaine_execution(datetime.datetime.now())
    if not derniere or time.time() - int(derniere.group(1)) > 26 * 3600:
        prochaine = datetime.datetime.now() + datetime.timedelta(minutes=2)
    journal("demarrage", prochaine=prochaine.isoformat(timespec="minutes"))
    while True:
        if os.path.exists(DECLENCHEUR) or datetime.datetime.now() >= prochaine:
            try:
                os.remove(DECLENCHEUR)
            except FileNotFoundError:
                pass
            try:
                with open(CONFIG, encoding="utf-8") as fichier:
                    cycle(json.load(fichier))
            except Exception as erreur:  # une veille en échec doit se voir (alerte VeilleEnPanne), pas s'arrêter
                journal("echec", erreur=repr(erreur)[:500])
            prochaine = prochaine_execution(datetime.datetime.now())
        time.sleep(20)


if __name__ == "__main__":
    main()
