---
title: "ADR 0008: Exposing personal services directly behind OPNsense and BunkerWeb"
description: Photos and the drive are published without Cloudflare, through a port forward to a BunkerWeb WAF in the DMZ.
date: 2026-09-26
status: accepté
tags: [network, security, waf, opnsense]
---

# ADR 0008: Exposing personal services directly behind OPNsense and BunkerWeb

## Context

Photos (Immich) and the drive must be reachable from the Internet, for the family as well as from a phone on 4G.
[ADR 0002](0002-cloudflare-tunnel.md) reserves Cloudflare Tunnel for public content, because Cloudflare decrypts
the traffic. On top of that, its free plan limits each request to 100 MB, which blocks video uploads.

## Options considered

1. **Cloudflare Tunnel + Cloudflare Access**: no open port and identity-based filtering, but Cloudflare sees the
   photos in clear text and large uploads fail.
2. **VPN only**: the safest solution, but every device in the family has to be configured.
3. **Port forward to a WAF in the DMZ**: traffic stays encrypted end to end up to the homelab, with no size limit;
   in return, the home IP address is public and the homelab takes the scans directly.

## Decision

Option 3, with defence in depth:

| Layer | Role |
|---|---|
| Cloudflare DNS in "DNS only" mode | Resolution only, no proxy |
| OPNsense | Only port 443 is forwarded, and only to the WAF; geo-filtering and block lists; the DMZ can reach only the applications' ports |
| BunkerWeb (DMZ) | TLS termination, OWASP rules (ModSecurity CRS), rate limiting, banning suspicious behaviour, CrowdSec |
| Authelia | Single sign-on portal with two-factor authentication (see [ADR 0011](0011-annuaire-sso.md)) |
| Applications | Permission checks, tracked updates |

## Consequences

- There is **no real IP allow-list**: the family's IP addresses change, on 4G in particular. Geo-filtering and
  suspicious-behaviour detection replace that allow-list; authentication (Authelia and the applications) becomes the
  last barrier and must be solid.
- The OWASP rules may block legitimate uploads (large files, mobile app APIs): they will need tuning, based on the
  WAF's logs.
- The home IP address is visible in public DNS. Only the names of the services actually published appear there:
  internal names stay resolved by OPNsense.
- The Cloudflare tunnel is still used for the showcase site and the status page (ADR 0002).
