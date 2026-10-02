---
title: "ADR 0003: OPNsense on a dedicated box, in the DMZ behind the Freebox Pop"
description: The Freebox stays in router mode; a dedicated OPNsense mini-PC receives all inbound traffic in the DMZ.
date: 2026-09-22
status: remplacé
tags: [network, opnsense, freebox]
---

# ADR 0003: OPNsense on a dedicated box, in the DMZ behind the Freebox Pop

> **Superseded decision.** This decision was superseded by [ADR 0010](0010-serveur-unique.md) on 26/09/2026. It is kept for the record.

## Context

The homelab must have its own firewall and VLANs, without breaking the home network or the TV Player. With three environments (PROD, storage, LAB), the firewall becomes the heart of the network.

## Options considered

1. **Freebox in bridge mode**: no double NAT, but the TV Player and stability become a problem.
2. **OPNsense as a VM**: free, but maintaining a host takes the whole network down.
3. **OPNsense on a dedicated mini-PC, in the Freebox's DMZ**: independent of the servers.

## Decision

Option 3: an N100 mini-PC with several 2.5 Gb ports (under 10 W). Possible evolution towards two OPNsense boxes in CARP.

## Consequences

- Maintaining a server no longer affects the network.
- Double NAT on the Freebox side, with no impact on the intended use.
