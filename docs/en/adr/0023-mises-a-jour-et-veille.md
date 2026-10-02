---
title: "ADR 0023: Fleet updates and security watch"
description: Each machine publishes its update status, a nightly watch compares versions and known vulnerabilities, and maintenance is launched in two clicks in Semaphore (announcement, then scheduled update).
date: 2026-09-29
status: accepté
tags: [security, updates, monitoring, semaphore]
---

# ADR 0023: Fleet updates and security watch

## Context

The 29/09 audit found several overdue updates, discovered by chance:

- the firewall without a single patch since it was installed;
- hypervisor packages pending;
- applications one version behind.

Conversely, a manual reading of the vault's security advisories got it wrong: vulnerabilities were believed open
when the running version had already fixed them.

Only Debian security patches were installed automatically (`unattended-upgrades`). Nothing watched the container
images, the application versions, the firewall or pending reboots. Updating meant logging in machine by machine.

The need as stated: be notified simply, then be able to announce and schedule the update of the whole fleet from
Semaphore.

## Options considered

1. **Automatic container updates** (Watchtower and the like): change versions without review, at any time, with
   access to the Docker socket. Ruled out.
2. **Automatic merge requests** (Renovate, Dependabot): very good for versions, but requires a forge and continuous
   integration that do not exist here yet, and sees neither the machines' packages, nor the vulnerabilities of the
   running images, nor the firewall. To be reconsidered with a local forge.
3. **New image notifications** (Diun, What's Up Docker): say nothing about vulnerabilities, one agent per machine
   with the Docker socket. Ruled out.
4. **Per-machine reporting, central watch, orchestrated maintenance** — chosen.

## Decision

1. **Per-machine reporting** (`agent_supervision` role), every hour, for Prometheus (textfile collector, no new
   port):
   - pending packages by origin (security, Debian, Proxmox);
   - reboot required, running kernel;
   - running container images and their digest;
   - on the hypervisor, the firewall's version (account restricted to the dashboard, pinned certificate).
2. **Security watch** every night on the monitoring VM (`supervision/files/veille`). It is Trivy, the official image
   **pinned by digest**, plus a dependency-free Python script. It looks at:
   - the vulnerabilities of the running images. The package list is computed only once per digest: on the following
     nights, only the vulnerability database is refreshed and no image is downloaded again;
   - new builds of the same version (manifest header);
   - the latest published release and the security advisories of each project (GitHub API, conditional requests).
3. **"Watch" alerts**: email and phone notification, a weekly reminder as long as nothing is done, then a "done"
   message. Never on the NOC, which the family looks at. The details are in a Grafana dashboard reserved for the
   administrator. Only what requires action raises an alert:
   - a security advisory targets the running version;
   - a new build fixes serious vulnerabilities;
   - security patches have not been installed for a day;
   - a reboot has been pending for three days;
   - the firewall is behind.
4. **Maintenance in two clicks** in Semaphore:
   - *Announce to members*: email and banner, handled the same way as the announcements page;
   - *Update the fleet*: each machine sets a **local timer** for the announced time. Neither Semaphore nor the VPN is
     needed at that moment. The machines go one after the other in a fixed order: the least visible first, the
     public entry point and the administration tool last. Alerts are silenced during the window. Each machine
     installs its packages, pulls the images **of the same version** again and reboots if needed;
   - the hypervisor is included only on request and never reboots on its own.
5. **Semaphore does not administer itself**: it drops a dated request into a folder mounted in its container. Its
   machine checks it strictly (format, date, without following links) before scheduling its own update.
6. **A version change always goes through the code** (review, commit, deployment), never through the fleet update.

## Consequences

- A night of watch costs one vulnerability database (a few tens of megabytes) and about fifty GitHub requests.
  Without a token, the home address is limited to 60 requests per hour: responses are cached, and a token with no
  repository access lifts the limit.
- The first run downloads every image once (several gigabytes).
- A project with no advisories published on GitHub is followed only through its releases and its image's
  vulnerabilities.
- The firewall is still updated by hand, in its interface: the watch only warns.
- Semaphore sees the whole fleet: its rights remain those of Ansible, its own machine excepted.
