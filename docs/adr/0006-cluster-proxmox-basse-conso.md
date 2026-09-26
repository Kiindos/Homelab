---
title: "ADR 0006 : Cluster Proxmox de PROD en mini-PC basse consommation"
description: Trois ThinkCentre Tiny en cluster, avec ZFS local et réplication, dans un budget énergie de 40 €/mois.
date: 2026-09-22
status: remplacé
tags: [proxmox, cluster, énergie]
---

# ADR 0006 : Cluster Proxmox de PROD en mini-PC basse consommation

> **Décision remplacée.** Cette décision a été remplacée par l'[ADR 0010](0010-serveur-unique.md) le 26/09/2026. Elle est conservée pour l'historique.


## Contexte

Les services 24/24 ont besoin de haute disponibilité, avec une contrainte forte : **40 € d'électricité par mois au maximum** pour toute l'infra, soit environ 280 W en moyenne continue.

## Options envisagées

1. **3 × ThinkCentre Tiny (M720q / M920q)** : ~10 W par nœud au repos, faible coût d'occasion.
2. **3 × Minisforum MS-01** : 10 Gb intégré, beaucoup plus de RAM, mais ~30 W par nœud et un coût d'achat élevé.
3. **2 nœuds + QDevice** : moins cher, mais moins de marge en cas de panne.

## Décision

Trois ThinkCentre Tiny. Stockage des VM en **ZFS local avec réplication Proxmox** et HA ; Ceph reporté à l'arrivée du 10 Gb et de SSD avec protection contre les coupures.

## Conséquences

- Infra estimée entre 20 et 28 € par mois, le serveur LAB n'étant allumé qu'à la demande.
- Réplication asynchrone : quelques minutes de données perdues au pire en cas de panne d'un nœud.
- Consommation mesurée via l'onduleur (NUT) et suivie comme indicateur du PDCA.
