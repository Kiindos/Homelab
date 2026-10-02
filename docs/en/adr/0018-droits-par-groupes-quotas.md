---
title: "ADR 0018: One group per service, with administration rights and quotas derived from the directory"
description: Access to each service is granted by adding someone to a group; applications' administration rights follow the administrators group; quotas are set from the accounts page.
date: 2026-09-28
status: accepté
tags: [identity, sso, authelia, lldap, security]
---

# ADR 0018: One group per service, with administration rights and quotas derived from the directory

## Context

Until now there were only two groups: `famille` (all personal services) and `admins` (everything). It was impossible
to give someone "photos, but not the drive". Each application also managed its administrators separately, and the
space allocated to each person (drive, photos) could only be set in each application's interface.

The directory (LLDAP) cannot nest groups.

## Options considered

1. **Per-service groups only** — fine-grained, but every service has to be ticked for every relative.
2. **One group per service, plus groups that open everything** (`famille`, `admins`) — chosen: current relatives
   are unaffected, and a guest can have just one service.
3. **Roles in each application** — as many places to keep up to date, invisible to the SSO.

## Decision

- One group per service (`photos`, `drive`…); each service accepts its group, `famille` and `admins`. The mapping is
  described **in a single place** in the inventory; Authelia's rules (OpenID Connect policies, the WAF's barrier) and
  the applications' directory filters are generated from it.
- Applications' **administration rights** are **derived from the `admins` group** at every sign-in, through
  Authelia's computed attributes (CEL expressions) passed as claims: role in the photo gallery, administration group
  in the drive.
- **Quotas** (drive, photos) are set on the accounts page, alongside the space used. Least privilege: for the drive,
  a dedicated account that is **sub-administrator of the family groups only** (it can touch neither the
  administrators nor other groups); for photos, an **API key restricted** to reading and modifying accounts. A
  dedicated firewall flow, from the identity machine to the applications machine.
- The behaviour was tested on a throwaway Authelia instance before production: a "photos only" account enters the
  gallery as a plain user and is refused the drive; an administrator gets their role in both.

## Consequences

- Granting or removing access = ticking a group (accounts page) or removing someone from a group (directory).
- Making someone an application administrator = adding them to `admins`; removing that group removes their rights
  at their next sign-in.
- The accounts page holds two more credentials (delegated account, API key): both restricted, revocable on their
  own, and inactive until they are provided.
- The photo gallery quota can only be set once the account exists (first sign-in); a default quota could be applied
  at creation.
