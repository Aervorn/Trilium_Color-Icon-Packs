#!/usr/bin/env python3
"""Rassemble les packs compilés en fichiers de release + un index release.json.

Objectif unique : préparer les fichiers à publier. Aucune compilation ni publication ici.

Usage : package_release.py <dossier_packs> <dossier_release> <version> <sources.json>
  dossier_packs : sortie de build_pack.py (un sous-dossier par source)
  sources.json  : sortie de source_revisions.sh (commit de chaque source)

Produit dans <dossier_release> :
  <prefix>.woff2, <prefix>.manifest.json, <prefix>.skipped.txt (pour chaque pack)
  release.json : {"version", "sources", "packs": [{source, prefix, title, icons, skipped, font, manifest, fontSha256, manifestSha256}]}
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    if len(sys.argv) != 5:
        sys.exit(__doc__)
    packs_dir, rel_dir, version, sources_file = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3], Path(sys.argv[4])
    rel_dir.mkdir(parents=True, exist_ok=True)

    packs = []
    for pack_json in sorted(packs_dir.glob("*/pack.json")):
        info = json.loads(pack_json.read_text())
        src, prefix = pack_json.parent, info["prefix"]
        font, manifest = rel_dir / f"{prefix}.woff2", rel_dir / f"{prefix}.manifest.json"
        shutil.copy(src / f"{prefix}.woff2", font)
        shutil.copy(src / "manifest.json", manifest)
        skipped = (src / "skipped.txt").read_text()
        # en-tête obligatoire : GitHub refuse les fichiers vides en pièce jointe de release
        (rel_dir / f"{prefix}.skipped.txt").write_text(
            f"# Skipped icons ({info['skipped']}): key, SVG file, reason\n{skipped}")
        packs.append({**info, "font": font.name, "manifest": manifest.name,
                      "fontSha256": sha256(font), "manifestSha256": sha256(manifest)})

    if not packs:
        sys.exit("Aucun pack trouvé")
    index = {"version": version, "sources": json.loads(sources_file.read_text()), "packs": packs}
    (rel_dir / "release.json").write_text(json.dumps(index, ensure_ascii=False, indent=2))
    for p in packs:
        print(f"{p['prefix']:>4} {p['icons']:>5} icons  {(rel_dir / p['font']).stat().st_size / 1024:>7.0f} KB  ({p['skipped']} skipped)")


if __name__ == "__main__":
    main()
