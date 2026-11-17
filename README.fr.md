# Trilium Color Icon Packs

[English](README.md) · **Français**

Packs d'icônes **en couleur** pour [Trilium Notes](https://github.com/TriliumNext/Trilium) (v0.102 ou plus), compilés chaque mois à partir de quatre collections libres : **plus de 5 600 icônes** pour les logiciels, langages de programmation, types de fichiers, actions et concepts du quotidien.

![Exemples d'icônes des quatre packs](docs/preview.png)

| Pack | Préfixe | Source | Contenu | Icônes* | Taille* | Licence |
| --- | --- | --- | --- | --- | --- | --- |
| selfh.st Icons | `sh` | [selfhst/icons](https://github.com/selfhst/icons) | Logos d'applications auto-hébergées et de services en ligne (Docker, Proxmox, Home Assistant, Plex, Nextcloud…) | 2 554 | 940 Ko | CC BY 4.0 |
| Devicon | `dev` | [devicons/devicon](https://github.com/devicons/devicon) | Langages, frameworks, outils de développement (Python, Git, Kubernetes, PostgreSQL…) | 641 | 334 Ko | MIT |
| Material Icon Theme | `mat` | [material-extensions/vscode-material-icon-theme](https://github.com/material-extensions/vscode-material-icon-theme) | Types de fichiers et dossiers, termes techniques (JSON, YAML, journaux, certificats, réglages…) | 910 | 120 Ko | MIT |
| Fluent Emoji | `fl` | [microsoft/fluentui-emoji](https://github.com/microsoft/fluentui-emoji) (style « Color ») | Actions et concepts (fusée, engrenage, cadenas, calendrier, alerte, coche…) | 1 568 | 1,4 Mo | MIT |

\* Première release (novembre 2026). Les chiffres suivent les sources et changent d'une release à l'autre.

## Sommaire

- [Pourquoi ce projet](#pourquoi-ce-projet)
- [Prérequis et limites](#prérequis-et-limites)
- [Installation](#installation)
  - [Option A : installation et mises à jour automatiques (recommandé)](#option-a--installation-et-mises-à-jour-automatiques-recommandé)
  - [Option B : installation manuelle](#option-b--installation-manuelle)
- [Utiliser les icônes](#utiliser-les-icônes)
- [Mises à jour](#mises-à-jour)
- [Dépannage](#dépannage)
- [Désinstallation](#désinstallation)
- [Fonctionnement](#fonctionnement)
- [Compiler en local, forker, ajouter une source](#compiler-en-local-forker-ajouter-une-source)
- [Licences et crédits](#licences-et-crédits)

## Pourquoi ce projet

Depuis la v0.102, Trilium accepte des packs d'icônes personnalisés (voir *Icon Packs* dans l'aide intégrée de Trilium), mais uniquement sous forme de **polices** (`woff2`, `woff`, `ttf`). Une police d'icônes est normalement d'une seule couleur, et Trilium n'accepte ni fichiers SVG ni images comme icônes.

Ce projet compile les SVG de chaque collection en une **police couleur COLRv1** avec [nanoemoji](https://github.com/googlefonts/nanoemoji) (Google). Une police COLRv1 est un fichier `woff2` ordinaire : Trilium la charge par son mécanisme officiel de packs d'icônes. Les icônes apparaissent dans le sélecteur d'icônes, avec la recherche et le filtre par pack, dans l'arbre des notes, les onglets et les en-têtes, et peuvent être insérées dans les notes texte.

Les anciennes méthodes (classes CSS avec `background-image`, comme dans la [discussion #4604](https://github.com/orgs/TriliumNext/discussions/4604)) n'apparaissent pas dans le sélecteur et ont cassé avec la v0.102.

## Prérequis et limites

- **Trilium v0.102 ou plus** (prise en charge des packs d'icônes personnalisés).
- **Le rendu en couleur dépend du client.** COLRv1 est pris en charge par les navigateurs basés sur Chromium (app de bureau Trilium, Chrome, Edge, Opera, Brave…) et par Firefox. **Safari ne prend pas en charge COLRv1** : dans Trilium ouvert dans Safari (macOS, iPhone, iPad), ces icônes n'apparaissent pas.
- **Option A** (mises à jour automatiques) : la machine qui exécute le script (ton serveur Trilium, ou une app de bureau autonome) doit pouvoir joindre `github.com` en HTTPS.
- **Logos sombres sur thème sombre :** certains logos sont noirs (GitHub, Bash, Apple…) et peu lisibles sur un thème sombre. Ils sont dessinés exactement comme dans leur source.
- **Icônes ignorées :** quelques SVG ne peuvent pas être convertis en police (masques, dégradés hors limites, tracés invalides après découpe). Ils sont écartés et listés dans `<préfixe>.skipped.txt` de chaque release (environ 1 % des icônes).
- **Taille :** les quatre polices pèsent environ 2,8 Mo au total et sont chargées par chaque client. Pour n'avoir que certains packs, exclure les autres (`#iconPacksExclude`, option A) ou n'installer que ceux voulus (option B).

## Installation

### Option A : installation et mises à jour automatiques (recommandé)

Un petit script backend, lancé par Trilium une fois par jour, télécharge la dernière release, la vérifie et crée ou met à jour les quatre notes de packs. Plus besoin de s'en occuper ensuite.

1. **Choisir un dossier** pour les packs d'icônes, par exemple une note `Icon packs`. Les notes des packs y seront créées.
2. **Créer la note du script** (n'importe où, par exemple dans ce dossier) : nouvelle note → type **Code** → langage **JavaScript (backend)**. Coller le contenu de [`trilium/update-icon-packs.js`](trilium/update-icon-packs.js).
3. **Ajouter ces attributs** à la note du script (attributs propres) :
   ```
   #run=daily
   #iconPacksRepo=Aervorn/Trilium_Color-Icon-Packs
   ~iconPacksFolder=<le dossier de l'étape 1>
   ```
   Pour la relation, taper `~iconPacksFolder=` puis choisir le dossier dans l'autocomplétion.
4. **Lancer le script une première fois** tout de suite : ouvrir la note et appuyer sur **Ctrl+Entrée** (ou le bouton *Exécuter*). Le journal du script, en bas de la note, indique ce qui s'est passé, et un message s'affiche quand des packs ont été installés.
5. **Rafraîchir Trilium** (**Ctrl+R**, ou *Recharger l'interface* dans le menu). Les packs sont alors disponibles dans le sélecteur d'icônes.

Remarques :
- **Avec un serveur de synchronisation**, le script n'est créé qu'une fois : il ne s'exécute **que sur le serveur**. Les apps de bureau synchronisées avec un serveur l'ignorent (pour éviter les conflits de synchronisation) et reçoivent les packs par la synchro. Ajouter `#iconPacksOnDesktop` à la note du script pour le forcer à tourner aussi sur les apps de bureau (déconseillé).
- **App de bureau autonome** (sans serveur de synchronisation) : le script tourne normalement dans l'app de bureau.
- **Seulement certains packs :** ajouter `#iconPacksExclude=<préfixes>` à la note du script, par exemple `#iconPacksExclude=sh,fl` pour n'avoir que Devicon et Material Icon Theme. Les packs exclus ne sont jamais créés ni mis à jour.
- Si la note a été créée par un assistant IA via le serveur MCP de Trilium, `#run` est enregistré en `#disabled:run` : l'activer avec l'interrupteur à côté du badge, près du titre de la note.

### Option B : installation manuelle

Sans script ni mise à jour automatique : on installe à la main les packs voulus, et on refait les étapes pour passer à une version plus récente. C'est la procédure standard de Trilium (voir *Creating an icon pack* dans l'aide intégrée).

1. Ouvrir la [dernière release](https://github.com/Aervorn/Trilium_Color-Icon-Packs/releases/latest) et télécharger, pour chaque pack voulu, `<préfixe>.manifest.json` et `<préfixe>.woff2` (préfixes : `sh`, `dev`, `mat`, `fl`).
2. Dans Trilium, créer une note de type **Code**, langage **JSON**, avec le nom du pack comme titre (par exemple `Fluent Emoji (color)`). Ce titre s'affiche dans le filtre du sélecteur d'icônes.
3. Coller le contenu de `<préfixe>.manifest.json` dans la note.
4. Ouvrir les **pièces jointes** de la note et y envoyer `<préfixe>.woff2`. Vérifier que la pièce jointe a le type MIME `font/woff2` et le rôle `file`.
5. Ajouter le label `#iconPack=<préfixe>` à la note (par exemple `#iconPack=fl`).
6. Rafraîchir Trilium (**Ctrl+R**).

Pour mettre un pack à jour plus tard : remplacer le contenu de la note par le nouveau manifeste et la pièce jointe par la nouvelle police, puis rafraîchir.

## Utiliser les icônes

- **Sélecteur d'icônes :** cliquer sur l'icône d'une note → taper un mot dans la recherche. Le bouton **filtre** à côté de la recherche n'affiche qu'un pack. Chaque icône se trouve par son nom et par les mots-clés de sa source (catégories et tags de selfh.st, tags et noms alternatifs de Devicon, mots-clés de Fluent Emoji). Les mots-clés sont en anglais.
- **Par label :** `#iconClass="<préfixe> <préfixe>-<nom>"`, par exemple :
  ```
  #iconClass="sh sh-docker"
  #iconClass="dev dev-python"
  #iconClass="mat mat-json"
  #iconClass="fl fl-rocket"
  ```
  Le label peut être héritable (`#iconClass(inheritable)=...`) pour donner la même icône à toute une branche, comme pour n'importe quelle icône de Trilium.
- **Dans les notes texte :** le bouton *Insérer une icône* de la barre de mise en forme fonctionne aussi avec ces packs. Les polices couleur ignorent la couleur du texte.
- **Noms des icônes :**

  | Pack | Règle | Exemples |
  | --- | --- | --- |
  | `sh` | `sh-` + la référence selfh.st (nom du fichier SVG) | `sh-home-assistant`, `sh-adguard-home`, `sh-paperless-ngx` |
  | `dev` | `dev-` + le nom Devicon ; la variante couleur `original` est utilisée, sinon `plain` | `dev-postgresql`, `dev-nodejs`, `dev-kubernetes` |
  | `mat` | `mat-` + le nom du fichier Material Icon Theme | `mat-folder-docker`, `mat-certificate`, `mat-console` |
  | `fl` | `fl-` + le nom Fluent Emoji, en minuscules, espaces remplacés par `-` | `fl-light-bulb`, `fl-check-mark-button`, `fl-hammer-and-wrench` |

  La liste complète d'un pack est son manifeste (`<préfixe>.manifest.json` dans la release). Les noms ne dépendent que des sources : une icône garde son nom d'une release à l'autre. Une icône supprimée ou renommée par sa source disparaît, et les notes qui l'utilisaient n'ont plus d'icône.

## Mises à jour

- **Releases :** un workflow GitHub Actions tourne le **1er de chaque mois** (03:23 UTC). Il ne publie une nouvelle release que si au moins une des quatre sources a changé depuis la précédente.
- **Option A :** le script tourne une fois par jour. Quand la dernière release a une nouvelle version, il télécharge les packs, vérifie leurs empreintes SHA-256 par rapport à `release.json`, ne met à jour que les packs modifiés et enregistre la version installée dans `#iconPacksVersion`. **Rafraîchir Trilium** ensuite pour charger les nouvelles polices.
- **Forcer une réinstallation :** ajouter `#iconPacksForce` à la note du script et l'exécuter (le label est retiré ensuite).
- **Option B :** consulter les [releases](https://github.com/Aervorn/Trilium_Color-Icon-Packs/releases) de temps en temps et refaire les étapes manuelles.

## Dépannage

| Symptôme | À vérifier |
| --- | --- |
| Les packs n'apparaissent pas dans le sélecteur | Rafraîchir Trilium (**Ctrl+R**). Vérifier que chaque note de pack a le label `#iconPack` et une pièce jointe `font/woff2` de rôle `file`. Trilium ignore les notes protégées. Consulter le journal du backend (accessible depuis le menu principal, ou dans le dossier `log` du répertoire de données de Trilium). |
| Icônes absentes ou carrés vides | Probablement Safari (pas de COLRv1). Essayer l'app de bureau, Chrome ou Firefox. |
| Journal : `Incomplete setup` | Il manque `#iconPacksRepo` ou `~iconPacksFolder` sur la note du script. |
| Journal : `Cannot read the latest release` | La machine qui fait tourner Trilium ne joint pas GitHub (pare-feu, proxy, DNS), ou le nom du dépôt dans `#iconPacksRepo` est faux. |
| Journal : `Desktop app synced with a server` | Normal sur une app de bureau synchronisée : c'est le serveur qui met à jour. Si aucun serveur n'exécute le script, ajouter `#iconPacksOnDesktop`. |
| Journal : `Prefix "xx" is already used by …` | Un autre pack utilise déjà ce préfixe. Le script n'écrase jamais un pack qu'il n'a pas créé : changer le préfixe de l'autre pack, ou le supprimer. |
| Journal : `SHA-256 does not match` | Téléchargement corrompu ou interrompu. Rien n'a été modifié ; le script réessaie à sa prochaine exécution. |
| Journal : `Icon packs already up to date` | Rien à faire. Ajouter `#iconPacksForce` pour réinstaller quand même. |
| Le script ne tourne jamais tout seul | Vérifier que la note a `#run=daily` (et pas `#disabled:run`), que son langage est *JavaScript (backend)* et que Trilium n'est pas en mode sans échec (`TRILIUM_SAFE_MODE`). |
| Icônes absentes des notes partagées | Pour la fonction de partage, les notes des packs doivent aussi être partagées. |

## Désinstallation

1. Retrouver les notes qui utilisent ces icônes : rechercher `#iconClass =* "sh "` (et de même avec `dev `, `mat `, `fl `), puis changer ou retirer leur icône, par exemple avec les *actions groupées* des résultats de recherche.
2. Supprimer les notes des packs (option A : notes portant le label `#iconPacksManaged`) et la note du script, puis rafraîchir Trilium.

Pour ne retirer que certains packs avec l'option A, ajouter leurs préfixes à `#iconPacksExclude` sur la note du script **avant** de supprimer leurs notes. Sinon, le script recrée tout pack manquant à la release suivante.

## Fonctionnement

```
GitHub Actions (le 1er du mois)                        Trilium (une fois par jour)
 source_revisions.sh  une source a changé ?             update-icon-packs.js
 fetch_sources.sh     clone partiel des SVG              ├─ lit releases/latest/download/release.json
 build_pack.py        police COLRv1 + manifeste          ├─ nouvelle version ? télécharge police + manifeste
 package_release.py   release.json + empreintes          ├─ vérifie les SHA-256
 gh release create                                       └─ crée / met à jour les notes #iconPack
```

- **Un job par source**, en parallèle (d'environ 5 minutes pour Material à environ 25 minutes pour selfh.st).
- **`build_pack.py`** rassemble les SVG et leurs termes de recherche, les valide avec picosvg, attribue à chaque icône un point de code de la zone d'usage privé supplémentaire A (U+F0000 et suivants), compile la police avec nanoemoji (`glyf_colr_1`, 1024 unités par em, glyphes carrés) et la convertit en `woff2`. Quand nanoemoji échoue sur une icône, le script rejoue l'étape en échec glyphe par glyphe pour trouver la fautive, l'écarte et relance.
- **Fichiers de release**, pour chaque pack : `<préfixe>.woff2`, `<préfixe>.manifest.json` (manifeste Trilium), `<préfixe>.skipped.txt`. Plus `release.json` :
  ```json
  {
    "version": "2026.11.17-7",
    "sources": { "selfhst": "<commit>", "devicon": "<commit>", "material": "<commit>", "fluent": "<commit>" },
    "packs": [
      { "source": "fluent", "prefix": "fl", "title": "Fluent Emoji (color)", "icons": 1568, "skipped": 27,
        "font": "fl.woff2", "manifest": "fl.manifest.json", "fontSha256": "…", "manifestSha256": "…" }
    ]
  }
  ```
- **Les releases** sont créées en brouillon et publiées seulement une fois tous les fichiers envoyés : un envoi raté ne devient jamais la release « latest ».
- **Maintien de la planification :** GitHub désactive les workflows planifiés d'un dépôt public après 60 jours sans activité. Chaque exécution réactive le workflow par l'API, ce qui remet ce délai à zéro sans aucun commit.

## Compiler en local, forker, ajouter une source

Compiler un pack sur sa machine (Python 3.11 ou plus) :

```bash
pip install -r requirements.txt
bash scripts/fetch_sources.sh src material      # ou : selfhst devicon fluent (sans argument = les quatre)
python scripts/build_pack.py material src out   # out/material/ : mat.woff2, manifest.json, skipped.txt, pack.json
```

- **Fork :** le workflow fonctionne tel quel dans un fork. Pointer le script Trilium vers le fork avec `#iconPacksRepo=<compte>/<dépôt>`. Garder le fork **public** (le script télécharge les releases sans token) ou adapter le script.
- **Ajouter une source :** écrire une fonction `collect_<nom>()` dans `scripts/build_pack.py` qui renvoie `(nom, chemin_svg, [termes de recherche])`, l'ajouter à `PACKS` et `COLLECTORS` avec un préfixe unique, ajouter son clone dans `fetch_sources.sh` et `source_revisions.sh`, et l'ajouter à la matrice du workflow.
- Les issues et pull requests sont les bienvenues.

## Licences et crédits

Le code de ce dépôt est sous [licence MIT](LICENSE). Les icônes appartiennent à leurs auteurs et sont redistribuées selon leurs propres licences :

- **selfh.st Icons** : © selfh.st, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Les icônes ont été converties en police (changement de format uniquement).
- **Devicon** : © konpa et contributeurs, MIT.
- **Material Icon Theme** : © Material Extensions (Philipp Kief et contributeurs), MIT.
- **Fluent Emoji** : © Microsoft Corporation, MIT.

Les logos de marques restent la propriété de leurs détenteurs. Ce projet n'est affilié ni à TriliumNext ni aux auteurs des collections d'icônes.
