---
name: css-cleanup-pass
description: Use when the user asks to re-read, clean up or simplify the styles of the website ("clean le CSS", "relis les styles", "passe de nettoyage CSS", "simplifie le stylus", "css cleanup pass", and for the reorganization step "réorganise le CSS", "range app.styl", "découpe la feuille principale"), on Vue components (scoped Stylus), on the main sheets app/assets/styles/app.styl and dark.styl, typically after a series of visual changes or before a commit. Makes the styles smaller without changing what the pages look like.
---

# CSS cleanup pass

## Overview

Re-read the styles that changed and make them smaller and more consistent
**without changing what any page looks like**, in light and dark, at every
width. A visual change is reported, never applied silently. The proof is a
screenshot comparison before and after, not a reading of the diff.

## Scope

1. Perimeter, in this order: files named by the user, else commits named by
   the user, else the working tree and `git diff origin/main...HEAD --stat`,
   limited to `app/**/*.vue` (their `<style>` blocks) and
   `app/assets/styles/*.styl`.
2. Review each `<style>` block in full, and in `app.styl` / `dark.styl` the
   whole section (`// PAGE: ...`, `// --- ... ---`) that holds a change.
   Carried-over code is in scope: tag its findings `(pre-existing)`.
3. The user's tree often holds other people's work in progress: run
   `git diff <file>` first and do not touch hunks you did not write unless
   the user put them in the perimeter.
4. Do not edit `app/assets/styles/bulma.css` (vendored Bulma 0.9.4). Its
   only local change is the navbar breakpoint (1216px), kept in sync with
   `Header.vue`, `ThemeToggle.vue` and the desktop rules in `app.styl`.

## How the styles are built

- `nuxt.config.ts` loads, in this order: `app.styl`, `bulma.css`,
  `dark.styl`. `variables.styl` is injected into every Stylus block
  (`additionalData`), so components use the color variables without an
  import.
- `app.styl`: everything is nested under `html, body, div.body`, in banner
  sections (UTILITY CLASSES, BASE, COMPONENTS, HEADER, one `PAGE: ...` per
  page, then RESPONSIVE MOBILE 800px and TABLET 960px at the end).
- `dark.styl`: every rule sits under `html.has-dark-mode.theme-dark`, in
  `// --- Name ---` sections. Colors come from the `dark-*` tokens at the
  top of the file (taken from Kitsu's dark theme). Page-specific rules go
  in the sections at the end.
- Components: `<style lang="stylus" scoped>`, 2-space indent;
  `app.styl` and `dark.styl` use 4 spaces. Keep the indent of the file.

## Checklist

Walk each block top to bottom. Apply what is a pure cleanup; list the rest.

**Dead rules**
- A selector nothing renders. Before deleting, grep the class in `app/`
  **and** `content/` (`*_pages.json` flags such as `colored`, `reverted`,
  `shadow` become classes) and look for classes built from a key
  (`SubNavElement`, `TeamMember`, `KitsuFeatureBlock`, `CustomerLogoBlock`,
  `:class` bindings, template strings). No hit anywhere: delete.
- A declaration overridden by a later one in the same rule, or a rule
  repeated with the same values in another section.
- Typos that make a selector match nothing (`.navbar-dropdowon`): fixing
  one makes it match, so it is a visual change. Report it.
- Commented-out rules and leftover debug (`outline red`, `border 1px solid
  red`).

**Duplication**
- The same block of declarations in two components or two page sections:
  one shared class in `app.styl` (COMPONENTS) only when both already render
  the same thing. Two similar but different blocks stay separate.
- A hard-coded color that equals a variable of `variables.styl`
  (`cgwiregreen`, `purple`, `lightgrey`, ...) or a `dark-*` token: use the
  name. A new color used once stays a literal; used in several places it
  becomes a variable.
- Selectors repeated with different prefixes to win specificity
  (`html body header ...`, `div.body header ...`): keep the shortest one
  that still wins, and prove it with the screenshot comparison.

**Placement**
- Dark-mode rules belong in `dark.styl` under the theme selector, not in
  components, except when they style markup only that component renders
  (then `html.theme-dark &` inside the component, as `ThemeToggle.vue`
  does).
- A rule for one page in `app.styl` goes in that page's section; a rule
  for one component goes in the component.
- Responsive rules: the page sections hold the desktop rules; the
  `RESPONSIVE` sections at the end hold the overrides. Do not scatter
  `@media` blocks with the same breakpoint inside one section.

**Style**
- Stylus syntax of the file: no colons, semicolons or braces in `.styl` and
  `lang="stylus"` blocks.
- Keep the declaration order of the file. Do not reorder a block only to
  sort it: it hides the real changes in the diff. Larger moves belong to
  the Reorganization step.
- `!important` only with a comment that gives the reason (a third-party
  rule, an inline style). Remove the ones nothing needs.
- Units: `px` for borders and fixed sizes, `rem`/`em` where the file
  already uses them. Do not convert a whole file.
- `0` without unit. Shorthand only when it does not reset something set
  elsewhere: `background` resets `background-image`, `-size` and
  `-position`; `border` resets `border-color`, `-width` and `-style` of all
  four sides; `margin` resets the four sides.

**Comments**
- Keep comments that give a reason (a library quirk, an order, why a value).
  Delete the ones that restate the selector. No em-dashes.

## Reorganization (only on request)

Moving whole sections, splitting a file or changing the order of a file is
not part of the default pass. Do it only when the user asks for it, after the
cleanup is committed, and in its own commit (or one commit per file), so
the cleanup diff and the move diff stay readable. A reorganization changes
no value: a commit that both moves and edits a rule cannot be reviewed.

**What it can cover**
- Order of the sections in `app.styl`: utilities, base, layout, blocks,
  buttons, components, header, then the `PAGE: ...` sections in the order
  of the site menu, then the responsive sections.
- `dark.styl` sections in the same order as their light counterparts in
  `app.styl`, so the dark rule of a block is easy to find.
- Splitting `app.styl` (about 1800 lines) into files under
  `app/assets/styles/` (`base.styl`, `components.styl`, `header.styl`,
  `pages/<page>.styl`, `responsive.styl`), imported from `app.styl` with
  `@import` in the current order. `nuxt.config.ts` keeps loading
  `app.styl` only.
- Moving a `PAGE: ...` section used by one page or one component into that
  component's `<style>`.
- The responsive overrides of one page moved next to its desktop rules, as
  a nested `@media` block, when the section gets its own file.

**Why it is risky**
- Order is part of the cascade: between two rules of equal specificity,
  the later one wins. Moving a section above another can flip which rule
  applies. Keep the relative order of rules that target the same elements;
  `@import` the split files in the order the sections had.
- Specificity changes when a rule leaves `app.styl`: there it sits under
  `html body div.body` (or `div.body`), in a component it becomes
  `.x[data-v-...]`. A rule that won by its `div.body` prefix can lose
  against a Bulma or an `app.styl` rule once moved. Do not move such rules
  into components unless the screenshots prove nothing changed.
- `scoped` styles do not reach child components or `v-html` content:
  moving a rule that styles them needs `:deep()`, which is a change of its
  own. Report it.
- The load order `app.styl`, `bulma.css`, `dark.styl` does not change.

**How**
1. Take the baseline screenshots (see Verify) of **every page that uses
   the moved sections**, light and dark, at 400, 1100 and 1440 px, plus the
   open burger menu. For `app.styl`-wide moves, that means all top-level
   pages, one page of each dynamic type (feature, alternative, audience,
   studio, customer story, tool) and the 404 page.
2. Move code with cut and paste only: no edits, no renames, no cleanup in
   the same commit. Keep comments with the rules they explain.
3. Check that the compiled CSS kept the same rules: build the site
   (`npm run build`) before and after, then compare the generated CSS
   files with the rules sorted (`npx prettier` on both, then `diff`); only
   their order may differ, and only where you meant it.
4. Compare the screenshots. Any pixel difference that is not an animation
   means a rule changed winner: put it back where it was and report it.

## Cleanup versus visual change

| Looks like cleanup, is a visual change | Do instead |
|---|---|
| Deleting a selector that seems unused but whose class comes from JSON or a template string | Grep `content/` and the dynamic class builders first |
| Merging two rules with different specificity | Prove it with the screenshot comparison, else report |
| Moving a rule between `app.styl` and `dark.styl` or a component | The load order (`app.styl`, `bulma.css`, `dark.styl`) and `scoped` change who wins: compare screenshots |
| Replacing a literal with a variable whose value differs by a few digits | Report it: it is a color change |
| Changing a breakpoint, or merging `max-width: 800px` and `960px` blocks | Report it |
| Turning `background-color` into `background`, `margin-top` into `margin` | Check that nothing else sets the other sub-properties |
| Fixing a selector typo | Report it: the rule starts to apply |
| Removing `scoped` or adding `:deep()` | Report it |

Rule: if a visitor could see the difference on any page, theme or width,
it is not cleanup.

## Verify

1. **Before editing**, take baseline screenshots of the pages that use the
   touched styles, light and dark, at 400, 1100 and 1440 px. Use the dev
   server on a second port (`npx nuxt dev --port 3999`), so the user's own
   server keeps running; do not `rm -rf .nuxt` while it runs:

   ```bash
   for theme in light dark; do for w in 400 1100 1440; do
     google-chrome --headless=new --disable-gpu --hide-scrollbars \
       --blink-settings=preferredColorScheme=$([ $theme = dark ] && echo 0 || echo 1) \
       --virtual-time-budget=8000 --window-size=$w,3000 \
       --screenshot=<scratch>/before-<page>-$theme-$w.png http://localhost:3999/<path>
   done; done
   ```

   Headless Chrome does not go below about 500px wide with
   `--window-size`; for narrower widths use the DevTools protocol
   (`Emulation.setDeviceMetricsOverride`) from a small Node script.
2. After the cleanup, take the same shots and compare:
   `compare -metric AE before.png after.png diff.png` (0 means identical;
   animated pages and carousels differ a little, so look at `diff.png`).
3. `npm run lint` must stay clean.
4. For header or menu changes, also check the open burger menu and the
   dropdowns.

## Report

Three lists, one line per item with `file:line`, `(pre-existing)` when the
code predates the diff:

1. **Applied**: cleanups done, grouped by file.
2. **Proposed**: visual changes worth making, each with what a visitor
   would see.
3. **Checked, unchanged**: what was reviewed and found fine.

Do not commit before the user has looked at it in the browser. Never use
`git stash`, `git reset --hard` or `git checkout --` on his tree. Stage only
your own hunks.
