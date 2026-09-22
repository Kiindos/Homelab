---
title: "ADR 0002 : Exposition publique via Cloudflare Tunnel"
description: Le site vitrine est exposé par un tunnel sortant, sans aucun port entrant ouvert.
date: 2026-09-21
status: accepté
tags: [cloudflare, réseau, sécurité]
---

# ADR 0002 : Exposition publique via Cloudflare Tunnel

## Contexte

Le site vitrine et la page de statut doivent être publics. L'infrastructure est derrière une Freebox, avec une IP résidentielle.

## Options envisagées

1. **Redirection de ports 80/443** : IP personnelle exposée et scannée, dépendance au DynDNS.
2. **VPS en frontal + WireGuard** : robuste, mais coûteux ou dépendant d'offres gratuites instables.
3. **Cloudflare Tunnel** : connexions sortantes uniquement, TLS, anti-DDoS et WAF inclus.

## Décision

Cloudflare Tunnel (`cloudflared` en deux réplicas dans le VLAN 40), décrit en OpenTofu avec le provider officiel.

## Conséquences

- Cloudflare déchiffre le trafic : acceptable pour du contenu public, **exclu** pour les données personnelles (VPN).
- Les domaines doivent utiliser les serveurs DNS de Cloudflare.
