# Extra Icons (`ex`)

Icons that none of the other collections provide, added by hand. Every `.svg` file of this folder becomes an icon of the **Extra Icons** pack, named after the file: `custom/remarkable.svg` → `#iconClass="ex ex-remarkable"`.

## Adding an icon

1. Put an SVG file in this folder. The file name (lowercase, `-` between words) becomes the icon name.
2. Optional: add search keywords in `terms.json`:
   ```json
   {
     "remarkable": ["reMarkable", "tablet", "e-ink"]
   }
   ```
   The search of Trilium's icon picker uses these keywords and the file name.
3. Commit and push: the workflow rebuilds the packs and publishes a new release (pushes to `custom/` trigger a build).

## What works

- Colors, gradients and the `currentColor` fill (the icon then takes the text color of the Trilium theme, useful for single-color logos).
- Styles written in a `<style>` element with class selectors (`.cls-1 { fill: #e57000 }`) are applied automatically.
- Not supported: masks, filters, embedded bitmap images, text (`<text>`: convert it to paths first, for example with Inkscape *Path → Object to Path*). Icons that cannot be converted are listed in `ex.skipped.txt` in the release.

## Licenses

Only add icons you are allowed to redistribute: your own drawings, or icons under a license compatible with this repository (MIT, Apache 2.0, CC0, CC BY). Brand logos remain the property of their owners. Note the source and license of each third-party icon below.

| File | Source | License |
| --- | --- | --- |
