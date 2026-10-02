---
title: "ADR 0009: A single domain, maximebertrand.net"
description: maximebertrand.net is used for everything (showcase site, public services, internal zone), replacing ADR 0004.
date: 2026-09-26
status: accepté
tags: [dns, cloudflare, security]
---

# ADR 0009: A single domain, maximebertrand.net

Supersedes [ADR 0004](0004-domaines.md).

## Context

ADR 0004 planned two domains: a `.eu` for the showcase site and a `.fr` for the lab. In practice, the domain
registered and managed at Cloudflare is `maximebertrand.net`. Yet the first machines had been given internal names
under `.eu`, a domain I do not own.

Using a domain you do not own, even internally only, is risky: if someone buys it, they answer instead of the
internal DNS as soon as a query leaks to the Internet (VPN down, misconfigured workstation) and can hijack
connections. It is also impossible to obtain a valid certificate for those names.

## Options considered

1. **Keep two domains**: a clean separation, but two zones, two API tokens and two certificates to manage.
2. **A single domain with subdomains**: one zone, one wildcard certificate, one thing to monitor.

## Decision

`maximebertrand.net` for everything:

| Use | Name | Resolution |
|---|---|---|
| Showcase site, status page | `maximebertrand.net`, `status.maximebertrand.net` | Public (Cloudflare) |
| Published personal services | subdomains of `maximebertrand.net` | Public (Cloudflare, "DNS only") |
| Internal machines and services | `*.home.maximebertrand.net` | **Only** through the internal DNS (OPNsense) |

## Consequences

- Internal names sit under a domain I control: no hijacking possible, and valid certificates through Let's
  Encrypt's DNS challenge, without exposing anything.
- Certificates: public names each have their own certificate, obtained through an **HTTP challenge** on the WAF, so
  as to leave **no DNS token** on the machine exposed to the Internet (a stolen token would allow the whole zone to
  be hijacked). These names appear in the Certificate Transparency logs, which is accepted: they are in public DNS
  anyway. The internal zone uses a **wildcard certificate** obtained through a DNS challenge from a machine
  reachable only over the VPN.
- Migration on 26/09/2026: internal DNS, hypervisor and tools migrated; the firewall's system name remains.
