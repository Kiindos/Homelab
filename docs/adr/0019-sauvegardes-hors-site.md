---
title: "ADR 0019 : Sauvegardes hors site chiffrées, ciblées sur ce qui est irremplaçable"
description: Chaque nuit, exports des VM, photos et fichiers partent chiffrés vers un stockage distant de 1 To ; ce qui peut être recopié depuis sa source n'en fait pas partie.
date: 2026-09-28
status: accepté
tags: [sauvegarde, restic, zfs, securite]
---

# ADR 0019 : Sauvegardes hors site chiffrées, ciblées sur ce qui est irremplaçable

## Contexte

Le homelab tient sur un seul serveur ([ADR 0010](0010-serveur-unique.md)). Le RAIDZ2 protège contre la panne de
deux disques, pas contre un incendie, un vol, une erreur de manipulation ou un rançongiciel. Le stockage distant
disponible fait **1 To** : bien moins que les données du serveur, dont une grande partie peut être recopiée depuis
sa source.

## Options envisagées

1. **Tout envoyer** (volumes complets) — impossible en 1 To, et inutile pour des données que l'on peut recopier.
2. **Serveur de sauvegarde Proxmox** — excellent pour les VM, mais demande un stockage compatible chez l'hébergeur.
3. **restic depuis l'hyperviseur, périmètre ciblé** — retenu : un seul outil, chiffrement avant envoi,
   déduplication et compression, SFTP accepté par tous les stockages distants.

## Décision

- **Ce qui part** : les exports complets des VM (vzdump à chaud, non compressés pour que restic déduplique d'une nuit
  à l'autre), les photos et les fichiers (instantanés ZFS figés pendant l'envoi, sans les miniatures ni les vidéos
  réencodées, recalculables), la configuration de l'hyperviseur.
- **Ce qui ne part pas** : les gros volumes recopiables depuis leur source ; la clé de descellement du coffre,
  gardée à part.
- **Transport** : SFTP avec une clé SSH dédiée et les clés d'hôte épinglées, vérifiées contre la documentation de
  l'hébergeur ; une seule règle de sortie du pare-feu.
- **Rétention** : 7 jours, 4 semaines, 6 mois ; vérification hebdomadaire d'un échantillon des données.
- **Surveillance** : le script publie son état ; alerte si un passage échoue, si aucune sauvegarde n'a réussi depuis
  30 heures, ou si le stockage dépasse 80 %.

## Conséquences

- Sans le **mot de passe du dépôt** (gardé hors ligne), les sauvegardes sont illisibles : il est noté dans le
  gestionnaire de mots de passe, pas seulement sur le serveur.
- La clé SSH disparaît avec le serveur : la reprise après sinistre passe par l'accès au compte du stockage distant.
- Les instantanés automatiques du stockage distant protègent contre une suppression, y compris depuis le homelab.
- Une restauration de test par mois (une petite VM sous un identifiant libre) garde la procédure éprouvée.
