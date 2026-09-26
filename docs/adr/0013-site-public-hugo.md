---
title: "ADR 0013 : Site public sur mesure, généré par Hugo et servi par le homelab"
description: Le portfolio est un site statique au design propre, construit depuis docs/ et publié par un tunnel Cloudflare.
date: 2026-09-26
status: accepté
tags: [site, cloudflare, documentation]
---

# ADR 0013 : Site public sur mesure, généré par Hugo et servi par le homelab

## Contexte

La documentation publique du dépôt sert aussi de portfolio. Un thème de documentation standard est lisible, mais
ressemble à tous les autres sites de documentation : il fallait un site avec une identité propre, qui présente le
projet (principes, architecture, décisions, journal) sans dupliquer le contenu.

## Options envisagées

1. **MkDocs Material** : excellent pour une documentation technique, mais un rendu générique.
2. **Framework JavaScript (Astro, Next.js…)** : très souple, mais une chaîne Node.js à maintenir pour un site statique.
3. **Hugo avec un thème écrit sur mesure** : un seul binaire, une construction en quelques dizaines de millisecondes,
   et un contrôle total du HTML et du CSS.

## Décision

**Hugo**, avec un thème écrit pour ce site (gabarits, CSS et JavaScript sans dépendance). Le contenu reste la
**source unique** `docs/` : Hugo le monte directement, et les liens entre fichiers Markdown deviennent des liens entre
pages. Le site est servi par nginx sur une VM dédiée et publié par **Cloudflare Tunnel** ([ADR 0002](0002-cloudflare-tunnel.md)).

## Conséquences

- Écrire une page de documentation suffit à la publier ; la construction est stricte (le moindre avertissement
  l'arrête), et vérifiée par la CI.
- Aucun cookie ni traceur ; une politique de sécurité du contenu (CSP) n'autorise que le site lui-même et la
  bibliothèque de schémas, chargée uniquement sur les pages qui en contiennent et vérifiée par empreinte (SRI).
- Le thème est à maintenir soi-même : pas de mises à jour gratuites d'un thème communautaire.
