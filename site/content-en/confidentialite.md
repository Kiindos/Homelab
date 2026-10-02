---
title: Privacy
description: What data is processed, why, for how long, and how to exercise your rights.
layout: juridique
slug: privacy
date: 2026-09-27
lastmod: 2026-10-02
---

## In short

- **This site** has no cookies, no audience measurement, no advertising and no forms. Only technical logs (IP
  address, page requested, browser) are kept briefly, for security and to keep the site running.
- **The private services** (photos, files, media…) are open only to invited people. Their data stays on the
  publisher's personal server, in France.
- Nothing is sold, rented or used for advertising.

## Data controller

Maxime Bertrand, publisher of the site. Contact: {{< contact >}}

## This site

**Data processed.** On every visit, the server records in its logs the IP address, the date, the page requested,
the referring page and the browser's identifier. **Purpose**: running the site, diagnosing failures, detecting
abuse. **Legal basis**: the publisher's legitimate interest in keeping the site secure and available. **Retention**:
logs are deleted automatically by rotation (a few days to a few weeks depending on traffic).

**Cloudflare**, through which the site's traffic passes, processes the same technical data to route requests and
protect the site; this processing falls under its [privacy policy](https://www.cloudflare.com/privacypolicy/).
Cloudflare may transfer data to the United States, under the EU–US Data Privacy Framework.

**External resource.** Pages containing diagrams load the Mermaid library from the jsDelivr content delivery
network: your browser then sends it your IP address, as with any web resource.

**Cookies.** None: the site sets none and uses no tracker. No consent banner is therefore needed.

**Writing to the contact address.** Messages sent to {{< contact >}} go through Cloudflare's email routing service,
which forwards them to the publisher's personal mailbox; they are kept there for as long as it takes to handle the
request.

## Private services

Photos, files, media, notifications and the sign-in portal are reserved for people invited by the publisher
(family use).

**Data processed**:

- **account**: username, name, email address, groups, password hash (never the password itself), two-factor
  authentication settings;
- **content** you upload: photos and videos (with their metadata, including location if any), files, playback
  history;
- **security logs**: IP address, date, address requested, outcome of sign-ins.

**Purposes**: providing the services, securing accounts (two-factor authentication, lockout after several failures)
and protecting the server against attacks. **Legal basis**: providing the service you accepted by joining the
homelab, and the publisher's legitimate interest in securing it.

**Where and for how long**: on the publisher's server, in France, for as long as the account exists; content is
deleted with the account, at your request. Security logs are gathered on the monitoring server, readable by the
publisher only, and deleted automatically after **30 days**. Backups, encrypted, stay on the publisher's equipment or
with a provider located in the European Union.

**Recipients and processors**:

- the service's emails (invitation, choosing a password, verification codes, notifications) are sent by
  **Scaleway SAS** (France, Transactional Email service, hosted in the European Union);
- the web application firewall uses **CrowdSec**: the IP address of a visitor behaving like an attacker (port
  scanning, intrusion attempts) is shared with CrowdSec's community network, to protect other servers. These alerts
  are kept for 7 days on the server;
- some application features may load third-party resources from your browser (for example the map tiles in the
  photos).

**Cookies**: only strictly necessary cookies (sign-in session and security), exempt from consent. No audience
measurement or advertising cookies.

## Your rights

Under the GDPR and the French Data Protection Act, you can request access to your data, its rectification, erasure
or portability, the restriction of processing, or object to it, by writing to {{< contact >}}. You will receive an
answer within one month.

If you believe your rights are not respected, you can lodge a complaint with the CNIL, the French data protection
authority (<https://www.cnil.fr>, 3 place de Fontenoy, TSA 80715, 75334 Paris Cedex 07, France).

## Security

Data is encrypted in transit (HTTPS), access to the services goes through a single portal with two-factor
authentication, and the server is protected by a firewall, a web application firewall and tracked updates. The
details of these measures are public: see the [architecture overview](/en/architecture/overview/).

*The French version of this policy is the reference version.*
