"""Annonces aux membres : maintenance prévue, incident en cours, résolution, information.

Publiées depuis la page des comptes (ou en ligne de commande dans le conteneur, publier.py) : un e-mail par personne
(personne ne voit les adresses des autres), selon les groupes visés, et un bandeau sur la page d'accueil jusqu'à la fin
prévue ou jusqu'à ce qu'il soit retiré. Historique dans un fichier JSON (volume du conteneur). Bibliothèque standard.
"""

import html
import json
import os
import secrets
import smtplib
import ssl
import threading
from datetime import datetime, timedelta
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

import bienvenue

FICHIER = os.environ.get("ANNONCES_FICHIER", "/donnees/annonces.json")
TYPES = {
    "maintenance": {"libelle": "Maintenance prévue", "couleur": "#b45309", "fond": "#fef3c7"},
    "incident": {"libelle": "Incident en cours", "couleur": "#b91c1c", "fond": "#fee2e2"},
    "resolu": {"libelle": "Résolu", "couleur": "#047857", "fond": "#d1fae5"},
    "info": {"libelle": "Information", "couleur": "#1d4ed8", "fond": "#dbeafe"},
}
# Bandeau sans fin prévue : une résolution ou une information s'efface d'elle-même, un incident ou une maintenance
# reste affiché jusqu'à son retrait (ou jusqu'à l'annonce « Résolu » qui le clôt).
DUREE_BANDEAU = {"resolu": timedelta(hours=24), "info": timedelta(days=3)}
TITRE_MAX, MESSAGE_MAX, DESTINATAIRES_MAX, HISTORIQUE_MAX = 120, 3000, 200, 200
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre",
        "décembre"]
_verrou = threading.Lock()


class Invalide(Exception):
    """Annonce refusée : message à montrer tel quel."""


# --- Stockage ------------------------------------------------------------------------------------------------

def charger():
    try:
        with open(FICHIER, encoding="utf-8") as fichier:
            return json.load(fichier)
    except FileNotFoundError:
        return []


def _ecrire(annonces):
    provisoire = f"{FICHIER}.{os.getpid()}.tmp"
    with open(provisoire, "w", encoding="utf-8") as fichier:
        json.dump(annonces[:HISTORIQUE_MAX], fichier, ensure_ascii=False, indent=1)
    os.replace(provisoire, FICHIER)


def modifier(fonction):
    """Lit, modifie et réécrit l'historique sous verrou (serveur à fils multiples)."""
    with _verrou:
        annonces = charger()
        resultat = fonction(annonces)
        _ecrire(annonces)
    return resultat


# --- Dates ---------------------------------------------------------------------------------------------------

def maintenant():
    return datetime.now().astimezone()


def lire_date(valeur):
    """Date d'un champ « datetime-local » (heure locale du conteneur, TZ) ; vide = None."""
    valeur = (valeur or "").strip()
    if not valeur:
        return None
    try:
        return datetime.fromisoformat(valeur).astimezone()
    except ValueError:
        raise Invalide(f"Date invalide : « {valeur} ».") from None


def date_humaine(date, avec_jour=True):
    heure = f"{date.hour} h {date.minute:02d}"
    if not avec_jour:
        return heure
    jour = "1er" if date.day == 1 else str(date.day)
    return f"{JOURS[date.weekday()]} {jour} {MOIS[date.month - 1]} à {heure}"


def periode(annonce):
    debut = datetime.fromisoformat(annonce["debut"]) if annonce.get("debut") else None
    fin = datetime.fromisoformat(annonce["fin"]) if annonce.get("fin") else None
    if debut and fin:
        if debut.date() == fin.date():
            return f"{date_humaine(debut)} → {date_humaine(fin, avec_jour=False)}"
        return f"du {date_humaine(debut)} au {date_humaine(fin)}"
    if debut:
        return f"depuis le {date_humaine(debut)}" if debut <= maintenant() else f"à partir du {date_humaine(debut)}"
    if fin:
        return f"jusqu'au {date_humaine(fin)}"
    return ""


# --- Annonces ------------------------------------------------------------------------------------------------

def noms_services(ids, catalogue):
    noms = {s["id"]: s["nom"] for s in catalogue.get("services", [])}
    return [noms[i] for i in ids if i in noms]


def preparer(champs, admin, catalogue, groupes_connus):
    """Valide le formulaire et construit l'annonce (sans l'enregistrer)."""
    genre = champs.get("type", "")
    if genre not in TYPES:
        raise Invalide("Choisissez le type d'annonce.")
    titre = " ".join((champs.get("titre") or "").split())
    if not titre or len(titre) > TITRE_MAX:
        raise Invalide(f"Indiquez un titre ({TITRE_MAX} caractères au plus).")
    message = (champs.get("message") or "").replace("\r\n", "\n").strip()
    if len(message) > MESSAGE_MAX:
        raise Invalide(f"Message trop long ({MESSAGE_MAX} caractères au plus).")
    debut, fin = lire_date(champs.get("debut")), lire_date(champs.get("fin"))
    if genre == "incident" and debut is None:
        debut = maintenant().replace(second=0, microsecond=0)
    if debut and fin and fin <= debut:
        raise Invalide("La fin doit suivre le début.")
    if genre == "maintenance" and debut is None:
        raise Invalide("Une maintenance prévue a besoin d'une date de début.")
    connus = {s["id"] for s in catalogue.get("services", [])}
    services = [s for s in dict.fromkeys(champs.get("services", [])) if s in connus]
    groupes = [g for g in dict.fromkeys(champs.get("groupes", [])) if g in groupes_connus]
    if champs.get("public") == "groupes" and not groupes:
        raise Invalide("Choisissez au moins un groupe destinataire, ou « Tout le monde ».")
    if champs.get("public") != "groupes":
        groupes = []
    courriel, bandeau = bool(champs.get("courriel")), bool(champs.get("bandeau"))
    if not (courriel or bandeau):
        raise Invalide("Cochez l'envoi par e-mail, le bandeau, ou les deux.")
    return {
        "id": maintenant().strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2),
        "type": genre, "titre": titre, "message": message, "services": services, "groupes": groupes,
        "debut": debut.isoformat(timespec="minutes") if debut else None,
        "fin": fin.isoformat(timespec="minutes") if fin else None,
        "courriel": courriel, "bandeau": bandeau, "resout": (champs.get("resout") or "").strip() or None,
        "auteur": admin, "cree_le": maintenant().isoformat(timespec="seconds"),
        "envoyes": 0, "echecs": 0, "retire_le": None,
    }


def bandeau_actif(annonce, a=None):
    a = a or maintenant()
    if not annonce.get("bandeau") or annonce.get("retire_le"):
        return False
    if annonce.get("fin"):
        return a < datetime.fromisoformat(annonce["fin"])
    duree = DUREE_BANDEAU.get(annonce["type"])
    return duree is None or a < datetime.fromisoformat(annonce["cree_le"]) + duree


def a_resoudre(annonces):
    """Incidents et maintenances encore affichés : une annonce « Résolu » peut les clore."""
    return [a for a in annonces if a["type"] in ("incident", "maintenance") and bandeau_actif(a)]


def vue_publique(annonce, catalogue):
    """Ce que montre la page d'accueil : ni auteur ni destinataires (les groupes servent au filtrage)."""
    return {"id": annonce["id"], "type": annonce["type"], "libelle": TYPES[annonce["type"]]["libelle"],
            "titre": annonce["titre"], "message": annonce["message"], "periode": periode(annonce),
            "services": noms_services(annonce["services"], catalogue), "groupes": annonce["groupes"]}


def destinataires(comptes, groupes):
    """Membres visés avec une adresse ; tous si aucun groupe n'est choisi."""
    vises = []
    for compte in comptes:
        leurs = {g["displayName"] for g in compte["groups"]}
        if compte.get("email") and (not groupes or leurs & set(groupes)):
            vises.append({"email": compte["email"], "prenom": (compte["displayName"] or compte["id"]).split(" ")[0]})
    if len(vises) > DESTINATAIRES_MAX:
        raise Invalide(f"Trop de destinataires ({len(vises)}).")
    return vises


# --- E-mail --------------------------------------------------------------------------------------------------

def e(texte):
    return html.escape(str(texte or ""), quote=True)


def sujet(annonce):
    return f"[Homelab] {TYPES[annonce['type']]['libelle']} : {annonce['titre']}"


def texte_brut(annonce, prenom, catalogue):
    lignes = [f"Bonjour {prenom},", "", f"{TYPES[annonce['type']]['libelle']} : {annonce['titre']}"]
    if periode(annonce):
        lignes.append(f"Quand : {periode(annonce)}")
    if annonce["services"]:
        lignes.append(f"Services concernés : {', '.join(noms_services(annonce['services'], catalogue))}")
    if annonce["message"]:
        lignes += ["", annonce["message"]]
    if catalogue.get("accueil"):
        lignes += ["", f"Vos services : {catalogue['accueil']}"]
    lignes += ["", f"Une question ? Contactez {bienvenue.CONTACT}.",
               "Vous recevez cet e-mail parce que vous avez un compte sur le homelab de la famille."]
    return "\n".join(lignes)


def texte_html(annonce, prenom, catalogue):
    style = TYPES[annonce["type"]]
    details = ""
    if periode(annonce):
        details += (f'<p style="margin:0 0 6px;"><strong>Quand :</strong> {e(periode(annonce))}</p>')
    if annonce["services"]:
        details += (f'<p style="margin:0 0 6px;"><strong>Services concernés :</strong> '
                    f'{e(", ".join(noms_services(annonce["services"], catalogue)))}</p>')
    paragraphes = "".join(f'<p style="margin:0 0 12px;">{e(p).replace(chr(10), "<br>")}</p>'
                          for p in annonce["message"].split("\n\n") if p.strip())
    bouton = ""
    if catalogue.get("accueil"):
        bouton = (f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" '
                  f'style="padding:8px 0 4px;"><a href="{e(catalogue["accueil"])}" style="display:inline-block;'
                  f'background-color:#2dd4bf;color:#041014;font-size:15px;font-weight:600;text-decoration:none;'
                  f'padding:12px 24px;border-radius:10px;">Ouvrir la page d\'accueil</a></td></tr></table>')
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(sujet(annonce))}</title></head>
<body style="margin:0;padding:0;background-color:#eef2f7;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#eef2f7;">
<tr><td align="center" style="padding:32px 12px;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background-color:#ffffff;border-radius:12px;overflow:hidden;">
    <tr><td style="background-color:#070b14;padding:20px 28px;">
      <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:#2dd4bf;margin-right:10px;"></span><span style="color:#e6edf7;font-size:16px;font-weight:600;">Homelab</span>
    </td></tr>
    <tr><td style="padding:28px;color:#0f172a;font-size:15px;line-height:1.6;">
      <p style="margin:0 0 14px;"><span style="display:inline-block;background-color:{style['fond']};color:{style['couleur']};font-size:13px;font-weight:700;padding:4px 10px;border-radius:999px;">{e(style['libelle'])}</span></p>
      <h1 style="margin:0 0 16px;font-size:21px;font-weight:600;">{e(annonce['titre'])}</h1>
      <p style="margin:0 0 14px;">Bonjour {e(prenom)},</p>
      <div style="margin:0 0 16px;padding:12px 16px;border-left:4px solid {style['couleur']};background-color:#f8fafc;border-radius:6px;font-size:14px;">{details or e(style['libelle'])}</div>
      {paragraphes}
      {bouton}
    </td></tr>
    <tr><td style="padding:16px 28px;background-color:#f8fafc;color:#64748b;font-size:12px;line-height:1.5;text-align:center;">
      Une question ? Contactez {e(bienvenue.CONTACT)}.<br>Vous recevez cet e-mail parce que vous avez un compte sur le homelab de la famille.
    </td></tr>
  </table>
</td></tr></table>
</body></html>
"""


def envoyer(annonce, personnes, catalogue):
    """Un e-mail par personne, dans une seule session SMTP ; renvoie (envoyés, échecs)."""
    if not personnes:
        return 0, 0
    with open(bienvenue.SMTP_MDP_FICHIER, encoding="utf-8") as fichier:
        mot_de_passe = fichier.read().strip()
    envoyes = echecs = 0
    with smtplib.SMTP(bienvenue.SMTP_SERVEUR, bienvenue.SMTP_PORT, timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(bienvenue.SMTP_UTILISATEUR, mot_de_passe)
        for personne in personnes:
            message = EmailMessage()
            message["Subject"] = sujet(annonce)
            message["From"] = formataddr(("Homelab", bienvenue.SMTP_EXPEDITEUR))
            message["To"] = personne["email"]
            message["Message-ID"] = make_msgid(domain=bienvenue.SMTP_EXPEDITEUR.split("@")[-1])
            message.set_content(texte_brut(annonce, personne["prenom"], catalogue))
            message.add_alternative(texte_html(annonce, personne["prenom"], catalogue), subtype="html")
            try:
                smtp.send_message(message)
                envoyes += 1
            except smtplib.SMTPRecipientsRefused:
                echecs += 1
    return envoyes, echecs


def publier(annonce, personnes, catalogue):
    """Envoie (si demandé), puis enregistre ; une annonce « Résolu » retire le bandeau de celle qu'elle clôt."""
    if annonce["courriel"]:
        annonce["envoyes"], annonce["echecs"] = envoyer(annonce, personnes, catalogue)

    def ajouter(annonces):
        if annonce["type"] == "resolu" and annonce["resout"]:
            for autre in annonces:
                if autre["id"] == annonce["resout"] and not autre.get("retire_le"):
                    autre["retire_le"] = annonce["cree_le"]
        annonces.insert(0, annonce)

    modifier(ajouter)
    return annonce


def retirer(identifiant):
    def fonction(annonces):
        for annonce in annonces:
            if annonce["id"] == identifiant and not annonce.get("retire_le"):
                annonce["retire_le"] = maintenant().isoformat(timespec="seconds")
                return annonce
        raise Invalide("Annonce introuvable, ou bandeau déjà retiré.")
    return modifier(fonction)
