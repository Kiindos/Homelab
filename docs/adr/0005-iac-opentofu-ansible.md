---
title: "ADR 0005 : OpenTofu et Ansible dès le départ"
description: Aucune ressource créée à la main, même si le démarrage est plus lent.
date: 2026-09-21
status: accepté
tags: [iac, opentofu, ansible]
---

# ADR 0005 : OpenTofu et Ansible dès le départ

## Contexte

L'objectif est de démontrer une pratique DevOps, et de pouvoir reconstruire l'infra après une panne.

## Décision

- **OpenTofu** (open source, compatible Terraform) avec les providers `bpg/proxmox` et `cloudflare/cloudflare`.
- **Ansible** pour la configuration des hôtes et des VM.
- État OpenTofu hors du dépôt : backend local chiffré au départ, puis backend S3 auto-hébergé.

## Conséquences

Plus lent au début ; en échange, chaque changement est relu, versionné et rejouable.
