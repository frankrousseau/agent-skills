---
name: audit-checklist
description: Use when the user wants to act on a code-audit report ("fais une checklist", "constitue des checklists par phase", "je choisis quoi implémenter", "turn the audit into a checklist", "implement the audit findings I pick", "reprends la checklist"). Bridges /code-audit (analysis) and the actual fixes.
---

# Audit checklist — choisir et implémenter les findings

Goal: take the findings produced by `/code-audit` (or an equivalent report), turn them into **actionable checklists grouped by phase/theme**, let the user **select** which items to act on, and then **implement only the selected ones**, one at a time, verifying as you go.

> **Where this fits.** This is the *act-on-it* stage of a three-skill pipeline: **`/code-audit`** (whole-repo analysis → report) → **`/audit-checklist`** (this skill: report → checklist → selective implementation). It consumes an audit report and does not itself audit — if none exists, point the user to `/code-audit` first. For fixing findings that are scoped to **the current diff** rather than a stored audit report, the built-in **`/code-review --fix`** is the lighter tool.

Three stages: **Build** the checklist → **Select** with the user → **Implement** the selection. Do not edit any source code before the Select stage is done and the user has chosen.

## Stage 1 — Build the checklist

1. **Find the source report.** Look for the most recent `.audit/code-audit-*.md` at the repo root. If several exist, pick the newest by date/suffix in the filename (confirm with the user if ambiguous). If none exists, tell the user and offer to run `/code-audit` first — don't invent findings.
   **Resume check:** before building anything, look for an existing `.audit/checklist-*.md` whose `Source:` line points at that report. If one exists, skip Stage 1 entirely — present its current state (done / remaining items) and go straight to Stage 2 with the unchecked items. Only build a fresh checklist when none exists for the chosen report.
2. **Parse every finding** into a checklist item. Preserve the report's structure: one section per **phase/theme** (Architecture, Bugs/debug, Tests & couverture, Security, Performance, Clean code, Dépendances, Documentation), and — on a full-stack report — keep the **Backend** and **Frontend** passes as separate top-level groups.
3. **Each item gets**, on one scannable line:
   - a **stable ID** = theme prefix + number, namespaced by pass on full-stack (e.g. `BE-SEC-1`, `FE-PERF-3`, `BE-DEP-2`);
   - the **severity** (critical/high/medium/low) from the report;
   - the **`file:line`** anchor;
   - a one-line **description**;
   - the **suggested fix** (short);
   - an **effort tag** you estimate: `quick` (≤15 min, mechanical), `small` (<1 h, localized), `medium` (a few hours, several files), `large` (cross-cutting / risky / needs a decision).
4. **Write it to `.audit/checklist-<YYYY-MM-DD>.md`** (today's date; suffix `-2`, `-3`, … if taken) as Markdown with `- [ ]` checkboxes, one per item, grouped by pass → theme, severity-sorted within each theme. Start the file with a `Source: <audit report filename>` line so the checklist stays tied to the report it was built from, then a short legend explaining IDs, severities, and effort tags, and a one-line "how to select" note. This file is the durable artifact the user edits and you update.

Format each item like:
```
- [ ] **BE-SEC-1** · 🔴 critical · `instances/views.py:159` · effort: small
      Token compared with non-constant-time `!=`; gates mutating endpoints.
      Fix: use `hmac.compare_digest`, add a scheme, split the secret.
```

## Stage 2 — Select with the user

Present the checklist (summarize counts per severity and per effort) and ask the user **which items to implement**. Support any of these selection modes — let them mix:
- **By ID** — "BE-SEC-1, FE-PERF-3, BE-DEP-2".
- **By batch** — "all criticals", "all quick wins", "the whole Security phase", "everything in the Frontend pass".
- **By editing the file** — they tick `- [x]` boxes in `.audit/checklist-*.md` and tell you to read it back.

If the selection is large or open-ended, use `AskUserQuestion` to offer a few sensible batches (e.g. "All criticals", "Criticals + quick wins", "Security phase only", "Let me pick IDs") so they can choose fast. Echo back the resolved concrete list of IDs and get a clear go-ahead before touching code. Flag any selected item whose fix is risky or needs a decision (e.g. a breaking dependency upgrade, an API contract change spanning front+back) so the user knows what they're authorizing.

## Stage 3 — Implement the selection

Work through the chosen items **one at a time**, in a sensible order (group related items; do paired cross-boundary fixes together — e.g. a backend change and its frontend counterpart; do prerequisite/foundational items before dependent ones). For each item:

1. **Re-read the actual code** at the `file:line` before changing it — the report is a snapshot and may be stale. If what you find contradicts the finding, stop and surface it instead of "fixing" it.
2. **Make the change**, matching the surrounding code's idioms.
3. **Verify** with whatever the project offers (run the relevant test, linter, type-check, or the app) — read-only verification, scoped to what you touched. Report the result honestly; if a test fails, say so.
4. **Update the checklist file**: flip `- [ ]` → `- [x]` and append a short note (what changed, file(s) touched, verification result). This keeps progress durable across context compaction.
5. Move to the next item. Don't `git commit` or push unless the user asks; if they do, branch first if on the default branch and group related items into coherent commits.

After the batch, give a short recap: what was implemented and verified, what was skipped or blocked and why, and what remains unchecked in the checklist for a future pass.

## Notes

- Stay **read-only until the user has selected.** The Build stage only writes the checklist artifact, never source.
- Keep the checklist file as the single source of truth for progress — re-runnable: the user can come back later, tick more boxes, and re-invoke to continue.
- Match the user's language in the checklist and recaps.
