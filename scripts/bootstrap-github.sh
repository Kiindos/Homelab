#!/usr/bin/env bash
# Pousse ce dossier vers un dépôt GitHub déjà créé.
# Usage : ./scripts/bootstrap-github.sh <utilisateur>/<depot>   (ex. maxime/homelab)
set -euo pipefail
REPO="${1:?Usage : $0 <utilisateur>/<depot>}"
cd "$(dirname "$0")/.."

[ -d .git ] || git init -b main
git add .
git diff --cached --quiet || git commit -m "chore: initialisation du dépôt"
git remote get-url origin >/dev/null 2>&1 || git remote add origin "git@github.com:${REPO}.git"

# Si le dépôt a été créé avec un README ou une licence sur GitHub, on intègre ce premier commit.
if git ls-remote --exit-code origin main >/dev/null 2>&1; then
  git pull --rebase --allow-unrelated-histories -X ours origin main || true
fi
git push -u origin main
