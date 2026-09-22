---
title: Vue d'ensemble de l'architecture
description: Les machines, les couches logicielles et ce qui est exposé ou non.
tags: [architecture]
---

# Vue d'ensemble

## Principes

1. **Tout en code** : aucune VM, aucun enregistrement DNS créé à la main. OpenTofu pour l'infrastructure, Ansible pour la configuration, Argo CD pour les applications.
2. **Exposition minimale** : seuls le site vitrine et la page de statut sont publics, via Cloudflare Tunnel (aucun port entrant ouvert). Le reste passe par le VPN.
3. **Séparation des zones** : réseau domestique (Freebox) et homelab (OPNsense) sont isolés ; le homelab est découpé en VLAN.
4. **Tout se restaure** : sauvegardes testées, procédures écrites dans `runbooks/`.

## Couches

| Couche | Outils |
|---|---|
| Matériel | Cluster 3 × ThinkCentre Tiny (PROD), Dell T330 (stockage), Dell 1U (LAB), mini-PC OPNsense |
| Hyperviseur & stockage | Proxmox VE, ZFS |
| Réseau & sécurité | OPNsense, VLAN, WireGuard, Cloudflare Tunnel & Access, CrowdSec |
| Provisionnement | OpenTofu (bpg/proxmox, cloudflare), Ansible |
| Orchestration | k3s, Argo CD, Traefik, cert-manager |
| Identité & secrets | Keycloak, SOPS + age |
| Observabilité | Prometheus, Grafana, Loki, Alertmanager, Uptime Kuma |
| Services d'infra | NetBox (source de vérité), Semaphore, bastion Teleport |

## Ce qui est exposé

| Service | Domaine | Accès |
|---|---|---|
| Site vitrine | `maximebertrand.eu` | Public (tunnel) |
| Page de statut | `status.maximebertrand.eu` | Public (tunnel) |
| Services du labo | `*.<domaine-labo>.fr` | Cloudflare Access (Zero Trust) |
| Administration, stockage, services personnels | — | VPN + bastion uniquement |
