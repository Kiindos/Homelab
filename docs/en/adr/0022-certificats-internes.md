---
title: "ADR 0022: An internal certificate authority and verified TLS on internal flows"
description: An internal authority (offline root, intermediate on the firewall) to encrypt and authenticate every flow between machines, and make DNS or ARP spoofing useless.
date: 2026-09-29
status: accepté
tags: [security, tls, pki, dns]
---

# ADR 0022: An internal certificate authority and verified TLS on internal flows

## Context

Everything that comes from the Internet is encrypted up to the WAF, and internal tools are served over HTTPS by the
internal proxy (Let's Encrypt wildcard certificate). But **behind** that, flows between machines are plain HTTP:

- WAF to the applications;
- internal proxy to the tools;
- session checks against the portal;
- collection of metrics and logs.

These flows designate their targets by **names** resolved by the internal DNS. Someone who spoofed a DNS answer or an
address (ARP) inside a zone could put themselves in the middle and read sessions and passwords. The risk is contained
(firewall between zones), but the 29/09 audit showed that nothing filters **inside** a zone (two zones host two VMs).
A certificate verified at every hop makes spoofing useless: the fake server does not have the key.

## Options considered

1. **Let's Encrypt certificates per machine (DNS-01)**: every VM would need a token able to modify the public DNS
   zone, and internal names would end up in the public certificate logs. Ruled out.
2. **Distributing the internal proxy's wildcard**: a single private key copied everywhere, which leaks with the first
   compromised VM. Ruled out.
3. **An intermediate in the OpenBao vault** (PKI engine with ACME): automatic renewal through ACME, but the vault
   becomes essential to every flow: a vault outage would cut every internal connection as certificates expire. The
   first option studied, ruled out for that reason.
4. **An intermediate on the firewall** (OPNsense's trust store) — chosen: the firewall is already the network's point
   of trust, the authority is administered in its interface, with its revocation list. OPNsense has no ACME server:
   certificates are issued and renewed by Ansible, through its API.

The existing authority ("AC interne homelab", used for LDAPS and the vault) cannot serve as the root: it forbids any
authority below it (`pathlen:0`). It is replaced, certificate by certificate.

## Decision

1. **Authority**:
   - an offline root (10 years), its key encrypted in the private repository's secrets, never on a server;
   - an intermediate on the firewall (5 years);
   - **name constraints** on both: only the internal domain and the homelab's network can be certified, even by a
     compromised firewall;
   - 90-day certificates per machine name. The key is created **on the machine**; only the request (CSR) goes to the
     firewall, signed through the API with an account restricted to certificates (it can neither create an authority
     nor read its key);
   - renewal by Ansible (weekly Semaphore task, within 30 days of expiry);
   - internal names never leave the homelab.
2. **Each VM terminates its own TLS**:
   - a small proxy (Caddy, with its built-in ACME client) in front of the local containers, or the application's
     native TLS when it has one;
   - plain HTTP ports are closed at the firewall.
3. **Each client verifies**: WAF, internal proxy, portal, probes, log and metric collection trust only the internal
   root and verify the name. Later, **mutual TLS** on the most sensitive flows (session checks, directory).
4. **Address spoofing blocked in parallel**:
   - the firewall's resolver already validates DNSSEC and refuses private answers for public names (29/09 audit); it
     resolves from the root servers itself, with no intermediary to encrypt;
   - LLMNR and mDNS turned off on the VMs (broadcast name resolution, easy to poison; done on 29/09);
   - and the hypervisor's per-VM firewall to be enabled with IP and MAC filtering: a VM can no longer pass itself off
     as a neighbour, or as the gateway.

## Consequences

- No ACME: renewal depends on Ansible and Semaphore. A miss shows up 30 days before expiry (expiry monitoring), and
  the current certificates stay valid during a firewall outage.
- Compromised firewall: the (offline) root revokes the intermediate and signs a new one; the name constraints prevent
  any certificate for a public name.
- Rolled out in stages, one flow at a time, starting with the most sensitive ones: portal and directory, then
  applications, then monitoring.
- An expired certificate cuts a flow: expiry is monitored like that of the public certificates.

## Implementation

1. Blocking spoofing inside a zone:
   - LLMNR and mDNS turned off on the VMs (**done on 29/09**, common role);
   - the hypervisor's per-VM firewall (OpenTofu) with IP and MAC filtering, in log mode first, then inbound denied by
     default except for the flows in the matrix.
2. Authority: offline root and intermediate on the firewall (creation script), API account restricted to
   certificates, Ansible role for issuance and renewal, expiry monitoring.
3. End-to-end TLS, one flow at a time: session checks and directory (portal), then WAF to the applications, internal
   proxy to the tools, and finally metric and log collection.
4. Closing the plain HTTP ports at the firewall, flow by flow, once each client has moved to verified TLS.
