---
title: "ADR 0017 : Inviter sans transmettre de mot de passe, depuis une page des comptes"
description: Les comptes sont créés sans mot de passe et la personne choisit le sien par un lien à usage unique ; une page d'administration, derrière le VPN et le SSO, remplace la ligne de commande.
date: 2026-09-27
status: accepté
tags: [identite, sso, authelia, lldap, securite]
---

# ADR 0017 : Inviter sans transmettre de mot de passe, depuis une page des comptes

## Contexte

Les comptes des proches sont dans l'annuaire LLDAP ; Authelia assure la connexion unique et la double
authentification ([ADR 0011](0011-annuaire-sso.md)). Il manquait deux choses :

- **donner un premier mot de passe** sans le faire circuler (message, papier, oral) ;
- **« mot de passe oublié »**, qui échouait : le compte de service d'Authelia n'avait que la lecture sur l'annuaire.

Créer les comptes demandait en outre l'interface de LLDAP ou un script sur le poste d'administration.

## Options envisagées

1. **Mot de passe temporaire** envoyé par e-mail ou SMS, à changer à la première connexion — le secret transite et
   reste dans une boîte ou un téléphone ; LLDAP ne sait pas imposer le changement.
2. **Interface de LLDAP + sa propre réinitialisation par e-mail** — rien à développer, mais e-mails en anglais,
   interface d'administration complète (trop de pouvoir pour un simple ajout) et parcours différent du portail.
3. **Compte créé vide + lien à usage unique d'Authelia**, déclenché depuis une petite page dédiée — retenu.

## Décision

- Le compte est créé **sans mot de passe** ; Authelia envoie un **lien personnel, à usage unique, valable 12 h**,
  par lequel la personne choisit le sien. C'est le même parcours que « mot de passe oublié » : chacun peut se
  débloquer seul. Le compte de service d'Authelia reçoit le droit de changer les mots de passe
  (`lldap_password_manager`), sauf ceux des administrateurs de l'annuaire.
- Les e-mails d'Authelia sont **traduits et aux couleurs du homelab**.
- Une **page des comptes** (Python, bibliothèque standard, conteneur non privilégié en lecture seule) crée le compte,
  l'ajoute aux groupes choisis (tous ceux de l'annuaire, **sauf les administrateurs** et les groupes techniques)
  et déclenche le lien ; elle sait aussi renvoyer un lien.
- Elle n'est joignable que **par le VPN**, derrière le proxy interne qui impose désormais le **SSO** aux services qui
  le demandent (forward-auth vers Authelia, double authentification, groupe `admins`). La page n'accepte l'identité
  transmise que depuis l'adresse du proxy, et refuse les envois de formulaires venus d'un autre site.

## Conséquences

- Aucun mot de passe n'est jamais connu de l'administrateur ni transmis.
- La page détient le secret d'administration de l'annuaire (déjà présent sur la machine d'identité) : sa surface est
  réduite au strict nécessaire (création, groupes non administrateurs, envoi de lien) ; suppression et droits
  d'administration restent dans l'interface de LLDAP.
- Chaque action est journalisée avec l'identifiant de l'administrateur.
- La sécurité du parcours repose sur la boîte e-mail de la personne : un lien court, à usage unique et révocable
  depuis le message limite le risque.
