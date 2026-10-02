---
title: "ADR 0002: Public exposure through Cloudflare Tunnel"
description: The showcase site is exposed through an outbound tunnel, with no inbound port open.
date: 2026-09-21
status: accepté
tags: [cloudflare, network, security]
---

# ADR 0002: Public exposure through Cloudflare Tunnel

## Context

The showcase site and the status page must be public. The infrastructure sits behind a Freebox, with a residential IP address.

## Options considered

1. **Forwarding ports 80/443**: personal IP exposed and scanned, dependency on dynamic DNS.
2. **A front-end VPS + WireGuard**: robust, but costly or dependent on unstable free offers.
3. **Cloudflare Tunnel**: outbound connections only, TLS, DDoS protection and WAF included.

## Decision

Cloudflare Tunnel (`cloudflared` as two replicas in the DMZ), described in OpenTofu with the official provider, **for public content only** (showcase site, status page). Personal services are published another way (see [ADR 0008](0008-exposition-directe-waf.md)).

## Consequences

- Cloudflare decrypts the traffic: acceptable for public content, **ruled out** for personal data (VPN).
- The domains must use Cloudflare's DNS servers.
