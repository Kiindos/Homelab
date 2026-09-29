---
title: "ADR 0022 : Autorité de certification interne et TLS vérifié sur les flux internes"
description: Une autorité interne (racine hors ligne, intermédiaire dans le coffre, ACME) pour chiffrer et authentifier chaque flux entre machines, et rendre inopérante une usurpation DNS ou ARP.
date: 2026-09-29
status: proposé
tags: [securite, tls, pki, dns]
---

# ADR 0022 : Autorité de certification interne et TLS vérifié sur les flux internes

## Contexte

Tout ce qui arrive d'Internet est chiffré jusqu'au WAF, et les outils internes sont servis en HTTPS par le proxy interne
(certificat joker Let's Encrypt). Mais **derrière**, les flux entre machines sont en HTTP clair :

- WAF vers les applications ;
- proxy interne vers les outils ;
- vérification des sessions auprès du portail ;
- collecte des métriques et des journaux.

Ces flux désignent leurs cibles par des **noms** résolus par le DNS interne. Quelqu'un qui usurperait une réponse DNS
ou une adresse (ARP) dans une zone pourrait se placer au milieu et lire sessions et mots de passe. Le risque est
contenu (une VM par zone, pare-feu entre les zones), mais une seule VM compromise suffirait dans sa zone. Un
certificat vérifié à chaque saut rend l'usurpation inutile : le faux serveur n'a pas la clé.

## Options envisagées

1. **Certificats Let's Encrypt par machine (DNS-01)** : chaque VM aurait besoin d'un jeton qui modifie la zone DNS
   publique, et les noms internes se retrouveraient dans les journaux publics de certificats. Écarté.
2. **Distribuer le joker du proxy interne** : une seule clé privée copiée partout, qui fuite avec la première VM
   compromise. Écarté.
3. **Autorité interne avec ACME** — retenu :
   - une racine **hors ligne** (reprise de l'autorité interne existante) ;
   - un intermédiaire dans le coffre OpenBao (moteur PKI), qui délivre des certificats courts par ACME, renouvelés
     automatiquement.

## Décision (proposée)

1. **Autorité** :
   - racine hors ligne, gardée chiffrée hors du serveur ;
   - intermédiaire dans OpenBao ;
   - certificats de 30 jours, par nom de machine, émis par ACME ;
   - les noms internes ne sortent jamais du homelab.
2. **Chaque VM termine son TLS** :
   - un petit mandataire (Caddy, client ACME intégré) devant les conteneurs locaux, ou le TLS natif de l'application
     quand il existe ;
   - les ports HTTP en clair sont fermés au pare-feu.
3. **Chaque client vérifie** : WAF, proxy interne, portail, sondes, collecte des journaux et des métriques font
   confiance à la seule racine interne et vérifient le nom. Plus tard, **TLS mutuel** sur les flux les plus
   sensibles (vérification des sessions, annuaire).
4. **DNS durci en parallèle** : validation DNSSEC, résolution publique chiffrée (DNS sur TLS) et protection contre le
   « rebinding » sur le résolveur du pare-feu.

## Conséquences

- La confiance repose sur le coffre : s'il est indisponible, les certificats en cours restent valables jusqu'à
  30 jours, largement de quoi le réparer.
- Mise en place par étapes, un flux à la fois, en commençant par les plus sensibles : portail et annuaire, puis
  applications, puis supervision.
- Un certificat expiré coupe un flux : l'expiration est surveillée comme celle des certificats publics.
