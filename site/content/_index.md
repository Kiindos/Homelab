---
title: Le homelab de Maxime Bertrand
description: Maxime Bertrand, administrateur systèmes et réseaux. Documentation de mon homelab.
---

Je suis administrateur systèmes et réseaux. Depuis septembre 2026, je fais tourner chez moi un homelab avec deux
objectifs : arrêter de payer des abonnements pour des services que je peux héberger moi-même, et construire une
infrastructure qui se gère comme en production.

Tout tient sur un Dell PowerEdge T330. Ma famille s'en sert pour ses photos et ses fichiers, publiés derrière un
WAF et un portail avec double authentification ; le reste n'est joignable que par le VPN.

Rien n'y est fait à la main : OpenTofu crée les machines, les règles du pare-feu et le DNS, Ansible les configure.
Chaque choix qui engage la suite est écrit dans une [décision d'architecture](/adr/), et le
[journal](/journal/) suit l'avancement, pannes comprises.
