---
title: "ADR 0015: Semaphore UI to run Ansible from the homelab"
description: An internal web interface, protected by SSO, runs the versioned playbooks; its access is restricted and verified.
date: 2026-09-27
status: accepté
tags: [ansible, automation, sso, security]
---

# ADR 0015: Semaphore UI to run Ansible from the homelab

## Context

The whole machine configuration is described by Ansible playbooks ([ADR 0005](0005-iac-opentofu-ansible.md)), run so
far from the administration workstation. That assumes having this workstation at hand, properly set up, and leaves
no shared record of what was run, when, and with what result.

## Options considered

1. **Stay on the admin workstation**: simple, but no history and no way to run from another device.
2. **AWX (the free Ansible Automation Platform)**: very complete, but requires Kubernetes: out of proportion here.
3. **Semaphore UI**: a single container, an SQLite database, OpenID Connect sign-in, run history, check-mode runs
   (*dry run* + *diff*) from the browser.

## Decision

**Semaphore UI**, on the internal tools VM, reachable **only over the VPN** and through **SSO** (administrators
group, second factor mandatory). There is no local password account.

Semaphore effectively holds the keys to the whole infrastructure, so its access is bounded:

- **repositories**: the public repository is cloned anonymously; the private one (inventory, encrypted secrets) with
  a **read-only** deploy key: Semaphore cannot push anything;
- **SSH**: a dedicated key, accepted by the machines **only from Semaphore's address**, without port or agent
  forwarding; the firewall opens port 22 only towards the managed machines;
- **machine identity**: the official image disables SSH host key checking (for git as for Ansible). It is restored:
  the keys are collected from the machines themselves by Ansible, GitHub's come from its official publication, and a
  wrapper strips the options that disable it;
- **secrets**: Semaphore has its own SOPS decryption key, revocable without touching the admin workstation's; its own
  secrets are encrypted in its database;
- **one run at a time**, so that two playbooks never modify the same machine at the same time.

Semaphore **does not manage the VM that hosts it**: restarting Docker or its own container would cut the running
task. That VM is still deployed from the admin workstation.

## Consequences

- Playbooks can be run from any device connected to the VPN, with a browsable history.
- The image is rebuilt locally (the playbooks' tools at the same versions as on the admin workstation): its updates
  go through this repository, not through an automatic `pull`.
- Compromising Semaphore would mean compromising the infrastructure: it is treated as administration equipment (VPN,
  SSO, minimal network access, availability monitoring).
