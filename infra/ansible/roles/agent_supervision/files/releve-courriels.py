#!/usr/bin/env python3
"""Relevé des e-mails envoyés par le relais transactionnel (Scaleway TEM), publié pour Prometheus (textfile).

Configuration : /etc/homelab/courriels.json = {"region": "fr-par", "projet": "<ID du projet>",
"cle_fichier": "/etc/homelab/courriels.cle"} ; la clé d'API (lecture des statistiques) est dans le fichier, 0600.
Deux périodes : depuis la création du projet (« total ») et depuis le 1er du mois en UTC (« mois », offre gratuite
mensuelle). États Scaleway : new, sending, sent, failed, canceled.
"""
import datetime
import json
import os
import tempfile
import time
import urllib.request

CONF = "/etc/homelab/courriels.json"
SORTIE = "/var/lib/prometheus/node-exporter/courriels.prom"
ETATS = ("new", "sending", "sent", "failed", "canceled")


def statistiques(conf, cle, depuis=None):
    url = (f"https://api.scaleway.com/transactional-email/v1alpha1/regions/{conf['region']}/statistics"
           f"?project_id={conf['projet']}" + (f"&since={depuis}" if depuis else ""))
    requete = urllib.request.Request(url, headers={"X-Auth-Token": cle})
    with urllib.request.urlopen(requete, timeout=20) as reponse:
        return json.load(reponse)


def main():
    conf = json.load(open(CONF, encoding="utf-8"))
    cle = open(conf["cle_fichier"], encoding="utf-8").read().strip()
    debut_mois = datetime.datetime.now(datetime.timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    lignes = [
        "# HELP homelab_courriels Nombre d'e-mails du relais transactionnel par période et par état.",
        "# TYPE homelab_courriels gauge",
    ]
    reussi = 1
    try:
        for periode, depuis in (("total", None), ("mois", debut_mois)):
            valeurs = statistiques(conf, cle, depuis)
            for etat in ETATS:
                lignes.append(f'homelab_courriels{{periode="{periode}",etat="{etat}"}} {valeurs.get(etat + "_count", 0)}')
    except Exception as erreur:  # API injoignable ou clé refusée : signalé, valeurs précédentes perdues
        print(f"Relevé impossible : {erreur}")
        reussi = 0
        lignes = lignes[:2]
    lignes += [
        "# HELP homelab_courriels_releve_reussi 1 si le dernier relevé auprès du relais a réussi.",
        "# TYPE homelab_courriels_releve_reussi gauge",
        f"homelab_courriels_releve_reussi {reussi}",
        f"homelab_courriels_releve_timestamp {int(time.time())}",
    ]
    dossier = os.path.dirname(SORTIE)
    with tempfile.NamedTemporaryFile("w", dir=dossier, delete=False, encoding="utf-8") as tmp:
        tmp.write("\n".join(lignes) + "\n")
    os.chmod(tmp.name, 0o644)
    os.replace(tmp.name, SORTIE)


if __name__ == "__main__":
    main()
