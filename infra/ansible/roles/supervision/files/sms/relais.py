#!/usr/bin/env python3
"""Relais SMS des alertes critiques : webhook d'Alertmanager -> API « Notifications par SMS » de Free Mobile.

L'API de Free n'envoie qu'au titulaire de la ligne : aucun numéro à configurer, seulement l'identifiant Free Mobile
et la clé de l'option (fichiers secrets). Écoute sur le réseau Docker de la supervision (port non publié).
Chaque SMS reste court : un titre, une ligne par alerte (nom, machine, résumé). Bibliothèque standard uniquement.
"""

import http.server
import json
import os
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

API = os.environ.get("API_FREE", "https://smsapi.free-mobile.fr/sendmsg")
LONGUEUR_MAX = 480
# Free répond 402 si les SMS sont trop rapprochés : un envoi à la fois, espacés.
INTERVALLE = float(os.environ.get("INTERVALLE_SECONDES", "5"))
CODES = {200: "envoyé", 400: "paramètre manquant", 402: "trop de SMS en peu de temps",
         403: "option non activée ou identifiants refusés", 500: "erreur chez Free"}


def lire(variable):
    with open(os.environ[variable], encoding="utf-8") as fichier:
        return fichier.read().strip()


UTILISATEUR, CLE = lire("FICHIER_UTILISATEUR"), lire("FICHIER_CLE")
verrou = threading.Lock()
dernier_envoi = 0.0


def journal(**champs):
    print(json.dumps({"quand": datetime.now(timezone.utc).isoformat(timespec="seconds"), **champs},
                     ensure_ascii=False), flush=True)


def texte(charge):
    """Message d'un groupe d'alertes d'Alertmanager."""
    alertes = charge.get("alerts", [])
    en_cours = [a for a in alertes if a.get("status") != "resolved"]
    titre = f"[ALERTE] homelab : {len(en_cours)} en cours" if en_cours else "[RÉSOLU] homelab"
    lignes = []
    for alerte in en_cours or alertes:
        etiquettes, notes = alerte.get("labels", {}), alerte.get("annotations", {})
        resume = notes.get("resume") or notes.get("summary") or etiquettes.get("instance", "")
        lignes.append(f"- {etiquettes.get('alertname', '?')} : {resume}")
    message = "\n".join([titre, *lignes])
    return message if len(message) <= LONGUEUR_MAX else message[:LONGUEUR_MAX - 1] + "…"


def envoyer(message):
    """Envoie le SMS (POST JSON, sinon paramètres dans l'URL) ; renvoie le code HTTP de Free."""
    global dernier_envoi
    with verrou:
        attente = dernier_envoi + INTERVALLE - time.monotonic()
        if attente > 0:
            time.sleep(attente)
        essais = [
            urllib.request.Request(API, data=json.dumps({"user": UTILISATEUR, "pass": CLE, "msg": message}).encode(),
                                   headers={"Content-Type": "application/json"}, method="POST"),
            urllib.request.Request(API + "?" + urllib.parse.urlencode({"user": UTILISATEUR, "pass": CLE,
                                                                        "msg": message})),
        ]
        code = 0
        for requete in essais:
            try:
                with urllib.request.urlopen(requete, timeout=15) as reponse:
                    code = reponse.status
            except urllib.error.HTTPError as erreur:
                code = erreur.code
            except (urllib.error.URLError, OSError):
                code = 0
            if code != 400:
                break
        dernier_envoi = time.monotonic()
    return code


class Gestionnaire(http.server.BaseHTTPRequestHandler):
    server_version = "relais-sms"
    sys_version = ""

    def log_message(self, format, *args):  # noqa: A002 - signature imposée ; journal applicatif seulement
        pass

    def repondre(self, code, texte_reponse):
        corps = texte_reponse.encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(corps)))
        self.end_headers()
        self.wfile.write(corps)

    def do_GET(self):
        if self.path == "/sante":
            return self.repondre(200, "ok\n")
        return self.repondre(404, "introuvable\n")

    def do_POST(self):
        if self.path != "/alertmanager":
            return self.repondre(404, "introuvable\n")
        longueur = int(self.headers.get("Content-Length") or 0)
        try:
            charge = json.loads(self.rfile.read(min(longueur, 1_000_000)))
        except ValueError:
            return self.repondre(400, "JSON invalide\n")
        code = envoyer(texte(charge))
        journal(action="sms", groupe=charge.get("groupKey", ""), statut=charge.get("status", ""),
                alertes=len(charge.get("alerts", [])), free=code, resultat=CODES.get(code, "injoignable"))
        # Alertmanager réessaie après une erreur 5xx, pas après une 4xx : identifiants refusés = 422 (inutile
        # d'insister), autre échec = 503.
        if code == 200:
            return self.repondre(200, "envoyé\n")
        return self.repondre(422 if code == 403 else 503, CODES.get(code, "Free injoignable") + "\n")


if __name__ == "__main__":
    journal(action="demarrage", api=API)
    http.server.ThreadingHTTPServer(("0.0.0.0", 8080), Gestionnaire).serve_forever()
