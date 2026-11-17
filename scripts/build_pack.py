#!/usr/bin/env python3
"""Compile un pack d'icônes Trilium en couleur (police COLRv1 + manifeste) à partir d'une source SVG.

Objectif unique : transformer UNE source déjà récupérée (voir fetch_sources.sh) en un pack Trilium.

Usage : build_pack.py <source> <dossier_sources> <dossier_sortie>
  source : selfhst | devicon | material | fluent

Produit dans <dossier_sortie>/<source>/ :
  <prefix>.woff2   police couleur COLRv1
  manifest.json    manifeste Trilium {"icons": {"<prefix>-<nom>": {"glyph": ..., "terms": [...]}}}
  skipped.txt      SVG ignorés (non convertibles) avec la raison
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

PACKS = {
    "selfhst": {"prefix": "sh", "title": "selfh.st Icons (couleur)"},
    "devicon": {"prefix": "dev", "title": "Devicon (couleur)"},
    "material": {"prefix": "mat", "title": "Material Icon Theme (couleur)"},
    "fluent": {"prefix": "fl", "title": "Fluent Emoji (couleur)"},
}
PUA_START = 0xF0000  # Supplementary Private Use Area-A (65 534 points de code)
KEY_RE = re.compile(r"[^a-z0-9_-]+")


def slug(text: str) -> str:
    return KEY_RE.sub("-", text.lower()).strip("-")


def terms_of(*values) -> list[str]:
    out: list[str] = []
    for v in values:
        for t in (v if isinstance(v, (list, tuple)) else [v]):
            t = str(t or "").strip()
            if t and t.lower() not in (x.lower() for x in out):
                out.append(t)
    return out


# ---------- Collecte par source : renvoie [(nom, chemin_svg, [termes])] ----------

def collect_selfhst(root: Path):
    index = {e["Reference"]: e for e in json.loads((root / "index.json").read_text())}
    for svg in sorted((root / "svg").glob("*.svg")):
        name = svg.stem
        if name.endswith(("-light", "-dark")) and name.rsplit("-", 1)[0] in index:
            continue  # variantes monochromes : on garde l'icône couleur
        meta = index.get(name, {})
        tags = [t.strip() for t in (meta.get("Tags") or "").split(",")]
        yield name, svg, terms_of(meta.get("Name") or name, name, tags, meta.get("Category"))


def collect_devicon(root: Path):
    for entry in json.loads((root / "devicon.json").read_text()):
        name = entry["name"]
        variants = entry.get("versions", {}).get("svg", [])
        for v in ("original", "plain", "line"):  # "original" = logo en couleur
            svg = root / "icons" / name / f"{name}-{v}.svg"
            if v in variants and svg.exists():
                yield name, svg, terms_of(name, entry.get("altnames", []), entry.get("tags", []))
                break


def collect_material(root: Path):
    for svg in sorted((root / "icons").glob("*.svg")):
        name = svg.stem
        words = name.replace("_", " ").replace("-", " ")
        yield name, svg, terms_of(words, name)


def collect_fluent(root: Path):
    for folder in sorted((root / "assets").iterdir()):
        meta_file = folder / "metadata.json"
        if not meta_file.exists():
            continue
        meta = json.loads(meta_file.read_text())
        svgs = sorted(folder.glob("Color/*.svg")) or sorted(folder.glob("Default/Color/*.svg"))
        if svgs:
            yield slug(folder.name), svgs[0], terms_of(meta.get("cldr") or folder.name, meta.get("keywords", []), meta.get("group"))


COLLECTORS = {"selfhst": collect_selfhst, "devicon": collect_devicon, "material": collect_material, "fluent": collect_fluent}


# ---------- Validation : nanoemoji échoue sur tout le lot si un seul SVG est invalide ----------

def check_svg(path: str):
    try:
        from picosvg.svg import SVG
        SVG.parse(path).topicosvg()
        return path, None
    except Exception as exc:  # noqa: BLE001 - on veut toutes les raisons d'échec
        return path, f"{type(exc).__name__}: {str(exc).splitlines()[0][:160] if str(exc) else ''}"


def find_unpaintable(build_dir: Path, prefix: str) -> dict[int, str]:
    """Rejoue, glyphe par glyphe, l'étape de nanoemoji qui a échoué et renvoie {point_de_code: erreur}.

    Certains SVG passent picosvg mais échouent plus tard (ex. dégradé hors des limites COLRv1).
    nanoemoji ne dit pas lequel : on le retrouve ici pour l'exclure.
    """
    from nanoemoji import config as nconfig, glyphmap
    from nanoemoji import write_font
    from nanoemoji.color_glyph import ColorGlyph
    from absl import flags
    from picosvg.svg import SVG

    if not flags.FLAGS.is_parsed():
        flags.FLAGS(["build_pack"])  # nanoemoji lit sa config via absl
    previous = os.getcwd()
    os.chdir(build_dir)  # les chemins de la config et du glyphmap sont relatifs au dossier de build
    try:
        cfg = nconfig.load(Path(f"{prefix}.toml"))
        ufo = write_font._ufo(cfg)
        bad = {}
        for gid, g in enumerate(glyphmap.parse_csv(Path(f"{prefix}.glyphmap")), start=1):
            if not g.codepoints:
                continue
            try:
                ColorGlyph.create(cfg, ufo, str(g.svg_file), gid, g.glyph_name, g.codepoints, SVG.parse(g.svg_file))
            except Exception as exc:  # noqa: BLE001
                bad[g.codepoints[0]] = f"{type(exc).__name__}: {str(exc)[:160]}"
    finally:
        os.chdir(previous)
    return bad


def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] not in PACKS:
        sys.exit(__doc__)
    source, src_root, out_root = sys.argv[1], Path(sys.argv[2]) / sys.argv[1], Path(sys.argv[3])
    prefix = PACKS[source]["prefix"]
    out = out_root / source
    out.mkdir(parents=True, exist_ok=True)

    items, seen = [], set()
    for name, svg, terms in COLLECTORS[source](src_root):
        key = f"{prefix}-{slug(name)}"
        if key in seen:
            continue
        seen.add(key)
        items.append((key, svg, terms))

    with ProcessPoolExecutor() as pool:
        errors = dict(pool.map(check_svg, [str(s) for _, s, _ in items], chunksize=16))
    valid = [i for i in items if errors[str(i[1])] is None]
    skipped = [f"{k}\t{s.name}\t{errors[str(s)]}" for k, s, _ in items if errors[str(s)] is not None]

    work = Path(tempfile.mkdtemp(prefix=f"pack-{source}-"))
    manifest, src_of = {}, {}
    for n, (key, svg, terms) in enumerate(valid):
        src_of[key] = svg.name
        cp = PUA_START + n
        shutil.copy(svg, work / f"emoji_u{cp:x}.svg")
        manifest[key] = {"glyph": chr(cp), "terms": terms}

    font = f"{prefix}.ttf"
    key_of = {ord(v["glyph"]): k for k, v in manifest.items()}
    for attempt in range(1, 4):
        cmd = ["nanoemoji", "--color_format", "glyf_colr_1", "--family", f"Trilium {prefix}",
               "--upem", "1024", "--width", "1024", "--ascender", "896", "--descender", "-128",
               "--build_dir", str(work / "build"), "--output_file", font,
               *sorted(str(p) for p in work.glob("emoji_u*.svg"))]
        run = subprocess.run(cmd, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if run.returncode == 0:
            break
        bad = find_unpaintable(work / "build", prefix)
        if not bad or attempt == 3:
            out = run.stdout
            start = out.find("FAILED:")  # ninja affiche ici la commande en échec et sa vraie erreur
            sys.stderr.write(out[start:start + 6000] if start >= 0 else out[-6000:])
            sys.exit(f"{source}: échec de nanoemoji (tentative {attempt})")
        for cp, err in bad.items():
            key = key_of[cp]
            skipped.append(f"{key}\t{src_of[key]}\t{err}")
            del manifest[key]
            (work / f"emoji_u{cp:x}.svg").unlink()
        print(f"{source}: {len(bad)} icône(s) non convertible(s) retirée(s), nouvelle tentative")

    from fontTools.ttLib import TTFont
    ttf = TTFont(work / "build" / font)
    ttf.flavor = "woff2"
    ttf.save(out / f"{prefix}.woff2")
    (out / "manifest.json").write_text(json.dumps({"icons": manifest}, ensure_ascii=False, separators=(",", ":")))
    (out / "skipped.txt").write_text("\n".join(skipped) + ("\n" if skipped else ""))
    (out / "pack.json").write_text(json.dumps({"source": source, "prefix": prefix, "title": PACKS[source]["title"],
                                               "icons": len(manifest), "skipped": len(skipped)}))
    shutil.rmtree(work, ignore_errors=True)
    size = (out / f"{prefix}.woff2").stat().st_size
    print(f"{source}: {len(manifest)} icônes, {len(skipped)} ignorées, police {size / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
