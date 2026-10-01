---
title: "Post-mortem : deux coupures du WAF dans la même matinée"
description: Une option invalide a arrêté CrowdSec (1 h de coupure), puis les gros envois de fichiers ont épuisé la mémoire du WAF (25 min) ; correction des envois et nouvelle alerte.
date: 2026-09-30
tags: [incident, waf, crowdsec, modsecurity, memoire]
---

# Post-mortem : deux coupures du WAF dans la même matinée

## Résumé

| | |
|---|---|
| **Impact** | Tous les services publiés injoignables de 9 h 36 à 10 h 39, puis d'environ 11 h 30 à 11 h 55 |
| **Services touchés** | Portail d'authentification, photos, drive, supervision publique, et tout ce qui passe par le WAF |
| **Causes** | 1) une option de configuration inexistante a empêché CrowdSec de redémarrer ; 2) le WAF gardait en mémoire l'intégralité des gros envois (vidéos du téléphone) |
| **Détection** | 1) vérification après déploiement et alerte `ServicePublicIndisponible` ; 2) déploiement bloqué, VM du WAF sans réponse en SSH. Aucune alerte n'avait signalé les incidents mémoire des jours précédents |

## Contexte

Depuis la veille, le module AppSec de CrowdSec **rejetait tout envoi de plus de 10 Mo** : 138 rejets en 20 heures,
surtout la synchronisation des vidéos du téléphone. Ces 403, ajoutés aux 405 normaux de WebDAV, avaient en plus fait
bannir la maison du drive par le module « comportement suspect » de BunkerWeb. La matinée a été consacrée à corriger
ce problème : c'est cette correction qui a provoqué la première coupure, et sa réussite qui a révélé la seconde.

## Chronologie (30/09/2026)

| Heure | Événement |
|---|---|
| 9 h 36 | Déploiement d'un réglage AppSec (que faire d'un corps trop gros) ajouté au fichier d'**acquisition** de CrowdSec, où cette option n'existe pas |
| 9 h 36 | CrowdSec refuse de démarrer (« unknown field ») ; sans lui, le module CrowdSec du WAF refuse chaque requête (comportement « fermé » en cas de panne) |
| Juste après | Délais dépassés à la vérification du déploiement ; alertes `ServicePublicIndisponible` |
| 10 h 39 | Ligne retirée, CrowdSec relancé : services rétablis |
| Entre-temps | Bannissement du drive levé : la synchronisation du téléphone reprend, avec toutes ses tentatives en retard ; le WAF est redémarré |
| ≈ 11 h 30 | Le WAF n'a plus de mémoire : VM figée, services injoignables |
| ≈ 11 h 55 | Le noyau tue les processus nginx en cause : rétablissement sans intervention |
| Dans la journée | Le réglage AppSec voulu est appliqué au bon endroit (*hook* `SetBodySizeExceededAction`), testé, sans coupure : les 10 premiers Mo d'un envoi sont inspectés, le reste passe |
| 15 h 24 | Correction de fond de la mémoire en service (voir plus bas) |

## Causes racines

**Première coupure** : un réglage écrit dans le mauvais fichier, déployé sans que la configuration de CrowdSec soit
testée avant d'être relue. Le WAF est conçu pour refuser plutôt que laisser passer quand CrowdSec ne répond pas :
c'est voulu, mais cela transforme toute erreur de configuration de CrowdSec en coupure totale.

**Seconde coupure** : deux composants gardaient le corps entier des envois en mémoire. Le module AppSec de CrowdSec
lit tout le corps pour le transmettre (`get_body` du *bouncer* Lua), et ModSecurity inspecte jusqu'à la taille
maximale autorisée par le site (16 Go pour le drive, 50 Go pour les photos). Un envoi de 1 Go donnait un processus
nginx de 1,3 Go, sur une VM de 2 Go. Le problème existait déjà : des processus nginx tués faute de mémoire 3 fois le
28/09, 15 fois le 29/09, 16 fois le 30/09 au matin, chaque fois une coupure brève passée inaperçue. La reprise de la
synchronisation du téléphone, plus le pic de mémoire au redémarrage du WAF, a suffi à tout faire tomber.

## Ce qui a bien marché / moins bien marché

- **Bien** : les sondes ont détecté la première coupure immédiatement ; lors de la seconde, le noyau a fini par tuer
  les processus en cause et le service est revenu seul.
- **Moins bien** : aucune alerte sur les processus tués faute de mémoire, alors que la métrique existait
  (`node_vmstat_oom_kill`) ; un réglage déployé sans test de syntaxe ; deux problèmes liés traités le même jour,
  le second masqué par le premier.

## Actions correctives

- [x] Le script qui pose les réglages de CrowdSec teste la configuration (`crowdsec -t`) avant de la faire relire,
  et remet la version précédente en cas d'échec.
- [x] Chemins réservés aux envois (`= /api/assets` pour les photos, `/remote.php/dav/uploads/` pour le drive) : ni
  ModSecurity ni AppSec, tout le reste des deux sites restant inspecté. Ces chemins exigent une session authentifiée
  de l'application, et leur contenu est binaire : l'inspection y apportait peu, pour un coût en mémoire illimité.
  Risque accepté : une faille dans le traitement des envois par l'application ne serait plus filtrée par le WAF ;
  il est couvert par les mises à jour et la veille de sécurité.
- [x] Alerte `ProcessusTuesFauteDeMemoire` sur toutes les machines. Depuis : aucun processus tué, 393 Mo disponibles
  au plus bas sur le WAF.
- [x] Transmission « au fil de l'eau » des envois essayée puis retirée le soir même : un envoi interrompu arrivait
  tronqué chez l'application (400). nginx garde la mise en tampon sur disque, qui ne coûte pas de mémoire.
- [ ] Mémoire de la VM du WAF portée à 3 Go (décrite dans OpenTofu, à appliquer avec le prochain redimensionnement
  des VM).

**Piste écartée** : plafonner l'inspection de ModSecurity (`SecRequestBodyLimit` avec `ProcessPartial`). Le
connecteur nginx de ModSecurity relit en mémoire tout corps passé par un fichier temporaire
(`msc_request_body_from_file`) : le plafond n'aurait rien changé.
