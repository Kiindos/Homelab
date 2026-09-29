#!/usr/bin/python3
"""État des mises à jour de la machine, pour Prometheus (collecteur « textfile » de node_exporter).

Géré par Ansible (rôle agent_supervision). Lecture seule : simule la mise à niveau des paquets avec les listes déjà
rafraîchies par apt-daily (aucun téléchargement), lit l'indicateur de redémarrage et les images des conteneurs en
service. Relancé par la minuterie etat-mises-a-jour.timer et à la fin de chaque mise à jour.

Métriques :
  homelab_apt_mises_a_jour{origine}                     paquets en attente par origine (securite, debian, proxmox…)
  homelab_apt_paquet_info{paquet,actuelle,disponible,origine}   détail (seulement s'il y en a)
  homelab_redemarrage_requis                            1 si un paquet installé demande un redémarrage
  homelab_redemarrage_requis_depuis_timestamp           depuis quand
  homelab_noyau_a_jour                                  0 si un noyau plus récent est installé mais pas en service
  homelab_conteneur_info{conteneur,pile,image,version,empreinte}   images en service (veille de sécurité)
  homelab_opnsense_info{version}                        version d'OPNsense (hyperviseur seulement, si configuré)
  homelab_etat_mises_a_jour_timestamp                   heure du relevé
"""

import base64
import json
import os
import re
import ssl
import subprocess
import tempfile
import time
import urllib.request

SORTIE = "/var/lib/prometheus/node-exporter/mises-a-jour.prom"
# Relevé de la version d'OPNsense (hyperviseur) : { url, cle, secret, certificat }, clé limitée au tableau de bord.
OPNSENSE = "/etc/homelab/opnsense-veille.json"
INST = re.compile(r"^Inst (\S+) (?:\[(\S+)\] )?\((\S+) (.*?) \[[^\]]+\]\)")


def echapper(valeur):
    return str(valeur).replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")


def etiquettes(**champs):
    return "{" + ",".join(f'{cle}="{echapper(val)}"' for cle, val in champs.items()) + "}"


def origine(texte):
    """« Debian-Security:13/stable-security », « Proxmox:… », « Docker CE:… » → catégorie courte."""
    if "security" in texte.lower():
        return "securite"
    for prefixe, nom in (("Debian", "debian"), ("Proxmox", "proxmox"), ("Docker", "docker")):
        if texte.startswith(prefixe):
            return nom
    return "autre"


def paquets():
    simulation = subprocess.run(
        ["apt-get", "-s", "-o", "Debug::NoLocking=1", "dist-upgrade"],
        capture_output=True, text=True, env={**os.environ, "LC_ALL": "C"}, check=False)
    liste = []
    for ligne in simulation.stdout.splitlines():
        trouve = INST.match(ligne)
        if trouve:
            nom, actuelle, disponible, source = trouve.groups()
            liste.append((nom, actuelle or "", disponible, origine(source)))
    return liste, simulation.returncode == 0


def noyau_a_jour():
    installes = [f[len("vmlinuz-"):] for f in os.listdir("/boot") if f.startswith("vmlinuz-")]
    if not installes:
        return 1
    tri = subprocess.run(["sort", "-V"], input="\n".join(installes), capture_output=True, text=True, check=False)
    return int(tri.stdout.split()[-1] == os.uname().release)


def conteneurs():
    try:
        ps = subprocess.run(["docker", "ps", "--format", "{{json .}}"], capture_output=True, text=True, timeout=30,
                            check=True)
    except (OSError, subprocess.SubprocessError):
        return []
    resultat = []
    for ligne in ps.stdout.splitlines():
        c = json.loads(ligne)
        image = c["Image"]
        empreinte = ""
        inspect = subprocess.run(["docker", "image", "inspect", "--format", "{{json .RepoDigests}}", image],
                                 capture_output=True, text=True, check=False)
        if inspect.returncode == 0:
            digests = json.loads(inspect.stdout or "null") or []
            if digests:
                empreinte = digests[0].split("@", 1)[1]
        # « depot/image:version@sha256:… » → dépôt et version séparés (l'empreinte vient de l'image locale).
        reference = image.split("@", 1)[0]
        depot, _, version = reference.rpartition(":") if ":" in reference.rsplit("/", 1)[-1] else (reference, "", "")
        pile = ""
        for etiquette in c.get("Labels", "").split(","):
            if etiquette.startswith("com.docker.compose.project="):
                pile = etiquette.split("=", 1)[1]
        resultat.append({"conteneur": c["Names"], "pile": pile, "image": depot, "version": version or "latest",
                         "empreinte": empreinte})
    return resultat


def opnsense():
    """Version d'OPNsense par l'API du tableau de bord. Certificat autosigné : seul le certificat relevé (et vérifié
    par son empreinte au déploiement) est accepté ; le nom n'est pas contrôlé, le certificat étant épinglé."""
    if not os.path.exists(OPNSENSE):
        return None
    with open(OPNSENSE, encoding="utf-8") as fichier:
        config = json.load(fichier)
    contexte = ssl.create_default_context(cafile=config["certificat"])
    contexte.check_hostname = False
    identifiants = base64.b64encode(f"{config['cle']}:{config['secret']}".encode()).decode()
    requete = urllib.request.Request(config["url"] + "/api/diagnostics/system/system_information",
                                     headers={"Authorization": "Basic " + identifiants})
    try:
        with urllib.request.urlopen(requete, timeout=20, context=contexte) as reponse:
            versions = json.load(reponse).get("versions", [])
    except (OSError, ValueError):
        return None
    trouve = next((re.match(r"OPNsense (\S+?)(?:-\w+)?$", v) for v in versions if v.startswith("OPNsense ")), None)
    return trouve.group(1) if trouve else None


def main():
    lignes = []
    liste, simulation_ok = paquets()
    lignes.append("# HELP homelab_apt_mises_a_jour Paquets en attente de mise à jour, par origine.")
    lignes.append("# TYPE homelab_apt_mises_a_jour gauge")
    comptes = {nom: 0 for nom in ("securite", "debian", "proxmox", "docker", "autre")}
    for *_, categorie in liste:
        comptes[categorie] += 1
    for categorie, nombre in comptes.items():
        lignes.append(f"homelab_apt_mises_a_jour{etiquettes(origine=categorie)} {nombre}")
    lignes.append(f"homelab_apt_simulation_ok {int(simulation_ok)}")
    for nom, actuelle, disponible, categorie in liste:
        lignes.append("homelab_apt_paquet_info"
                      f"{etiquettes(paquet=nom, actuelle=actuelle, disponible=disponible, origine=categorie)} 1")

    drapeau = "/run/reboot-required"
    requis = os.path.exists(drapeau)
    lignes.append(f"homelab_redemarrage_requis {int(requis)}")
    if requis:
        lignes.append(f"homelab_redemarrage_requis_depuis_timestamp {int(os.path.getmtime(drapeau))}")
    lignes.append(f"homelab_noyau_a_jour {noyau_a_jour()}")

    for c in conteneurs():
        lignes.append(f"homelab_conteneur_info{etiquettes(**c)} 1")
    version_opnsense = opnsense()
    if version_opnsense:
        lignes.append(f"homelab_opnsense_info{etiquettes(version=version_opnsense)} 1")
    lignes.append(f"homelab_etat_mises_a_jour_timestamp {int(time.time())}")

    dossier = os.path.dirname(SORTIE)
    with tempfile.NamedTemporaryFile("w", dir=dossier, delete=False, prefix=".mises-a-jour.") as temporaire:
        temporaire.write("\n".join(lignes) + "\n")
    os.chmod(temporaire.name, 0o644)
    os.replace(temporaire.name, SORTIE)


if __name__ == "__main__":
    main()
