---
title: "ADR 0014: Monitoring with Prometheus, a custom public NOC behind SSO"
description: Prometheus collects, Alertmanager notifies by email and on the phone (ntfy), and a custom page publishes a NOC viewable after authentication.
date: 2026-09-27
status: accepté
tags: [monitoring, prometheus, grafana, sso, alerts]
---

# ADR 0014: Monitoring with Prometheus, a custom public NOC behind SSO

## Context

The platform runs about ten services across six VMs and a hypervisor whose disks already have more than 50,000
power-on hours. We need to:

- know **before the users do** when a service, a VM or a disk goes down;
- be notified **on the phone** about serious failures, without being disturbed for the rest;
- have a **dashboard (NOC)** viewable from anywhere, without exposing data to just anyone.

## Options considered

1. **Uptime Kuma**: very simple, but limited to probes (no machine or disk metrics).
2. **Zabbix**: complete, but heavy (database, dedicated agents) for a homelab.
3. **Prometheus + Alertmanager + Grafana**: the industry standard, fully declarative configuration (versioned in
   this repository), exporters available for everything that matters here (Linux, SMART, Proxmox, HTTP probes).

For phone notifications: SMS (paid, third-party provider), Telegram/Discord (a third-party account that reads the
alerts) or **self-hosted ntfy** (free app, password-protected topics).

## Decision

- **Prometheus** collects metrics from the machines (node_exporter), the disks (smartctl_exporter), Proxmox (a
  **read-only** API account) and probes the published services through the WAF, like a visitor.
- **Alertmanager** sorts alerts into two levels:
  - *critical* (machine unreachable, public service down, degraded ZFS pool, failing disk, certificate about to
    expire): **email** from a dedicated sending address and a **priority notification** on the phone;
  - *warning* (disk space, memory, new defective sectors): visible on the NOC only.
- The **NOC** is a **custom-written page**, in the site's visual identity: overall status, published services
  (response time, availability, certificates), machines, disks and active alerts. A small collector queries
  Prometheus and Alertmanager every 30 seconds with a set of queries fixed in the code, and writes a JSON snapshot
  that the page displays: **the Internet cannot send a single query to Prometheus**. The page can only read; the WAF
  accepts only `GET` and `HEAD`.
- Sign-in is enforced **by the WAF**: every request is checked with Authelia (*auth_request*) before reaching the
  page, with a second factor, for the family and administrator groups. Only a probe URL, which answers "ok", stays
  open.
- **Grafana** remains available to explore metrics in detail, but as an **internal tool** (VPN, SSO,
  administrators only).
- Self-hosted **ntfy** relays alerts to the mobile app; everything is denied by default, Alertmanager can only
  write and the phone can only read.

## Consequences

- Prometheus, Alertmanager and Grafana stay internal (VPN only); only the NOC and ntfy are published, with the same
  protections as the other services (WAF, country allow-list, rate limiting).
- First version (the same day): Grafana published directly as the NOC. Replaced by the custom page, more readable
  for the family, with a smaller exposed surface, and true to the project's visual identity.
- Monitoring runs on its own VM: an application failure does not take it down with it. However, a hypervisor
  failure takes everything down, monitoring included: an external probe (outside the homelab) is still needed.
- Alert rules are code: every new alert goes through review, like the rest of the infrastructure.
