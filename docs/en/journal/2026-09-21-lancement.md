---
title: "Launching the homelab"
description: Why I am building a personal 24/7 infrastructure, and how it will be built.
date: 2026-09-21
tags: [journal]
---

# Launching the homelab

This repository starts before the first screw is turned: the idea is to document the project from the very
beginning, decisions included.

Two goals drive the project: stop paying subscriptions for services I can host myself, and build an infrastructure
that is run like production, with IaC, GitOps, monitoring and written procedures.

First decisions, detailed in the ADRs: a low-power Proxmox cluster for PROD, the Dell T330 dedicated to storage, a
dedicated OPNsense firewall in the DMZ behind the Freebox, a LAB isolated behind its own firewall, public exposure
only through Cloudflare Tunnel, and everything described in OpenTofu and Ansible.

Next step: the physical build.
