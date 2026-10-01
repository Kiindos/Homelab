#!/usr/bin/env python3
"""Relevé de l'occupation des jeux de données ZFS de l'hyperviseur, publié pour Prometheus (collecteur textfile).

Configuration : /etc/homelab/stockage.json = {"pool": "<pool>", "jeux": {"<libellé>": "<jeu de données>", ...}}.
Par jeu : occupé (instantanés compris), données vivantes, disponible (quota pris en compte), quota (0 = aucun).
Pour le pool : total occupé et disponible, en espace utile (parité RAIDZ déduite).
"""
import json
import os
import subprocess
import tempfile

CONF = "/etc/homelab/stockage.json"
SORTIE = "/var/lib/prometheus/node-exporter/stockage.prom"


def zfs_list(champs, jeu):
    sortie = subprocess.run(["zfs", "list", "-Hp", "-o", champs, jeu], capture_output=True, text=True, check=True)
    return sortie.stdout.split()


def main():
    conf = json.load(open(CONF, encoding="utf-8"))
    lignes = [
        "# HELP homelab_stockage_utilise_octets Espace occupé par le jeu de données, instantanés compris.",
        "# TYPE homelab_stockage_utilise_octets gauge",
        "# HELP homelab_stockage_donnees_octets Données vivantes du jeu (sans les instantanés).",
        "# TYPE homelab_stockage_donnees_octets gauge",
        "# HELP homelab_stockage_disponible_octets Espace encore disponible pour le jeu (quota ou place du pool).",
        "# TYPE homelab_stockage_disponible_octets gauge",
        "# HELP homelab_stockage_quota_octets Quota du jeu (0 : aucun).",
        "# TYPE homelab_stockage_quota_octets gauge",
    ]
    for libelle, jeu in conf.get("jeux", {}).items():
        utilise, disponible, quota, donnees = zfs_list("used,avail,quota,refer", jeu)
        etiquettes = f'jeu="{libelle}",dataset="{jeu}"'
        lignes += [
            f"homelab_stockage_utilise_octets{{{etiquettes}}} {utilise}",
            f"homelab_stockage_donnees_octets{{{etiquettes}}} {donnees}",
            f"homelab_stockage_disponible_octets{{{etiquettes}}} {disponible}",
            f"homelab_stockage_quota_octets{{{etiquettes}}} {quota}",
        ]
    pool = conf.get("pool", "rpool")
    utilise, disponible = zfs_list("used,avail", pool)
    lignes += [
        "# HELP homelab_stockage_total_utilise_octets Espace utile occupé sur le pool (tout compris).",
        "# TYPE homelab_stockage_total_utilise_octets gauge",
        f'homelab_stockage_total_utilise_octets{{pool="{pool}"}} {utilise}',
        "# HELP homelab_stockage_total_disponible_octets Espace utile encore libre sur le pool.",
        "# TYPE homelab_stockage_total_disponible_octets gauge",
        f'homelab_stockage_total_disponible_octets{{pool="{pool}"}} {disponible}',
    ]
    dossier = os.path.dirname(SORTIE)
    with tempfile.NamedTemporaryFile("w", dir=dossier, delete=False, encoding="utf-8") as tmp:
        tmp.write("\n".join(lignes) + "\n")
    os.chmod(tmp.name, 0o644)
    os.replace(tmp.name, SORTIE)


if __name__ == "__main__":
    main()
