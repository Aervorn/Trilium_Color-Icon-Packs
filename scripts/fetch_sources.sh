#!/usr/bin/env bash
# Récupère les SVG des 4 sources d'icônes (clone Git partiel : uniquement les fichiers utiles).
# Objectif unique : télécharger les sources. Aucune compilation ici (voir build_pack.py).
#
# Usage : fetch_sources.sh <dossier_destination> [source...]
#   sans source : les 4 (selfhst devicon material fluent)
set -euo pipefail

dest="${1:?Usage : fetch_sources.sh <dossier_destination> [source...]}"
shift
(($#)) || set -- selfhst devicon material fluent
sources=("$@")
mkdir -p "$dest"

sparse_clone() {
  local repo=$1 dir=$2
  shift 2
  rm -rf "${dest:?}/$dir"
  git clone --quiet --depth 1 --filter=blob:none --sparse "https://github.com/$repo.git" "$dest/$dir"
  git -C "$dest/$dir" sparse-checkout set --no-cone "$@"
  echo "$dir : $(find "$dest/$dir" -name '*.svg' | wc -l) SVG ($(git -C "$dest/$dir" rev-parse --short HEAD))"
}

for s in "${sources[@]}"; do
  case "$s" in
    selfhst)  sparse_clone selfhst/icons selfhst '/svg/*' '/index.json' '/LICENSE' ;;
    devicon)  sparse_clone devicons/devicon devicon '/icons/**/*.svg' '/devicon.json' '/LICENSE' ;;
    material) sparse_clone material-extensions/vscode-material-icon-theme material '/icons/*.svg' '/LICENSE' ;;
    fluent)   sparse_clone microsoft/fluentui-emoji fluent '/assets/*/Color/*.svg' '/assets/*/Default/Color/*.svg' '/assets/*/metadata.json' '/LICENSE' ;;
    *) echo "Source inconnue : $s" >&2; exit 1 ;;
  esac
done
