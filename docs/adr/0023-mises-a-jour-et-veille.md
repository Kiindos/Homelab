---
title: "ADR 0023 : Mises à jour du parc et veille de sécurité"
description: Chaque machine publie son état de mise à jour, une veille nocturne compare versions et failles connues, et la maintenance se lance en deux clics dans Semaphore (annonce, puis mise à jour programmée).
date: 2026-09-29
status: accepté
tags: [securite, mises-a-jour, supervision, semaphore]
---

# ADR 0023 : Mises à jour du parc et veille de sécurité

## Contexte

L'audit du 29/09 a trouvé plusieurs mises à jour en retard, découvertes par hasard :

- le pare-feu sans aucun correctif depuis son installation ;
- des paquets de l'hyperviseur en attente ;
- des applications en retard d'une version.

À l'inverse, une lecture manuelle des avis de sécurité du coffre s'est trompée : des failles ont été crues ouvertes
alors que la version en service les corrigeait déjà.

Seuls les correctifs de sécurité Debian s'installaient tout seuls (`unattended-upgrades`). Rien ne surveillait les
images des conteneurs, les versions des applications, le pare-feu ni les redémarrages en attente. Mettre à jour
demandait de se connecter machine par machine.

Besoin exprimé : être prévenu simplement, puis pouvoir annoncer et programmer la mise à jour de tout le parc depuis
Semaphore.

## Options envisagées

1. **Mises à jour automatiques des conteneurs** (Watchtower et équivalents) : changent de version sans relecture, à
   n'importe quelle heure, avec l'accès au socket Docker. Écarté.
2. **Demandes de fusion automatiques** (Renovate, Dependabot) : très bien pour les versions, mais demande une forge et
   une intégration continue qui n'existent pas encore ici, et ne voit ni les paquets des machines, ni les failles des
   images en service, ni le pare-feu. À reconsidérer avec une forge locale.
3. **Notification de nouvelles images** (Diun, What's Up Docker) : ne dit rien des failles, un agent par machine
   avec le socket Docker. Écarté.
4. **Relevé par machine, veille centrale, maintenance orchestrée** — retenu.

## Décision

1. **Relevé par machine** (rôle `agent_supervision`), toutes les heures, pour Prometheus (collecteur « textfile »,
   sans nouveau port) :
   - paquets en attente par origine (sécurité, Debian, Proxmox) ;
   - redémarrage nécessaire, noyau en service ;
   - images des conteneurs en service et leur empreinte ;
   - sur l'hyperviseur, version du pare-feu (compte limité au tableau de bord, certificat épinglé).
2. **Veille de sécurité** chaque nuit sur la VM de supervision (`supervision/files/veille`). C'est Trivy, image
   officielle **figée par empreinte**, plus un script Python sans dépendance. Elle regarde :
   - les failles des images en service. La liste des paquets est calculée une seule fois par empreinte : les nuits
     suivantes, seule la base de failles est rafraîchie, aucune image n'est retéléchargée ;
   - les nouvelles constructions de la même version (en-tête du manifeste) ;
   - la dernière version publiée et les avis de sécurité de chaque projet (API GitHub, requêtes conditionnelles).
3. **Alertes « veille »** : e-mail et notification sur le téléphone, rappel chaque semaine tant que rien n'est fait,
   puis message « fait ». Jamais sur le NOC, que la famille consulte. Le détail est dans un tableau Grafana
   réservé à l'administrateur. N'alerte que ce qui demande une action :
   - un avis de sécurité vise la version en service ;
   - une nouvelle construction corrige des failles graves ;
   - des correctifs de sécurité ne sont pas installés depuis un jour ;
   - un redémarrage attend depuis trois jours ;
   - le pare-feu est en retard.
4. **Maintenance en deux clics** dans Semaphore :
   - *Annoncer aux membres* : e-mail et bandeau, même traitement que la page des annonces ;
   - *Mettre à jour le parc* : chaque machine pose une **minuterie locale** à l'heure annoncée. Ni Semaphore ni le
     VPN ne sont nécessaires à ce moment-là. Les machines passent l'une après l'autre dans un ordre fixé : les
     moins visibles d'abord, l'entrée publique et l'outil d'administration à la fin. Les alertes sont en sourdine
     pendant la fenêtre. Chaque machine installe ses paquets, retélécharge les images **de la même version** et
     redémarre si nécessaire ;
   - l'hyperviseur n'est inclus qu'à la demande et ne redémarre jamais tout seul.
5. **Semaphore ne s'administre pas lui-même** : il dépose une demande datée dans un dossier monté dans son conteneur.
   Sa machine la vérifie strictement (format, date, sans suivre de lien) avant de programmer sa propre mise à jour.
6. **Un changement de version passe toujours par le code** (relecture, commit, déploiement), jamais par la mise à jour
   du parc.

## Conséquences

- Une nuit de veille coûte une base de failles (quelques dizaines de mégaoctets) et une cinquantaine de requêtes
  GitHub. Sans jeton, l'adresse de la maison est limitée à 60 requêtes par heure : les réponses sont mises en cache,
  et un jeton sans accès aux dépôts lève la limite.
- Le premier passage télécharge toutes les images une fois (plusieurs gigaoctets).
- Un projet sans avis publiés sur GitHub n'est suivi que par ses versions et par les failles de son image.
- Le pare-feu reste mis à jour à la main, dans son interface : la veille ne fait que prévenir.
- Semaphore voit tout le parc : ses droits restent ceux d'Ansible, sa propre machine exceptée.
