---
title: "Runbook : réagir à une alerte"
description: Où arrivent les alertes, et les premiers gestes pour chacune.
tags: [supervision, alertes, prometheus]
---

# Runbook : réagir à une alerte

**Quand l'utiliser :** à la réception d'une alerte (e-mail, notification sur le téléphone) ou devant un voyant
rouge du NOC.
**Durée estimée :** quelques minutes pour qualifier ; le reste dépend de l'alerte.
**Prérequis :** VPN d'administration (Grafana, Alertmanager et SSH n'existent que derrière lui).

Règles : `infra/ansible/roles/supervision/files/alertes.yml`. Choix de la supervision :
[ADR 0014](../adr/0014-supervision-noc.md) ; journaux : [ADR 0020](../adr/0020-journaux-centralises.md).

## Où arrivent les alertes

| Gravité | Destination | Rappel |
|---|---|---|
| critique | e-mail + notification prioritaire sur le téléphone (ntfy) + NOC | toutes les 6 h tant que ça dure, puis un message de fin |
| avertissement | NOC (et Grafana) | — |
| sécurité | e-mail + notification, une par machine | toutes les 12 h |
| veille (mises à jour, failles connues) | e-mail + notification, regroupées | chaque semaine |
| info | notification discrète | une fois par jour |

Une alerte critique en cours fait taire les avertissements de la même machine (règle d'inhibition) : traiter la
critique d'abord.

## Premiers gestes

| Alerte | Premiers gestes |
|---|---|
| `MachineInjoignable` | Console de la VM dans Proxmox ; si c'est l'hyperviseur lui-même : accès de secours par la carte de gestion à distance |
| `VMArretee` | `qm status <vmid>` puis `qm start <vmid>` ; lire `journalctl -b -1` dans la VM au redémarrage |
| `ServicePublicIndisponible` | Tester depuis le VPN ; `docker compose ps` sur la VM du service ; journaux du WAF si seul le WAF répond en erreur ([exemple](../postmortems/2026-09-30-coupures-du-waf.md)) |
| `PoolZFSDegrade` | `zpool status -x` ; identifier le disque par son numéro de série ; **ne rien détacher** avant d'avoir le disque de remplacement |
| `DisqueEnEchecSMART`, `DefautsDisqueEnHausse` | `smartctl -a /dev/<disque>` ; noter l'évolution ; commander un disque si elle continue ; vérifier que le pool est sain |
| `EspaceDisqueFaible`, `EspaceDisqueCritique` | `df -h` puis `docker system df` ; purger les images inutiles |
| `StockageDonneesPresquePlein`, `StockagePoolPresquePlein` | Grafana « Stockage et e-mails » ; `zfs list -o name,used,refer,usedbysnapshots,quota` ; instantanés et zones de transit d'abord ; au-delà de 80-90 %, ZFS ralentit |
| `MemoireSaturee`, `ProcessusTuesFauteDeMemoire`, `ProcesseurSature` | `docker stats` pour trouver le conteneur ; `journalctl -k \| grep -i oom` ; revoir les ressources de la VM si c'est durable |
| `CertificatBientotExpire`, `CertificatExpireImminent` | Journaux du renouvellement (HTTP-01 sur le WAF, DNS-01 sur le proxy interne) |
| `Sauvegarde…` | [Runbook des sauvegardes](sauvegardes.md) : contrôle à la demande depuis Semaphore |
| `MiseAJourEchouee`, `PaquetsSecuriteEnAttente`, `RedemarrageEnAttente` | Journal de la mise à jour sur la machine ; relancer depuis Semaphore (« Mettre à jour le parc ») |
| `CourrielsEnEchec`, `CourrielsReleveImpossible` | Console du relais d'e-mails (activité, rejets) ; vérifier SPF, DKIM et DMARC du domaine |
| `OutilInterneIndisponible`, `CibleDeCollecteInjoignable` | `docker compose ps` et journaux du service concerné |
| `JournauxNonRecus` | Sur la machine : `systemctl status systemd-journal-upload` ; côté supervision : le conteneur VictoriaLogs |

## Chercher dans les journaux

Grafana → **Explore** → source **Journaux** (VictoriaLogs, LogsQL, 30 jours) :

| Besoin | Requête |
|---|---|
| Erreurs de la dernière heure, par machine | `_time:1h (error OR erreur OR "level=error") \| stats by (_HOSTNAME) count()` |
| Connexions SSH de la semaine | `_time:7d _SYSTEMD_UNIT:ssh.service Accepted` |
| Paquets refusés par le pare-feu | `_time:15m app_name:filterlog block` |
| Un conteneur précis | `_time:30m CONTAINER_NAME:<nom>` |

## Mettre une alerte en sourdine

Pendant une maintenance prévue : Alertmanager → *New Silence*, en ciblant l'instance, pour une durée bornée. Ne
jamais désactiver une règle dans le code pour faire taire une alerte : corriger la règle ou la cause.

## Vérification

L'alerte passe à « résolue » (message de fin pour les critiques) et le NOC revient au vert. Si la cause n'est pas
évidente ou si le service a été coupé, ouvrir un [post-mortem](../postmortems/).

## Tester la chaîne de notification

Envoyer à Alertmanager une alerte factice de gravité critique, qui expire seule au bout de cinq minutes
(`POST /api/v2/alerts`) : l'e-mail et la notification doivent arriver en moins d'une minute.
