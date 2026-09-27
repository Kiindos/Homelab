---
title: "ADR 0014 : Supervision par Prometheus, NOC public sur mesure derrière le SSO"
description: Prometheus collecte, Alertmanager prévient par e-mail et sur téléphone (ntfy), une page sur mesure publie un NOC consultable après authentification.
date: 2026-09-27
status: accepté
tags: [supervision, prometheus, grafana, sso, alertes]
---

# ADR 0014 : Supervision par Prometheus, NOC public sur mesure derrière le SSO

## Contexte

La plateforme compte une dizaine de services répartis sur six VM et un hyperviseur dont les disques ont déjà
plus de 50 000 heures de fonctionnement. Il faut :

- savoir **avant les utilisateurs** qu'un service, une VM ou un disque tombe ;
- être prévenu **sur le téléphone** pour les pannes graves, sans être dérangé pour le reste ;
- disposer d'un **tableau de bord (NOC)** consultable de partout, sans exposer de données à n'importe qui.

## Options envisagées

1. **Uptime Kuma** : très simple, mais se limite à des sondes (pas de métriques des machines ni des disques).
2. **Zabbix** : complet, mais lourd (base de données, agents dédiés) pour un homelab.
3. **Prometheus + Alertmanager + Grafana** : standard du marché, configuration entièrement déclarative (versionnée
   dans ce dépôt), exporteurs disponibles pour tout ce qui compte ici (Linux, SMART, Proxmox, sondes HTTP).

Pour les notifications sur téléphone : SMS (payant, fournisseur tiers), Telegram/Discord (compte tiers qui lit les
alertes) ou **ntfy auto-hébergé** (application libre, sujets protégés par mot de passe).

## Décision

- **Prometheus** collecte les métriques des machines (node_exporter), des disques (smartctl_exporter), de Proxmox
  (compte API en **lecture seule**) et sonde les services publiés à travers le WAF, comme un visiteur.
- **Alertmanager** classe les alertes en deux niveaux :
  - *critique* (machine injoignable, service public en panne, pool ZFS dégradé, disque en échec, certificat sur le
    point d'expirer) : **e-mail** depuis une adresse d'envoi dédiée et **notification prioritaire** sur le téléphone ;
  - *avertissement* (espace disque, mémoire, nouveaux secteurs défectueux) : visibles sur le NOC seulement.
- Le **NOC** est une **page écrite sur mesure**, à la charte du site : état global, services publiés (temps de
  réponse, disponibilité, certificats), machines, disques et alertes en cours. Un petit collecteur interroge
  Prometheus et Alertmanager toutes les 30 secondes avec un jeu de requêtes fixé dans le code, et écrit un
  instantané JSON que la page affiche : **Internet ne peut envoyer aucune requête à Prometheus**. La page ne sait
  que lire ; le WAF n'accepte que `GET` et `HEAD`.
- La connexion est imposée **par le WAF** : chaque requête est vérifiée auprès d'Authelia (*auth_request*) avant
  d'atteindre la page, avec second facteur, pour les groupes famille et administrateurs. Seule une URL de sonde,
  qui répond « ok », reste ouverte.
- **Grafana** reste disponible pour explorer les métriques en détail, mais comme **outil interne** (VPN, SSO,
  administrateurs uniquement).
- **ntfy** auto-hébergé relaie les alertes vers l'application mobile ; tout est refusé par défaut, Alertmanager ne
  peut qu'écrire et le téléphone ne peut que lire.

## Conséquences

- Prometheus, Alertmanager et Grafana restent internes (VPN uniquement) ; seuls le NOC et ntfy sont publiés, avec
  les mêmes protections que les autres services (WAF, liste blanche de pays, limitation de débit).
- Première version (le même jour) : Grafana publié directement comme NOC. Remplacé par la page sur mesure, plus
  lisible pour la famille, plus sobre en surface exposée, et fidèle à l'identité visuelle du projet.
- La supervision tourne sur sa propre VM : une panne d'une application ne l'emporte pas avec elle. En revanche, une
  panne de l'hyperviseur coupe tout, supervision comprise : une sonde externe (hors du homelab) reste à prévoir.
- Les règles d'alerte sont du code : chaque nouvelle alerte passe par une revue, comme le reste de l'infrastructure.
