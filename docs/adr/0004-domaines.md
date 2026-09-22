---
title: "ADR 0004 : Répartition des domaines"
description: maximebertrand.eu pour la vitrine publique, le domaine .fr existant pour le labo.
date: 2026-09-21
status: accepté
tags: [dns, cloudflare]
---

# ADR 0004 : Répartition des domaines

## Contexte

Un domaine à mon pseudo en `.fr` existe déjà. La vitrine doit être trouvable en cherchant mon nom.

## Décision

- `maximebertrand.eu` : site vitrine, blog, page de statut, adresse de contact (Cloudflare Email Routing).
- Domaine `.fr` existant : labo, services internes (`*.home.<domaine>.fr` résolus uniquement en interne ou en VPN, certificats par challenge DNS).

## Conséquences

Les deux zones sont gérées chez Cloudflare et décrites dans `infra/tofu/cloudflare`.
