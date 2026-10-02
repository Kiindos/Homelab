---
title: "ADR 0019: Encrypted off-site backups, focused on what cannot be replaced"
description: Every night, VM exports, photos and files leave encrypted for a 1 TB remote storage; anything that can be copied again from its source is left out.
date: 2026-09-28
status: accepté
tags: [backup, restic, zfs, security]
---

# ADR 0019: Encrypted off-site backups, focused on what cannot be replaced

## Context

The homelab runs on a single server ([ADR 0010](0010-serveur-unique.md)). RAIDZ2 protects against two disk failures,
not against fire, theft, a handling mistake or ransomware. The available remote storage is **1 TB**: much less than
the server's data, a large part of which can be copied again from its source.

## Options considered

1. **Send everything** (full volumes) — impossible in 1 TB, and pointless for data that can be copied again.
2. **Proxmox Backup Server** — excellent for VMs, but requires compatible storage at the hosting provider.
3. **restic from the hypervisor, with a targeted scope** — chosen: a single tool, encryption before sending,
   deduplication and compression, SFTP accepted by every remote storage.

## Decision

- **What leaves**: full VM exports (hot vzdump, uncompressed so that restic deduplicates from one night to the
  next), photos and files (ZFS snapshots frozen during the upload, without thumbnails or re-encoded videos, which can
  be recomputed), the hypervisor's configuration.
- **What does not**: large volumes that can be copied again from their source; the vault's unseal key, kept
  separately.
- **Transport**: SFTP with a dedicated SSH key and pinned host keys, checked against the provider's documentation; a
  single outbound firewall rule.
- **Retention**: 7 days, 4 weeks, 6 months; weekly verification of a sample of the data.
- **Monitoring**: the script publishes its status; an alert fires if a run fails, if no backup has succeeded for 30
  hours, or if the storage goes over 80 %.

## Consequences

- Without the **repository password** (kept offline), the backups are unreadable: it is recorded in the password
  manager, not only on the server.
- The SSH key disappears with the server: disaster recovery goes through access to the remote storage account.
- The remote storage's automatic snapshots protect against deletion, including from the homelab.
- A monthly test restore (a small VM under a free ID) keeps the procedure proven.

## Changes since

- *29/09/2026*: remote storage raised to **5 TB** (data imported from Google Drive and Proton Drive). Verification
  **every night**: SHA-256 hashes of every VM export and of a sample of files, read back from the provider, and one
  seventh of the repository read back (the whole repository within a week).
- *01/10/2026*: on-demand check from Semaphore, quick or full; stale locks removed
  ([post-mortem](../postmortems/2026-10-01-sauvegarde-maintenance-hebergeur.md)).
- The monthly test restore of a VM has **not been done yet**: see the test status in the
  [backup runbook](../runbooks/sauvegardes.md).
