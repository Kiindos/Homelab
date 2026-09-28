#!/usr/bin/env python3
"""Annonces en ligne de commande, dans le conteneur de la page des comptes (même traitement que la page).

    python3 /app/publier.py annonce --type maintenance --titre "Redémarrage du serveur" \\
        --debut 2026-09-29T22:00 --fin 2026-09-29T22:30 --services photos,drive --message "…"   # aperçu
    python3 /app/publier.py annonce … --oui        # publie (e-mails et bandeau)
    python3 /app/publier.py liste
    python3 /app/publier.py retirer <identifiant>

Sans --oui, rien n'est envoyé ni enregistré. « --message - » lit le message sur l'entrée standard.
"""

import argparse
import contextlib
import sys

import annonces
import app
import bienvenue
from app import Annuaire, groupes_annonces, membres


def journal(**champs):
    """Même journal que la page : la sortie du processus principal du conteneur (« docker logs »)."""
    try:
        with open("/proc/1/fd/1", "w", encoding="utf-8") as sortie, contextlib.redirect_stdout(sortie):
            app.journal(**champs)
    except OSError:
        app.journal(**champs)


def liste(_):
    for annonce in annonces.charger()[:20]:
        etat = "bandeau actif" if annonces.bandeau_actif(annonce) else "—"
        print(f"{annonce['id']}  {annonces.TYPES[annonce['type']]['libelle']:<18} {annonce['titre']}  ({etat})")


def retirer(arguments):
    annonce = annonces.retirer(arguments.identifiant)
    journal(admin=arguments.auteur, action="annonce-retiree", annonce=annonce["id"])
    print(f"Bandeau retiré : {annonce['titre']}")


def annonce(arguments):
    catalogue = bienvenue.catalogue()
    with Annuaire() as annuaire:
        comptes, groupes = annuaire.etat()
    message = sys.stdin.read() if arguments.message == "-" else arguments.message.replace("\\n", "\n")
    groupes_vises = [g for g in arguments.groupes.split(",") if g]
    champs = {"type": arguments.type, "titre": arguments.titre, "message": message, "debut": arguments.debut,
              "fin": arguments.fin, "services": [s for s in arguments.services.split(",") if s],
              "groupes": groupes_vises, "public": "groupes" if groupes_vises else "tous", "resout": arguments.resout,
              "courriel": "" if arguments.sans_courriel else "1", "bandeau": "" if arguments.sans_bandeau else "1"}
    prete = annonces.preparer(champs, arguments.auteur, catalogue, groupes_annonces(groupes))
    personnes = annonces.destinataires(membres(comptes), prete["groupes"]) if prete["courriel"] else []
    print(annonces.sujet(prete))
    print(f"Destinataires ({len(personnes)}) : {', '.join(p['prenom'] for p in personnes) or 'aucun'}")
    print(f"Bandeau : {'oui' if prete['bandeau'] else 'non'}\n")
    print(annonces.texte_brut(prete, "…", catalogue))
    if not arguments.oui:
        print("\nAperçu seulement : relancer avec --oui pour publier.")
        return
    if prete["courriel"] and not bienvenue.actif():
        sys.exit("Envoi d'e-mails non configuré : ajouter --sans-courriel.")
    annonces.publier(prete, personnes, catalogue)
    journal(admin=arguments.auteur, action="annonce", annonce=prete["id"], type=prete["type"],
            groupes=prete["groupes"], envoyes=prete["envoyes"], echecs=prete["echecs"], bandeau=prete["bandeau"])
    print(f"\nPubliée ({prete['id']}) : {prete['envoyes']} e-mail(s) envoyé(s), {prete['echecs']} refusé(s).")


def main():
    analyse = argparse.ArgumentParser(description="Annonces aux membres du homelab.")
    analyse.add_argument("--auteur", default="ligne-de-commande")
    sous = analyse.add_subparsers(dest="commande", required=True)
    nouvelle = sous.add_parser("annonce", help="préparer (aperçu) ou publier une annonce")
    nouvelle.add_argument("--type", required=True, choices=list(annonces.TYPES))
    nouvelle.add_argument("--titre", required=True)
    nouvelle.add_argument("--message", default="", help="texte (\\n pour un saut de ligne), ou - pour l'entrée standard")
    nouvelle.add_argument("--debut", default="", help="AAAA-MM-JJTHH:MM, heure de Paris")
    nouvelle.add_argument("--fin", default="", help="AAAA-MM-JJTHH:MM, heure de Paris")
    nouvelle.add_argument("--services", default="", help="identifiants du catalogue, séparés par des virgules")
    nouvelle.add_argument("--groupes", default="", help="groupes destinataires (vide = tout le monde)")
    nouvelle.add_argument("--resout", default="", help="identifiant de l'annonce que celle-ci clôt (type resolu)")
    nouvelle.add_argument("--sans-courriel", action="store_true")
    nouvelle.add_argument("--sans-bandeau", action="store_true")
    nouvelle.add_argument("--oui", action="store_true", help="publier (sinon : aperçu)")
    nouvelle.set_defaults(fonction=annonce)
    sous.add_parser("liste", help="les 20 dernières annonces").set_defaults(fonction=liste)
    retrait = sous.add_parser("retirer", help="retirer un bandeau")
    retrait.add_argument("identifiant")
    retrait.set_defaults(fonction=retirer)
    arguments = analyse.parse_args()
    try:
        arguments.fonction(arguments)
    except annonces.Invalide as erreur:
        sys.exit(f"Refusé : {erreur}")


if __name__ == "__main__":
    main()
