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

## Un coffre pour les secrets

Dernier chantier de la journée : un coffre **OpenBao** ([ADR 0016](../adr/0016-coffre-openbao.md)), en test. On s'y
connecte par le SSO, Semaphore n'y lit que ce dont il a besoin et depuis sa seule adresse, chaque accès est tracé.
Il se descelle seul au démarrage grâce à une clé qui ne quitte pas l'hyperviseur. Avant de s'y fier, un déploiement
complet « à blanc » a été rejoué en lisant les secrets dans le coffre plutôt que dans le fichier chiffré : aucune
configuration n'aurait changé.

## Des comptes sans mot de passe temporaire

Inviter un proche ne passe plus par un mot de passe transmis à la main : le compte est créé vide dans l'annuaire,
puis le portail d'authentification envoie un lien personnel, à usage unique et limité dans le temps, pour choisir
son mot de passe. Le même lien sert au « mot de passe oublié », qui ne fonctionnait pas : le compte de service du
portail n'avait que la lecture sur l'annuaire. Les e-mails sont traduits et aux couleurs du homelab ; ils ont été
éprouvés sur une instance jetable (faux serveur SMTP) avant la mise en production.

## Ce que la journée a appris

- **Tester l'échec, pas seulement le succès.** La vérification des clés SSH a été validée en présentant
  volontairement une identité inconnue.
- **Une coupure réseau ne doit pas figer un déploiement.** Une reconnexion du VPN a laissé Ansible bloqué ;
  les connexions vérifient maintenant qu'elles sont vivantes.
- **Une valeur par défaut peut trahir.** Une règle OWASP a pris l'adresse de retour de la connexion en ligne de
  commande (`http://localhost`) pour une attaque SSRF : exclusion ciblée sur ce seul paramètre.
- **Un montage peut casser ce qu'il vise.** Monter un fichier dans un dossier que l'application crée elle-même
  au démarrage fait créer ce dossier par Docker, en root : l'application, non privilégiée, ne peut plus s'installer.
  Le fichier est désormais copié une fois l'application prête.
- **Une limite de débit se mesure sur le vrai usage.** Deux requêtes par seconde suffisent pour une page, pas pour
  une application qui en envoie des dizaines au démarrage.
- **Un nom mal résolu se cache bien.** La supervision ne se voyait pas elle-même : le nom de la machine pointait
  vers l'adresse de boucle locale. Corrigé à la source, pour toutes les machines.
- **Deux serveurs DNS qui répondent, c'est une course.** Sans domaine de routage, le poste interrogeait à la fois
  la box et le serveur du homelab et gardait la première réponse : les noms internes marchaient une fois sur deux.
- **Redémarrer une pile d'un bloc ignore ses dépendances.** Le portail vérifie l'annuaire au démarrage ; relancés
  ensemble, il échouait avant de se relancer. L'annuaire redémarre maintenant d'abord, et une simple modification
  de configuration ne relance plus que le portail.
