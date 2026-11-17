#!/usr/bin/env python3
"""Compile un pack d'icônes Trilium en couleur (police COLRv1 + manifeste) à partir d'une source SVG.

Objectif unique : transformer UNE source déjà récupérée (voir fetch_sources.sh) en un pack Trilium.

Usage : build_pack.py <source> <dossier_sources> <dossier_sortie>
  source : selfhst | devicon | material | fluent | dashboard | simpleicons | flatcolor | fluentsystem | extra

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
    "selfhst": {"prefix": "sh", "title": "selfh.st Icons (color)"},
    "devicon": {"prefix": "dev", "title": "Devicon (color)"},
    "material": {"prefix": "mat", "title": "Material Icon Theme (color)"},
    "fluent": {"prefix": "fl", "title": "Fluent Emoji (color)"},
    "dashboard": {"prefix": "di", "title": "Dashboard Icons (color)"},
    "simpleicons": {"prefix": "si", "title": "Simple Icons (brand colors)"},
    "flatcolor": {"prefix": "fc", "title": "Flat Color Icons"},
    "fluentsystem": {"prefix": "fs", "title": "Fluent UI System Icons (color)"},
    "extra": {"prefix": "ex", "title": "Extra Icons (color)"},
}
PUA_START = 0xF0000  # Supplementary Private Use Area-A (65 534 points de code)
KEY_RE = re.compile(r"[^a-z0-9_-]+")


def slug(text: str) -> str:
    return KEY_RE.sub("-", text.lower()).strip("-")


def terms_of(*values) -> list[str]:
    """Termes de recherche d'une icône : le nom affiché en premier (infobulle du sélecteur), puis
    chaque terme en minuscules. Le sélecteur de Trilium met la recherche en minuscules mais compare
    les termes tels quels : un terme avec une majuscule (« Proxmox ») ne serait jamais trouvé."""
    out: list[str] = []
    for v in values:
        for t in (v if isinstance(v, (list, tuple)) else [v]):
            for part in str(t or "").split(","):  # certaines catégories sont des listes (« Self-Hosted,Other »)
                part = part.strip()
                if part and part not in out:
                    out.append(part)
    if not out:
        return out
    display, lowered = out[0], []
    for t in out:
        t = t.lower()
        if t not in lowered:
            lowered.append(t)
    return ([display] if display != display.lower() else []) + lowered


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


def collect_dashboard(root: Path):
    """Dashboard Icons (homarr-labs), sans les icônes déjà présentes dans selfh.st (même nom)."""
    index = root.parent / "selfhst-index" / "index.json"
    # seules les icônes que selfh.st fournit en SVG sont dans le pack « sh » (certaines n'existent qu'en PNG)
    in_selfhst = {e["Reference"] for e in json.loads(index.read_text()) if e.get("SVG") == "Yes"} if index.exists() else set()
    svgs = {p.stem: p for p in (root / "svg").glob("*.svg")}
    for stem in sorted(svgs):
        base = re.sub(r"-(light|dark)$", "", stem)
        if base != stem and base in svgs:
            continue  # variante claire/sombre : on garde l'icône de base
        name = re.sub(r"-svg$", "", base)  # ex. « dockhand-svg »
        if name in in_selfhst:
            continue
        meta_file = root / "meta" / f"{base}.json"
        meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
        words = name.replace("-", " ")
        yield name, svgs[stem], terms_of(words, name, meta.get("aliases", []),
                                         [c.replace("-", " ") for c in meta.get("categories", [])])


def _simpleicons_slug(title: str) -> str:
    """Règle de nommage des fichiers de Simple Icons (titleToSlug)."""
    import unicodedata
    for a, b in [("+", "plus"), (".", "dot"), ("&", "and"), ("đ", "d"), ("ħ", "h"), ("ı", "i"), ("ĸ", "k"),
                 ("ŀ", "l"), ("ł", "l"), ("ß", "ss"), ("ŧ", "t")]:
        title = title.replace(a, b)
    title = unicodedata.normalize("NFD", title.lower())
    title = "".join(c for c in title if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9]", "", title)


def _luminance(hex_color: str) -> float:
    def channel(c: int) -> float:
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


def collect_simpleicons(root: Path):
    """Simple Icons : logos monochromes colorés avec la couleur officielle de la marque.
    Une couleur trop sombre ou trop claire devient « currentColor » (couleur du texte du thème),
    pour que le logo reste lisible sur un thème clair comme sombre."""
    out_dir = root / "_colored"
    out_dir.mkdir(exist_ok=True)
    for entry in json.loads((root / "data" / "simple-icons.json").read_text()):
        name = entry.get("slug") or _simpleicons_slug(entry["title"])
        src = root / "icons" / f"{name}.svg"
        if not src.exists():
            continue
        hex_color = entry.get("hex", "000000")
        lum = _luminance(hex_color)
        fill = "currentColor" if lum < 0.04 or lum > 0.8 else f"#{hex_color}"
        dst = out_dir / src.name
        dst.write_text(src.read_text().replace("<svg ", f'<svg fill="{fill}" ', 1))
        aliases = entry.get("aliases", {})
        alias_terms = aliases.get("aka", []) + [d.get("title", "") for d in aliases.get("dup", [])] \
            + list(aliases.get("loc", {}).values())
        yield name, dst, terms_of(entry["title"], name, alias_terms)


def collect_flatcolor(root: Path):
    for svg in sorted((root / "svg").glob("*.svg")):
        name = svg.stem.replace("_", "-")
        yield name, svg, terms_of(svg.stem.replace("_", " "), name)


def collect_fluentsystem(root: Path):
    """Fluent UI System Icons, style « Color » ; on garde la plus grande taille disponible."""
    for folder in sorted((root / "assets").iterdir()):
        svgs = list(folder.glob("SVG/*_color.svg"))
        if not svgs:
            continue
        def size(p: Path) -> int:
            m = re.search(r"_(\d+)_color\.svg$", p.name)
            return int(m.group(1)) if m else 0
        svg = max(svgs, key=size)
        meta_file = folder / "metadata.json"
        meta = json.loads(meta_file.read_text()) if meta_file.exists() else {}
        yield slug(folder.name), svg, terms_of(meta.get("name", folder.name), slug(folder.name), meta.get("metaphor", []))


def collect_extra(root: Path):
    """Icônes ajoutées à la main dans le dossier custom/ du dépôt (nom du fichier = nom de l'icône).
    Mots-clés optionnels dans custom/terms.json : {"remarkable": ["reMarkable", "tablet", "e-ink"]}."""
    terms_file = root / "terms.json"
    extra_terms = json.loads(terms_file.read_text()) if terms_file.exists() else {}
    for svg in sorted(root.glob("*.svg")):
        name = slug(svg.stem)
        yield name, svg, terms_of(svg.stem.replace("-", " ").replace("_", " "), name, extra_terms.get(svg.stem, []))


COLLECTORS = {"selfhst": collect_selfhst, "devicon": collect_devicon, "material": collect_material, "fluent": collect_fluent,
              "dashboard": collect_dashboard, "simpleicons": collect_simpleicons, "flatcolor": collect_flatcolor,
              "fluentsystem": collect_fluentsystem, "extra": collect_extra}


# ---------- Nettoyage : rattrape des SVG que picosvg refuse tels quels ----------

_CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")


def _square_viewbox(root) -> None:
    """Rend le cadre (viewBox) carré en centrant le dessin : nanoemoji cale la hauteur sur la
    hauteur de la police, et un logo plus large que haut débordait de sa case."""
    def num(v):
        m = re.match(r"\s*([-+]?[\d.]+(?:e[-+]?\d+)?)", v or "")
        return float(m.group(1)) if m else None
    vb = root.get("viewBox")
    if vb:
        parts = [float(x) for x in re.split(r"[\s,]+", vb.strip())]
        if len(parts) != 4:
            return
        x, y, w, h = parts
    else:
        w, h = num(root.get("width")), num(root.get("height"))
        if not w or not h:
            return
        x = y = 0.0
    if w <= 0 or h <= 0 or abs(w - h) < 1e-6:
        return
    side = max(w, h)
    x -= (side - w) / 2
    y -= (side - h) / 2
    root.set("viewBox", f"{x:g} {y:g} {side:g} {side:g}")
    for attr in ("width", "height"):
        if attr in root.attrib:
            root.set(attr, f"{side:g}")


def normalize_svg(args: tuple[str, str]) -> str:
    """Copie le SVG en le rendant acceptable par picosvg : styles CSS de classes (<style>) recopiés
    sur les éléments, attributs data-* et éléments sans effet (<title>, <desc>, <metadata>) retirés.
    En cas d'échec, le fichier est copié tel quel (picosvg dira ensuite s'il est utilisable)."""
    src, dst = args
    try:
        from lxml import etree
        tree = etree.parse(src, etree.XMLParser(remove_comments=True, huge_tree=True))
        root = tree.getroot()
        rules: dict[str, list[str]] = {}
        for style in list(root.iter("{*}style")):
            css = re.sub(r"/\*.*?\*/", "", style.text or "", flags=re.S)
            for selectors, decls in _CSS_RULE.findall(css):
                for sel in selectors.split(","):
                    sel = sel.strip()
                    if re.fullmatch(r"\.[\w-]+", sel):
                        rules.setdefault(sel[1:], []).append(decls.strip().rstrip(";"))
            style.getparent().remove(style)
        for el in root.iter():
            if not isinstance(el.tag, str):
                continue
            if etree.QName(el).localname in ("title", "desc", "metadata"):
                el.getparent().remove(el)
                continue
            for attr in [a for a in el.attrib if a.startswith("data-")]:
                del el.attrib[attr]
            classes = (el.get("class") or "").split()
            decls = [d for c in classes for d in rules.get(c, [])]
            if decls:
                own = el.get("style")
                el.set("style", ";".join(decls + ([own] if own else [])))
            # picosvg ne lit pas les unités (« stroke-width: 7.5px ») ni « transparent »
            for attr, value in list(el.attrib.items()):
                fixed = re.sub(r"(\d)px\b", r"\1", value)
                fixed = re.sub(r"\btransparent\b", "none", fixed)
                if fixed != value:
                    el.set(attr, fixed)
            if "class" in el.attrib and rules:
                del el.attrib["class"]
        _square_viewbox(root)
        tree.write(dst)
    except Exception:  # noqa: BLE001
        shutil.copy(src, dst)
    return dst


# ---------- Validation : nanoemoji échoue sur tout le lot si un seul SVG est invalide ----------

def check_svg(path: str):
    try:
        from picosvg.svg import SVG
        SVG.parse(path).topicosvg()
        return path, None
    except Exception as exc:  # noqa: BLE001 - on veut toutes les raisons d'échec
        return path, f"{type(exc).__name__}: {str(exc).splitlines()[0][:160] if str(exc) else ''}"


def failed_files(ninja_output: str) -> dict[int, str]:
    """Points de code des SVG nommés dans les étapes en échec de ninja (« FAILED: … emoji_uf0123 … »),
    avec la dernière ligne d'erreur Python qui suit."""
    bad = {}
    blocks = ninja_output.split("FAILED:")[1:]
    for block in blocks:
        first_line = block.splitlines()[0] if block.splitlines() else ""
        errors = [l.strip() for l in block.splitlines() if re.match(r"\s*\w+(Error|Exception)\b", l)]
        for cp in set(re.findall(r"emoji_u([0-9a-f]{5,6})", first_line)):
            bad[int(cp, 16)] = (errors[-1] if errors else "nanoemoji")[:160]
    return bad


def find_unpaintable(build_dir: Path, prefix: str) -> dict[int, str]:
    """Rejoue, glyphe par glyphe, l'étape de nanoemoji qui a échoué et renvoie {point_de_code: erreur}.

    Certains SVG passent picosvg mais échouent plus tard (ex. dégradé hors des limites COLRv1).
    nanoemoji ne dit pas lequel : on le retrouve ici pour l'exclure.
    """
    from nanoemoji import config as nconfig, glyphmap
    from nanoemoji import write_font
    from nanoemoji.color_glyph import ColorGlyph
    from absl import flags
    from lxml import etree
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
                # tracé qui ne commence pas par un point de départ (bug de découpe de picosvg, ex. notifiarr)
                for el in etree.parse(str(g.svg_file)).iter("{*}path"):
                    d = (el.get("d") or "").lstrip()
                    if d and d[0] not in "Mm":
                        raise ValueError(f"tracé sans point de départ : {d[:40]}")
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
    limit = int(os.environ.get("BUILD_PACK_LIMIT", "0"))  # tests rapides en local
    if limit:
        items = items[::max(1, len(items) // limit)][:limit]
    if not items:
        print(f"{source}: aucune icône, pas de pack")  # ex. dossier custom/ vide
        return

    norm_dir = Path(tempfile.mkdtemp(prefix=f"norm-{source}-"))
    with ProcessPoolExecutor() as pool:
        normalized = list(pool.map(normalize_svg, [(str(s), str(norm_dir / f"{i}.svg")) for i, (_, s, _) in enumerate(items)], chunksize=16))
        original = {k: s for k, s, _ in items}
        items = [(k, Path(n), t) for (k, _, t), n in zip(items, normalized)]
        errors = dict(pool.map(check_svg, [str(s) for _, s, _ in items], chunksize=16))
    valid = [i for i in items if errors[str(i[1])] is None]
    skipped = [f"{k}\t{original[k].name}\t{errors[str(s)]}" for k, s, _ in items if errors[str(s)] is not None]

    work = Path(tempfile.mkdtemp(prefix=f"pack-{source}-"))
    manifest, src_of = {}, {}
    for n, (key, svg, terms) in enumerate(valid):
        src_of[key] = original[key].name
        cp = PUA_START + n
        shutil.copy(svg, work / f"emoji_u{cp:x}.svg")
        manifest[key] = {"glyph": chr(cp), "terms": terms}

    font = f"{prefix}.ttf"
    key_of = {ord(v["glyph"]): k for k, v in manifest.items()}
    for attempt in range(1, 6):
        cmd = ["nanoemoji", "--color_format", "glyf_colr_1", "--family", f"Trilium {prefix}",
               "--upem", "1024", "--width", "1024", "--ascender", "896", "--descender", "-128",
               "--build_dir", str(work / "build"), "--output_file", font, "--noexec_ninja",
               *sorted(str(p) for p in work.glob("emoji_u*.svg"))]
        subprocess.run(cmd, cwd=work, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # ninja lancé ici avec -k 0 : il va au bout et signale tous les SVG en échec en une passe
        run = subprocess.run(["ninja", "-C", str(work / "build"), "-k", "0"], cwd=work,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        if run.returncode == 0:
            break
        # 1) un SVG a échoué à une étape par fichier (picosvg, découpe…) : ninja nomme le fichier
        bad = failed_files(run.stdout)
        # 2) sinon, l'échec vient de l'assemblage de la police : on rejoue glyphe par glyphe
        if not bad and (work / "build" / f"{prefix}.glyphmap").exists():
            bad = find_unpaintable(work / "build", prefix)
        bad = {cp: err for cp, err in bad.items() if cp in key_of and key_of[cp] in manifest}
        if not bad or attempt == 5:
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
    shutil.rmtree(norm_dir, ignore_errors=True)
    size = (out / f"{prefix}.woff2").stat().st_size
    print(f"{source}: {len(manifest)} icônes, {len(skipped)} ignorées, police {size / 1024:.0f} Ko")


if __name__ == "__main__":
    main()
