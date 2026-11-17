/*
 * Trilium – mise à jour automatique des packs d'icônes couleur
 * Dépôt : https://github.com/Aervorn/Trilium_Color-Icon-Packs
 *
 * Objectif unique : installer ou mettre à jour, dans Trilium, les packs publiés dans la dernière
 * release GitHub du dépôt (police COLRv1 + manifeste). Aucune compilation ici.
 *
 * Installation : note de code « JavaScript backend » avec les attributs
 *   #run=daily                         exécution quotidienne (rien n'est fait si la release n'a pas changé)
 *   #iconPacksRepo=Aervorn/Trilium_Color-Icon-Packs
 *   ~iconPacksFolder=<note ICON PACKS> dossier où créer les packs
 * Le script ajoute lui-même #iconPacksVersion (dernière release installée).
 * Exécution manuelle possible (Ctrl+Entrée) ; ajouter #iconPacksForce pour tout réinstaller.
 */
(async () => {
    const script = api.currentNote;

    // Le script tourne sur chaque instance (serveur et applis de bureau) : seul le serveur met à jour,
    // la synchro propage ensuite les notes, ce qui évite les conflits.
    if (typeof process !== "undefined" && process.versions && process.versions.electron) {
        api.log("Instance de bureau : mise à jour laissée au serveur.");
        return;
    }

    const repo = script.getLabelValue("iconPacksRepo");
    const folder = script.getRelationTarget("iconPacksFolder");
    if (!repo || !folder) {
        api.log("Configuration incomplète : #iconPacksRepo et ~iconPacksFolder sont obligatoires.");
        return;
    }
    const force = script.hasLabel("iconPacksForce");

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
        api.log(`Lecture de la dernière release impossible : ${e.message}`);
        return;
    }

    if (!force && script.getLabelValue("iconPacksVersion") === release.version) {
        api.log(`Packs déjà à jour (${release.version}).`);
        return;
    }

    const changed = [];
    for (const pack of release.packs) {
        const signature = `${pack.manifestSha256}:${pack.fontSha256}`;
        let note = api.searchForNote(`#iconPack="${pack.prefix}"`);
        if (note && !note.hasLabel("iconPacksManaged")) {
            api.log(`Préfixe « ${pack.prefix} » déjà utilisé par « ${note.title} » (pack non géré par ce script) : ignoré.`);
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
                throw new Error("empreinte SHA-256 différente de celle de release.json");
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
            changed.push(`${pack.title} (${pack.icons} icônes)`);
        } catch (e) {
            api.log(`Échec du pack ${pack.prefix} : ${e.message}`);
            return; // la version n'est pas enregistrée : nouvel essai au prochain passage
        }
    }

    script.setLabel("iconPacksVersion", release.version);
    if (force) script.removeLabel("iconPacksForce");

    const message = changed.length
        ? `Packs d'icônes ${release.version} : ${changed.join(", ")}. Rafraîchis Trilium (Ctrl+R) pour les voir.`
        : `Release ${release.version} : aucun pack modifié.`;
    api.log(message);
    if (changed.length) api.runOnFrontend((msg) => api.showMessage(msg), [message]);
})();
