---
title: "ADR 0007: A LAB isolated behind its own firewall"
description: The LAB has its own OPNsense, connected to PROD through a routed transit without NAT.
date: 2026-09-22
status: accepté
tags: [network, lab, security]
---

# ADR 0007: A LAB isolated behind its own firewall

## Context

The LAB reproduces a small-business infrastructure (AD, RADIUS, 802.1X, Wi-Fi, WAF) and is used to test before moving to PROD. A failed experiment must never reach PROD.

## Decision

- A **virtual OPNsense** on the LAB server, connected to PROD through a **routed transit zone, without NAT** (PROD's logs see the real addresses).
- LAB → PROD flows **denied by default**.
- The **LAB server's iDRAC stays on PROD's administration network**, so that it can be powered back on even when its firewall is off.

## Consequences

The LAB is a self-contained, realistic infrastructure. When the LAB server is off, its whole network disappears, which is expected.
