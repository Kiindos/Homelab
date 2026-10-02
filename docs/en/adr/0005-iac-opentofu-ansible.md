---
title: "ADR 0005: OpenTofu and Ansible from day one"
description: No resource created by hand, even if getting started is slower.
date: 2026-09-21
status: accepté
tags: [iac, opentofu, ansible]
---

# ADR 0005: OpenTofu and Ansible from day one

## Context

The goal is to demonstrate a DevOps practice, and to be able to rebuild the infrastructure after a failure.

## Decision

- **OpenTofu** (open source, Terraform-compatible) with the `bpg/proxmox` and `cloudflare/cloudflare` providers.
- **Ansible** to configure the hosts and the VMs.
- OpenTofu state kept out of the repository: an encrypted local backend at first, then a self-hosted S3 backend.

## Consequences

Slower at first; in return, every change is reviewed, versioned and replayable.
