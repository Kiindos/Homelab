---
title: "ADR 0006: A low-power mini-PC Proxmox cluster for PROD"
description: Three ThinkCentre Tiny machines in a cluster, with local ZFS and replication, within an energy budget of €40 a month.
date: 2026-09-22
status: remplacé
tags: [proxmox, cluster, energy]
---

# ADR 0006: A low-power mini-PC Proxmox cluster for PROD

> **Superseded decision.** This decision was superseded by [ADR 0010](0010-serveur-unique.md) on 26/09/2026. It is kept for the record.

## Context

The 24/7 services need high availability, with a strong constraint: **at most €40 of electricity a month** for the whole infrastructure, i.e. about 280 W of continuous average draw.

## Options considered

1. **3 × ThinkCentre Tiny (M720q / M920q)**: ~10 W per node at idle, low second-hand cost.
2. **3 × Minisforum MS-01**: built-in 10 Gb, much more RAM, but ~30 W per node and a high purchase cost.
3. **2 nodes + QDevice**: cheaper, but less headroom when something fails.

## Decision

Three ThinkCentre Tiny machines. VM storage on **local ZFS with Proxmox replication** and HA; Ceph postponed until 10 Gb networking and SSDs with power-loss protection arrive.

## Consequences

- Infrastructure estimated at €20 to €28 a month, with the LAB server powered on only on demand.
- Asynchronous replication: at worst a few minutes of data lost if a node fails.
- Power draw measured through the UPS (NUT) and tracked as a PDCA indicator.
