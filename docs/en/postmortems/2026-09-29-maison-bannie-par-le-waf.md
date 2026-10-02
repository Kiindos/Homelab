---
title: "Post-mortem: the whole household banned by the WAF"
description: Intrusion tests run from the home network got its public address banned; the whole family received 403s on the sign-in portal.
date: 2026-09-29
tags: [incident, waf, crowdsec, security]
---

# Post-mortem: the whole household banned by the WAF

## Summary

| | |
|---|---|
| **Impact** | The sign-in portal answered 403 to every device in the house: no more access to photos, the drive or the other SSO-protected services, until the ban was lifted manually. The outside world was not affected |
| **Services affected** | All published services, as seen from home |
| **Cause** | Black-box tests from the security audit (`/.git/config`, `/.env`…) run from home; CrowdSec recognised a scan and banned the address, which is that of the **whole** household |
| **Detection** | A family member stuck on the portal |

## Timeline (29/09/2026)

| Moment | Event |
|---|---|
| Afternoon | Security audit: requests to well-known sensitive paths, from the administration workstation at home |
| Shortly after | CrowdSec classifies these requests as a scan and bans the source address |
| | 403 on the portal for every device in the house |
| | Diagnosis: the ban decision targets the router's public address, the one used by every request leaving the house |
| | Ban lifted, exception put in place, active tests from home ruled out |

## Root cause

Seen from the WAF, the whole house is **a single address**: the router's, whether requests come from the
administration workstation, a phone or the TV. CrowdSec does exactly what it is there for: an address probing
sensitive paths is banned, globally, across every site. The test was legitimate, but it was run from the one address
that must never be banned.

## What went well / less well

- **Well**: the WAF detected and blocked the scan within a few requests; that was precisely what the audit wanted to
  check.
- **Less well**: nothing distinguished "home" from any other attacker, and the exception would have vanished with
  every recreation of the WAF's container (CrowdSec's allow-lists did not survive a recreation).

## Corrective actions

- [x] The home address is never banned by CrowdSec any more (*postoverflow* rule); its requests are still filtered
  one by one by the WAF's rules: a malicious request still gets its 403.
- [x] CrowdSec's allow-lists are restored automatically after every recreation of the WAF (systemd timer).
- [x] Operating rule: no active testing of the WAF from home; black-box tests are run from outside.
