---
name: cleanup-pass
description: Use when asked to re-read, clean up or simplify Kitsu code that was just written or heavily changed ("relis", "clean", "simplifie", "passe de nettoyage", "cleanup pass"), typically after a migration pass, a long series of additions, or before opening a PR.
---

# Cleanup Pass

## Overview

A cleanup pass re-reads recently changed code and makes it smaller and more conventional **without changing what it does**. Behavior changes are reported, never applied silently.

## Scope

1. Determine the perimeter, in this order: files named by the user, else commits named by the user, else `git diff origin/main...HEAD --stat` plus the working tree.
2. Every file in the perimeter is reviewed in full, style block included. Carried-over code in those files is in scope: tag its findings `(pre-existing)`.
3. Read `git diff` for each file to tell new code from carried-over code. Files outside the perimeter are out of scope, even when a finding points at them: mention them in the report instead.

## Checklist

Walk each file top to bottom against these, in order. Apply what is a pure cleanup; list the rest.

**Dead code**
- Members not referenced by the template or another file (grep both the camelCase and kebab-case forms).
- Imports, props, emits, store getters, refs and template `ref="…"` nobody reads.
- CSS selectors that match nothing in the template, and scoped rules that target a child's inner elements without `:deep()`.

**Kitsu script conventions** (see `CLAUDE.md`)
- `<script setup>` sections in order, each title underlined with dashes padded to column 80. The composables block right after the imports carries no title.
- Imports in three blocks (packages, `@/lib` + `@/composables` + `@/store`, `@/components`), alphabetical inside each.
- Arrow functions, `defineProps` with types and defaults, `defineEmits` declared.
- `t()` from `useI18n` only inside computeds and handlers, never at setup top level.
- `defineExpose` for anything a parent reaches through a ref.
- No `fetch` in components: API module plus store action.

**Simplification**
- Duplicate promise chains or try/catch blocks: extract one helper.
- Imperative loops that are a `map`/`filter`/`reduce`/`some`. No `continue`.
- Helpers return new values, arguments are never mutated (`{ ...form, id }`).
- Comments that restate the code: delete. Comments that explain a non-obvious why: keep.

**CSS**
- Theme colors through `var(--*)` tokens. A `.dark { }` block or `$white`/hex for a background, text or border color is a finding: replace with the token when one exists (defined in `src/variables.scss`), list it otherwise.
- SCSS variables stay for accents only (`$red`, `$green`).
- Dark mode and responsive blocks contain only overrides, not duplicated rules.

**i18n**
- New keys exist in `src/locales/en.js`. Plural calls pass `{ count }`, never a bare number.
- A key whose English mentions shot, sequence or episode has its `en_nft.js` / `en_video-game.js` override.

## Cleanup versus behavior change

| Looks like cleanup, is a behavior change | Do instead |
|---|---|
| Replacing local state with a store computed that sorts or filters differently | Report it |
| `v-if` to `v-show` or the reverse | Report it |
| Dropping a guard, a `nextTick`, a `setTimeout` you cannot trace to its reason | Read `git log -S` first, then report if still unsure |
| Renaming an emitted event, a prop, a route name | Out of scope |

Rule: if a test or a screenshot could tell the before from the after, it is not cleanup.

## Verify

Run on every touched file before reporting:

```bash
npx eslint <files> && npx prettier --check <files>
npx vitest run tests/unit/<matching dir>
```

## Report

Three lists, in this order, one line per item with `file:line`, `(pre-existing)` appended when the code predates the diff:

1. **Applied**: cleanups done, grouped by file.
2. **Proposed**: behavior changes worth making, each with the observable difference.
3. **Checked, unchanged**: what was reviewed and found conventional.

Do not commit. The user tests in the browser and asks for the commit.
