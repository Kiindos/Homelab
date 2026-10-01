---
title: "Post-mortem : toute la maison bannie par le WAF"
description: Des tests d'intrusion lancés depuis le réseau de la maison ont fait bannir son adresse publique ; toute la famille a reçu des 403 sur le portail d'authentification.
date: 2026-09-29
tags: [incident, waf, crowdsec, securite]
---

# Post-mortem : toute la maison bannie par le WAF

## Résumé

| | |
|---|---|
| **Impact** | Le portail d'authentification répondait 403 à tous les appareils de la maison : plus d'accès aux photos, au drive ni aux autres services protégés par le SSO, jusqu'à la levée manuelle du bannissement. L'extérieur n'était pas touché |
| **Services touchés** | Tous les services publiés, vus depuis la maison |
| **Cause** | Tests « boîte noire » de l'audit de sécurité (`/.git/config`, `/.env`…) lancés depuis la maison ; CrowdSec a reconnu un balayage et banni l'adresse, qui est celle de **toute** la maison |
| **Détection** | Un membre de la famille bloqué sur le portail |

## Chronologie (29/09/2026)

| Moment | Événement |
|---|---|
| Après-midi | Audit de sécurité : requêtes vers des chemins sensibles connus, depuis le poste d'administration à la maison |
| Peu après | CrowdSec classe ces requêtes comme un balayage et bannit l'adresse source |
| | 403 sur le portail pour tous les appareils de la maison |
| | Diagnostic : la décision de bannissement porte sur l'adresse publique de la box, celle de toutes les requêtes sortant de la maison |
| | Bannissement levé, exception mise en place, tests actifs proscrits depuis la maison |

## Cause racine

Vu du WAF, toute la maison est **une seule adresse** : celle de la box, que les requêtes viennent du poste
d'administration, d'un téléphone ou de la télévision. CrowdSec fait exactement ce pour quoi il est là : une
adresse qui sonde des chemins sensibles est bannie, globalement, sur tous les sites. Le test était légitime, mais
lancé depuis la seule adresse qu'il ne fallait pas faire bannir.

## Ce qui a bien marché / moins bien marché

- **Bien** : le WAF a détecté et bloqué le balayage en quelques requêtes ; c'était précisément ce que l'audit voulait
  vérifier.
- **Moins bien** : rien ne distinguait « la maison » d'un attaquant quelconque, et l'exception aurait disparu à
  chaque recréation du conteneur du WAF (les listes blanches de CrowdSec ne survivaient pas à une recréation).

## Actions correctives

- [x] L'adresse de la maison n'est plus jamais bannie par CrowdSec (règle *postoverflow*) ; ses requêtes restent
  filtrées une à une par les règles du WAF : une requête malveillante reçoit toujours son 403.
- [x] Les listes blanches de CrowdSec sont remises automatiquement après chaque recréation du WAF (minuterie systemd).
- [x] Règle d'exploitation : aucun test actif du WAF depuis la maison ; les tests boîte noire se lancent depuis
  l'extérieur.
