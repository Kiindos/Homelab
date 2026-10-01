---
title: "Runbook : vérifier et restaurer les sauvegardes"
description: Contrôler la sauvegarde hors site, restaurer un fichier ou une VM, reconstruire après la perte du serveur.
tags: [sauvegarde, restic, zfs]
---

# Runbook : vérifier et restaurer les sauvegardes

**Quand l'utiliser :** une alerte de sauvegarde, une maintenance ou un incident chez l'hébergeur du stockage distant,
un fichier ou une VM à récupérer, ou la perte du serveur.
**Durée estimée :** quelques minutes pour un contrôle rapide ou un fichier ; une à deux heures pour un contrôle
complet ou une VM ; une journée pour une reprise après sinistre.
**Prérequis :** VPN d'administration ; pour la reprise après sinistre, le **mot de passe du dépôt restic** (gardé
hors ligne) et l'accès au compte du stockage distant.

Choix et périmètre : [ADR 0019](../adr/0019-sauvegardes-hors-site.md). Code : rôle Ansible `sauvegarde`.

## Ce qui tourne chaque nuit

À 2 h 30, l'hyperviseur lance la sauvegarde :

1. **exports des VM**, à chaud, sans compression (restic déduplique et compresse lui-même) ;
2. **instantanés ZFS** des photos et du drive, figés pendant l'envoi ;
3. **envoi restic** chiffré côté client vers le stockage distant, en SFTP, avec une clé SSH dédiée et des clés
   d'hôte épinglées ; la configuration de l'hyperviseur part aussi ;
4. **vérification de bout en bout** : chaque export de VM et un échantillon de fichiers sont relus chez l'hébergeur
   et comparés à l'original par empreinte SHA-256 ; un septième du dépôt est relu chaque nuit (`restic check
   --read-data-subset=N/7`), donc tout le dépôt en une semaine ;
5. **rétention** : 7 quotidiennes, 4 hebdomadaires, 6 mensuelles.

Le script publie son état pour Prometheus : alertes si un passage ou sa vérification échoue, si rien n'a réussi
depuis 30 heures, ou si le stockage distant dépasse 80 %. Le NOC affiche le dernier passage.

## Vérifier

Après une alerte, une maintenance chez l'hébergeur ou toute coupure pendant l'envoi : **Semaphore** → modèle
**« Vérifier la sauvegarde »**, sans attendre la nuit suivante.

- **rapide** : structure du dépôt et 5 % des données relues (une dizaine de minutes) ;
- **complet** : tout le dépôt relu et chaque export de VM comparé octet pour octet à l'original (une à deux heures,
  de préférence la nuit, hors de la fenêtre de sauvegarde).

Le contrôle attend son tour si une sauvegarde tourne (verrou commun). Il commence, comme la sauvegarde, par
`restic unlock`, qui retire les verrous laissés par un processus disparu (cas d'une connexion coupée :
[post-mortem du 01/10](../postmortems/2026-10-01-sauvegarde-maintenance-hebergeur.md)). Tâche verte = conforme ;
rouge = écart ou échec, avec le compte rendu dans la tâche.

En ligne de commande, sur l'hyperviseur :

```bash
systemctl list-timers sauvegarde-homelab.timer
journalctl -u sauvegarde-homelab -n 30 --no-pager
restic snapshots          # avec RESTIC_REPOSITORY et RESTIC_PASSWORD_FILE de la configuration du rôle
```

## Restaurer un fichier

```bash
restic ls latest | grep 'nom-du-fichier'
restic restore latest --target /chemin/de/restauration --include '<chemin complet du fichier dans l instantané>'
```

Remettre le fichier à sa place, puis le faire voir à l'application (drive : `occ files:scan <utilisateur>`).
Supprimer le dossier de restauration après usage.

## Restaurer une VM

1. Restaurer l'export : `restic restore latest --target /chemin/de/restauration --include <dossier des exports>` ;
2. `qmrestore <export>.vma <identifiant> --storage local-zfs` : sous un **nouvel identifiant** pour un essai ; sous
   le même identifiant seulement après avoir supprimé la VM d'origine, ce qui se décide explicitement ;
3. démarrer la VM, vérifier le service (sonde du NOC au vert).

## Reprise après sinistre (serveur perdu)

La clé SSH du serveur disparaît avec lui : l'accès au dépôt passe par le compte du stockage distant (nouvelle clé
déposée depuis sa console) et par le mot de passe du dépôt restic.

1. Réinstaller Proxmox et recréer le pool ZFS ;
2. installer restic, déposer une nouvelle clé, restaurer les exports de VM, la configuration de l'hyperviseur (comme
   référence) et les données (photos, drive) ;
3. restaurer les VM dans l'ordre : pare-feu, identité, coffre (clé de descellement gardée à part), applications ;
4. relancer OpenTofu et Ansible : un `plan` sans changement confirme que la reconstruction correspond au code.

## État des tests

| Ce qui est éprouvé | Comment | Dernier résultat |
|---|---|---|
| Lecture des données chez l'hébergeur | Empreintes SHA-256 de chaque export de VM et d'un échantillon de fichiers, chaque nuit | Conforme le 30/09/2026 |
| Intégrité du dépôt | Un septième relu chaque nuit ; contrôle rapide à la demande | Contrôle rapide conforme le 01/10/2026 |
| Restauration complète d'une VM | `qmrestore` sous un identifiant libre, démarrage, puis suppression | **Pas encore faite** ; prévue une fois par mois |
| Reprise après sinistre | — | Jamais exercée |

## Retour arrière

Une restauration se fait toujours **à côté** de l'existant (dossier ou identifiant de VM libres) : rien n'est
écrasé tant que le résultat n'est pas vérifié. En cas d'erreur, supprimer la copie restaurée.
