---
title: "Supervision, NOC sur mesure et automatisation"
description: Le homelab se surveille lui-même, prévient sur le téléphone, affiche son état sur un NOC maison et se pilote depuis Semaphore.
date: 2026-09-27
tags: [journal, supervision, sso, ansible, design]
---

# Supervision, NOC sur mesure et automatisation

Deuxième journée : rendre la plateforme **observable** et **pilotable**, sans rien céder sur la sécurité.

## Voir et être prévenu

Une machine virtuelle dédiée fait tourner Prometheus et Alertmanager ([ADR 0014](../adr/0014-supervision-noc.md)).
Chaque machine expose ses métriques, les quatre disques du serveur leur santé SMART, et les services publiés sont
sondés à travers le WAF, comme le ferait un visiteur. Les pannes graves partent par e-mail et en notification
prioritaire sur le téléphone, grâce à une instance ntfy auto-hébergée.

## Un NOC dessiné pour le homelab

La première version publiait Grafana tel quel. Efficace, mais générique : elle est remplacée par une **page écrite
sur mesure**, à la charte du site, qui répond d'un coup d'œil à la seule question utile (« est-ce que tout
fonctionne ? ») avant d'entrer dans le détail. La page ne parle jamais à Prometheus : elle lit un instantané produit
toutes les 30 secondes par un petit collecteur, et le WAF impose la connexion SSO avant même qu'elle soit servie.

Le portail de connexion adopte la même identité visuelle. Plutôt que de modifier Authelia, le WAF injecte une
feuille de style qui redéfinit ses variables de thème : l'habillage survit aux mises à jour.

## Piloter sans le poste d'admin

Semaphore UI lance désormais les playbooks Ansible depuis le navigateur, avec historique et mode « à blanc »
([ADR 0015](../adr/0015-semaphore-ansible.md)). Un détail a demandé de l'attention : l'image officielle désactive la
vérification de l'identité des serveurs SSH. Elle est rétablie, et testée : un serveur inconnu est refusé.

## Ce que la journée a appris

- **Tester l'échec, pas seulement le succès.** La vérification des clés SSH a été validée en présentant
  volontairement une identité inconnue.
- **Une coupure réseau ne doit pas figer un déploiement.** Une reconnexion du VPN a laissé Ansible bloqué ;
  les connexions vérifient maintenant qu'elles sont vivantes.
- **Un nom mal résolu se cache bien.** La supervision ne se voyait pas elle-même : le nom de la machine pointait
  vers l'adresse de boucle locale. Corrigé à la source, pour toutes les machines.
