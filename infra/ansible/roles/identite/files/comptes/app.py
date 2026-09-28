#!/usr/bin/env python3
"""Page des comptes du homelab : inviter un proche, lui renvoyer un lien pour choisir son mot de passe.

Servie derrière le proxy interne (VPN d'administration), qui impose la connexion SSO : l'identité de
l'administrateur arrive dans Remote-User / Remote-Groups, acceptés uniquement depuis les adresses du proxy.
Le compte est créé dans LLDAP sans mot de passe, puis Authelia envoie un lien à usage unique pour que la personne
choisisse le sien : aucun mot de passe ne transite. Bibliothèque standard uniquement.
"""

import base64
import html
import http.server
import ipaddress
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

LLDAP = os.environ.get("LLDAP_URL", "http://lldap:17170")
LLDAP_UTILISATEUR = os.environ.get("LLDAP_UTILISATEUR", "admin")
LLDAP_MDP_FICHIER = os.environ.get("LLDAP_MOT_DE_PASSE_FICHIER", "/run/secrets/lldap_admin_password")
AUTHELIA = os.environ.get("AUTHELIA_URL", "http://authelia:9091")
PORTAIL = os.environ.get("PORTAIL", "https://auth.example.com").rstrip("/")
SOURCES = [ipaddress.ip_network(s) for s in os.environ.get("SOURCES_AUTORISEES", "127.0.0.1/32").split()]
GROUPE_ADMIN = os.environ.get("GROUPE_ADMIN", "admins")
# Groupes proposés à l'invitation : tous ceux de l'annuaire, sauf les groupes techniques (lldap_*) et les groupes
# exclus (administrateurs) ; ceux-là se gèrent dans l'interface de LLDAP. Descriptions affichées si connues.
GROUPES_EXCLUS = set(os.environ.get("GROUPES_EXCLUS", "admins").split())
DESCRIPTIONS = json.loads(os.environ.get("GROUPES_DESCRIPTIONS", "{}"))
DUREE_LIEN = os.environ.get("DUREE_LIEN_HEURES", "12")
LIEN_ANNUAIRE = os.environ.get("LIEN_ANNUAIRE", "")
STATIQUE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "statique")
FICHIERS_STATIQUES = {
    "comptes.css": "text/css; charset=utf-8",
    "comptes.js": "text/javascript; charset=utf-8",
    "favicon.svg": "image/svg+xml",
}
CSP = ("default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; form-action 'self'; "
       "frame-ancestors 'none'; base-uri 'none'")
MOTIF_IDENTIFIANT = re.compile(r"^[a-z0-9][a-z0-9._-]{1,31}$")
MOTIF_EMAIL = re.compile(r"^[^@\s]{1,64}@[^@\s]+\.[^@\s]{2,}$")
# Quotas : drive (API de provisionnement de Nextcloud, compte sous-administrateur des groupes de la famille) et photos
# (API d'administration d'Immich, clé limitée aux comptes). Chaque service n'est actif que si son secret est présent.
NEXTCLOUD_URL = os.environ.get("NEXTCLOUD_URL", "").rstrip("/")
NEXTCLOUD_HOTE = os.environ.get("NEXTCLOUD_HOTE", "")
NEXTCLOUD_UTILISATEUR = os.environ.get("NEXTCLOUD_UTILISATEUR", "")
NEXTCLOUD_MDP_FICHIER = os.environ.get("NEXTCLOUD_MOT_DE_PASSE_FICHIER", "")
IMMICH_URL = os.environ.get("IMMICH_URL", "").rstrip("/")
IMMICH_CLE_FICHIER = os.environ.get("IMMICH_CLE_FICHIER", "")
GIO = 1024 ** 3
QUOTA_MAX_GO = 10_000


class Refus(Exception):
    """Erreur à montrer telle quelle à l'administrateur."""


def journal(**champs):
    champs = {"quand": datetime.now(timezone.utc).isoformat(timespec="seconds"), **champs}
    print(json.dumps(champs, ensure_ascii=False), flush=True)


def appel(url, donnees=None, entetes=None):
    corps = json.dumps(donnees).encode() if donnees is not None else None
    requete = urllib.request.Request(url, data=corps, headers={"Content-Type": "application/json", **(entetes or {})},
                                     method="POST" if corps is not None else "GET")
    with urllib.request.urlopen(requete, timeout=15) as reponse:
        texte = reponse.read()
    return json.loads(texte) if texte else {}


class Annuaire:
    """Session d'administration LLDAP (GraphQL), ouverte le temps d'une requête."""

    def __enter__(self):
        with open(LLDAP_MDP_FICHIER, encoding="utf-8") as fichier:
            mot_de_passe = fichier.read().strip()
        reponse = appel(f"{LLDAP}/auth/simple/login", {"username": LLDAP_UTILISATEUR, "password": mot_de_passe})
        self.jeton, self.renouvellement = reponse["token"], reponse.get("refreshToken", "")
        return self

    def __exit__(self, *erreur):
        try:
            requete = urllib.request.Request(f"{LLDAP}/auth/logout", headers={
                "Authorization": f"Bearer {self.jeton}", "Cookie": f"refresh_token={self.renouvellement}"})
            urllib.request.urlopen(requete, timeout=5).close()
        except (urllib.error.URLError, OSError):
            pass

    def gql(self, requete, variables=None):
        reponse = appel(f"{LLDAP}/api/graphql", {"query": requete, "variables": variables or {}},
                        {"Authorization": f"Bearer {self.jeton}"})
        if reponse.get("errors"):
            raise RuntimeError(reponse["errors"][0].get("message", "erreur GraphQL"))
        return reponse["data"]

    def etat(self):
        donnees = self.gql("{ users { id email displayName creationDate groups { displayName } } "
                           "groups { id displayName } }")
        return donnees["users"], {g["displayName"]: g["id"] for g in donnees["groups"]}


def proposables(groupes):
    """Groupes que la page peut attribuer, dans l'ordre alphabétique."""
    return sorted(g for g in groupes if not g.startswith("lldap_") and g not in GROUPES_EXCLUS)


def membres(comptes):
    """Comptes de personnes : sans les comptes techniques (groupes lldap_*), triés par nom."""
    personnes = [c for c in comptes if not any(g["displayName"].startswith("lldap_") for g in c["groups"])]
    return sorted(personnes, key=lambda c: (c["displayName"] or c["id"]).casefold())


def envoyer_lien(identifiant, adresse_client):
    """Demande à Authelia le lien « choisir son mot de passe » (le même que « mot de passe oublié »)."""
    portail = urllib.parse.urlsplit(PORTAIL)
    reponse = appel(f"{AUTHELIA}/api/reset-password/identity/start", {"username": identifiant}, {
        "X-Forwarded-Proto": portail.scheme, "X-Forwarded-Host": portail.netloc, "X-Forwarded-For": adresse_client})
    if reponse.get("status") != "OK":
        raise Refus("Authelia a refusé l'envoi du lien (voir ses journaux).")


def inviter(formulaire, admin, adresse_client):
    prenom = formulaire.get("prenom", "").strip()
    nom = formulaire.get("nom", "").strip()
    email = formulaire.get("email", "").strip().lower()
    identifiant = formulaire.get("identifiant", "").strip().lower()
    groupes = list(dict.fromkeys(formulaire.get("groupes", [])))
    if not prenom or len(prenom) > 64 or len(nom) > 64:
        raise Refus("Indiquez un prénom (64 caractères au plus, comme le nom).")
    if not MOTIF_IDENTIFIANT.match(identifiant):
        raise Refus("Identifiant invalide : 2 à 32 caractères, minuscules, chiffres, « . », « _ » ou « - ».")
    if len(email) > 254 or not MOTIF_EMAIL.match(email):
        raise Refus("Adresse e-mail invalide.")
    if not groupes:
        raise Refus("Choisissez au moins un groupe.")
    with Annuaire() as annuaire:
        comptes, tous_groupes = annuaire.etat()
        if any(c["id"] == identifiant for c in comptes):
            raise Refus(f"L'identifiant « {identifiant} » est déjà pris.")
        if any((c["email"] or "").lower() == email for c in comptes):
            raise Refus("Cette adresse e-mail est déjà utilisée par un autre compte.")
        interdits = [g for g in groupes if g not in proposables(tous_groupes)]
        if interdits:
            raise Refus(f"Groupe non attribuable ici : {', '.join(interdits)} (voir l'interface de l'annuaire).")
        nom_affiche = f"{prenom} {nom}".strip()
        annuaire.gql("mutation($u: CreateUserInput!) { createUser(user: $u) { id } }",
                     {"u": {"id": identifiant, "email": email, "displayName": nom_affiche,
                            "firstName": prenom, "lastName": nom}})
        for groupe in groupes:
            annuaire.gql("mutation($u: String!, $g: Int!) { addUserToGroup(userId: $u, groupId: $g) { ok } }",
                         {"u": identifiant, "g": tous_groupes[groupe]})
    journal(admin=admin, action="creation", compte=identifiant, groupes=groupes)
    try:
        envoyer_lien(identifiant, adresse_client)
    except (Refus, urllib.error.URLError, OSError, KeyError) as erreur:
        journal(admin=admin, action="erreur", compte=identifiant, detail=f"lien : {erreur}")
        raise Refus(f"Compte « {identifiant} » créé, mais l'envoi du lien a échoué : "
                    "réessayez avec « Renvoyer un lien » ci-dessous.") from erreur
    journal(admin=admin, action="invitation", compte=identifiant)
    return identifiant, email


def renvoyer(formulaire, admin, adresse_client):
    identifiant = formulaire.get("identifiant", "").strip()
    with Annuaire() as annuaire:
        compte = next((c for c in membres(annuaire.etat()[0]) if c["id"] == identifiant), None)
    if compte is None:
        raise Refus("Compte inconnu, ou compte technique (à gérer dans l'interface de LLDAP).")
    envoyer_lien(identifiant, adresse_client)
    journal(admin=admin, action="lien", compte=identifiant)
    return identifiant, compte["email"]


# --- Espace de stockage (quotas du drive et des photos) ---------------------------------------------------------

def lire_secret(chemin):
    try:
        with open(chemin, encoding="utf-8") as fichier:
            return fichier.read().strip()
    except (OSError, TypeError):
        return ""


class Indisponible(Exception):
    """Service de stockage injoignable ou refusant l'accès."""


class Drive:
    """Nextcloud : compte sous-administrateur des groupes de la famille (ni administrateurs ni autres groupes)."""

    nom = "drive"

    def __init__(self):
        self.mot_de_passe = lire_secret(NEXTCLOUD_MDP_FICHIER) if NEXTCLOUD_URL and NEXTCLOUD_UTILISATEUR else ""
        self.actif = bool(self.mot_de_passe)

    def _appel(self, methode, identifiant, donnees=None):
        jeton = base64.b64encode(f"{NEXTCLOUD_UTILISATEUR}:{self.mot_de_passe}".encode()).decode()
        requete = urllib.request.Request(
            f"{NEXTCLOUD_URL}/ocs/v2.php/cloud/users/{urllib.parse.quote(identifiant)}?format=json", method=methode,
            data=urllib.parse.urlencode(donnees).encode() if donnees else None,
            headers={"OCS-APIRequest": "true", "Authorization": f"Basic {jeton}", "Host": NEXTCLOUD_HOTE,
                     "Accept": "application/json", "Content-Type": "application/x-www-form-urlencoded"})
        try:
            with urllib.request.urlopen(requete, timeout=5) as reponse:
                return json.load(reponse)["ocs"]
        except urllib.error.HTTPError as erreur:
            if erreur.code in (403, 404):
                return None   # pas encore de compte, ou administrateur (hors délégation)
            raise Indisponible(f"Nextcloud : HTTP {erreur.code}") from erreur
        except (urllib.error.URLError, OSError, ValueError, KeyError) as erreur:
            raise Indisponible(f"Nextcloud : {erreur}") from erreur

    def espaces(self, comptes):
        resultat = {}
        for compte in comptes:
            ocs = self._appel("GET", compte["id"])
            if ocs:
                quota = ocs["data"].get("quota", {})
                total = quota.get("quota")
                resultat[compte["id"]] = {"utilise": quota.get("used", 0),
                                         "quota": total if isinstance(total, (int, float)) and total >= 0 else None}
        return resultat

    def fixer(self, compte, cible, octets):
        ocs = self._appel("PUT", compte["id"], {"key": "quota", "value": "none" if octets is None else str(octets)})
        if not ocs or ocs.get("meta", {}).get("statuscode") not in (100, 200):
            raise Refus("Nextcloud a refusé le quota (compte administrateur ou hors des groupes délégués).")


class Photos:
    """Immich : clé d'API d'un administrateur, limitée à la lecture et à la modification des comptes."""

    nom = "photos"

    def __init__(self):
        self.cle = lire_secret(IMMICH_CLE_FICHIER) if IMMICH_URL else ""
        self.actif = bool(self.cle)

    def _appel(self, methode, chemin, donnees=None):
        requete = urllib.request.Request(
            f"{IMMICH_URL}{chemin}", method=methode, data=json.dumps(donnees).encode() if donnees is not None else None,
            headers={"x-api-key": self.cle, "Accept": "application/json", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(requete, timeout=5) as reponse:
                return json.load(reponse)
        except urllib.error.HTTPError as erreur:
            raise Indisponible(f"Immich : HTTP {erreur.code}") from erreur
        except (urllib.error.URLError, OSError, ValueError) as erreur:
            raise Indisponible(f"Immich : {erreur}") from erreur

    def espaces(self, comptes):
        par_email = {u["email"].lower(): u for u in self._appel("GET", "/api/admin/users")}
        resultat = {}
        for compte in comptes:
            utilisateur = par_email.get((compte["email"] or "").lower())
            if utilisateur:
                resultat[compte["id"]] = {"utilise": utilisateur.get("quotaUsageInBytes") or 0,
                                         "quota": utilisateur.get("quotaSizeInBytes"), "id": utilisateur["id"]}
        return resultat

    def fixer(self, compte, cible, octets):
        self._appel("PUT", f"/api/admin/users/{cible['id']}", {"quotaSizeInBytes": octets})


def etat_stockage(comptes):
    """Espace de chaque membre par service ; un service injoignable est signalé sans bloquer la page."""
    services = {}
    for service in (Drive(), Photos()):
        if not service.actif:
            services[service.nom] = {"etat": "non configuré", "espaces": {}}
            continue
        try:
            services[service.nom] = {"etat": "ok", "espaces": service.espaces(comptes)}
        except Indisponible as erreur:
            journal(action="erreur", detail=str(erreur))
            services[service.nom] = {"etat": "injoignable", "espaces": {}}
    return services


def octets_depuis(valeur):
    valeur = (valeur or "").strip().replace(",", ".")
    if not valeur:
        return None
    try:
        go = float(valeur)
    except ValueError:
        raise Refus("Quota invalide : un nombre de Go, ou vide pour « illimité ».") from None
    if not 1 <= go <= QUOTA_MAX_GO:
        raise Refus(f"Quota invalide : entre 1 et {QUOTA_MAX_GO} Go (vide = illimité).")
    return int(go * GIO)


def modifier_quotas(formulaire, admin, adresse_client):
    identifiant = formulaire.get("identifiant", "").strip()
    with Annuaire() as annuaire:
        compte = next((c for c in membres(annuaire.etat()[0]) if c["id"] == identifiant), None)
    if compte is None:
        raise Refus("Compte inconnu, ou compte technique.")
    changements = []
    for service in (Drive(), Photos()):
        if not service.actif or service.nom not in formulaire:
            continue
        voulu = octets_depuis(formulaire[service.nom])
        try:
            cible = service.espaces([compte]).get(compte["id"])
            if cible is None or cible["quota"] == voulu:
                continue
            service.fixer(compte, cible, voulu)
        except Indisponible as erreur:
            raise Refus(f"{erreur} : quota non modifié.") from erreur
        changements.append(service.nom)
        journal(admin=admin, action="quota", compte=identifiant, service=service.nom,
                quota_go=None if voulu is None else round(voulu / GIO, 2))
    return identifiant, ", ".join(changements) or "aucun changement"


# --- Page ----------------------------------------------------------------------------------------------------

def e(texte):
    return html.escape(str(texte or ""), quote=True)


def date_courte(valeur):
    try:
        return datetime.fromisoformat(valeur.replace("Z", "+00:00")).strftime("%d/%m/%Y")
    except (AttributeError, ValueError):
        return ""


def taille(octets):
    return f"{(octets or 0) / GIO:.1f}".replace(".", ",") + " Go"


def cellule_quota(service, compte, stockage):
    etat = stockage.get(service, {"etat": "non configuré", "espaces": {}})
    if etat["etat"] != "ok":
        return f'<td class="mono">{e(etat["etat"])}</td>'
    espace = etat["espaces"].get(compte["id"])
    if espace is None:
        return '<td class="discret" title="Aucun compte (première connexion à venir) ou compte administrateur">—</td>'
    quota = espace["quota"]
    valeur = "" if quota is None else f"{quota / GIO:g}"
    return (f'<td><div class="quota"><input type="number" name="{service}" form="q-{e(compte["id"])}" min="1" '
            f'max="{QUOTA_MAX_GO}" step="any" inputmode="decimal" value="{e(valeur)}" placeholder="illimité" '
            f'aria-label="Quota {service} (Go)"><span>Go</span></div>'
            f'<small>{taille(espace["utilise"])} utilisés</small></td>')


def page(admin, comptes, groupes, message=None, formulaire=None, stockage=None):
    stockage = stockage or {}
    formulaire = formulaire or {}
    coches = formulaire.get("groupes", ["famille"])
    alerte = ""
    if message:
        genre, texte = message
        alerte = f'<p class="message message--{genre}" role="status">{texte}</p>'
    choix_groupes = "".join(
        f'<label class="choix"><input type="checkbox" name="groupes" value="{e(g)}"{" checked" if g in coches else ""}>'
        f'<span><strong>{e(g)}</strong><small>{e(DESCRIPTIONS.get(g, ""))}</small></span></label>' for g in groupes)
    lignes = "".join(
        f'<tr><td><strong>{e(c["displayName"] or c["id"])}</strong></td><td class="mono">{e(c["id"])}</td>'
        f'<td>{e(c["email"])}</td>'
        f'<td>{"".join(f"<span class=puce>{e(g["displayName"])}</span>" for g in c["groups"]) or "—"}</td>'
        f'<td class="mono">{date_courte(c.get("creationDate"))}</td>'
        f'<td><form method="post" action="/lien"><input type="hidden" name="identifiant" value="{e(c["id"])}">'
        f'<button class="bouton bouton--discret" type="submit">Renvoyer un lien</button></form></td></tr>'
        for c in comptes)
    lignes_espace = "".join(
        f'<tr><td><strong>{e(c["displayName"] or c["id"])}</strong><br><small class="mono">{e(c["id"])}</small></td>'
        f'{cellule_quota("drive", c, stockage)}{cellule_quota("photos", c, stockage)}'
        f'<td><form method="post" action="/quotas" id="q-{e(c["id"])}"><input type="hidden" name="identifiant" '
        f'value="{e(c["id"])}"><button class="bouton bouton--discret" type="submit">Enregistrer</button></form></td></tr>'
        for c in comptes)
    annuaire = (f'<p class="pied__note">Groupes, suppression, comptes techniques : '
                f'<a href="{e(LIEN_ANNUAIRE)}">interface de l\'annuaire</a>.</p>' if LIEN_ANNUAIRE else "")
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Comptes · homelab</title>
<link rel="icon" href="/statique/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/statique/comptes.css">
<script src="/statique/comptes.js" defer></script>
</head>
<body>
<div class="halos" aria-hidden="true"><span></span><span></span></div>
<header class="entete">
  <div class="enveloppe entete__barre">
    <a class="marque" href="/" aria-label="Comptes du homelab, accueil">
      <span class="marque__logo" aria-hidden="true"><svg viewBox="0 0 32 32"><path d="M8 22V10l8 7 8-7v12"/></svg></span>
      <span class="marque__nom">maxime<span class="marque__point">.</span>bertrand</span>
      <span class="marque__tag">comptes</span>
    </a>
    <div class="entete__droite">
      <span class="utilisateur">{e(admin)}</span>
      <a class="lien-discret" href="{e(PORTAIL)}/logout">Se déconnecter</a>
    </div>
  </div>
</header>
<main class="enveloppe">
  <section class="accroche">
    <p class="surtitre">Annuaire du homelab</p>
    <h1>Comptes</h1>
    <p class="accroche__texte">La personne invitée reçoit un e-mail avec un lien personnel, à usage unique et valable
    {e(DUREE_LIEN)} heures, pour choisir elle-même son mot de passe. Aucun mot de passe ne transite.</p>
  </section>
  {alerte}
  <section class="carte" aria-labelledby="titre-invitation">
    <h2 id="titre-invitation">Inviter quelqu'un</h2>
    <form method="post" action="/inviter" class="formulaire" id="formulaire-invitation">
      <label class="champ"><span>Prénom</span>
        <input id="prenom" name="prenom" required maxlength="64" autocomplete="off" value="{e(formulaire.get("prenom"))}"></label>
      <label class="champ"><span>Nom</span>
        <input id="nom" name="nom" maxlength="64" autocomplete="off" value="{e(formulaire.get("nom"))}"></label>
      <label class="champ"><span>E-mail</span>
        <input name="email" type="email" required maxlength="254" autocomplete="off" value="{e(formulaire.get("email"))}"></label>
      <label class="champ"><span>Identifiant</span>
        <input id="identifiant" name="identifiant" required pattern="[a-z0-9][a-z0-9._\\-]{{1,31}}" maxlength="32"
          autocomplete="off" spellcheck="false" value="{e(formulaire.get("identifiant"))}">
        <small>Pour se connecter : minuscules, chiffres, « . », « _ » ou « - ».</small></label>
      <fieldset class="groupes"><legend>Accès</legend>{choix_groupes}</fieldset>
      <div class="formulaire__actions">
        <button class="bouton" type="submit">Créer le compte et envoyer l'invitation</button>
      </div>
    </form>
  </section>
  <section class="carte" aria-labelledby="titre-membres">
    <div class="carte__titre">
      <h2 id="titre-membres">Membres</h2>
      <p>Renvoyer un lien : invitation expirée ou mot de passe oublié.</p>
    </div>
    <div class="tableau-defilant">
      <table>
        <thead><tr><th>Nom</th><th>Identifiant</th><th>E-mail</th><th>Groupes</th><th>Créé le</th><th></th></tr></thead>
        <tbody>{lignes or '<tr><td colspan="6">Aucun compte.</td></tr>'}</tbody>
      </table>
    </div>
  </section>
  <section class="carte" id="espace" aria-labelledby="titre-espace">
    <div class="carte__titre">
      <h2 id="titre-espace">Espace de stockage</h2>
      <p>Quota en Go, appliqué aussitôt ; vide = illimité. « — » : pas encore de compte, ou administrateur.</p>
    </div>
    <div class="tableau-defilant">
      <table>
        <thead><tr><th>Membre</th><th>Drive</th><th>Photos</th><th></th></tr></thead>
        <tbody>{lignes_espace or '<tr><td colspan="4">Aucun compte.</td></tr>'}</tbody>
      </table>
    </div>
  </section>
  {annuaire}
</main>
</body>
</html>
"""


class Gestionnaire(http.server.BaseHTTPRequestHandler):
    server_version = "comptes"
    sys_version = ""

    def log_message(self, format, *args):  # noqa: A002 - signature imposée ; journal applicatif seulement
        pass

    def envoyer(self, code, corps=b"", type_contenu="text/html; charset=utf-8", entetes=None):
        self.send_response(code)
        self.send_header("Content-Type", type_contenu)
        self.send_header("Content-Length", str(len(corps)))
        self.send_header("Content-Security-Policy", CSP)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        for cle, valeur in (entetes or {"Cache-Control": "no-store"}).items():
            self.send_header(cle, valeur)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(corps)

    def entete(self, nom):
        """En-tête transmis en UTF-8 (noms accentués), lu en latin-1 par http.server."""
        valeur = self.headers.get(nom, "")
        try:
            return valeur.encode("latin-1").decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            return valeur

    def administrateur(self):
        """Identifiant fourni par le proxy (SSO) ; None si la requête ne vient pas du proxy ou d'un administrateur."""
        source = ipaddress.ip_address(self.client_address[0])
        utilisateur = self.entete("Remote-User")
        groupes = [g.strip() for g in self.entete("Remote-Groups").split(",")]
        if not any(source in reseau for reseau in SOURCES) or not utilisateur or GROUPE_ADMIN not in groupes:
            journal(action="refus", source=str(source), utilisateur=utilisateur)
            self.envoyer(403, "Accès réservé aux administrateurs, par le proxy interne.".encode(),
                         "text/plain; charset=utf-8")
            return None
        self.nom_admin = self.entete("Remote-Name") or utilisateur
        return utilisateur

    def adresse_client(self):
        return (self.headers.get("X-Forwarded-For", "").split(",")[0].strip() or self.client_address[0])[:45]

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        chemin = urllib.parse.urlsplit(self.path).path
        if chemin == "/sante":
            return self.envoyer(200, b"ok\n", "text/plain; charset=utf-8")
        if chemin.startswith("/statique/") and chemin[10:] in FICHIERS_STATIQUES:
            with open(os.path.join(STATIQUE, chemin[10:]), "rb") as fichier:
                return self.envoyer(200, fichier.read(), FICHIERS_STATIQUES[chemin[10:]],
                                    {"Cache-Control": "public, max-age=3600"})
        admin = self.administrateur()
        if admin is None:
            return None
        if chemin != "/":
            return self.envoyer(404, "Page introuvable.".encode(), "text/plain; charset=utf-8")
        message = None
        parametres = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
        compte, email = parametres.get("compte", [""])[0], parametres.get("email", [""])[0]
        if parametres.get("fait") == ["invitation"]:
            message = ("ok", f"Compte <strong>{e(compte)}</strong> créé : invitation envoyée à {e(email)}.")
        elif parametres.get("fait") == ["lien"]:
            message = ("ok", f"Lien envoyé à {e(email)} (compte <strong>{e(compte)}</strong>).")
        elif parametres.get("fait") == ["quotas"]:
            message = ("ok", f"Quotas de <strong>{e(compte)}</strong> : {e(email)}.")
        return self.afficher(admin, message)

    def afficher(self, admin, message=None, formulaire=None, code=200):
        try:
            with Annuaire() as annuaire:
                comptes, groupes = annuaire.etat()
            comptes, groupes = membres(comptes), proposables(groupes)
        except (urllib.error.URLError, OSError, RuntimeError, KeyError) as erreur:
            journal(action="erreur", detail=f"annuaire : {erreur}")
            comptes, groupes, message = [], [], ("erreur", "Annuaire injoignable : réessayez dans un instant.")
        stockage = etat_stockage(comptes)
        return self.envoyer(code, page(self.nom_admin, comptes, groupes, message, formulaire, stockage).encode())

    def do_POST(self):
        admin = self.administrateur()
        if admin is None:
            return None
        # Formulaires de cette page uniquement (en plus du cookie SSO « SameSite=Lax ») : refus des envois intersites.
        origine = self.headers.get("Origin", "")
        site = self.headers.get("Sec-Fetch-Site", "")
        if site not in ("same-origin", "") or (origine and origine != f"https://{self.headers.get('Host', '')}") \
                or not (site or origine):
            journal(action="refus", admin=admin, detail="requête intersite")
            return self.envoyer(403, "Requête refusée (origine).".encode(), "text/plain; charset=utf-8")
        longueur = int(self.headers.get("Content-Length") or 0)
        if longueur > 4096 or not self.headers.get("Content-Type", "").startswith("application/x-www-form-urlencoded"):
            return self.envoyer(400, "Requête invalide.".encode(), "text/plain; charset=utf-8")
        # Champs vides conservés : un quota vidé signifie « illimité ».
        champs = urllib.parse.parse_qs(self.rfile.read(longueur).decode("utf-8", "replace"), keep_blank_values=True,
                                       max_num_fields=20)
        formulaire = {cle: valeurs[0] for cle, valeurs in champs.items() if cle != "groupes"}
        formulaire["groupes"] = champs.get("groupes", [])
        chemin = urllib.parse.urlsplit(self.path).path
        actions = {"/inviter": ("invitation", inviter), "/lien": ("lien", renvoyer),
                   "/quotas": ("quotas", modifier_quotas)}
        if chemin not in actions:
            return self.envoyer(404, "Page introuvable.".encode(), "text/plain; charset=utf-8")
        fait, action = actions[chemin]
        try:
            compte, email = action(formulaire, admin, self.adresse_client())
        except Refus as refus:
            return self.afficher(admin, ("erreur", e(refus)), formulaire if fait == "invitation" else None, 422)
        except (urllib.error.URLError, OSError, RuntimeError, KeyError) as erreur:
            journal(action="erreur", admin=admin, detail=str(erreur))
            return self.afficher(admin, ("erreur", "Échec de l'opération (voir les journaux du conteneur)."),
                                 formulaire if fait == "invitation" else None, 502)
        suite = urllib.parse.urlencode({"fait": fait, "compte": compte, "email": email})
        ancre = "#espace" if fait == "quotas" else ""
        return self.envoyer(303, b"", entetes={"Location": f"/?{suite}{ancre}", "Cache-Control": "no-store"})


if __name__ == "__main__":
    serveur = http.server.ThreadingHTTPServer(("0.0.0.0", 8080), Gestionnaire)
    journal(action="demarrage", sources=[str(s) for s in SOURCES], exclus=sorted(GROUPES_EXCLUS),
            quotas={"drive": Drive().actif, "photos": Photos().actif})
    serveur.serve_forever()
