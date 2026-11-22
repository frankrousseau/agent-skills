---
name: svg-cleanup-pass
description: Use when the user asks to clean up, lighten or check the SVG files of the website ("clean les SVG", "allège les svg", "passe de nettoyage SVG", "optimise les icônes", "svg cleanup pass"), the icons, illustrations, logos and animated screenshots under app/assets/images, typically after adding or exporting SVGs (Figma, Inkscape) or after a series of animated screenshots. Makes the files smaller and cleaner without changing how they look or move.
---

# SVG cleanup pass

## Overview

Re-read the SVG files in scope and make them smaller and cleaner **without
changing what they look like or how they animate**, in light and dark. A
visual change is reported, never applied silently. The proof is a render
comparison before and after in headless Chrome (the only renderer here that
handles `feDropShadow` and CSS animations), not a reading of the diff.

## Scope

1. Perimeter, in this order: files named by the user, else commits named by
   the user, else the SVGs added or changed in the working tree and in
   `git diff origin/main...HEAD --stat`. A whole-site pass covers
   `app/assets/images/**/*.svg` and `public/images/*.svg`.
2. The user's tree often holds other agents' work in progress: run
   `git status` first and leave untracked SVGs you did not make out of the
   pass unless the user names them.
3. Inline `<svg>` in Vue templates (`Header.vue`, `ThemeToggle.vue`,
   `FeatureBlock.vue`, ...) is in scope only when the user names the
   component.

## How the SVGs are used

- They load as images (`<img>`, `NuxtImg`) through IPX, which strips
  `<script>`: an SVG never relies on JS. `FeatureBlock.vue` skips the WebP
  conversion for `.svg` (it would freeze the animation).
- Feature screenshots come in pairs: `kitsu-<name>-animated.svg` (light) and
  `kitsu-<name>-animated-dark.svg` (dark, `imageDark` in
  `content/*_pages.json`). Playlist screens are dark only. A change to one
  file of a pair goes to the other.
- The animated screenshots and illustrations are **generated** by the
  `kitsu-screenshot-svg` skill from a Python draft and crop files kept in a
  session scratchpad (`gen.py`, `build.sh`, `crops.json`). When that source
  still exists, fix the generator and rebuild; editing only the output means
  the next rebuild undoes the cleanup. When it is gone, edit the output and
  say so in the report.
- `width`/`height` on the root give the intrinsic size (about 1440 wide for
  screenshots): the feature column has no max width, so removing them or
  shrinking them makes the image look small on large screens.

## Checklist

Walk each file against these, in order. Apply what is a pure cleanup; list
the rest.

**Embedded pixels** (the biggest wins)
- Find embedded rasters and their size:
  `grep -o 'data:image/[a-z]*' f.svg | sort | uniq -c`, then decode one
  with Python and `identify` to read its pixel size.
- A raster larger than 2x the size it is drawn at gets downscaled to 2x.
  Example found on this site: 67px icons (`icons/casting-management.svg`,
  `icons/conferences.svg`) carrying a 2882x1283 PNG, about 150 KB each.
- A photo or a video frame stored as PNG can become JPEG (quality 85) when
  it has no transparency: often half the size. Keep PNG for UI crops with
  flat colors and text, and for anything with alpha.
- The same raster embedded several times becomes one `<symbol>` (or one
  `<image>` in `<defs>`) used with `<use>`.
- For generated screenshots, change the crop or the embed step, not the
  output (see above).

**Dead markup**
- Editor leftovers: `inkscape:*`, `sodipodi:*`, `<metadata>`, Illustrator
  and Sketch comments, `data-name`, unused `xmlns:*`.
- Unused `<defs>` entries: `<symbol>`, `<clipPath>`, `<filter>`,
  `<linearGradient>`, `<pattern>` that no `href`/`url(#...)` references.
- CSS rules and `@keyframes` that match nothing; classes that no rule uses.
- Shapes drawn under an opaque shape of the same size, empty `<g>`,
  `<g>` without attributes around one child.
- `xlink:href` becomes `href` (and drop `xmlns:xlink` when unused).

**Size**
- Numbers: 2 decimals at most in coordinates of a 1440-wide picture, 3 in
  small icons. Paths in relative commands. SVGO does this (below).
- Repeated pieces (avatars, thumbnails, tags, icons) as `<symbol>` + `<use>`.
- Repeated attributes moved to a parent `<g>` or to a class.

**Animation** (animated files)
- CSS `@keyframes` in a `<style>`, opacity and transform only, one loop of
  6 to 16 s.
- A `@media (prefers-reduced-motion: reduce)` rule that stops every
  animated class. A class missing from it is a finding.
- Percentages in one keyframe selector are comma-separated
  (`0%, 40% { ... }`): a missing comma silently drops the whole block.
- `transform-box: fill-box` and `transform-origin` on elements that scale
  or rotate around their own center.

**Look and accessibility**
- Root: `role="img"` and an `aria-label` that says what the picture shows.
- Dark files: colors from Kitsu's dark theme (`make_dark.py` of the
  `kitsu-screenshot-svg` skill), no leftover light surface such as `#fff`.
- Selection outline `#00b242` with the soft green `feDropShadow`, status
  tags in the ValidationTag style: report differences, do not restyle.

## SVGO

SVGO 4 is in `node_modules` (transitive dependency). Use the skill config,
which keeps what animations and `<use>` need:

```bash
node_modules/.bin/svgo --config .claude/skills/svg-cleanup-pass/svgo.config.mjs -i in.svg -o out.svg
```

It disables `removeHiddenElems` (animated elements start at opacity 0),
`inlineStyles` and `minifyStyles` (class rules carry the animations),
`cleanupIds` (ids referenced from CSS and `<use>`), `collapseGroups`,
`mergePaths` and the group/element attribute moves (classes and transforms
on groups), and keeps `<desc>`, `role` and the `aria-*` attributes (the
default preset drops `role="img"`). Do not run SVGO with its default preset on
an animated file.

On the hand-built screenshots SVGO only saves about 1%: their weight is in
the embedded pixels. Its real use is on exported icons and illustrations.

## Cleanup versus visual change

| Looks like cleanup, is a visual change | Do instead |
|---|---|
| Removing an element that is invisible at rest (opacity 0) | It may be shown by a keyframe: check the `<style>` first |
| Changing `width`/`height` on the root or the `viewBox` | Report it: the size on the page or the crop changes |
| Downscaling a raster below 2x its drawn size | Report it: it gets blurry on retina screens |
| JPEG for a raster with alpha, text or flat UI colors | Keep PNG |
| Merging paths or groups that carry a class or a transform | Keep them: the animation targets them |
| Renaming or removing an id | Check `url(#...)`, `href="#..."`, the `<style>` and the other file of the pair |
| Changing a color in one file of a light/dark pair | Report it, or change both |
| Removing the `prefers-reduced-motion` rule or a `<desc>` | Never: accessibility |

Rule: if a visitor could see the difference at any moment of the loop, in
either theme, it is not cleanup.

## Verify

1. Valid XML: `xmllint --noout file.svg`.
2. Render before and after with the `kitsu-screenshot-svg` script and
   compare:

   ```bash
   R=.claude/skills/kitsu-screenshot-svg/scripts/render.sh
   $R before.svg before.png; $R after.svg after.png
   compare -metric AE before.png after.png diff.png   # 0 means identical
   ```

   SVGO rounds numbers, so a few hundred pixels of anti-aliasing can
   differ (AE around 0.05%). Look at `diff.png` (`convert diff.png -trim
   info:` gives the box): scattered edge pixels are fine, a shape or a
   text that moved is not.

   Keep a copy of the original before editing (`git show HEAD:<path>` for
   a tracked file, a copy in the scratchpad otherwise).
3. Animated files: also compare frames in the middle of the loop. Inject
   after `<style>`:
   `* { animation-delay: -<seconds>s !important; animation-play-state: paused !important }`
   into a copy of each file and render it, at 3 or 4 moments of the loop.
4. Rasters downscaled: zoom on them (`convert out.png -crop ... -scale
   400%`) and look at the result.
5. Optionally, on a second dev server port (`npx nuxt dev --port 3999`,
   leave the user's own server running), `curl -sI` the `/_ipx/_/images/...svg` URL of the page: it must
   return `image/svg+xml`.

## Report

Three lists, one line per item with the file and the size before and after:

1. **Applied**: cleanups done, with the total size saved.
2. **Proposed**: visual changes worth making, each with what a visitor
   would see.
3. **Checked, unchanged**: files reviewed and found clean.

Do not commit before the user has looked at the pictures in the browser. Never
use `git stash`, `git reset --hard` or `git checkout --` on his tree. Stage
only your own files and hunks.
