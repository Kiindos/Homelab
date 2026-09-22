---
title: "ADR 0001 : Le Dell T330 dédié au stockage"
description: Le T330 devient la machine de stockage (ZFS RAIDZ2, PBS), le calcul part sur un cluster dédié.
date: 2026-09-22
status: accepté
tags: [proxmox, zfs, stockage]
---

# ADR 0001 : Le Dell T330 dédié au stockage

## Contexte

Le T330 (8 baies hot-plug, 32 Go DDR4 ECC, PERC H330) devait d'abord tout héberger : pare-feu, stockage et services. Une seule machine pour tout, c'est un point unique de défaillance, et chaque maintenance coupe l'ensemble.

## Options envisagées

1. **Tout sur le T330** : simple, mais fragile et difficile à maintenir.
2. **T330 en stockage seul, calcul sur un cluster** : rôles séparés, comme en entreprise.
3. **TrueNAS SCALE sur le T330** : très adapté au NAS, mais un outil de plus à maîtriser.

## Décision

Le T330 reste sous **Proxmox VE** (un seul outil sur toute l'infra, pilotable par OpenTofu) et ne porte que le stockage : pool **ZFS RAIDZ2** sur 4 disques SAS, PERC H330 en **mode HBA**, **Proxmox Backup Server** pour les sauvegardes du cluster.

## Conséquences

- Environ 6 To utiles, deux pannes de disque tolérées (pertinent avec des disques d'occasion).
- Données du NAS et sauvegardes sur la même machine : **copie hors site chiffrée obligatoire**.
- Les disques des VM ne sont pas stockés sur le NAS, pour ne pas en faire un point unique de défaillance du cluster.
