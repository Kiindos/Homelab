---
title: "Runbook: verifying and restoring backups"
description: Checking the off-site backup, restoring a file or a VM, rebuilding after losing the server.
tags: [backup, restic, zfs]
---

# Runbook: verifying and restoring backups

**When to use it:** a backup alert, a maintenance or an incident at the remote storage provider, a file or a VM to
recover, or the loss of the server.
**Estimated time:** a few minutes for a quick check or a file; one to two hours for a full check or a VM; a day for
disaster recovery.
**Prerequisites:** the administration VPN; for disaster recovery, the **restic repository password** (kept offline)
and access to the remote storage account.

Choices and scope: [ADR 0019](../adr/0019-sauvegardes-hors-site.md). Code: the `sauvegarde` Ansible role.

## What runs every night

At 2:30, the hypervisor starts the backup:

1. **VM exports**, hot, uncompressed (restic deduplicates and compresses by itself);
2. **ZFS snapshots** of the photos and the drive, frozen during the upload;
3. **restic upload**, encrypted client-side, to the remote storage, over SFTP, with a dedicated SSH key and pinned
   host keys; the hypervisor's configuration goes too;
4. **end-to-end verification**: every VM export and a sample of files are read back from the provider and compared
   with the original by SHA-256 hash; one seventh of the repository is read back every night (`restic check
   --read-data-subset=N/7`), hence the whole repository within a week;
5. **retention**: 7 daily, 4 weekly, 6 monthly.

The script publishes its status for Prometheus: alerts if a run or its verification fails, if nothing has succeeded
for 30 hours, or if the remote storage goes over 80 %. The NOC shows the last run.

## Verifying

After an alert, a maintenance at the provider or any interruption during the upload: **Semaphore** → **"Vérifier la
sauvegarde"** template, without waiting for the next night.

- **quick**: repository structure and 5 % of the data read back (about ten minutes);
- **full**: the whole repository read back and every VM export compared byte for byte with the original (one to two
  hours, preferably at night, outside the backup window).

The check waits its turn if a backup is running (shared lock). Like the backup, it starts with `restic unlock`, which
removes locks left by a process that no longer exists (the case of a dropped connection:
[post-mortem of 01/10](../postmortems/2026-10-01-sauvegarde-maintenance-hebergeur.md)). Green task = compliant; red
= discrepancy or failure, with the report in the task.

From the command line, on the hypervisor:

```bash
systemctl list-timers sauvegarde-homelab.timer
journalctl -u sauvegarde-homelab -n 30 --no-pager
restic snapshots          # with RESTIC_REPOSITORY and RESTIC_PASSWORD_FILE from the role's configuration
```

## Restoring a file

```bash
restic ls latest | grep 'file-name'
restic restore latest --target /path/to/restore --include '<full path of the file in the snapshot>'
```

Put the file back in place, then make the application see it (drive: `occ files:scan <user>`). Delete the restore
folder afterwards.

## Restoring a VM

1. Restore the export: `restic restore latest --target /path/to/restore --include <exports folder>`;
2. `qmrestore <export>.vma <id> --storage local-zfs`: under a **new ID** for a trial; under the same ID only after
   deleting the original VM, which is an explicit decision;
3. start the VM, check the service (NOC probe green).

## Disaster recovery (server lost)

The server's SSH key disappears with it: access to the repository goes through the remote storage account (a new key
uploaded from its console) and the restic repository password.

1. Reinstall Proxmox and recreate the ZFS pool;
2. install restic, upload a new key, restore the VM exports, the hypervisor's configuration (as a reference) and the
   data (photos, drive);
3. restore the VMs in order: firewall, identity, vault (unseal key kept separately), applications;
4. rerun OpenTofu and Ansible: a `plan` with no changes confirms that the rebuild matches the code.

## Test status

| What is proven | How | Last result |
|---|---|---|
| Reading the data back from the provider | SHA-256 hashes of every VM export and of a sample of files, every night | Compliant on 02/10/2026 (49 files) |
| Repository integrity | One seventh read back every night; quick check on demand | Quick check compliant on 01/10/2026 |
| Full restore of a VM | `qmrestore` under a free ID, boot, then deletion | **Not done yet**; planned once a month |
| Disaster recovery | — | Never exercised |

## Rollback

A restore is always done **next to** what exists (a free folder or VM ID): nothing is overwritten until the result
has been checked. In case of error, delete the restored copy.
