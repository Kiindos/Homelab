---
title: "ADR 0020 : Journaux centralisés avec VictoriaLogs, collecte sans agent"
description: Les journaux de toutes les machines arrivent dans VictoriaLogs sur la VM de supervision, par les mécanismes déjà présents (journald, syslog), consultables dans Grafana.
date: 2026-09-28
status: accepté
tags: [supervision, journaux, securite]
---

# ADR 0020 : Journaux centralisés avec VictoriaLogs, collecte sans agent

## Contexte

Chaque machine garde ses journaux pour elle : diagnostiquer un problème qui traverse plusieurs services (une
réinitialisation de mot de passe passe par le WAF, le portail SSO, l'annuaire et la messagerie) oblige à se connecter
sur chaque VM et à croiser les heures à la main. Les métriques sont déjà centralisées (Prometheus), pas les
journaux. La mémoire du serveur est comptée : 32 Go pour tout le homelab.

## Options envisagées

1. **Loki + Alloy** : l'écosystème Grafana de référence, mais un agent Alloy par machine (≈ 150 Mo chacun, une dizaine
   de machines) et un Loki qui demande du réglage pour rester sobre.
2. **Pile Elastic / OpenSearch** : puissante, mais plusieurs Go de RAM pour la seule base : hors de propos ici.
3. **VictoriaLogs, collecte sans agent** — retenu : un seul binaire (quelques centaines de Mo), compression forte, et
   il accepte directement ce que les machines savent déjà envoyer : le journal systemd (`systemd-journal-upload`) et
   syslog (pare-feu).

## Décision

- **Stockage** : VictoriaLogs sur la VM de supervision, rétention **30 jours**, plafond d'espace disque.
- **Collecte, sans agent** :
  - VM Debian et hyperviseur : `systemd-journal-upload` envoie le journal systemd ;
  - conteneurs : pilote de journaux `journald` de Docker (`docker logs` continue de fonctionner), donc même chemin ;
  - pare-feu : syslog distant intégré à OPNsense (filtrage, VPN, DNS).
- **Exposition minimale** : seules les routes d'**écriture** sont joignables depuis les machines, par un relais qui
  refuse la lecture ; la lecture se fait uniquement depuis Grafana, sur le réseau interne de la VM de supervision.
- **Consultation** : Grafana (outil interne, VPN et SSO des administrateurs), source de données VictoriaLogs.
  *Ajout du 02/10/2026* : un tableau « Journaux » (volume, vraies erreurs, lignes filtrables), et l'interface web de
  VictoriaLogs en **lecture seule** derrière le proxy interne (VPN, SSO imposé, administrateurs). Le relais n'y
  laisse passer que les requêtes (`/select/`), et seulement depuis le proxy ; l'écriture reste séparée.
- **Alertes sur les journaux** (dans un second temps) : échecs de connexion répétés, erreurs de réinitialisation de mot
  de passe, via le gestionnaire d'alertes existant.
- **Pare-feu** : un flux d'écriture des journaux par zone vers la supervision, et un flux syslog depuis le pare-feu.

## Conséquences

- Les journaux contiennent des données personnelles (adresses IP, identifiants) : accès réservé aux administrateurs,
  30 jours de conservation, mention dans la page de confidentialité du site.
- Passer les conteneurs sur le pilote `journald` demande de les recréer : fait lors d'une maintenance annoncée.
- Les journaux restent aussi sur chaque machine (journald local) : la centralisation ne remplace pas le diagnostic local
  quand la supervision est elle-même en panne.
- Un envoi interrompu reprend où il s'était arrêté (`systemd-journal-upload` garde son curseur) : pas de trou après une
  coupure de la supervision.
