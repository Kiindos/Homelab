---
title: "Group-based access, quotas and documentation in the homelab's colours"
description: Access to each service is granted by ticking a group, administration rights follow the directory, and allocated space is set from a single page.
date: 2026-09-28
tags: [journal, identity, sso, documentation]
---

# Group-based access, quotas and documentation in the homelab's colours

## One group per service

Two groups were no longer enough: impossible to open the photos without opening the drive. Each service now has its
own group, and the "family" and "administrators" groups still open everything
([ADR 0018](../adr/0018-droits-par-groupes-quotas.md)). The mapping fits in one table of the inventory, from which
the SSO rules and the directory filter are generated.

The applications' administration rights now follow the directory: at every sign-in, Authelia computes a role from
the groups (CEL expressions) and passes it in a claim. Before touching the SSO in production, the full OpenID Connect
journey was replayed on a throwaway instance: the administrator gets their role, the "photos only" account enters as
a plain user and is refused the drive.

## Everyone's space

The accounts page shows the space used on the drive and in the photo gallery, and lets you set a quota right there.
Each credential is cut as narrowly as possible: a delegated account that manages only the family groups, an API key
restricted to accounts. If a service does not answer, the page says so and stays usable.

## Welcome

On top of the link to choose a password, a new member now receives a **welcome email** that presents only their
services, with how to use them (app to install, address, how to sign in). The same exists as a web page, behind the
SSO barrier: a **home page** showing the cards of the signed-in person's services, based on the groups forwarded by
the web application firewall. A single catalogue feeds both; the page accepts only the web application firewall and
keeps only safe characters from the identity it receives.

## Off-site backups

The single server had a blind spot: disaster (theft, fire, mistake, ransomware). Every night, the virtual machines'
exports, the photos and the files now leave **encrypted** for a 1 TB remote storage
([ADR 0019](../adr/0019-sauvegardes-hors-site.md)); anything that can be copied again from its source is left out.
The storage's host keys were compared with those published by the provider before being pinned, and monitoring
alerts if a night fails or if the storage fills up.

Semaphore, for its part, finally ran its first task: cloning the repositories, reading the secrets from the vault,
a dry run on one machine.

## Documentation

The internal documentation adopts the site's visual identity (palette, logo, headings, tables as cards), without any
font loaded from the Internet. The decisions on the secrets vault and the accounts page moved from "proposed" to
"accepted".

## What the day taught

- **An option passed on the command line is a string.** `-e option=true` is not a boolean for Ansible; the condition
  rejected it and the deployment stopped before its handler. Hence a systematic `| bool`, and a restart that is
  checked rather than assumed.
- **An empty field means something.** A cleared quota means "unlimited"; the default form decoding dropped empty
  fields, and the change went unnoticed. The test bench caught it before production.
