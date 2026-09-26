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
  FB -- DMZ --> OPN[OPNsense · VM sur le T330]
  OPN --- VPN[VPN d'administration]
  OPN --- ADM[Administration]
  OPN --- DMZ[DMZ · WAF]
  OPN --- ID[Identité · annuaire et SSO]
  OPN --- APPS[Services personnels]
  OPN --- SVC[Services internes]
  OPN --- TR[Transit routé] --- OPL[OPNsense LAB]
  OPL --- LABZ[Auth · serveurs · Wi-Fi · DMZ LAB]
  OPL --- DOT1X[VLAN dynamiques 802.1X]
  NET -. tunnel sortant .- CF[Cloudflare] -.- VIT[Vitrine]
```

## Parcours d'une requête vers un service personnel

```mermaid
flowchart LR
  U[Utilisateur] --> FB[Freebox] --> OPN[OPNsense<br/>port 443 uniquement,<br/>filtrage géographique] --> WAF[BunkerWeb<br/>règles OWASP,<br/>limitation de débit]
  WAF --> SSO[Authelia<br/>double authentification]
  WAF --> APP[Application]
  APP -. vérifie l'identité .-> SSO
```

Chaque couche arrête ce que la précédente a laissé passer : le pare-feu ne laisse entrer que le port du WAF, le WAF
bloque les attaques web connues, et Authelia exige un second facteur avant d'ouvrir une session.

## Principes

- **Tout est interdit entre zones par défaut** ; chaque flux autorisé est justifié dans une matrice de flux (interne).
- **Administration** : uniquement par le VPN, avec double authentification sur les interfaces d'administration. Pas de bastion (voir l'[ADR 0010](../adr/0010-serveur-unique.md)).
- **Exposition** : un seul port entrant, redirigé vers le WAF en DMZ ; la vitrine passe par un tunnel Cloudflare sortant.
- **La DMZ ne voit presque rien** : depuis le WAF, seuls les ports des applications publiées sont joignables. Une compromission du WAF ne donne pas accès au reste.
- **DNS interne** : les machines ont des noms dans une zone qui n'existe que sur le DNS interne, avec validation DNSSEC.
- **LAB** : derrière son propre pare-feu, relié à la PROD par un transit routé (sans NAT), flux LAB → PROD interdits par défaut.
- **Accès hors bande** : l'interface de gestion à distance du serveur reste joignable même quand le pare-feu est arrêté.
