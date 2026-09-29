#!/usr/bin/python3
"""Demande de mise à jour déposée par Semaphore, sur l'hôte de Semaphore. Géré par Ansible (rôle mises_a_jour).

Semaphore ne se connecte pas à sa propre machine : il écrit une demande dans un dossier monté dans son conteneur.
Ce script (root, lancé par demande-mise-a-jour.path) la lit sans suivre de lien, la vérifie strictement, puis
programme la mise à jour locale (minuterie systemd) ou l'annule. Le conteneur ne peut donc que demander une mise à
jour à une heure donnée, rien d'autre. Réponse dans mise-a-jour.etat, lue par le playbook.

  {"action": "programmer" | "annuler", "quand": "AAAA-MM-JJ HH:MM" | "maintenant",
   "attente": secondes (0 à 86400), "redemarrage": "si_necessaire" | "jamais", "images": true | false}
"""

import datetime
import json
import os
import re
import stat
import subprocess
import sys

DOSSIER = sys.argv[1]
DEMANDE = os.path.join(DOSSIER, "mise-a-jour.json")
ETAT = os.path.join(DOSSIER, "mise-a-jour.etat")


def lire():
    try:
        descripteur = os.open(DEMANDE, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as erreur:
        raise ValueError(f"demande illisible ({erreur.strerror})") from erreur
    try:
        infos = os.fstat(descripteur)
        if not stat.S_ISREG(infos.st_mode) or infos.st_size > 4096:
            raise ValueError("demande refusée : pas un fichier ordinaire, ou trop grande")
        return json.loads(os.read(descripteur, 4096))
    finally:
        os.close(descripteur)


def verifier(demande):
    if not isinstance(demande, dict) or demande.get("action") not in ("programmer", "annuler"):
        raise ValueError("action attendue : programmer ou annuler")
    if demande["action"] == "annuler":
        return demande
    quand = demande.get("quand")
    if quand != "maintenant":
        if not isinstance(quand, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}", quand):
            raise ValueError("quand attendu : AAAA-MM-JJ HH:MM ou maintenant")
        date = datetime.datetime.strptime(quand, "%Y-%m-%d %H:%M")
        if not datetime.datetime.now() < date < datetime.datetime.now() + datetime.timedelta(days=60):
            raise ValueError("date passée ou à plus de 60 jours")
    attente = demande.get("attente", 0)
    if not isinstance(attente, int) or isinstance(attente, bool) or not 0 <= attente <= 86400:
        raise ValueError("attente attendue : 0 à 86400 secondes")
    if demande.get("redemarrage", "si_necessaire") not in ("si_necessaire", "jamais"):
        raise ValueError("redémarrage attendu : si_necessaire ou jamais")
    if not isinstance(demande.get("images", True), bool):
        raise ValueError("images attendu : vrai ou faux")
    return demande


def executer(demande):
    subprocess.run(["systemctl", "stop", "mise-a-jour.timer"], capture_output=True, check=False)
    if demande["action"] == "annuler":
        return "Mise à jour annulée."
    commande = ["/usr/local/sbin/mise-a-jour", "--attente", str(demande.get("attente", 0)),
                "--redemarrage", demande.get("redemarrage", "si_necessaire")]
    if not demande.get("images", True):
        commande.append("--sans-images")
    # « maintenant » : 2 minutes de délai, le temps que la tâche Semaphore se termine (elle tourne sur cette machine).
    moment = (["--on-active=2min"] if demande["quand"] == "maintenant"
              else [f"--on-calendar={demande['quand']}:00", "--timer-property=AccuracySec=1s"])
    subprocess.run(["systemd-run", "--unit=mise-a-jour", "--collect",
                    "--description=Mise à jour de la machine (demandée depuis Semaphore)", *moment, *commande],
                   capture_output=True, text=True, check=True)
    debut = "dans 2 minutes" if demande["quand"] == "maintenant" else f"le {demande['quand']}"
    return f"Mise à jour programmée {debut}, plus {demande.get('attente', 0) // 60} min d'attente (ordre de passage)."


def main():
    try:
        reponse = "OK " + executer(verifier(lire()))
    except (ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as erreur:
        reponse = f"REFUS {erreur}"
    finally:
        # Toujours retirer la demande (un lien compris : unlink ne suit pas les liens), sinon l'unité .path
        # relancerait ce script en boucle.
        try:
            os.unlink(DEMANDE)
        except FileNotFoundError:
            pass
    # Le dossier est modifiable par le conteneur : réponse créée à neuf, sans jamais suivre un lien qu'il y aurait mis.
    try:
        os.unlink(ETAT)
    except FileNotFoundError:
        pass
    descripteur = os.open(ETAT, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    with os.fdopen(descripteur, "w", encoding="utf-8") as sortie:
        sortie.write(reponse + "\n")
    print(reponse)


if __name__ == "__main__":
    main()
