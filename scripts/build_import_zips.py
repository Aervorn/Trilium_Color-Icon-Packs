#!/usr/bin/env python3
"""Builds the two Trilium import archives (.zip) of a release.

Single purpose: turn the release files into archives that Trilium imports as notes
(right-click on a note > Import). Nothing is compiled or published here.

Usage: build_import_zips.py <release_dir> <update_script.js> <owner/repo>
  release_dir       output of package_release.py (release.json + fonts + manifests)
  update_script.js  trilium/update-icon-packs.js
  owner/repo        repository the installed script reads its releases from

Writes into <release_dir>:
  trilium-color-icon-packs.zip          "Color Icon Packs" folder with the update script, ready to run
                                        (#run=daily, #iconPacksRepo); the packs are downloaded on its first run
  trilium-color-icon-packs-offline.zip  "Color Icon Packs (offline)" folder with every pack of the release
                                        (manifest + font), without the script: no automatic updates

The archives follow the format of a Trilium export (!!!meta.json, formatVersion 2), as read by
packages/trilium-core/src/services/import/zip.ts. Note and attachment IDs are derived from the
content (stable from one release to the next); Trilium replaces them with new IDs on import.
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

INSTALLER = "trilium-color-icon-packs.zip"
OFFLINE = "trilium-color-icon-packs-offline.zip"
SCRIPT_TITLE = "Update color icon packs (script)"
ALPHABET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def entity_id(*parts: str) -> str:
    """12-character ID in Trilium's alphabet, derived from the given strings."""
    digest = int.from_bytes(hashlib.sha256("\0".join(parts).encode()).digest(), "big")
    out = []
    for _ in range(12):
        digest, i = divmod(digest, len(ALPHABET))
        out.append(ALPHABET[i])
    return "".join(out)


def label(name: str, value: str = "", position: int = 10) -> dict:
    return {"type": "label", "name": name, "value": value, "isInheritable": False, "position": position}


def folder_meta(note_id: str, title: str, icon: str, children: list) -> dict:
    return {
        "isClone": False, "noteId": note_id, "notePath": [note_id], "title": title,
        "notePosition": 10, "prefix": None, "isExpanded": True, "type": "book", "mime": "",
        "attributes": [label("iconClass", icon)], "attachments": [],
        "dirFileName": title, "children": children,
    }


def child_meta(parent_id: str, note_id: str, title: str, position: int, mime: str,
               data_file: str, attributes: list, attachments: list | None = None) -> dict:
    return {
        "isClone": False, "noteId": note_id, "notePath": [parent_id, note_id], "title": title,
        "notePosition": position, "prefix": None, "isExpanded": False, "type": "code", "mime": mime,
        "attributes": attributes, "attachments": attachments or [], "dataFileName": data_file,
    }


def write_zip(path: Path, root: dict, files: dict, app_version: str) -> None:
    """files: {path in the archive: bytes}, the directory entry of the folder is added here."""
    meta = {"formatVersion": 2, "appVersion": app_version, "files": [root]}
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("!!!meta.json", json.dumps(meta, ensure_ascii=False, indent=2))
        z.writestr(f"{root['dirFileName']}/", "")
        for name, data in files.items():
            # fonts are already compressed
            z.writestr(name, data, zipfile.ZIP_STORED if name.endswith(".woff2") else zipfile.ZIP_DEFLATED)


def build_installer(rel_dir: Path, script: str, repo: str, version: str) -> Path:
    folder_id, script_id = entity_id(repo, "folder"), entity_id(repo, "script")
    data_file = f"{SCRIPT_TITLE}.js"
    child = child_meta(folder_id, script_id, SCRIPT_TITLE, 10, "application/javascript;env=backend", data_file,
                       [label("run", "daily", 10), label("iconPacksRepo", repo, 20)])
    root = folder_meta(folder_id, "Color Icon Packs", "bx bx-palette", [child])
    out = rel_dir / INSTALLER
    write_zip(out, root, {f"{root['dirFileName']}/{data_file}": script.encode()}, version)
    return out


def build_offline(rel_dir: Path, release: dict, repo: str) -> Path:
    folder_id = entity_id(repo, "offline-folder")
    root_dir = "Color Icon Packs (offline)"
    children, files = [], {}
    for position, pack in enumerate(release["packs"], start=1):
        prefix = pack["prefix"]
        note_id = entity_id(repo, "offline", prefix)
        manifest_file, font_file = f"{prefix}.manifest.json", f"{prefix}.woff2"
        attributes = [
            label("iconPack", prefix, 10),
            label("iconPacksManaged", "", 20),  # lets the update script take the pack over later
            label("iconPacksSignature", f"{pack['manifestSha256']}:{pack['fontSha256']}", 30),
            label("iconPacksIcons", str(pack["icons"]), 40),
        ]
        attachment = {"attachmentId": entity_id(repo, "offline-font", prefix), "title": pack["font"],
                      "role": "file", "mime": "font/woff2", "position": 10, "dataFileName": font_file}
        children.append(child_meta(folder_id, note_id, pack["title"], position * 10, "application/json",
                                   manifest_file, attributes, [attachment]))
        files[f"{root_dir}/{manifest_file}"] = (rel_dir / pack["manifest"]).read_bytes()
        files[f"{root_dir}/{font_file}"] = (rel_dir / pack["font"]).read_bytes()
    root = folder_meta(folder_id, root_dir, "bx bx-palette", children)
    out = rel_dir / OFFLINE
    write_zip(out, root, files, release["version"])
    return out


def main() -> None:
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    rel_dir, script_path, repo = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    release = json.loads((rel_dir / "release.json").read_text())
    for out in (build_installer(rel_dir, script_path.read_text(), repo, release["version"]),
                build_offline(rel_dir, release, repo)):
        print(f"{out.name}: {out.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
