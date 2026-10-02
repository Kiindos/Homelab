---
title: "ADR 0011: LLDAP directory and Authelia single sign-on"
description: A single LDAP directory for accounts and an SSO portal with two-factor authentication for every published service.
date: 2026-09-26
status: accepté
tags: [security, identity, sso, ldap]
---

# ADR 0011: LLDAP directory and Authelia single sign-on

## Context

Several services are published on the Internet and used by the family. With local accounts in each application, a
departure or a compromised password means going through every tool, and two-factor authentication depends on what
each application offers. Constraint: **free and open-source** tools.

## Options considered

1. **Local accounts in each application**: no extra component, but no central management.
2. **Keycloak**: the enterprise reference, very complete, but heavy (Java, about 1 GB of RAM).
3. **Authentik**: complete and modern, but heavier (database, cache, several processes).
4. **LLDAP + Authelia**: a lightweight LDAP directory and a lightweight SSO portal, designed to work together.

## Decision

Option 4, two tools under free licences:

- **LLDAP** is the **single source** of accounts and groups (for example `famille`, `admins`). Its administration
  interface is reachable only over the VPN.
- **Authelia** is the sign-in portal: it checks the password against LLDAP, enforces **two-factor authentication**
  (TOTP app or WebAuthn security key) and decides who can access what based on groups.

Each application is connected in the strongest way it supports:

| Method | Principle | When |
|---|---|---|
| **OpenID Connect** | The application delegates sign-in to Authelia | First choice (web and mobile apps that support it) |
| **LDAP** | The application checks the password directly against the directory | Native clients that do not handle OpenID Connect |
| **Forward auth** | The WAF asks Authelia before letting the request through | Web applications without authentication of their own |

## Consequences

- One account to create, disable or reset, in a single place.
- Some native clients (TVs, sync apps) cannot go through a web portal: they authenticate over LDAP, **without
  two-factor authentication**. An application whose SSO plugin is no longer maintained goes entirely through LDAP.
  The WAF (rate limiting, banning), strong passwords and app passwords compensate.
- Authelia becomes critical: if it goes down, nobody can sign in. It must be backed up and monitored.
- A way to send emails is needed (password resets, two-factor enrolment).
