"""E-mail de bienvenue : les services de la personne (selon ses groupes), leur mode d'emploi et la page d'accueil.

Envoyé par la page des comptes juste après l'invitation (l'e-mail « Choisir votre mot de passe » part séparément,
par Authelia) ; renvoyable depuis la page. Le catalogue des services vient de l'inventaire (fichier JSON).
"""

import html
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

SMTP_SERVEUR = os.environ.get("SMTP_SERVEUR", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_UTILISATEUR = os.environ.get("SMTP_UTILISATEUR", "")
SMTP_EXPEDITEUR = os.environ.get("SMTP_EXPEDITEUR", "")
SMTP_MDP_FICHIER = os.environ.get("SMTP_MOT_DE_PASSE_FICHIER", "")
CATALOGUE_FICHIER = os.environ.get("CATALOGUE_FICHIER", "")
CONTACT = os.environ.get("CONTACT_ADMINISTRATEUR", "l'administrateur du homelab")
REGLE_MDP = os.environ.get("REGLE_MOT_DE_PASSE", "")


def catalogue():
    try:
        with open(CATALOGUE_FICHIER, encoding="utf-8") as fichier:
            return json.load(fichier)
    except (OSError, TypeError, ValueError):
        return {}


def actif():
    return bool(SMTP_SERVEUR and SMTP_EXPEDITEUR and catalogue().get("services"))


def services_de(groupes):
    groupes = set(groupes)
    return [s for s in catalogue().get("services", []) if groupes & set(s.get("groupes", []))]


def e(texte):
    return html.escape(str(texte or ""), quote=True)


def texte_brut(prenom, identifiant, services, accueil, duree_lien):
    lignes = [f"Bonjour {prenom},", "",
              f"Un compte vient d'être créé pour vous sur le homelab de la famille. Votre identifiant : {identifiant}", "",
              "Pour commencer :",
              f"1. Choisissez votre mot de passe grâce au second e-mail « Choisir votre mot de passe » "
              f"(lien personnel, valable {duree_lien} heures)." + (f" Il doit comporter {REGLE_MDP}." if REGLE_MDP else ""),
              "2. À la première connexion, enregistrez une double authentification. Le plus simple : une clé d'accès, "
              "c'est-à-dire l'empreinte ou le visage de votre téléphone (ou le code PIN de l'ordinateur), sans "
              "application à installer. Une application de codes (Aegis, Google Authenticator…) reste possible : "
              "bouton « Méthodes » en haut du portail.",
              f"3. Tous vos services, au même endroit : {accueil}", "",
              "Vos services", "-----------"]
    for service in services:
        lignes += ["", f"{service['nom']} ({service.get('appli', '')}) : {service['url']}", service.get("description", "")]
        if service.get("connexion"):
            lignes.append(f"Connexion : {service['connexion']}")
        lignes += [f"  {n}. {etape}" for n, etape in enumerate(service.get("etapes", []), 1)]
        lignes += [f"  - {appli['nom']} : {appli['lien']}" for appli in service.get("applis", [])]
    lignes += ["", f"Une question, un souci ? Contactez {CONTACT}.",
               "Ne transférez pas les e-mails du homelab : ils sont personnels."]
    return "\n".join(lignes)


def texte_html(prenom, identifiant, services, accueil, duree_lien):
    cartes = []
    for service in services:
        etapes = "".join(f"<li style=\"margin:2px 0;\">{e(etape)}</li>" for etape in service.get("etapes", []))
        applis = "".join(f"<li style=\"margin:2px 0;\"><a href=\"{e(a['lien'])}\" style=\"color:#0f766e;\">{e(a['nom'])}</a></li>"
                         for a in service.get("applis", []))
        cartes.append(f"""
      <tr><td style="padding:14px 16px;border:1px solid #e2e8f0;border-radius:10px;">
        <p style="margin:0;font-size:16px;font-weight:700;color:#0f172a;">{e(service['nom'])}
          <span style="font-weight:400;color:#64748b;font-size:13px;">· {e(service.get('appli', ''))}</span></p>
        <p style="margin:6px 0;color:#334155;">{e(service.get('description', ''))}</p>
        <p style="margin:6px 0;"><a href="{e(service['url'])}" style="color:#0f766e;font-weight:600;">{e(service['url'])}</a></p>
        {f'<p style="margin:6px 0;font-size:13px;color:#475569;"><strong>Connexion :</strong> {e(service["connexion"])}</p>' if service.get('connexion') else ''}
        {f'<ol style="margin:6px 0 0;padding-left:20px;font-size:13px;color:#475569;">{etapes}</ol>' if etapes else ''}
        {f'<ul style="margin:6px 0 0;padding-left:20px;font-size:13px;">{applis}</ul>' if applis else ''}
      </td></tr>
      <tr><td style="height:10px;"></td></tr>""")
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Bienvenue sur le homelab</title></head>
<body style="margin:0;padding:0;background-color:#eef2f7;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#eef2f7;">
<tr><td align="center" style="padding:32px 12px;font-family:system-ui,-apple-system,'Segoe UI',Roboto,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background-color:#ffffff;border-radius:12px;overflow:hidden;">
    <tr><td style="background-color:#070b14;padding:20px 28px;">
      <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background-color:#2dd4bf;margin-right:10px;"></span><span style="color:#e6edf7;font-size:16px;font-weight:600;">Homelab</span>
    </td></tr>
    <tr><td style="padding:28px;color:#0f172a;font-size:15px;line-height:1.6;">
      <h1 style="margin:0 0 16px;font-size:22px;font-weight:600;">Bienvenue, {e(prenom)} !</h1>
      <p style="margin:0 0 14px;">Un compte vient d'être créé pour vous sur le homelab de la famille.
        Votre identifiant : <strong style="font-family:ui-monospace,Menlo,Consolas,monospace;">{e(identifiant)}</strong></p>
      <ol style="margin:0 0 18px;padding-left:20px;">
        <li style="margin:4px 0;"><strong>Choisissez votre mot de passe</strong> avec le second e-mail « Choisir votre mot de passe » (lien personnel, valable {e(duree_lien)} heures).{f" Il doit comporter <strong>{e(REGLE_MDP)}</strong>." if REGLE_MDP else ""}</li>
        <li style="margin:4px 0;">À la première connexion, <strong>enregistrez une double authentification</strong>. Le plus simple : une <strong>clé d'accès</strong>, c'est-à-dire l'empreinte ou le visage de votre téléphone (ou le code PIN de l'ordinateur), sans application à installer. Une application de codes (Aegis, Google Authenticator…) reste possible : bouton « Méthodes » en haut du portail.</li>
        <li style="margin:4px 0;">Retrouvez <strong>tous vos services</strong> sur la page d'accueil.</li>
      </ol>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0"><tr><td align="center" style="padding:4px 0 22px;">
        <a href="{e(accueil)}" style="display:inline-block;background-color:#2dd4bf;color:#041014;font-size:15px;font-weight:600;text-decoration:none;padding:13px 26px;border-radius:10px;">Ouvrir la page d'accueil</a>
      </td></tr></table>
      <h2 style="margin:0 0 12px;font-size:17px;">Vos services</h2>
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0">{''.join(cartes)}
      </table>
    </td></tr>
    <tr><td style="padding:16px 28px;background-color:#f8fafc;color:#64748b;font-size:12px;line-height:1.5;text-align:center;">
      Une question, un souci ? Contactez {e(CONTACT)}. Ne transférez pas les e-mails du homelab : ils sont personnels.
    </td></tr>
  </table>
</td></tr></table>
</body></html>
"""


def envoyer(email, prenom, identifiant, groupes, duree_lien):
    """Envoie l'e-mail de bienvenue ; renvoie la liste des services présentés."""
    services = services_de(groupes)
    accueil = catalogue().get("accueil", "")
    message = EmailMessage()
    message["Subject"] = "[Homelab] Bienvenue : vos services et comment vous connecter"
    message["From"] = formataddr(("Homelab", SMTP_EXPEDITEUR))
    message["To"] = email
    message["Message-ID"] = make_msgid(domain=SMTP_EXPEDITEUR.split("@")[-1])
    message.set_content(texte_brut(prenom, identifiant, services, accueil, duree_lien))
    message.add_alternative(texte_html(prenom, identifiant, services, accueil, duree_lien), subtype="html")
    with open(SMTP_MDP_FICHIER, encoding="utf-8") as fichier:
        mot_de_passe = fichier.read().strip()
    with smtplib.SMTP(SMTP_SERVEUR, SMTP_PORT, timeout=20) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(SMTP_UTILISATEUR, mot_de_passe)
        smtp.send_message(message)
    return [s["id"] for s in services]
