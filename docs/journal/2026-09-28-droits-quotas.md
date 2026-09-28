---
title: "Droits par groupes, quotas et documentation aux couleurs du homelab"
description: L'accès à chaque service se donne en cochant un groupe, les droits d'administration suivent l'annuaire, la place allouée se règle en une page.
date: 2026-09-28
tags: [journal, identite, sso, documentation]
---

# Droits par groupes, quotas et documentation aux couleurs du homelab

## Un groupe par service

Deux groupes ne suffisaient plus : impossible d'ouvrir les photos sans ouvrir le drive. Chaque service a maintenant
son groupe, et les groupes « famille » et « administrateurs » continuent d'ouvrir tout
([ADR 0018](../adr/0018-droits-par-groupes-quotas.md)). La correspondance tient en une table de l'inventaire, dont
sont générées les règles du SSO et du filtre de l'annuaire.

Les droits d'administration des applications suivent désormais l'annuaire : Authelia calcule, à chaque connexion,
un rôle à partir des groupes (expressions CEL) et le transmet dans un claim. Avant de toucher au SSO en production,
le parcours OpenID Connect complet a été rejoué sur une instance jetable : l'administrateur reçoit son rôle, le
compte « photos seulement » entre en simple utilisateur et se voit refuser le drive.

## La place de chacun

La page des comptes affiche l'espace utilisé sur le drive et dans la galerie photo, et permet de fixer un quota sur
place. Chaque accès est taillé au plus juste : un compte délégué qui ne gère que les groupes de la famille, une clé
d'API limitée aux comptes. Si un service ne répond pas, la page le dit et reste utilisable.

## Documentation

La documentation interne reprend la charte du site (palette, logo, titres, tableaux en cartes), sans police
chargée depuis Internet. Les décisions sur le coffre à secrets et la page des comptes sont passées de « proposé » à
« accepté ».

## Ce que la journée a appris

- **Une option passée en ligne de commande est une chaîne.** `-e option=true` n'est pas un booléen pour Ansible ;
  la condition l'a refusé et le déploiement s'est arrêté avant son gestionnaire. D'où un `| bool` systématique, et
  un redémarrage vérifié plutôt que supposé.
- **Un champ vide a un sens.** Un quota effacé veut dire « illimité » ; le décodage par défaut des formulaires
  jetait les champs vides, et le changement passait inaperçu. Le banc d'essai l'a vu avant la production.
