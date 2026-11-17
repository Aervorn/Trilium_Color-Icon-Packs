/*
 * Trilium Color Icon Packs – installer / updater
 * https://github.com/Aervorn/Trilium_Color-Icon-Packs
 *
 * Single purpose: install or update, in Trilium, the icon packs published in the latest GitHub
 * release of the repository (COLRv1 color font + manifest). Nothing is compiled here.
 *
 * Setup: a "JavaScript (backend)" code note with these attributes
 *   #run=daily                                        runs once a day (does nothing if the release did not change)
 *   #iconPacksRepo=Aervorn/Trilium_Color-Icon-Packs   repository to read the releases from
 *   ~iconPacksFolder=<folder note>                    where the icon pack notes are created
 * Optional:
 *   #iconPacksExclude=sh,fl  prefixes of the packs you do not want (never created nor updated)
 *   #iconPacksForce        reinstall every pack on the next run (removed automatically)
 *   #iconPacksOnDesktop    also run on a desktop app that syncs with a server (not recommended)
 * The script maintains #iconPacksVersion (last release installed) by itself.
 * It can also be run manually (Ctrl+Enter, or the "Execute" button).
 */
(async () => {
    const script = api.currentNote;

    // A desktop app synced with a server would download the same packs as the server and create
    // sync conflicts: in that case only the server updates, and sync brings the notes to the desktop.
    // A desktop app without sync server (standalone install) runs the script normally.
    const isDesktop = typeof process !== "undefined" && process.versions && process.versions.electron;
    const syncServer = (api.getOption("syncServerHost") || {}).value;
    if (isDesktop && syncServer && !script.hasLabel("iconPacksOnDesktop")) {
        api.log("Desktop app synced with a server: updates are left to the server.");
        return;
    }

    const repo = script.getLabelValue("iconPacksRepo");
    const folder = script.getRelationTarget("iconPacksFolder");
    if (!repo || !folder) {
        api.log("Incomplete setup: #iconPacksRepo and ~iconPacksFolder are required.");
        return;
    }
    const force = script.hasLabel("iconPacksForce");
    const excluded = (script.getLabelValue("iconPacksExclude") || "").split(/[\s,]+/).filter(Boolean);

    const base = `https://github.com/${repo}/releases`;
    const download = async (url, binary) => {
        const res = await fetch(url, { redirect: "follow", headers: { "User-Agent": "trilium-icon-packs" } });
        if (!res.ok) throw new Error(`${url} → HTTP ${res.status}`);
        return binary ? new Uint8Array(await res.arrayBuffer()) : await res.text();
    };
    const sha256 = async (data) => {
        const bytes = typeof data === "string" ? new TextEncoder().encode(data) : data;
        const hash = await crypto.subtle.digest("SHA-256", bytes);
        return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, "0")).join("");
    };

    let release;
    try {
        release = JSON.parse(await download(`${base}/latest/download/release.json`));
    } catch (e) {
        api.log(`Cannot read the latest release: ${e.message}`);
        return;
    }

    if (!force && script.getLabelValue("iconPacksVersion") === release.version) {
        api.log(`Icon packs already up to date (${release.version}).`);
        return;
    }

    const changed = [];
    for (const pack of release.packs) {
        if (excluded.includes(pack.prefix)) continue;
        const signature = `${pack.manifestSha256}:${pack.fontSha256}`;
        let note = api.searchForNote(`#iconPack="${pack.prefix}"`);
        if (note && !note.hasLabel("iconPacksManaged")) {
            api.log(`Prefix "${pack.prefix}" is already used by "${note.title}" (not managed by this script): skipped.`);
            continue;
        }
        if (note && !force && note.getLabelValue("iconPacksSignature") === signature) continue;

        try {
            const tag = encodeURIComponent(release.version);
            const [manifest, font] = await Promise.all([
                download(`${base}/download/${tag}/${pack.manifest}`, false),
                download(`${base}/download/${tag}/${pack.font}`, true),
            ]);
            if ((await sha256(manifest)) !== pack.manifestSha256 || (await sha256(font)) !== pack.fontSha256) {
                throw new Error("SHA-256 does not match release.json");
            }

            api.transactional(() => {
                if (!note) {
                    note = api.createNewNote({
                        parentNoteId: folder.noteId,
                        title: pack.title,
                        type: "code",
                        mime: "application/json",
                        content: manifest,
                    }).note;
                    note.setLabel("iconPack", pack.prefix);
                    note.setLabel("iconPacksManaged");
                } else {
                    note.setContent(manifest);
                }
                note.saveAttachment({ role: "file", mime: "font/woff2", title: pack.font, content: font }, "title");
                note.setLabel("iconPacksSignature", signature);
                note.setLabel("iconPacksIcons", String(pack.icons));
            });
            changed.push(`${pack.title} (${pack.icons} icons)`);
        } catch (e) {
            api.log(`Pack ${pack.prefix} failed: ${e.message}`);
            return; // version not saved: the next run tries again
        }
    }

    script.setLabel("iconPacksVersion", release.version);
    if (force) script.removeLabel("iconPacksForce");

    const message = changed.length
        ? `Icon packs ${release.version}: ${changed.join(", ")}. Reload Trilium (Ctrl+R) to see them.`
        : `Release ${release.version}: no pack changed.`;
    api.log(message);
    if (changed.length) api.runOnFrontend((msg) => api.showMessage(msg), [message]);
})();
