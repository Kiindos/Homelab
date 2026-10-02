---
title: "Monitoring, a custom NOC and automation"
description: The homelab monitors itself, sends alerts to the phone, shows its status on a home-made NOC and is driven from Semaphore.
date: 2026-09-27
tags: [journal, monitoring, sso, ansible, design]
---

# Monitoring, a custom NOC and automation

Day two: making the platform **observable** and **operable**, without giving anything up on security.

## Seeing and being warned

A dedicated virtual machine runs Prometheus and Alertmanager ([ADR 0014](../adr/0014-supervision-noc.md)). Every
machine exposes its metrics, the server's four disks their SMART health, and the published services are probed
through the WAF, as a visitor would. Serious failures go out by email and as a priority notification on the phone,
thanks to a self-hosted ntfy instance.

## A NOC designed for the homelab

The first version published Grafana as is. Effective, but generic: it is replaced by a **custom-written page**, in
the site's visual identity, which answers the only useful question ("is everything working?") at a glance before
going into detail. The page never talks to Prometheus: it reads a snapshot produced every 30 seconds by a small
collector, and the WAF enforces SSO sign-in before the page is even served.

The sign-in portal adopts the same visual identity. Rather than modifying Authelia, the WAF injects a style sheet
that redefines its theme variables: the styling survives updates.

## Operating without the admin workstation

Semaphore UI now runs the Ansible playbooks from the browser, with history and a "dry run" mode
([ADR 0015](../adr/0015-semaphore-ansible.md)). One detail needed attention: the official image disables SSH server
identity checks. They are restored, and tested: an unknown server is refused.

## A vault for secrets

The day's last piece of work: an **OpenBao** vault ([ADR 0016](../adr/0016-coffre-openbao.md)), on trial. You sign
in to it through SSO, Semaphore reads only what it needs and only from its own address, and every access is
recorded. It unseals itself at boot thanks to a key that never leaves the hypervisor. Before relying on it, a full
"dry run" deployment was replayed reading the secrets from the vault rather than from the encrypted file: no
configuration would have changed.

## Accounts without temporary passwords

Inviting a relative no longer involves a password handed over manually: the account is created empty in the
directory, then the sign-in portal sends a personal, one-time, time-limited link to choose a password. The same link
serves for "forgot password", which did not work: the portal's service account only had read access to the
directory. The emails are translated and in the homelab's colours; they were tested on a throwaway instance (fake
SMTP server) before going into production.

## A page to invite people

The command line has given way to an **accounts page** ([ADR 0017](../adr/0017-invitations-page-comptes.md)): first
name, last name, email, access, and the invitation goes out. It is reachable only over the VPN, behind the internal
proxy, which can now enforce SSO sign-in too (two-factor authentication, administrators only). The page accepts the
forwarded identity only from the proxy and rejects forms submitted from another site; it was tested against a fake
directory before going anywhere near the real one.

On the monitoring side, a service published behind the WAF's SSO barrier is now probed **without a session**: the
probe expects a redirect to the portal. If the barrier disappeared, the alert would fire.

## Seeing the homelab from outside

Monitoring lives inside the homelab: if the power, the router or the hypervisor goes down, it goes silent with it.
An **external probe** (UptimeRobot, free plan) now checks every 5 minutes the showcase site (via Cloudflare) and
direct access to the web application firewall. Since the WAF only accepts France, the second probe stays at TCP
level rather than loosening the filtering. The monitors are described in a file and applied by an idempotent
script, like everything else. An **SMS** relay for critical alerts has been written (the mobile operator's free
option, which can only text the line's owner: no phone number to store), but it is not enabled yet.

The site finally has its **legal notice** and **privacy** pages, written from what the services actually log
(rotation periods, community sharing of attackers' addresses, processors).

## What the day taught

- **Test failure, not just success.** SSH key checking was validated by deliberately presenting an unknown
  identity.
- **A network drop must not freeze a deployment.** A VPN reconnection left Ansible hanging; connections now check
  that they are alive.
- **A default value can betray you.** An OWASP rule took the command-line sign-in's return address
  (`http://localhost`) for an SSRF attack: a targeted exclusion on that single parameter.
- **A mount can break what it targets.** Mounting a file into a folder that the application creates itself at
  startup makes Docker create that folder, as root: the unprivileged application can no longer install itself. The
  file is now copied once the application is ready.
- **A rate limit is measured against real use.** Two requests per second are enough for a page, not for an
  application that sends dozens at startup.
- **A badly resolved name hides well.** Monitoring could not see itself: the machine's name pointed to the loopback
  address. Fixed at the source, for every machine.
- **Two DNS servers answering means a race.** Without a routing domain, the workstation queried both the router and
  the homelab's server and kept the first answer: internal names worked one time in two.
- **Restarting a stack in one go ignores its dependencies.** The portal checks the directory at startup; restarted
  together, it failed before restarting. The directory now restarts first, and a simple configuration change only
  restarts the portal.
- **A security header can break an application.** The WAF added `HttpOnly` to every cookie; but the photo
  gallery's interface reads one of its cookies in JavaScript to know whether you are signed in. The result: a sign-in
  loop. The flags are now enforced on session cookies only.
