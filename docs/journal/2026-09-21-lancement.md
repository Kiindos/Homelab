---
title: "Lancement du homelab"
description: Pourquoi je monte une infra perso 24/24, et comment elle sera construite.
date: 2026-09-21
tags: [journal]
---

# Lancement du homelab

Ce dépôt démarre avant la première vis : l'idée est de documenter le projet dès le départ, décisions comprises.

Deux objectifs guident le projet : arrêter de payer des abonnements pour des services que je peux héberger moi-même, et construire une infrastructure qui se gère comme en production, avec de l'IaC, du GitOps, de la supervision et des procédures écrites.

Premières décisions, détaillées dans les ADR : un cluster Proxmox basse consommation pour la PROD, le Dell T330 dédié au stockage, un pare-feu OPNsense dédié en DMZ derrière la Freebox, un LAB isolé derrière son propre pare-feu, une exposition publique uniquement via Cloudflare Tunnel, et tout décrit en OpenTofu et Ansible.

Prochaine étape : le montage physique.
