---
title: "ADR 0012 : Nextcloud pour le stockage de fichiers"
description: Nextcloud est retenu pour le drive familial, pour sa compatibilité avec tous les appareils.
date: 2026-09-26
status: accepté
tags: [services, stockage]
---

# ADR 0012 : Nextcloud pour le stockage de fichiers

## Contexte

La famille a besoin d'un espace de fichiers synchronisé, sur ordinateur (Windows, macOS, Linux) comme sur
téléphone, avec des partages par lien. Le critère principal est la **compatibilité** : un outil qui fonctionne sur
tous les appareils sans bricolage. Les photos ont déjà leur outil dédié (Immich).

## Options envisagées

1. **Nextcloud** : clients officiels sur tous les systèmes, WebDAV, agendas et contacts, OpenID Connect et LDAP.
   En contrepartie, une application PHP lourde, avec un vaste catalogue d'extensions à surveiller.
2. **Seafile** : très rapide et économe, mais un protocole de synchronisation propre et une intégration SSO plus
   limitée dans l'édition gratuite.
3. **Syncthing + FileBrowser** : synchronisation pair à pair robuste, mais deux outils, et pas de partage simple
   pour des non-techniciens.

## Décision

**Nextcloud**, en installation minimale : seules les applications utiles sont activées (fichiers, partage,
éventuellement agendas et contacts). Connexion par OpenID Connect via Authelia (voir l'[ADR 0011](0011-annuaire-sso.md)).

## Conséquences

- Mises à jour fréquentes, dont des versions majeures tous les quelques mois : à suivre dans la routine de
  correctifs.
- Chaque extension ajoutée élargit la surface d'attaque : on n'active que le nécessaire.
- La base de données et le cache restent sur le disque local de la machine virtuelle ; les fichiers sont sur un
  dataset ZFS de l'hôte, sauvegardé séparément.
- Les clients WebDAV et agendas utilisent des **mots de passe d'application**, révocables un par un.
