#!/usr/bin/env bash
# Télécharge les manifestes de la dernière release publiée.
#
# Objectif unique : fournir à build_pack.py les points de code déjà attribués, pour qu'une icône
# garde le même point de code d'une release à l'autre. Sans cela, une icône ajoutée à une source
# décale toutes les suivantes : un client Trilium qui garde l'ancienne police avec le nouveau
# manifeste (ou l'inverse, le temps d'une synchro) affiche alors de mauvaises icônes.
#
# Usage : fetch_previous_manifests.sh <owner/repo> <dossier_sortie>
# Produit <dossier_sortie>/<prefix>.manifest.json pour chaque pack de la dernière release.
# Sans release (premier build, fork neuf), le dossier reste vide et build_pack.py numérote depuis le début.
set -euo pipefail

repo="${1:?owner/repo}"
out="${2:?dossier de sortie}"
mkdir -p "$out"
base="https://github.com/$repo/releases"

if ! release=$(curl -fsSL "$base/latest/download/release.json"); then
    echo "Pas de release publiée : numérotation depuis le début"
    exit 0
fi
tag=$(jq -r '.version' <<<"$release")
jq -r '.packs[] | "\(.prefix) \(.manifest)"' <<<"$release" | while read -r prefix manifest; do
    curl -fsSL -o "$out/$prefix.manifest.json" "$base/download/$tag/$manifest"
    echo "$prefix : manifeste de la release $tag"
done
