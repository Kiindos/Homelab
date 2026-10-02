---
title: "ADR 0017: Inviting people without sending a password, from an accounts page"
description: Accounts are created without a password and the person chooses their own through a one-time link; an administration page, behind the VPN and SSO, replaces the command line.
date: 2026-09-27
status: accepté
tags: [identity, sso, authelia, lldap, security]
---

# ADR 0017: Inviting people without sending a password, from an accounts page

## Context

Relatives' accounts are in the LLDAP directory; Authelia provides single sign-on and two-factor authentication
([ADR 0011](0011-annuaire-sso.md)). Two things were missing:

- **giving a first password** without circulating it (message, paper, spoken);
- **"forgot password"**, which failed: Authelia's service account only had read access to the directory.

Creating accounts also required LLDAP's interface or a script on the administration workstation.

## Options considered

1. **A temporary password** sent by email or SMS, to be changed at first sign-in — the secret travels and stays in a
   mailbox or on a phone; LLDAP cannot force the change.
2. **LLDAP's interface + its own email reset** — nothing to develop, but emails in English, a full administration
   interface (too much power for a simple addition) and a different journey from the portal.
3. **An empty account + Authelia's one-time link**, triggered from a small dedicated page — chosen.

## Decision

- The account is created **without a password**; Authelia sends a **personal, one-time link, valid for 12 h**,
  through which the person chooses their own. It is the same journey as "forgot password": everyone can unblock
  themselves. Authelia's service account is given the right to change passwords (`lldap_password_manager`), except
  those of the directory's administrators.
- Authelia's emails are **translated and styled in the homelab's colours**.
- An **accounts page** (Python, standard library, unprivileged read-only container) creates the account, adds it to
  the chosen groups (all of the directory's groups, **except administrators** and technical groups) and triggers the
  link; it can also resend a link.
- It is reachable **only over the VPN**, behind the internal proxy, which now enforces **SSO** for the services that
  ask for it (forward-auth to Authelia, two-factor authentication, `admins` group). The page accepts the forwarded
  identity only from the proxy's address, and rejects form submissions coming from another site.

## Consequences

- No password is ever known to the administrator or sent.
- The page holds the directory's administration secret (already present on the identity machine): its surface is
  reduced to the bare minimum (creation, non-administrator groups, sending a link); deletion and administration
  rights stay in LLDAP's interface.
- Every action is logged with the administrator's username.
- The journey's security relies on the person's mailbox: a short-lived, one-time link that can be revoked from the
  message limits the risk.
