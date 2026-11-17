#!/usr/bin/env bash
# Affiche en JSON le dernier commit de chaque source d'icônes, sans rien télécharger.
# Objectif unique : savoir si une source a changé depuis la dernière release.
set -euo pipefail

declare -A repos=(
  [selfhst]=selfhst/icons
  [devicon]=devicons/devicon
  [material]=material-extensions/vscode-material-icon-theme
  [fluent]=microsoft/fluentui-emoji
  [dashboard]=homarr-labs/dashboard-icons
  [simpleicons]=simple-icons/simple-icons
  [flatcolor]=icons8/flat-color-icons
  [fluentsystem]=microsoft/fluentui-system-icons
)

first=1
printf '{'
for s in selfhst devicon material fluent dashboard simpleicons flatcolor fluentsystem; do
  sha=$(git ls-remote "https://github.com/${repos[$s]}.git" HEAD | head -1 | cut -f1)
  [[ -n "$sha" ]] || { echo "Impossible de lire $s" >&2; exit 1; }
  ((first)) || printf ','
  printf '"%s":"%s"' "$s" "$sha"
  first=0
done
# icônes ajoutées à la main : empreinte du dossier custom/ dans le dépôt (exécuté depuis le dépôt)
custom=$(git -C "$(dirname "$0")/.." rev-parse --verify --quiet HEAD:custom || echo none)
printf ',"extra":"%s"}\n' "$custom"
