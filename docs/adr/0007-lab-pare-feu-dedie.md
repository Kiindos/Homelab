---
title: "ADR 0007 : LAB isolé derrière son propre pare-feu"
description: Le LAB a sa propre OPNsense, reliée à la PROD par un transit routé sans NAT.
date: 2026-09-22
status: accepté
tags: [réseau, lab, sécurité]
---

# ADR 0007 : LAB isolé derrière son propre pare-feu

## Contexte

Le LAB reproduit une infra PME (AD, RADIUS, 802.1X, Wi-Fi, WAF) et sert à tester avant passage en PROD. Une expérimentation ratée ne doit jamais atteindre la PROD.

## Décision

- Une **OPNsense virtuelle** sur le serveur LAB, reliée à la PROD par une **zone de transit routée, sans NAT** (les journaux de la PROD voient les vraies adresses).
- Flux LAB → PROD **interdits par défaut**.
- L'**iDRAC du serveur LAB reste sur le réseau d'administration de la PROD**, pour pouvoir le rallumer même quand son pare-feu est éteint.

## Conséquences

Le LAB est une infra autonome et réaliste. Quand le serveur LAB est éteint, tout son réseau disparaît, ce qui est attendu.
