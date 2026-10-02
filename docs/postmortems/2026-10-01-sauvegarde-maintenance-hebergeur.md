---
title: "Post-mortem : sauvegarde de la nuit coupée par une maintenance de l'hébergeur"
description: Une maintenance du stockage distant a coupé l'envoi de la sauvegarde et laissé le dépôt restic verrouillé ; rien de perdu, mais les nuits suivantes auraient échoué aussi.
date: 2026-10-01
tags: [incident, sauvegarde, restic]
---

# Post-mortem : sauvegarde de la nuit coupée par une maintenance de l'hébergeur

## Résumé

| | |
|---|---|
| **Impact** | Pas de sauvegarde hors site pour la nuit du 01/10. Rien de perdu : la sauvegarde précédente (30/09) restait valable et vérifiée |
| **Services touchés** | Aucun service visible ; seule la sauvegarde |
| **Cause** | Maintenance du stockage distant (Storage Box) pendant l'envoi ; restic, coupé net, n'a pas pu retirer son verrou |
| **Détection** | Alerte `SauvegardeEchouee` |

## Chronologie (01/10/2026)

| Heure | Événement |
|---|---|
| 2 h 30 | Début de la sauvegarde : exports des VM, instantanés ZFS |
| 4 h 01 | Début de l'envoi. Il est long : les données importées de Google Drive et Proton Drive partent pour la première fois |
| 10 h 12 | Connexion coupée par l'hébergeur (`ssh command exited: exit status 255`) ; alerte `SauvegardeEchouee` |
| Journée | Diagnostic : maintenance chez l'hébergeur ; le dépôt reste verrouillé par un processus qui n'existe plus |
| Soirée | Après la maintenance : verrou orphelin retiré, contrôle rapide du dépôt lancé depuis Semaphore : conforme (12 min) |

## Cause racine

restic pose un verrou sur le dépôt pendant chaque opération et le retire à la fin. Coupé par la perte de la
connexion, le processus n'a pas pu le retirer : le dépôt est resté verrouillé « par » un processus mort. La
sauvegarde de la nuit suivante, comme sa vérification, se seraient arrêtées sur ce verrou. Une panne
passagère de l'hébergeur devenait ainsi une panne durable de la sauvegarde.

## Ce qui a bien marché / moins bien marché

- **Bien** : l'alerte est arrivée tout de suite ; la sauvegarde précédente était intacte et vérifiée (empreintes
  SHA-256 relues chez l'hébergeur).
- **Moins bien** : vérifier l'état du dépôt après la maintenance demandait une session SSH sur l'hyperviseur et des
  commandes restic à la main.

## Actions correctives

- [x] Chaque opération (sauvegarde, vérification, contrôle) commence par `restic unlock`, qui ne retire que les
  verrous de processus disparus.
- [x] Contrôle à la demande depuis Semaphore (« Vérifier la sauvegarde ») : **rapide** (structure du dépôt et 5 %
  des données relues) ou **complet** (tout le dépôt relu, chaque export de VM comparé octet pour octet à sa copie).
  Il attend son tour si une sauvegarde tourne (verrou commun). Voir le
  [runbook des sauvegardes](../runbooks/sauvegardes.md).
- [x] Passage suivant réussi malgré le volume des imports : 02/10, 2 h 30 → 7 h 08, vérification conforme.
- [ ] Lancer un contrôle complet du dépôt (tout relire), une nuit hors de la fenêtre de sauvegarde.
