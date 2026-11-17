#!/usr/bin/env bash
# Récupère les SVG des sources d'icônes (clone Git partiel : uniquement les fichiers utiles).
# Objectif unique : télécharger les sources. Aucune compilation ici (voir build_pack.py).
#
# Usage : fetch_sources.sh <dossier_destination> [source...]
#   sans source : toutes (selfhst devicon material fluent dashboard simpleicons flatcolor fluentsystem extra)
set -euo pipefail

dest="${1:?Usage : fetch_sources.sh <dossier_destination> [source...]}"
shift
(($#)) || set -- selfhst devicon material fluent dashboard simpleicons flatcolor fluentsystem extra
repo_root="$(cd "$(dirname "$0")/.." && pwd)"
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
    dashboard)
      sparse_clone homarr-labs/dashboard-icons dashboard '/svg/*' '/meta/*' '/LICENSE'
      # liste de selfh.st, pour ne pas dupliquer ses icônes
      sparse_clone selfhst/icons selfhst-index '/index.json' ;;
    simpleicons)  sparse_clone simple-icons/simple-icons simpleicons '/icons/*' '/data/simple-icons.json' '/LICENSE.md' ;;
    flatcolor)    sparse_clone icons8/flat-color-icons flatcolor '/svg/*' '/LICENSE.md' ;;
    fluentsystem) sparse_clone microsoft/fluentui-system-icons fluentsystem '/assets/*/SVG/*_color.svg' '/assets/*/metadata.json' '/LICENSE' ;;
    extra)        # icônes ajoutées à la main dans custom/ (dépôt lui-même)
      rm -rf "${dest:?}/extra" && mkdir -p "$dest/extra"
      if compgen -G "$repo_root/custom/*.svg" > /dev/null; then cp "$repo_root"/custom/*.svg "$dest/extra/"; fi
      [[ -f "$repo_root/custom/terms.json" ]] && cp "$repo_root/custom/terms.json" "$dest/extra/"
      echo "extra : $(find "$dest/extra" -name '*.svg' | wc -l) SVG (custom/)" ;;
    *) echo "Source inconnue : $s" >&2; exit 1 ;;
  esac
done
