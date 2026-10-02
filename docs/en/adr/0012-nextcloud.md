---
title: "ADR 0012: Nextcloud for file storage"
description: Nextcloud is chosen for the family drive, for its compatibility with every device.
date: 2026-09-26
status: accepté
tags: [services, storage]
---

# ADR 0012: Nextcloud for file storage

## Context

The family needs a synchronised file space, on computers (Windows, macOS, Linux) as well as on phones, with
link-based sharing. The main criterion is **compatibility**: a tool that works on every device without tinkering.
Photos already have their dedicated tool (Immich).

## Options considered

1. **Nextcloud**: official clients on every system, WebDAV, calendars and contacts, OpenID Connect and LDAP. In
   return, a heavy PHP application, with a vast catalogue of extensions to keep an eye on.
2. **Seafile**: very fast and frugal, but its own sync protocol and more limited SSO integration in the free
   edition.
3. **Syncthing + FileBrowser**: robust peer-to-peer sync, but two tools, and no simple sharing for non-technical
   people.

## Decision

**Nextcloud**, as a minimal installation: only the useful apps are enabled (files, sharing, possibly calendars and
contacts). Sign-in through OpenID Connect via Authelia (see [ADR 0011](0011-annuaire-sso.md)).

## Consequences

- Frequent updates, including major versions every few months: to be followed in the patching routine.
- Every extension added widens the attack surface: only what is needed is enabled.
- The database and the cache stay on the virtual machine's local disk; the files are on a ZFS dataset of the host,
  backed up separately.
- WebDAV and calendar clients use **app passwords**, revocable one by one.
