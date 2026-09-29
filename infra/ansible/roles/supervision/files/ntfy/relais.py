#!/usr/bin/env python3
"""Relais des notifications sur téléphone : webhook d'Alertmanager -> ntfy, message mis en forme ici.

Le modèle « alertmanager » intégré à ntfy a un délai de rendu de 100 ms codé en dur ; sur la VM de supervision,
souvent en attente du disque, il est parfois dépassé : ntfy répond 400 et Alertmanager ne réessaie jamais un 4xx
(notifications perdues, constaté le 29/09). Ici, pas de modèle côté ntfy : titre, priorité et texte sont envoyés tels
quels, avec plusieurs essais. Écoute sur le réseau Docker de la supervision (port non publié).

  POST /alertmanager?priorite=high&prefixe=ALERTE    (priorite : min à urgent ; prefixe : ALERTE, SECURITE, VEILLE, INFO)
"""

import base64
import http.server
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

NTFY = os.environ.get("NTFY_URL", "http://ntfy").rstrip("/")
SUJET = os.environ["SUJET"]
LIEN = os.environ.get("LIEN", "")
with open(os.environ["FICHIER_MOT_DE_PASSE"], encoding="utf-8") as fichier:
    IDENTIFIANTS = base64.b64encode(f"alertmanager:{fichier.read().strip()}".encode()).decode()
PRIORITES = {"min", "low", "default", "high", "urgent"}
PREFIXES = {"ALERTE": "ALERTE", "SECURITE": "SÉCURITÉ", "VEILLE": "VEILLE", "INFO": "INFO"}
ESSAIS = 4


def journal(**champs):
    print(json.dumps({"quand": datetime.now(timezone.utc).isoformat(timespec="seconds"), **champs},
                     ensure_ascii=False), flush=True)


def mettre_en_forme(charge, prefixe):
    alertes = charge.get("alerts", [])
    en_cours = [a for a in alertes if a.get("status") != "resolved"]
    communes = charge.get("commonLabels", {})
    nom = communes.get("alertname") or (alertes[0]["labels"].get("alertname", "?") if alertes else "?")
    instance = communes.get("instance", "")
    etat = prefixe if en_cours else "RÉSOLU"
    titre = f"[{etat}] {nom}" + (f" — {instance}" if instance else "") + (f" ({len(alertes)})" if len(alertes) > 1 else "")
    lignes = []
    for alerte in (en_cours or alertes)[:15]:
        etiquettes, notes = alerte.get("labels", {}), alerte.get("annotations", {})
        resume = notes.get("resume") or notes.get("summary") or etiquettes.get("alertname", "")
        description = notes.get("description", "")
        lignes.append(f"• {resume}" + (f"\n  {description}" if description and len(alertes) <= 3 else ""))
    if len(alertes) > 15:
        lignes.append(f"… et {len(alertes) - 15} autre(s)")
    return titre, "\n".join(lignes)[:3900]


def envoyer(titre, message, priorite, etiquette):
    # Titre accentué : passé en paramètre d'adresse (UTF-8), les en-têtes HTTP n'acceptant que le latin-1.
    parametres = {"title": titre, "priority": priorite, "tags": etiquette, **({"click": LIEN} if LIEN else {})}
    adresse = f"{NTFY}/{SUJET}?" + urllib.parse.urlencode(parametres)
    entetes = {"Authorization": f"Basic {IDENTIFIANTS}", "Content-Type": "text/plain; charset=utf-8"}
    code, delai = 0, 1.0
    for essai in range(1, ESSAIS + 1):
        requete = urllib.request.Request(adresse, data=message.encode(), headers=entetes, method="POST")
        try:
            with urllib.request.urlopen(requete, timeout=10) as reponse:
                return reponse.status, essai
        except urllib.error.HTTPError as erreur:
            code = erreur.code
            if code in (401, 403):  # identifiants refusés : inutile d'insister
                return code, essai
        except (urllib.error.URLError, OSError):
            code = 0
        time.sleep(delai)
        delai *= 2
    return code, ESSAIS


class Gestionnaire(http.server.BaseHTTPRequestHandler):
    server_version = "relais-ntfy"
    sys_version = ""

    def log_message(self, format, *args):  # noqa: A002 - signature imposée ; journal applicatif seulement
        pass

    def repondre(self, code, texte):
        corps = texte.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        return self.repondre(200 if self.path == "/sante" else 404, "ok\n" if self.path == "/sante" else "introuvable\n")

    def do_POST(self):
        adresse = urllib.parse.urlsplit(self.path)
        if adresse.path != "/alertmanager":
            return self.repondre(404, "introuvable\n")
        parametres = dict(urllib.parse.parse_qsl(adresse.query))
        priorite = parametres.get("priorite", "default")
        priorite = priorite if priorite in PRIORITES else "default"
        prefixe = PREFIXES.get(parametres.get("prefixe", "ALERTE"), "ALERTE")
        try:
            charge = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length") or 0), 1_000_000)))
        except ValueError:
            return self.repondre(400, "JSON invalide\n")
        titre, message = mettre_en_forme(charge, prefixe)
        resolu = charge.get("status") == "resolved"
        code, essais = envoyer(titre, message, "default" if resolu else priorite,
                               "white_check_mark" if resolu else "rotating_light")
        journal(action="ntfy", groupe=charge.get("groupKey", ""), statut=charge.get("status", ""),
                alertes=len(charge.get("alerts", [])), ntfy=code, essais=essais)
        # Échec après plusieurs essais : 503, pour qu'Alertmanager réessaie plus tard.
        return self.repondre(200, "envoyé\n") if code == 200 else self.repondre(503, f"ntfy : {code}\n")


if __name__ == "__main__":
    journal(action="demarrage", ntfy=NTFY, sujet=SUJET)
    http.server.ThreadingHTTPServer(("0.0.0.0", 8080), Gestionnaire).serve_forever()
