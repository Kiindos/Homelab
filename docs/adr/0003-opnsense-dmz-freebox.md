---
title: "ADR 0003 : OPNsense sur boîtier dédié, en DMZ derrière la Freebox Pop"
description: La Freebox reste en routeur ; un mini-PC OPNsense dédié reçoit tout le trafic entrant en DMZ.
date: 2026-09-22
status: remplacé
tags: [réseau, opnsense, freebox]
---

# ADR 0003 : OPNsense sur boîtier dédié, en DMZ derrière la Freebox Pop

> **Décision remplacée.** Cette décision a été remplacée par l'[ADR 0010](0010-serveur-unique.md) le 26/09/2026. Elle est conservée pour l'historique.


## Contexte

Le homelab doit avoir son propre pare-feu et ses VLAN, sans casser le réseau de la maison ni le Player TV. Avec trois environnements (PROD, stockage, LAB), le pare-feu devient le cœur du réseau.

## Options envisagées

1. **Freebox en bridge** : pas de double NAT, mais Player TV et stabilité problématiques.
2. **OPNsense en VM** : gratuit, mais la maintenance d'un hôte coupe tout le réseau.
3. **OPNsense sur un mini-PC dédié, en DMZ de la Freebox** : indépendant des serveurs.

## Décision

Option 3 : un mini-PC N100 avec plusieurs ports 2,5 Gb (moins de 10 W). Évolution possible vers deux OPNsense en CARP.

## Conséquences

- La maintenance d'un serveur n'affecte plus le réseau.
- Double NAT côté Freebox, sans impact pour l'usage prévu.
