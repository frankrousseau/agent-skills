---
name: kitsu-screenshot-svg
description: Use when the user asks to turn a Kitsu screenshot of the website into a simplified animated SVG ("transforme ce screenshot en SVG animé", "fais la même chose pour le screenshot X", "anime ce screenshot", "version dark de ce screenshot"). Rebuilds the screen as a light and dark SVG pair (dark only for playlist screens), reuses the avatars, thumbnails and screens of the original PNG, and wires it into the feature pages.
---

# Kitsu screenshot to animated SVG

Turns a feature screenshot (`app/assets/images/screenshots/kitsu-*.png`) into a hand-built SVG: simpler than the real UI, with one short looping animation, in light and dark versions. Reference result: `kitsu-todos-animated.svg` / `kitsu-todos-animated-dark.svg` (Team Collaboration, Todo-Lists).

## 1. Read the source

- Find where the screenshot is used: `/bin/grep -n '"image": "<name>.png"' content/*_pages.json` and `/bin/grep -rn '<name>' app`. Note every locale entry and its flags (`shadow`, `reverted`, `colored`).
- Look at the PNG (Read tool) and zoom on regions with `convert <png> -crop WxH+X+Y +repage -scale 400% <scratch>/z.png` to measure the exact crop boxes of avatars, thumbnails, production icons and embedded screens (rows of Kitsu tables are evenly spaced: measure the first row and the pitch).
- Check the **current** Kitsu UI in `../kitsu` before drawing, not the screenshot, which is often years old: tab bars (`src/App.vue` `.tabs`), page layout of the matching page component, labels in `src/locales/en.js`, theme colors in `src/styles/theme.scss`.

## 2. Simplify

- Keep the structure a visitor recognizes (tabs, filters, table header, a handful of rows); drop columns and chrome that carry no message (top bar, description, estimates, scrollbars).
- Use the current Kitsu labels and styles. Tabs are an underline bar: active tab weight 600, text `#363636`, 2px underline `--text-selected` (`#8f91eb` light, `#9ea0fa` dark); others `#7a7a7a`; bar line `#dbdbdb`. Do not reproduce the new raised filter panels: they look awkward in an illustration.
- Status tags use Kitsu's real `ValidationTag` style: filled pill (20px high, `rx 10`, 10px bold, letter-spacing .8, uppercase) in the status color with white text. Default colors: DONE `#22d160`, WFA `#ab26ff`, RETAKE `#ff3860`, WIP `#3273dc`; TODO is `#ececec` with `#333` text. `make_dark.py` turns them into Kitsu's dark colors (`colors.darkenColor`). Do not use the thin outlined variant, even where Kitsu does.
- The selected or focused item (row, card, cell) is outlined in green `#00b242`, 1.5 to 2px, with a soft green `feDropShadow`, the same on every illustration.
- Make the data plausible today: dates in the current year, consistent with the visible filters (e.g. "Due this week" means all due dates in one week).
- Structure the SVG with `<symbol>` for repeated pieces (production icon, thumbnails, avatars) and `<g id>` for shared cell contents, as in the reference file. Font: `Lato, 'Helvetica Neue', Helvetica, Arial, sans-serif`.
- Frame: a white card (`rx 12`, soft `feDropShadow`) with a viewBox tight around it plus room for the shadow. Set `width`/`height` close to the old PNG (about 1440 wide): the feature column has no max width, so a small intrinsic size makes the image look shrunk on large screens; `max-width: 100%` scales it down elsewhere.

## 3. Animate

- One 6 to 10 s loop that tells the feature's story (status change, focus moving to the next item, a comment appearing). CSS `@keyframes` in a `<style>` inside the SVG, opacity and transform only.
- Always add `@media (prefers-reduced-motion: reduce) { ... { animation: none } }`.
- No `<script>`: the image goes through IPX, which strips scripts.

## 4. Reuse the original pixels

Every avatar, thumbnail, production icon or embedded screen comes from the original PNG, not a drawing. Draw placeholder symbols first, then replace them:

```
python3 -I .claude/skills/kitsu-screenshot-svg/scripts/embed_crops.py <draft.svg> <original.png> <crops.json> <out.svg>
```

`crops.json` maps a symbol id to its crop box in the PNG: `{"prod-snow": [40, 272, 40, 40], "thumb-a": [241, 273, 58, 38]}` (x, y, w, h). The script replaces the symbol content with the cropped image (base64 PNG), keeps the symbol viewBox and its clip-path, and fills the box (`slice`).

Keep the draft SVG and the crops JSON in the scratchpad and regenerate from them on every change, never edit the generated file by hand.

## 5. Light and dark

- **Playlist screens** (the player, review room, comparison) are dark in Kitsu whatever the theme: produce only the dark version and use it as `image`.
- **Everything else**: produce both. The dark one follows Kitsu's dark theme:

```
python3 -I .claude/skills/kitsu-screenshot-svg/scripts/make_dark.py <light.svg> <dark.svg> [extra-map.json]
```

It maps surfaces, borders and text colors (white text on colored pills stays white) and prints the colors it left alone, so you can add them to `extra-map.json` (`{"#abcdef": "#123456"}`).

## 6. Wire it in

- Files: `app/assets/images/screenshots/kitsu-<name>-animated.svg` and `kitsu-<name>-animated-dark.svg`.
- In each `content/{en,fr,ja}_pages.json` entry: `"image": "kitsu-<name>-animated.svg"`, `"imageDark": "kitsu-<name>-animated-dark.svg"`, and drop `"shadow": true` (the SVG draws its own card shadow). `FeatureBlock.vue` serves SVGs without WebP conversion (which would freeze the animation) and shows `imageDark` under `.only-dark`. Other components (homepage tabs, `KitsuFeatureBlock`) do not support this yet: check before wiring an image there.
- Validate the JSON: `node -e 'for(const l of ["en","fr","ja"])JSON.parse(require("fs").readFileSync(`content/${l}_pages.json`))'`.

## 7. Check

- Render both files in headless Chrome (Inkscape and rsvg drop `feDropShadow` and CSS animations, so their previews lie):

```
.claude/skills/kitsu-screenshot-svg/scripts/render.sh <file.svg> <out.png> [background]
```

  Look at the PNG, then crop and zoom the dense areas (tabs, filters) to check spacing and overflow.
- Restart the dev server with `rm -rf .nuxt .data && npm run dev` and curl the feature page: both `<img>` must be there (`only-light` / `only-dark`) with `/_ipx/_/images/screenshots/...svg` URLs returning `image/svg+xml`.
- The old PNG becomes unused: tell the user, do not delete it without asking.
- Do not commit before the user has looked at it in the browser.
