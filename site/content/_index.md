---
title: Homelab
description: Maxime Bertrand, administrateur systèmes et réseaux. Documentation de mon homelab.
---

Je suis Maxime Bertrand, administrateur systèmes et réseaux. Ce site documente le homelab que je fais tourner
chez moi.

Je l'ai lancé en septembre 2026 avec deux objectifs : arrêter de payer des abonnements pour des services que je
peux héberger moi-même, et construire une infrastructure qui se gère comme en production.

Tout tient aujourd'hui sur un seul serveur, un Dell PowerEdge T330 : Proxmox VE, un pool ZFS en RAIDZ2 et une
dizaine de machines virtuelles, dont le pare-feu OPNsense. Ma famille s'en sert pour ses photos (Immich) et ses
fichiers (Nextcloud). Ces deux services sont publiés derrière un WAF et un portail de connexion avec double
authentification ; le reste n'est joignable que par le VPN.

Rien n'y est fait à la main. OpenTofu crée les machines, les règles du pare-feu et les enregistrements DNS,
Ansible les configure, et un second passage ne doit rien changer. Les choix qui engagent la suite sont écrits dans
des [décisions d'architecture](/adr/) ; quand l'une ne tient plus, j'en écris une nouvelle qui la remplace. Le
[journal](/journal/) suit l'avancement, pannes comprises.

Le code est public sur [GitHub](https://github.com/maximebertrand-dev/Homelab), celui de ce site compris.
