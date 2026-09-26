---
title: "ADR 0011 : Annuaire LLDAP et authentification unique Authelia"
description: Un annuaire LDAP unique pour les comptes et un portail SSO avec double authentification pour tous les services publiés.
date: 2026-09-26
status: accepté
tags: [sécurité, identité, sso, ldap]
---

# ADR 0011 : Annuaire LLDAP et authentification unique Authelia

## Contexte

Plusieurs services sont publiés sur Internet et utilisés par la famille. Avec des comptes locaux dans chaque
application, un départ ou un mot de passe compromis impose de passer dans chaque outil, et la double
authentification dépend de ce que chaque application propose. Contrainte : des outils **gratuits et open source**.

## Options envisagées

1. **Comptes locaux dans chaque application** : aucun composant en plus, mais aucune gestion centralisée.
2. **Keycloak** : la référence en entreprise, très complet, mais lourd (Java, environ 1 Go de RAM).
3. **Authentik** : complet et moderne, mais plus lourd (base de données, cache, plusieurs processus).
4. **LLDAP + Authelia** : un annuaire LDAP léger et un portail SSO léger, conçus pour fonctionner ensemble.

## Décision

Option 4, deux outils sous licence libre :

- **LLDAP** est la **source unique** des comptes et des groupes (par exemple `famille`, `admins`). Son interface
  d'administration n'est joignable que par le VPN.
- **Authelia** est le portail de connexion : il vérifie le mot de passe dans LLDAP, impose la **double
  authentification** (application TOTP ou clé de sécurité WebAuthn) et décide qui accède à quoi selon les groupes.

Chaque application est branchée de la façon la plus solide qu'elle supporte :

| Méthode | Principe | Quand |
|---|---|---|
| **OpenID Connect** | L'application délègue la connexion à Authelia | En priorité (applications web et mobiles qui le supportent) |
| **LDAP** | L'application vérifie le mot de passe directement dans l'annuaire | Clients natifs qui ne gèrent pas OpenID Connect |
| **Forward auth** | Le WAF demande à Authelia avant de laisser passer | Applications web sans authentification propre |

## Conséquences

- Un compte à créer, à désactiver ou à réinitialiser en un seul endroit.
- Certains clients natifs (TV, applications de synchronisation) ne savent pas passer par un portail web : ils
  s'authentifient en LDAP, **sans double authentification**. Une application dont l'extension SSO n'est plus
  maintenue passe entièrement par LDAP. Le WAF (limitation de débit, bannissement), les mots de passe forts et les
  mots de passe d'application compensent.
- Authelia devient critique : s'il tombe, plus personne ne se connecte. Il doit être sauvegardé et supervisé.
- Il faut un moyen d'envoyer des e-mails (réinitialisation de mot de passe, enrôlement de la double
  authentification).
