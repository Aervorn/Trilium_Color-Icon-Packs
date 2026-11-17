#!/usr/bin/env bash
# Affiche en JSON le dernier commit de chaque source d'icônes, sans rien télécharger.
# Objectif unique : savoir si une source a changé depuis la dernière release.
set -euo pipefail

declare -A repos=(
  [selfhst]=selfhst/icons
  [devicon]=devicons/devicon
  [material]=material-extensions/vscode-material-icon-theme
  [fluent]=microsoft/fluentui-emoji
)

first=1
printf '{'
for s in selfhst devicon material fluent; do
  sha=$(git ls-remote "https://github.com/${repos[$s]}.git" HEAD | cut -f1)
  [[ -n "$sha" ]] || { echo "Impossible de lire $s" >&2; exit 1; }
  ((first)) || printf ','
  printf '"%s":"%s"' "$s" "$sha"
  first=0
done
printf '}\n'
