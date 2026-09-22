---
title: Réseau
description: Découpage en zones, pare-feux et principes de filtrage (version publique, sans adressage).
tags: [architecture, réseau, opnsense]
---

# Réseau

> Version publique volontairement épurée : pas d'adresses IP, d'identifiants de VLAN ni de règles détaillées.

```mermaid
flowchart TB
  NET((Internet)) --- FB[Freebox Pop · mode routeur]
  FB --- HOME[Réseau domestique]
  FB -- DMZ --> OPN[OPNsense PROD · boîtier dédié]
  OPN --- VPN[VPN admin / VPN famille]
  OPN --- BAS[Bastion]
  OPN --- ADM[Administration · OOB]
  OPN --- SVC[Services internes]
  OPN --- PERSO[Services personnels]
  OPN --- DMZ[DMZ · WAF]
  OPN --- WEB[Web · Kubernetes]
  OPN --- TR[Transit routé] --- OPL[OPNsense LAB]
  OPL --- LABZ[Auth · serveurs · Wi-Fi · DMZ LAB]
  OPL --- DOT1X[VLAN dynamiques 802.1X]
  CL[Cluster Proxmox] -. niveau 2, sans passerelle .- ST[Stockage T330]
```

## Principes

- **Tout est interdit entre zones par défaut** ; chaque flux autorisé est justifié dans une matrice de flux (interne).
- **Administration** : uniquement VPN, puis bastion avec MFA, puis la cible.
- **Exposition** : seule la DMZ est joignable depuis Internet, via Cloudflare Tunnel, sans aucun port entrant.
- **Stockage et cluster** : réseaux de niveau 2 qui ne traversent pas le pare-feu.
- **LAB** : derrière son propre pare-feu, relié à la PROD par un transit routé (sans NAT), flux LAB → PROD interdits par défaut.
- **Accès hors bande** : l'iDRAC du serveur LAB reste sur le réseau d'administration de la PROD, pour pouvoir le rallumer à distance.
