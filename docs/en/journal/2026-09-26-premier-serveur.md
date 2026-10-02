---
title: "First server in service, first audit"
description: The T330 is running, and so is the firewall; an audit of what exists sets the priorities before adding services.
date: 2026-09-26
tags: [journal, proxmox, opnsense, security]
---

# First server in service, first audit

The Dell T330 is in service under Proxmox VE, with its four disks in ZFS RAIDZ2 and OPNsense in a virtual machine.
Before installing a single service, I carried out an **audit of what exists**: comparing what actually runs with what
the documentation said.

## What the audit changed

- **The architecture adapts to the actual hardware.** The mini-PC cluster and the dedicated firewall are not for
  now: a single server carries everything, and the corresponding ADRs are superseded by
  [ADR 0010](../adr/0010-serveur-unique.md) rather than edited, to keep a record of the reasoning.
- **One domain, and only mine.** Internal names had been created under a domain that does not belong to me.
  Harmless today, but exploitable by whoever bought it: everything moved under `maximebertrand.net`
  ([ADR 0009](../adr/0009-domaine-unique.md)).
- **Names rather than IP addresses.** The internal DNS now knows every machine, with DNSSEC validation.
- **A list of fixes ranked by priority**, to be dealt with before opening anything to the Internet.

## Decisions for what comes next

- Personal services (photos, files) will be published **without going through Cloudflare**, behind the firewall and
  a WAF ([ADR 0008](../adr/0008-exposition-directe-waf.md)).
- **A single directory and an SSO portal with two-factor authentication** for every published service
  ([ADR 0011](../adr/0011-annuaire-sso.md)).
- **Nextcloud** for files, chosen for its compatibility with every device ([ADR 0012](../adr/0012-nextcloud.md)).

## The same evening: the platform as code

The audit's priority fixes were applied, then five virtual machines were created by OpenTofu, each in its own network
zone, and configured by Ansible: WAF, identity (directory + SSO), applications, internal tools and documentation. The
firewall rules are generated from the code too, from the flow matrix. Everything is replayable: a second run of the
playbooks no longer changes anything.

A few lessons along the way:

- a Proxmox token with "privilege separation" only gets the **intersection** of the token's rights and its user's;
- removing a bridge's IPv4 address is not enough: its link-local IPv6 address was still reachable;
- an Ansible role that enforces the permissions of a database folder can break the database using it: the owner
  must be the container's user, not root.

Next step: public certificates and opening up to the first users.
