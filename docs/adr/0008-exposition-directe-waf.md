---
title: "ADR 0008 : Exposition directe des services personnels derrière OPNsense et BunkerWeb"
description: Les photos et le drive sont publiés sans Cloudflare, via une redirection de port vers un WAF BunkerWeb en DMZ.
date: 2026-09-26
status: accepté
tags: [réseau, sécurité, waf, opnsense]
---

# ADR 0008 : Exposition directe des services personnels derrière OPNsense et BunkerWeb

## Contexte

Les photos (Immich) et le drive doivent être joignables depuis Internet, pour la famille comme depuis un téléphone
en 4G. L'[ADR 0002](0002-cloudflare-tunnel.md) réserve Cloudflare Tunnel au contenu public, car Cloudflare
déchiffre le trafic. En plus, son offre gratuite limite chaque requête à 100 Mo, ce qui bloque l'envoi de vidéos.

## Options envisagées

1. **Cloudflare Tunnel + Cloudflare Access** : aucun port ouvert et un filtrage par identité, mais Cloudflare voit
   les photos en clair et les gros envois échouent.
2. **VPN uniquement** : la solution la plus sûre, mais chaque appareil de la famille doit être configuré.
3. **Redirection de port vers un WAF en DMZ** : le trafic reste chiffré de bout en bout jusqu'au homelab et sans limite
   de taille ; en contrepartie, l'IP de la maison est publique et le homelab encaisse directement les scans.

## Décision

Option 3, avec une défense en profondeur :

| Couche | Rôle |
|---|---|
| DNS Cloudflare en mode « DNS only » | Résolution uniquement, sans proxy |
| OPNsense | Seul le port 443 est redirigé, uniquement vers le WAF ; filtrage géographique et listes de blocage ; la DMZ ne peut joindre que les ports des applications |
| BunkerWeb (DMZ) | Terminaison TLS, règles OWASP (ModSecurity CRS), limitation de débit, bannissement des comportements suspects, CrowdSec |
| Authelia | Portail de connexion unique avec double authentification (voir l'[ADR 0011](0011-annuaire-sso.md)) |
| Applications | Contrôle des droits, mises à jour suivies |

## Conséquences

- Il n'y a **pas de vraie liste blanche par IP** : les IP de la famille changent, en 4G notamment. Le filtrage
  géographique et le comportement suspect remplacent cette liste blanche ; l'authentification (Authelia et
  applications) devient la dernière barrière et doit être solide.
- Les règles OWASP peuvent bloquer des envois légitimes (gros fichiers, API des applis mobiles) : il faudra les
  ajuster, en consultant les journaux du WAF.
- L'IP de la maison est visible dans le DNS public. Seuls les noms des services réellement publiés y figurent :
  les noms internes restent résolus par OPNsense.
- Le tunnel Cloudflare reste utilisé pour la vitrine et la page de statut (ADR 0002).
