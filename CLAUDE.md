# CLAUDE.md — Homelab

Contexte pour Claude Code. À lire au début de chaque session.

## Le projet

- Homelab personnel de Maxime (admin sys/réseau orienté DevOps), tournant 24/24.
- Double objectif : **portfolio DevOps** (vitrine : maximebertrand.net) et **série de vidéos**
  pour novices du réseau (étudiants BTS SIO SISR, passionnés).
  → La doc doit être **pédagogique** : expliquer le *pourquoi* des choix, pas seulement le *comment*.
- Deux dépôts : `Homelab` (public) et `Homelab-interne` (privé, doc interne).

## Matériel

- **Dell PowerEdge T330** (Xeon E3 v6) : prod perso + NAS, sous Proxmox VE.
- **Dell 1U bi-processeur** : futur environnement DEV / LAB.
- Réseau : Freebox Pop + switch manageable.

## État actuel (fin sept. 2026)

Opérationnel : Proxmox VE (`hv01`), OPNsense en VM (`fw01`), pool ZFS RAIDZ2, DNS interne
(zone `home.maximebertrand.net`, DNSSEC).

Décisions récentes (ADR 0008 à 0012) : domaine unique `maximebertrand.net`, serveur unique, services personnels
publiés en direct derrière OPNsense + WAF BunkerWeb (pas via Cloudflare), annuaire LLDAP + SSO Authelia,
Nextcloud comme drive.

En cours : **plateforme applicative**

- Une VM par zone de sécurité (WAF, identité, applis, outils internes), en Docker Compose, créées en OpenTofu
  et configurées en Ansible. Détail et découpage : `CLAUDE.local.md` et doc interne.

- Données sur des datasets ZFS de l'hôte, exposées aux VM par virtiofs.
- Les bases de données restent sur le disque local des VM (jamais sur un partage réseau).
- Durcissement de l'hyperviseur (audit du 26/09/2026) : voir le runbook interne.

## Feuille de route

1. Accès : FQDN pour toute l'infra, reverse proxy, VPN via OPNsense.
2. Services médias (détails dans `CLAUDE.local.md` uniquement : **ne jamais les citer dans ce dépôt public**).
3. Sauvegarde : photos (films en option) vers une Storage Box Hetzner ; PBS pour les VM ;
   à terme une machine de sauvegarde à disques SATA agrégés, allumée en Wake on LAN.
   Les configs vont sur GitHub.
4. Supervision : stack Prometheus, dashboard final sur un site web NOC.
5. NetBox, Ansible/Terraform pilotés via une interface (Semaphore).
6. Doc interne MkDocs joignable depuis Internet, uniquement en liste blanche derrière un WAF.
7. Env DEV : ADDS + 802.1X (VLAN dynamique), contrôleur Wi-Fi, reverse proxy/WAF, K8s avec autoscaling.

## Contraintes

- Consommation électrique plafonnée à **40 €/mois**.
- Pas de cluster Proxmox ni d'achat de mini PC avant longtemps.
- Pas de bastion (jugé inutile ici).

## Conventions

- **Sécurité d'abord** ; démarche PDCA.
- Documentation au fil de l'eau, style Read the Docs (MkDocs), pour limiter le facteur bus.
- Tout ce qui est config doit être versionné.

## Règles pour Claude

- Domaine : **maximebertrand.net** uniquement (`maximebertrand.eu` ne nous appartient pas).
- `Homelab` est **public** : aucun secret, mot de passe, clé, token, IP publique ni détail
  d'adressage interne dans ce dépôt. Utiliser des `.env` ignorés par git et des `.env.example`.

- Les détails internes sont dans `CLAUDE.local.md` (non versionné).
- Ne jamais lancer de commande destructrice (`zfs destroy`, `wipefs`, `rm -rf`, suppression de VM…)
  sans validation explicite.

- Proposer, expliquer, puis appliquer : Maxime valide les choix d'architecture.
- Répondre en français.
