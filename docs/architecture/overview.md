---
title: Vue d'ensemble de l'architecture
description: Les machines, les couches logicielles et ce qui est exposé ou non.
tags: [architecture]
---

# Vue d'ensemble

## Principes

1. **Tout en code** : aucune VM, aucun enregistrement DNS créé à la main. OpenTofu pour l'infrastructure, Ansible pour la configuration.
2. **Exposition minimale** : la vitrine et la page de statut passent par Cloudflare Tunnel ; les services personnels passent par un seul port entrant, filtré par le pare-feu puis par un WAF, avec authentification unique. L'administration n'est accessible que par le VPN.
3. **Séparation des zones** : réseau domestique (Freebox) et homelab (OPNsense) sont isolés ; le homelab est découpé en VLAN, et chaque zone n'a accès qu'à ce dont elle a besoin.
4. **Tout se restaure** : sauvegardes testées, procédures écrites dans `runbooks/`.

## Couches

| Couche | Outils |
|---|---|
| Matériel | Dell PowerEdge T330 (serveur unique), Dell 1U (LAB, à venir) |
| Hyperviseur & stockage | Proxmox VE, ZFS RAIDZ2 |
| Réseau & sécurité | OPNsense (virtualisé), VLAN, WireGuard, BunkerWeb (WAF), CrowdSec, Cloudflare (DNS, tunnel de la vitrine) |
| Identité | LLDAP (annuaire), Authelia (SSO et double authentification) |
| Provisionnement | OpenTofu (bpg/proxmox, cloudflare), Ansible |
| Applications | Docker Compose dans des VM dédiées par zone ; Kubernetes (k3s, Argo CD) pour l'environnement de test |
| Secrets | SOPS + age |
| Observabilité | Prometheus, Grafana, Loki, Alertmanager, Uptime Kuma |
| Services d'infra | NetBox (source de vérité), Semaphore |

Les choix structurants sont expliqués dans les ADR, en particulier l'[ADR 0010](../adr/0010-serveur-unique.md)
(un seul serveur) et l'[ADR 0008](../adr/0008-exposition-directe-waf.md) (publication des services).

## Ce qui est exposé

| Service | Domaine | Accès |
|---|---|---|
| Site vitrine | `maximebertrand.net` | Public (Cloudflare Tunnel) |
| Page de statut | `status.maximebertrand.net` | Public (Cloudflare Tunnel) |
| Services personnels (photos, fichiers) | sous-domaines de `maximebertrand.net` | Public, derrière OPNsense, WAF et SSO avec double authentification |
| Administration, annuaire, outils internes | `*.home.maximebertrand.net` (DNS interne uniquement) | VPN uniquement |
