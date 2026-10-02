---
title: "ADR 0016: An OpenBao secrets vault, alongside SOPS"
description: Secrets move into an OpenBao vault (SSO sign-in, identity-based access, audit); SOPS remains the bootstrap store.
date: 2026-09-27
status: accepté
tags: [secrets, openbao, security, sso]
---

# ADR 0016: An OpenBao secrets vault, alongside SOPS

## Context

The platform's secrets are in a file encrypted with SOPS and age, versioned in the private repository
([ADR 0005](0005-iac-opentofu-ansible.md)). It is simple and robust, but:

- **all or nothing**: whoever can decrypt the file reads every secret. Giving Semaphore
  ([ADR 0015](0015-semaphore-ansible.md)) its own key meant handing it everything;
- **no record** of who read what, and revoking access requires re-encrypting and rotating the secrets;
- tool tokens (APIs, DNS provider…) were still kept in separate files on the admin workstation.

## Options considered

1. **SOPS, one file per recipient**: lightweight, but secrets are duplicated and there is still no audit.
2. **HashiCorp Vault**: the reference, but under a non-free licence (BSL) since 2023.
3. **OpenBao**: a free fork of Vault (MPL 2.0, Linux Foundation), same API, compatible with Ansible and OpenTofu.

## Decision

**OpenBao**, on a small dedicated VM in the identity zone, without Docker (put on trial on 27/09/2026, adopted on
28/09/2026: Semaphore reads its secrets from it in production):

- **people sign in through SSO** (OpenID Connect via Authelia, second factor, administrators group);
- **machines sign in with AppRole**: Semaphore only gets **read** access to the platform's secrets, from its own
  address only; its credentials work nowhere else;
- **audit log** declared in the server configuration (it cannot be disabled through the API);
- **automatic unsealing** with a static key that stays **on the hypervisor**, in a separate dataset, shared
  read-only and handed to the service alone by systemd, in memory. A copy of the VM's disk is not enough to open the
  vault; a reboot needs no intervention;
- **end-to-end TLS** with the homelab's internal certificate authority; the certificate is renewed automatically;
- **configuration as code** (OpenTofu): secrets engine, policies, auth methods.

SOPS remains the **bootstrap store**: it is used to rebuild the vault itself, and the playbooks read one or the
other depending on a variable, for a gradual and reversible switch-over.

## Consequences

- Semaphore no longer needs to be able to decrypt the SOPS file: its access is narrower and can be revoked on its
  own.
- One more critical service: if it is down, nothing can be deployed, but the running services keep working (their
  secrets are already on the machines).
- The unseal key and the recovery keys are kept **offline**: without them, the vault's data is unrecoverable.
- Coming next: dynamic secrets (short-lived SSH certificates rather than fixed keys), tool tokens stored in the
  vault, regular backups of its database, revoking the root token once SSO sign-in has been validated by the
  administrator.
