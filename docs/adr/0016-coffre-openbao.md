---
title: "ADR 0016 : Un coffre à secrets OpenBao, à côté de SOPS"
description: Les secrets passent dans un coffre OpenBao (connexion SSO, accès par identité, audit) ; SOPS reste le magasin de démarrage.
date: 2026-09-27
status: proposé
tags: [secrets, openbao, securite, sso]
---

# ADR 0016 : Un coffre à secrets OpenBao, à côté de SOPS

## Contexte

Les secrets de la plateforme sont dans un fichier chiffré par SOPS et age, versionné dans le dépôt privé
([ADR 0005](0005-iac-opentofu-ansible.md)). C'est simple et robuste, mais :

- **tout ou rien** : qui peut déchiffrer le fichier lit tous les secrets. Donner à Semaphore
  ([ADR 0015](0015-semaphore-ansible.md)) sa propre clé revenait à lui confier l'intégralité ;
- **aucune trace** de qui a lu quoi, et une révocation impose de rechiffrer et de changer les secrets ;
- des jetons d'outils (API, hébergeur DNS…) restaient dans des fichiers à part sur le poste d'admin.

## Options envisagées

1. **SOPS, un fichier par destinataire** : léger, mais duplication des secrets et toujours aucun audit.
2. **HashiCorp Vault** : la référence, mais sous licence non libre (BSL) depuis 2023.
3. **OpenBao** : fork libre (MPL 2.0, fondation Linux) de Vault, même API, compatible avec Ansible et OpenTofu.

## Décision

**OpenBao**, en test, sur une petite VM dédiée dans la zone identité, sans Docker :

- **connexion des personnes par le SSO** (OpenID Connect via Authelia, second facteur, groupe des administrateurs) ;
- **connexion des machines par AppRole** : Semaphore n'obtient qu'un droit de **lecture** sur les secrets de la
  plateforme, depuis sa seule adresse ; ses identifiants ne fonctionnent nulle part ailleurs ;
- **journal d'audit** déclaré dans la configuration du serveur (impossible à désactiver par l'API) ;
- **descellement automatique** par une clé statique qui reste **sur l'hyperviseur**, dans un dataset à part,
  partagée en lecture seule et remise au seul service par systemd, en mémoire. Une copie du disque de la VM ne
  suffit pas à ouvrir le coffre ; un redémarrage ne demande aucune intervention ;
- **TLS de bout en bout** avec l'autorité interne du homelab ; certificat renouvelé automatiquement ;
- **configuration en code** (OpenTofu) : moteur de secrets, politiques, méthodes de connexion.

SOPS reste le **magasin de démarrage** : il sert à reconstruire le coffre lui-même, et les playbooks lisent l'un ou
l'autre selon une variable, pour une bascule progressive et réversible.

## Conséquences

- Semaphore n'a plus besoin de pouvoir déchiffrer le fichier SOPS : son accès est plus étroit et révocable seul.
- Un service critique de plus : s'il est arrêté, on ne peut plus déployer, mais les services en place continuent
  de fonctionner (leurs secrets sont déjà sur les machines).
- La clé de descellement et les clés de récupération sont conservées **hors ligne** : sans elles, les données du
  coffre sont irrécupérables.
- À venir si le test est concluant : secrets dynamiques (certificats SSH à courte durée plutôt que des clés fixes),
  jetons des outils rangés dans le coffre, sauvegarde régulière de sa base.
