---
title: "Post-mortem: two WAF outages in the same morning"
description: An invalid option stopped CrowdSec (1 h outage), then large file uploads exhausted the WAF's memory (25 min); uploads fixed and a new alert added.
date: 2026-09-30
tags: [incident, waf, crowdsec, modsecurity, memory]
---

# Post-mortem: two WAF outages in the same morning

## Summary

| | |
|---|---|
| **Impact** | Every published service unreachable from 9:36 to 10:39, then from about 11:30 to 11:55 |
| **Services affected** | Sign-in portal, photos, drive, public monitoring, and everything that goes through the WAF |
| **Causes** | 1) a non-existent configuration option prevented CrowdSec from restarting; 2) the WAF kept large uploads (phone videos) entirely in memory |
| **Detection** | 1) post-deployment check and `ServicePublicIndisponible` alert; 2) deployment stuck, WAF VM not answering over SSH. No alert had reported the memory incidents of the previous days |

## Context

Since the day before, CrowdSec's AppSec module had been **rejecting every upload larger than 10 MB**: 138 rejections
in 20 hours, mostly the phone's video sync. These 403s, added to WebDAV's normal 405s, had also got the house banned
from the drive by BunkerWeb's "bad behaviour" module. The morning was spent fixing that problem: it was the fix that
caused the first outage, and its success that revealed the second.

## Timeline (30/09/2026)

| Time | Event |
|---|---|
| 9:36 | Deployment of an AppSec setting (what to do with an oversized body) added to CrowdSec's **acquisition** file, where that option does not exist |
| 9:36 | CrowdSec refuses to start ("unknown field"); without it, the WAF's CrowdSec module refuses every request ("fail closed" behaviour) |
| Right after | Timeouts during the deployment check; `ServicePublicIndisponible` alerts |
| 10:39 | Line removed, CrowdSec restarted: services restored |
| Meanwhile | Drive ban lifted: the phone's sync resumes, with all its overdue retries; the WAF is restarted |
| ≈ 11:30 | The WAF runs out of memory: VM frozen, services unreachable |
| ≈ 11:55 | The kernel kills the nginx processes involved: recovery without intervention |
| During the day | The intended AppSec setting is applied in the right place (the `SetBodySizeExceededAction` *hook*), tested, without an outage: the first 10 MB of an upload are inspected, the rest goes through |
| 15:24 | Root fix for the memory issue in service (see below) |

## Root causes

**First outage**: a setting written to the wrong file, deployed without CrowdSec's configuration being tested before
it was reloaded. The WAF is designed to refuse rather than let traffic through when CrowdSec does not answer: that is
intended, but it turns any CrowdSec configuration mistake into a total outage.

**Second outage**: two components kept the whole body of uploads in memory. CrowdSec's AppSec module reads the entire
body to forward it (`get_body` in the Lua *bouncer*), and ModSecurity inspects up to the maximum size allowed by the
site (16 GB for the drive, 50 GB for photos). A 1 GB upload produced a 1.3 GB nginx process, on a 2 GB VM. The
problem already existed: nginx processes killed for lack of memory 3 times on 28/09, 15 times on 29/09, 16 times on
the morning of 30/09, each time a brief outage that went unnoticed. The phone's sync resuming, plus the memory spike
when the WAF restarted, was enough to bring everything down.

## What went well / less well

- **Well**: the probes detected the first outage immediately; during the second, the kernel eventually killed the
  processes involved and the service came back on its own.
- **Less well**: no alert on processes killed for lack of memory, although the metric existed
  (`node_vmstat_oom_kill`); a setting deployed without a syntax test; two related problems handled on the same day,
  the second masked by the first.

## Corrective actions

- [x] The script that applies CrowdSec's settings tests the configuration (`crowdsec -t`) before reloading it, and
  restores the previous version if the test fails.
- [x] Paths reserved for uploads (`= /api/assets` for photos, `/remote.php/dav/uploads/` for the drive): neither
  ModSecurity nor AppSec, while the rest of both sites stays inspected. These paths require an authenticated session
  in the application, and their content is binary: inspection added little there, at an unbounded memory cost.
  Accepted risk: a flaw in the application's handling of uploads would no longer be filtered by the WAF; it is
  covered by updates and the security watch.
- [x] `ProcessusTuesFauteDeMemoire` alert on every machine. Since then: no process killed, 393 MB available at the
  lowest point on the WAF.
- [x] Streaming uploads straight through was tried, then removed the same evening: an interrupted upload reached the
  application truncated (400). nginx keeps buffering to disk, which costs no memory.
- [ ] WAF VM memory raised to 3 GB (described in OpenTofu, to be applied with the next VM resizing).

**Option ruled out**: capping ModSecurity's inspection (`SecRequestBodyLimit` with `ProcessPartial`). ModSecurity's
nginx connector reads back into memory any body that went through a temporary file (`msc_request_body_from_file`):
the cap would have changed nothing.
