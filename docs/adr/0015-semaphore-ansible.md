---
title: "ADR 0015 : Semaphore UI pour lancer Ansible depuis le homelab"
description: Une interface web interne, protégée par le SSO, lance les playbooks versionnés ; ses accès sont limités et vérifiés.
date: 2026-09-27
status: accepté
tags: [ansible, automatisation, sso, securite]
---

# ADR 0015 : Semaphore UI pour lancer Ansible depuis le homelab

## Contexte

Toute la configuration des machines est décrite par des playbooks Ansible ([ADR 0005](0005-iac-opentofu-ansible.md)),
lancés jusqu'ici depuis le poste d'administration. Cela suppose d'avoir ce poste sous la main, correctement installé,
et ne laisse aucune trace partagée de ce qui a été lancé, quand et avec quel résultat.

## Options envisagées

1. **Rester sur le poste d'admin** : simple, mais pas d'historique ni de lancement depuis un autre appareil.
2. **AWX (Ansible Automation Platform libre)** : très complet, mais demande Kubernetes : disproportionné ici.
3. **Semaphore UI** : un seul conteneur, une base SQLite, connexion OpenID Connect, historique des exécutions,
   lancement en mode test (*dry run* + *diff*) depuis le navigateur.

## Décision

**Semaphore UI**, sur la VM des outils internes, accessible **uniquement par le VPN** et par le **SSO** (groupe des
administrateurs, second facteur obligatoire). Il n'existe aucun compte à mot de passe local.

Semaphore détient de fait les clés de toute l'infrastructure ; ses accès sont donc bornés :

- **dépôts** : le dépôt public est cloné anonymement ; le dépôt privé (inventaire, secrets chiffrés) avec une clé de
  déploiement en **lecture seule** : Semaphore ne peut rien pousser ;
- **SSH** : une clé dédiée, acceptée par les machines **uniquement depuis l'adresse de Semaphore**, sans redirection
  de ports ni d'agent ; le pare-feu n'ouvre le port 22 que vers les machines administrées ;
- **identité des machines** : l'image officielle désactive la vérification des clés d'hôtes SSH (pour git comme pour
  Ansible). Elle est rétablie : les clés sont relevées sur les machines elles-mêmes par Ansible, celles de GitHub
  viennent de sa publication officielle, et un relais retire les options qui la désactivent ;
- **secrets** : Semaphore a sa propre clé de déchiffrement SOPS, révocable sans toucher à celle du poste d'admin ;
  ses propres secrets sont chiffrés dans sa base ;
- **une exécution à la fois**, pour que deux playbooks ne modifient jamais la même machine en même temps.

Semaphore **ne gère pas la VM qui l'héberge** : redémarrer Docker ou son propre conteneur couperait la tâche en cours.
Cette VM reste déployée depuis le poste d'admin.

## Conséquences

- Les playbooks deviennent lançables depuis n'importe quel appareil connecté au VPN, avec un historique consultable.
- L'image est reconstruite localement (outils des playbooks aux mêmes versions que sur le poste d'admin) : ses
  mises à jour passent par ce dépôt, pas par un `pull` automatique.
- Compromettre Semaphore reviendrait à compromettre l'infrastructure : il est traité comme un équipement
  d'administration (VPN, SSO, accès réseau minimal, supervision de sa disponibilité).
