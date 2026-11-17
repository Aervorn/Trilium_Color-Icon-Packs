# Trilium Color Icon Packs

Packs d'icônes **en couleur** pour [Trilium Notes](https://github.com/TriliumNext/Trilium) (v0.102+), compilés chaque mois depuis quatre collections libres :

| Pack | Préfixe | Source | Contenu | Licence |
| --- | --- | --- | --- | --- |
| selfh.st Icons | `sh` | [selfhst/icons](https://github.com/selfhst/icons) | Logos de logiciels et services auto-hébergés | CC BY 4.0 |
| Devicon | `dev` | [devicons/devicon](https://github.com/devicons/devicon) | Langages, frameworks et outils de développement | MIT |
| Material Icon Theme | `mat` | [material-extensions/vscode-material-icon-theme](https://github.com/material-extensions/vscode-material-icon-theme) | Types de fichiers, dossiers, termes techniques | MIT |
| Fluent Emoji | `fl` | [microsoft/fluentui-emoji](https://github.com/microsoft/fluentui-emoji) | Actions et concepts génériques (style « Color ») | MIT |

## Pourquoi c'est possible

Trilium n'accepte que des **polices** comme packs d'icônes. Les SVG de chaque collection sont donc compilés avec [nanoemoji](https://github.com/googlefonts/nanoemoji) en une police couleur **COLRv1** (au format `woff2`), accompagnée du manifeste JSON attendu par Trilium.

> COLRv1 est affiché en couleur par Chromium (Trilium desktop, Chrome, Edge, Opera) et Firefox. Safari ne le prend pas en charge : les icônes n'y apparaissent pas.

## Fonctionnement

```
GitHub Actions (le 1er du mois)                    Trilium (serveur, chaque jour)
 source_revisions.sh  ─ une source a changé ?        update-icon-packs.js
 fetch_sources.sh     ─ clone partiel des SVG          ├─ lit releases/latest/release.json
 build_pack.py        ─ police COLRv1 + manifeste      ├─ nouvelle version ? télécharge police + manifeste
 package_release.py   ─ release.json + empreintes      ├─ vérifie les SHA-256
 gh release create                                      └─ crée / met à jour les notes #iconPack
```

- Une release n'est publiée que si au moins une source a changé (lancement manuel possible avec l'option *force*). Un push qui modifie le code de compilation relance aussi une compilation complète.
- Les SVG que nanoemoji ne sait pas convertir (images bitmap intégrées, filtres…) sont ignorés et listés dans `<prefix>.skipped.txt`.
- GitHub désactive les workflows planifiés d'un dépôt public après 60 jours sans activité : chaque exécution réactive le workflow par l'API pour remettre ce délai à zéro, sans commit.
- Les noms d'icônes ne dépendent que du nom dans la source : `#iconClass="sh sh-docker"` reste valable d'une version à l'autre.

## Installation dans Trilium

1. Crée une note de code **JavaScript (backend)** et colle le contenu de [`trilium/update-icon-packs.js`](trilium/update-icon-packs.js).
2. Ajoute-lui les attributs :
   ```
   #run=daily
   #iconPacksRepo=Aervorn/Trilium_Color-Icon-Packs
   ~iconPacksFolder=<la note qui doit contenir les packs>
   ```
3. Exécute-la une première fois à la main (bouton *Exécuter* ou Ctrl+Entrée), puis rafraîchis Trilium.
4. Les packs apparaissent dans le sélecteur d'icônes (bouton *Filtre*).

Ajouter `#iconPacksForce` puis exécuter le script réinstalle tous les packs.

## Compiler en local

```bash
pip install -r requirements.txt
bash scripts/fetch_sources.sh src material
python scripts/build_pack.py material src out
```

## Licences

Le code de ce dépôt est sous licence MIT. Les icônes restent la propriété de leurs auteurs et sont redistribuées selon leurs licences :

- **selfh.st Icons** — © selfh.st, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Les icônes ont été converties en police (modification de format).
- **Devicon** — © konpa et contributeurs, MIT.
- **Material Icon Theme** — © Material Extensions (Philipp Kief et contributeurs), MIT.
- **Fluent Emoji** — © Microsoft Corporation, MIT.

Les logos de marques restent la propriété de leurs détenteurs respectifs.
