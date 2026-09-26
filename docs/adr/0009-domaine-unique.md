---
title: "ADR 0009 : Un seul domaine, maximebertrand.net"
description: maximebertrand.net sert à tout (vitrine, services publics, zone interne), en remplacement de l'ADR 0004.
date: 2026-09-26
status: accepté
tags: [dns, cloudflare, sécurité]
---

# ADR 0009 : Un seul domaine, maximebertrand.net

Remplace l'[ADR 0004](0004-domaines.md).

## Contexte

L'ADR 0004 prévoyait deux domaines : un `.eu` pour la vitrine et un `.fr` pour le labo. En pratique, le domaine
enregistré et géré chez Cloudflare est `maximebertrand.net`. Les premières machines avaient pourtant reçu des noms
internes en `.eu`, un domaine qui ne m'appartient pas.

Utiliser un domaine qu'on ne possède pas, même uniquement en interne, est risqué : si quelqu'un l'achète, il répond
à la place du DNS interne dès qu'une requête part vers Internet (VPN coupé, poste mal configuré) et peut détourner
les connexions. Il est aussi impossible d'obtenir un certificat valide pour ces noms.

## Options envisagées

1. **Garder deux domaines** : séparation nette, mais deux zones, deux jetons API et deux certificats à gérer.
2. **Un seul domaine avec des sous-domaines** : une zone, un certificat wildcard, une seule chose à surveiller.

## Décision

`maximebertrand.net` pour tout :

| Usage | Nom | Résolution |
|---|---|---|
| Vitrine, page de statut | `maximebertrand.net`, `status.maximebertrand.net` | Public (Cloudflare) |
| Services personnels publiés | sous-domaines de `maximebertrand.net` | Public (Cloudflare, « DNS only ») |
| Machines et services internes | `*.home.maximebertrand.net` | **Uniquement** par le DNS interne (OPNsense) |

## Conséquences

- Les noms internes sont sous un domaine que je contrôle : pas de détournement possible, et des certificats valides
  via le challenge DNS de Let's Encrypt, sans rien exposer.
- Certificats : les noms publics ont chacun leur certificat, obtenu par **challenge HTTP** sur le WAF, pour ne
  laisser **aucun jeton DNS** sur la machine exposée à Internet (un jeton volé permettrait de détourner toute la
  zone). Ces noms apparaissent dans les journaux de transparence (Certificate Transparency), ce qui est accepté :
  ils sont de toute façon dans le DNS public. La zone interne utilise un **certificat wildcard** obtenu par
  challenge DNS depuis une machine joignable uniquement par le VPN.
- Migration du 26/09/2026 : DNS interne, hyperviseur et outils migrés ; reste le nom système du pare-feu.
