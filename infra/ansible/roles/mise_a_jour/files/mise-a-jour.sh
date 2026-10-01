#!/bin/bash
# Géré par Ansible (rôle mise_a_jour). Met la machine à jour : paquets (apt), images des piles Docker pour la même
# version, puis redémarrage si un paquet l'exige. Lancé tout de suite ou par une minuterie locale (playbook
# mises-a-jour.yml) : ni Semaphore ni VPN ne sont nécessaires au moment de la maintenance.
#
#   mise-a-jour [--attente SECONDES] [--redemarrage si_necessaire|jamais] [--sans-images]
#
# Journal : journalctl -u mise-a-jour ; état pour Prometheus : mise-a-jour.prom (collecteur textfile).
set -uo pipefail
export DEBIAN_FRONTEND=noninteractive LC_ALL=C.UTF-8
METRIQUES=/var/lib/prometheus/node-exporter/mise-a-jour.prom

attente=0 redemarrage=si_necessaire images=1
while (( $# )); do
  case "$1" in
    --attente) attente="${2:-}"; shift 2 ;;
    --redemarrage) redemarrage="${2:-}"; shift 2 ;;
    --sans-images) images=0; shift ;;
    *) echo "Option inconnue : $1" >&2; exit 2 ;;
  esac
done
[[ "$attente" =~ ^[0-9]{1,5}$ ]] || { echo "Attente invalide : $attente" >&2; exit 2; }
[[ "$redemarrage" =~ ^(si_necessaire|jamais)$ ]] || { echo "Redémarrage invalide : $redemarrage" >&2; exit 2; }

if (( attente > 0 )); then
  echo "Ordre de passage : début dans $(( attente / 60 )) min."
  sleep "$attente"
fi

debut=$(date +%s) statut=1 paquets=0 piles=0

ecrire_etat() {
  local reussite temporaire
  reussite=$(awk '/^homelab_mise_a_jour_derniere_reussite_timestamp/ {print $2}' "$METRIQUES" 2>/dev/null)
  (( statut )) && reussite=$(date +%s)
  temporaire=$(mktemp "${METRIQUES%/*}/.mise-a-jour.XXXXXX") || return
  {
    echo "# HELP homelab_mise_a_jour_statut 1 si la dernière mise à jour de la machine a réussi."
    echo "homelab_mise_a_jour_statut $statut"
    echo "homelab_mise_a_jour_derniere_execution_timestamp $(date +%s)"
    [[ -n "$reussite" ]] && echo "homelab_mise_a_jour_derniere_reussite_timestamp $reussite"
    echo "homelab_mise_a_jour_duree_secondes $(( $(date +%s) - debut ))"
    echo "homelab_mise_a_jour_paquets $paquets"
    echo "homelab_mise_a_jour_piles_recreees $piles"
  } > "$temporaire"
  chmod 0644 "$temporaire" && mv "$temporaire" "$METRIQUES"
}

noyau_a_jour() {
  local recent
  recent=$(find /boot -maxdepth 1 -name 'vmlinuz-*' -printf '%f\n' | sed 's/^vmlinuz-//' | sort -V | tail -n 1)
  [[ -z "$recent" || "$recent" == "$(uname -r)" ]]
}

echo "== Paquets"
avant=$(dpkg-query -W -f '${Package} ${Version}\n' | sort)
apt_options=(-q -o DPkg::Lock::Timeout=900 -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold)
if apt-get "${apt_options[@]}" update && apt-get "${apt_options[@]}" -y dist-upgrade; then
  paquets=$(comm -13 <(echo "$avant") <(dpkg-query -W -f '${Package} ${Version}\n' | sort) | wc -l)
  echo "$paquets paquet(s) installé(s) ou mis à jour."
else
  echo "ÉCHEC de la mise à jour des paquets."
  statut=0
fi

if (( images )) && command -v docker >/dev/null; then
  echo "== Images des piles (même version)"
  while IFS=$'\t' read -r projet fichiers; do
    options=()
    IFS=, read -ra liste <<< "$fichiers"
    for fichier in "${liste[@]}"; do options+=(-f "$fichier"); done
    dossier=$(dirname "${liste[0]}")
    avant_ids=$(docker compose -p "$projet" "${options[@]}" ps -q | sort)
    if (cd "$dossier" && docker compose -p "$projet" "${options[@]}" pull --ignore-buildable --quiet \
        && docker compose -p "$projet" "${options[@]}" up -d); then
      if [[ "$avant_ids" != "$(docker compose -p "$projet" "${options[@]}" ps -q | sort)" ]]; then
        echo "Pile $projet : nouvelle image, conteneurs recréés."
        piles=$(( piles + 1 ))
      else
        echo "Pile $projet : déjà à jour."
      fi
    else
      echo "Pile $projet : ÉCHEC."
      statut=0
    fi
  done < <(docker compose ls --format json | python3 -c 'import json, sys
for p in json.load(sys.stdin): print(p["Name"] + "\t" + p["ConfigFiles"])')
  docker image prune -f >/dev/null
  docker ps --format '{{.Names}} {{.Status}}'
fi

/usr/local/sbin/etat-mises-a-jour 2>/dev/null || true
echo "== Bilan : $paquets paquet(s), $piles pile(s) recréée(s), $(( $(date +%s) - debut )) s, statut $statut."

if [[ -f /run/reboot-required ]] || ! noyau_a_jour; then
  if [[ "$redemarrage" == si_necessaire ]]; then
    echo "Redémarrage demandé par : $(sort -u /run/reboot-required.pkgs 2>/dev/null | tr '\n' ' ')(noyau $(uname -r))."
    ecrire_etat
    systemctl reboot
    exit 0
  fi
  echo "Redémarrage nécessaire : laissé à l'appelant (Ansible) ou à une maintenance dédiée (hyperviseur)."
fi
ecrire_etat
(( statut ))
