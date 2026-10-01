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

## Une page pour inviter

La ligne de commande a laissé place à une **page des comptes** ([ADR 0017](../adr/0017-invitations-page-comptes.md)) :
prénom, nom, e-mail, accès, et l'invitation part. Elle n'est joignable que par le VPN, derrière le proxy interne,
qui sait maintenant imposer lui aussi la connexion SSO (double authentification, administrateurs seulement). La page
n'accepte l'identité transmise que depuis le proxy et refuse les formulaires envoyés depuis un autre site ; elle a été
éprouvée contre un faux annuaire avant d'approcher le vrai.

Côté supervision, un service publié derrière la barrière SSO du WAF est désormais sondé **sans session** : la sonde
exige une redirection vers le portail. Si la barrière disparaissait, l'alerte partirait.

## Voir le homelab depuis l'extérieur

La supervision vit dans le homelab : si le courant, la box ou l'hyperviseur tombent, elle se tait avec lui. Une
**sonde externe** (UptimeRobot, offre gratuite) vérifie désormais toutes les 5 minutes la vitrine (via Cloudflare)
et l'accès direct au pare-feu applicatif. Le WAF n'acceptant que la France, la seconde sonde reste au niveau TCP
plutôt que d'assouplir le filtrage. Les moniteurs sont décrits dans un fichier et appliqués par un script
idempotent, comme le reste. Un relais **SMS** pour les alertes critiques est écrit (option gratuite de l'opérateur
mobile, qui n'écrit qu'au titulaire de la ligne : aucun numéro à stocker), mais pas encore activé.

Le site a enfin ses pages **mentions légales** et **confidentialité**, écrites à partir de ce que les services
journalisent réellement (durées de rotation, partage communautaire des adresses d'attaquants, sous-traitants).

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
- **Un en-tête de sécurité peut casser une application.** Le WAF ajoutait `HttpOnly` à tous les cookies ; or
  l'interface de la galerie photo lit un de ses cookies en JavaScript pour savoir si l'on est connecté. Résultat :
  une boucle de connexion. Les drapeaux sont maintenant imposés aux seuls cookies de session.
