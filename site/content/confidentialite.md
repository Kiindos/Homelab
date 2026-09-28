---
title: Confidentialité
description: Quelles données sont traitées, pourquoi, combien de temps, et comment exercer vos droits.
layout: juridique
date: 2026-09-27
lastmod: 2026-09-28
---

## En bref

- **Ce site** n'a ni cookie, ni mesure d'audience, ni publicité, ni formulaire. Seuls des journaux techniques
  (adresse IP, page demandée, navigateur) sont conservés brièvement, pour la sécurité et le bon fonctionnement.
- **Les services privés** (photos, fichiers, médias…) ne sont ouverts qu'aux personnes invitées. Leurs données
  restent sur le serveur personnel de l'éditeur, en France.
- Rien n'est vendu, loué ni utilisé à des fins publicitaires.

## Responsable du traitement

Maxime Bertrand, éditeur du site. Contact : {{< contact >}}

## Ce site

**Données traitées.** À chaque visite, le serveur enregistre dans ses journaux l'adresse IP, la date, la page
demandée, la page d'origine et l'identifiant du navigateur. **Finalité** : faire fonctionner le site, diagnostiquer
les pannes, détecter les abus. **Base légale** : l'intérêt légitime de l'éditeur à assurer la sécurité et la
disponibilité du site. **Durée** : les journaux sont effacés automatiquement par rotation (quelques jours à
quelques semaines selon le trafic).

**Cloudflare**, par qui passe le trafic du site, traite ces mêmes données techniques pour acheminer les requêtes et
protéger le site ; ce traitement relève de sa [politique de confidentialité](https://www.cloudflare.com/privacypolicy/).
Cloudflare peut transférer des données aux États-Unis, dans le cadre du Data Privacy Framework UE–États-Unis.

**Ressource externe.** Les pages contenant des schémas chargent la bibliothèque Mermaid depuis le réseau de
diffusion jsDelivr : votre navigateur lui communique alors son adresse IP, comme pour toute ressource web.

**Cookies.** Aucun : le site n'en dépose pas et n'utilise aucun traceur. Aucune bannière de consentement n'est donc
nécessaire.

## Services privés

Photos, fichiers, médias, notifications et portail de connexion sont réservés aux personnes invitées par
l'éditeur (usage familial).

**Données traitées** :

- **compte** : identifiant, nom, adresse e-mail, groupes, empreinte du mot de passe (jamais le mot de passe
  lui-même), réglages de double authentification ;
- **contenus** que vous déposez : photos et vidéos (avec leurs métadonnées, dont la localisation éventuelle),
  fichiers, historique de lecture ;
- **journaux de sécurité** : adresse IP, date, adresse demandée, résultat des connexions.

**Finalités** : fournir les services, sécuriser les comptes (double authentification, blocage après plusieurs échecs)
et protéger le serveur contre les attaques. **Base légale** : la fourniture du service que vous avez accepté en
rejoignant le homelab, et l'intérêt légitime de l'éditeur à le sécuriser.

**Où et combien de temps** : sur le serveur de l'éditeur, en France, tant que le compte existe ; les contenus sont
effacés avec le compte, à votre demande. Les journaux de sécurité sont regroupés sur le serveur de supervision,
consultables par l'éditeur seul, et effacés automatiquement au bout de **30 jours**. Les sauvegardes, chiffrées, restent sur des équipements de l'éditeur ou chez un prestataire situé dans
l'Union européenne.

**Destinataires et sous-traitants** :

- les e-mails du service (invitation, choix du mot de passe, codes de vérification) sont envoyés par
  **Proton AG** (Suisse, pays reconnu comme offrant un niveau de protection adéquat) ;
- le pare-feu applicatif utilise **CrowdSec** : l'adresse IP d'un visiteur qui se comporte comme un attaquant
  (analyse de ports, tentatives d'intrusion) est partagée avec le réseau communautaire de CrowdSec, pour protéger
  d'autres serveurs. Ces alertes sont conservées 7 jours sur le serveur ;
- certaines fonctions des applications peuvent charger des ressources de tiers depuis votre navigateur (par
  exemple les fonds de carte des photos).

**Cookies** : uniquement des cookies strictement nécessaires (session de connexion et sécurité), exemptés de
consentement. Aucun cookie de mesure d'audience ni de publicité.

## Vos droits

Conformément au RGPD et à la loi Informatique et Libertés, vous pouvez demander l'accès à vos données, leur
rectification, leur effacement, leur portabilité, la limitation du traitement ou vous y opposer, en écrivant à
{{< contact >}}. Une réponse vous sera apportée dans un délai d'un mois.

Si vous estimez que vos droits ne sont pas respectés, vous pouvez adresser une réclamation à la CNIL
(<https://www.cnil.fr>, 3 place de Fontenoy, TSA 80715, 75334 Paris Cedex 07).

## Sécurité

Les données sont chiffrées en transit (HTTPS), les accès aux services passent par un portail unique avec double
authentification, et le serveur est protégé par un pare-feu, un pare-feu applicatif et des mises à jour suivies.
Le détail de ces mesures est public : voir la [vue d'ensemble de l'architecture](/architecture/overview/).
