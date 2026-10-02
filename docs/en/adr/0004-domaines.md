---
title: "ADR 0004: Splitting the domains"
description: maximebertrand.eu for the public showcase site, the existing .fr domain for the lab.
date: 2026-09-21
status: remplacé
tags: [dns, cloudflare]
---

# ADR 0004: Splitting the domains

> **Superseded decision.** This decision was superseded by [ADR 0009](0009-domaine-unique.md) on 26/09/2026. It is kept for the record.

## Context

A `.fr` domain under my handle already exists. The showcase site must be findable by searching for my name.

## Decision

- `maximebertrand.eu`: showcase site, blog, status page, contact address (Cloudflare Email Routing).
- Existing `.fr` domain: lab, internal services (`*.home.<domain>.fr` resolved only internally or over VPN, certificates through a DNS challenge).

## Consequences

Both zones are managed at Cloudflare and described in `infra/tofu/cloudflare`.
