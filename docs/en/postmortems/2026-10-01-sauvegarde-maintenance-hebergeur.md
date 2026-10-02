---
title: "Post-mortem: the nightly backup cut by the hosting provider's maintenance"
description: A maintenance of the remote storage cut the backup upload and left the restic repository locked; nothing was lost, but the following nights would have failed too.
date: 2026-10-01
tags: [incident, backup, restic]
---

# Post-mortem: the nightly backup cut by the hosting provider's maintenance

## Summary

| | |
|---|---|
| **Impact** | No off-site backup for the night of 01/10. Nothing lost: the previous backup (30/09) was still valid and verified |
| **Services affected** | No visible service; only the backup |
| **Cause** | Maintenance of the remote storage (Storage Box) during the upload; restic, cut off abruptly, could not remove its lock |
| **Detection** | `SauvegardeEchouee` alert |

## Timeline (01/10/2026)

| Time | Event |
|---|---|
| 2:30 | Backup starts: VM exports, ZFS snapshots |
| 4:01 | Upload starts. It is long: the data imported from Google Drive and Proton Drive is being sent for the first time |
| 10:12 | Connection cut by the provider (`ssh command exited: exit status 255`); `SauvegardeEchouee` alert |
| During the day | Diagnosis: maintenance at the provider; the repository is still locked by a process that no longer exists |
| Evening | After the maintenance: stale lock removed, quick repository check run from Semaphore: compliant (12 min) |

## Root cause

restic puts a lock on the repository during every operation and removes it at the end. Cut off by the loss of the
connection, the process could not remove it: the repository stayed locked "by" a dead process. The next night's
backup, like its verification, would have stopped on that lock. A transient outage at the provider thus turned into
a lasting backup outage.

## What went well / less well

- **Well**: the alert arrived immediately; the previous backup was intact and verified (SHA-256 hashes read back
  from the provider).
- **Less well**: checking the repository's state after the maintenance required an SSH session on the hypervisor and
  restic commands by hand.

## Corrective actions

- [x] Every operation (backup, verification, check) starts with `restic unlock`, which only removes locks left by
  processes that no longer exist.
- [x] On-demand check from Semaphore ("Vérifier la sauvegarde"): **quick** (repository structure and 5 % of the data
  read back) or **full** (the whole repository read back, every VM export compared byte for byte with its copy). It
  waits its turn if a backup is running (shared lock). See the [backup runbook](../runbooks/sauvegardes.md).
- [x] The next run succeeded despite the volume of imports: 02/10, 2:30 → 7:08, verification compliant.
- [ ] Run a full check of the repository (read everything back), on a night outside the backup window.
