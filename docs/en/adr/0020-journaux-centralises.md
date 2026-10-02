---
title: "ADR 0020: Centralised logs with VictoriaLogs, agentless collection"
description: Logs from every machine reach VictoriaLogs on the monitoring VM through mechanisms already in place (journald, syslog), and can be searched in Grafana.
date: 2026-09-28
status: accepté
tags: [monitoring, logs, security]
---

# ADR 0020: Centralised logs with VictoriaLogs, agentless collection

## Context

Each machine keeps its logs to itself: diagnosing a problem that crosses several services (a password reset goes
through the WAF, the SSO portal, the directory and the mail relay) means logging in to each VM and matching times by
hand. Metrics are already centralised (Prometheus), logs are not. The server's memory is tight: 32 GB for the whole
homelab.

## Options considered

1. **Loki + Alloy**: the reference Grafana ecosystem, but one Alloy agent per machine (≈ 150 MB each, about ten
   machines) and a Loki that needs tuning to stay frugal.
2. **The Elastic / OpenSearch stack**: powerful, but several GB of RAM for the database alone: out of the question
   here.
3. **VictoriaLogs, agentless collection** — chosen: a single binary (a few hundred MB), strong compression, and it
   accepts directly what the machines can already send: the systemd journal (`systemd-journal-upload`) and syslog
   (firewall).

## Decision

- **Storage**: VictoriaLogs on the monitoring VM, **30-day** retention, disk space cap.
- **Agentless collection**:
  - Debian VMs and the hypervisor: `systemd-journal-upload` sends the systemd journal;
  - containers: Docker's `journald` logging driver (`docker logs` keeps working), hence the same path;
  - firewall: OPNsense's built-in remote syslog (filtering, VPN, DNS).
- **Minimal exposure**: only the **write** routes are reachable from the machines, through a relay that refuses
  reads; reading happens only from Grafana, on the monitoring VM's internal network.
- **Viewing**: Grafana (internal tool, VPN and administrators' SSO), VictoriaLogs data source.
  *Added on 02/10/2026*: a "Logs" dashboard (volume, real errors, filterable lines), and the VictoriaLogs web
  interface, **read-only**, behind the internal proxy (VPN, enforced SSO, administrators). The relay only lets
  queries through (`/select/`), and only from the proxy; writing stays separate.
- **Alerts on logs** (at a later stage): repeated sign-in failures, password reset errors, through the existing
  alert manager.
- **Firewall**: one log-writing flow per zone towards monitoring, and a syslog flow from the firewall.

## Consequences

- Logs contain personal data (IP addresses, usernames): access restricted to administrators, 30-day retention,
  mentioned in the site's privacy page.
- Moving containers to the `journald` driver requires recreating them: done during an announced maintenance.
- Logs also stay on each machine (local journald): centralisation does not replace local diagnosis when monitoring
  itself is down.
- An interrupted upload resumes where it stopped (`systemd-journal-upload` keeps its cursor): no gap after a
  monitoring outage.
