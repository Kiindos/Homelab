---
title: "Premier serveur en service, premier audit"
description: Le T330 tourne, le pare-feu aussi ; un audit de l'existant fixe les priorités avant d'ajouter des services.
date: 2026-09-26
tags: [journal, proxmox, opnsense, sécurité]
---

# Premier serveur en service, premier audit

Le Dell T330 est en service sous Proxmox VE, avec ses quatre disques en ZFS RAIDZ2 et OPNsense dans une machine
virtuelle. Avant d'installer le moindre service, j'ai fait un **audit de l'existant** : comparer ce qui tourne
vraiment à ce que disait la documentation.

## Ce que l'audit a changé

- **L'architecture s'adapte au matériel réel.** Le cluster de mini-PC et le pare-feu dédié ne sont pas pour tout
  de suite : un seul serveur porte tout, et les ADR correspondants sont remplacés par l'[ADR 0010](../adr/0010-serveur-unique.md)
  plutôt que modifiés, pour garder la trace du raisonnement.
- **Un domaine, et seulement le mien.** Des noms internes avaient été créés sous un domaine qui ne m'appartient
  pas. Sans conséquence aujourd'hui, mais exploitable par quiconque l'achèterait : tout est passé sous
  `maximebertrand.net` ([ADR 0009](../adr/0009-domaine-unique.md)).
- **Des noms plutôt que des IP.** Le DNS interne connaît maintenant chaque machine, avec validation DNSSEC.
- **Une liste de corrections classées par priorité**, à traiter avant d'ouvrir quoi que ce soit sur Internet.

## Les décisions pour la suite

- Les services personnels (photos, fichiers) seront publiés **sans passer par Cloudflare**, derrière le pare-feu et
  un WAF ([ADR 0008](../adr/0008-exposition-directe-waf.md)).
- Un **annuaire unique et un portail SSO avec double authentification** pour tous les services publiés
  ([ADR 0011](../adr/0011-annuaire-sso.md)).
- **Nextcloud** pour les fichiers, choisi pour sa compatibilité avec tous les appareils
  ([ADR 0012](../adr/0012-nextcloud.md)).

## Le soir même : la plateforme en code

Les corrections prioritaires de l'audit sont appliquées, puis cinq machines virtuelles ont été créées par OpenTofu,
chacune dans sa zone réseau, et configurées par Ansible : WAF, identité (annuaire + SSO), applications, outils
internes et documentation. Les règles du pare-feu sont elles aussi générées depuis le code, à partir de la matrice
de flux. Tout est rejouable : un second passage des playbooks ne change plus rien.

Quelques leçons au passage :

- un jeton Proxmox « à privilèges séparés » n'a que l'**intersection** des droits du jeton et de son utilisateur ;
- retirer l'adresse IPv4 d'un pont ne suffit pas : l'adresse IPv6 de lien local restait joignable ;
- un rôle Ansible qui impose les droits d'un dossier de base de données peut couper la base qui l'utilise :
  le propriétaire doit être celui du conteneur, pas root.

Prochaine étape : les certificats publics et l'ouverture aux premiers utilisateurs.
