---
title: "ADR 0018 : Un groupe par service, droits d'administration et quotas dérivés de l'annuaire"
description: L'accès à chaque service se donne en ajoutant quelqu'un à un groupe ; les droits d'administration des applications suivent le groupe des administrateurs ; les quotas se règlent depuis la page des comptes.
date: 2026-09-28
status: accepté
tags: [identite, sso, authelia, lldap, securite]
---

# ADR 0018 : Un groupe par service, droits d'administration et quotas dérivés de l'annuaire

## Contexte

Jusqu'ici, deux groupes seulement : `famille` (tous les services personnels) et `admins` (tout). Impossible de donner
« les photos, mais pas le drive » à quelqu'un. Chaque application gérait en plus ses administrateurs à part, et la
place allouée à chacun (drive, photos) ne se réglait que dans l'interface de chaque application.

L'annuaire (LLDAP) ne sait pas imbriquer les groupes.

## Options envisagées

1. **Des groupes par service uniquement** — fin, mais il faut cocher chaque service pour chaque proche.
2. **Un groupe par service, plus des groupes qui ouvrent tout** (`famille`, `admins`) — retenu : les proches actuels
   ne changent pas, un invité peut n'avoir qu'un service.
3. **Des rôles dans chaque application** — autant d'endroits à tenir à jour, que le SSO ne voit pas.

## Décision

- Un groupe par service (`photos`, `drive`…) ; chaque service accepte son groupe, `famille` et `admins`. La
  correspondance est décrite **à un seul endroit** de l'inventaire ; les règles d'Authelia (politiques OpenID
  Connect, barrière du WAF) et les filtres d'annuaire des applications en sont générés.
- Les **droits d'administration** des applications sont **dérivés du groupe `admins`** à chaque connexion, par des
  attributs calculés d'Authelia (expressions CEL) transmis en claims : rôle dans la galerie photo, groupe
  d'administration du drive.
- Les **quotas** (drive, photos) se règlent sur la page des comptes, avec l'espace utilisé. Moindre privilège : pour
  le drive, un compte dédié **sous-administrateur des seuls groupes de la famille** (il ne peut toucher ni aux
  administrateurs ni aux autres groupes) ; pour les photos, une **clé d'API limitée** à la lecture et à la
  modification des comptes. Un flux dédié du pare-feu, de la machine d'identité vers celle des applications.
- Le comportement a été éprouvé sur une instance jetable d'Authelia avant la production : un compte « photos
  seulement » entre dans la galerie en simple utilisateur et se voit refuser le drive ; un administrateur reçoit
  son rôle dans les deux.

## Conséquences

- Donner ou retirer un accès = cocher un groupe (page des comptes) ou retirer quelqu'un d'un groupe (annuaire).
- Nommer un administrateur des applications = l'ajouter à `admins` ; lui retirer ce groupe lui retire ses droits à
  la connexion suivante.
- La page des comptes détient deux accès de plus (compte délégué, clé d'API) : tous deux limités, révocables seuls,
  et inactifs tant qu'ils ne sont pas fournis.
- Le quota de la galerie photo ne peut être fixé qu'une fois le compte créé (première connexion) ; un quota par
  défaut pourra s'appliquer à la création.
