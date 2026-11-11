---
name: memory-audit
description: Use when asked to audit, consolidate, or clean accumulated agent memory and CLAUDE.md instructions ("consolide la mémoire", "audit memory", "clean up CLAUDE.md", "la mémoire a dérivé", "dedupe instructions"). Inventories every knowledge source, verifies entries against code/git/PRs, dedupes across levels, restructures per the loading mechanics.
---

# Memory audit & consolidation

Curation, not creation. The core rule: **verify every claim against reality — code, git log, merged PRs — never against the note itself.** Most drift is "still marked pending but actually shipped".

## 0. Backup first

Before ANY modification, copy all memory files and CLAUDE.md files to a timestamped folder outside the repos (e.g. `~/.claude/backups/memory-consolidation-<ts>/`). Nothing disappears without a trace.

## 1. Inventory — report volumes before continuing

- CLAUDE.md at every level: global (`~/.claude/`), workspace root, per repo; `CLAUDE.local.md`; `.claude/rules/`.
- Auto-memory: `~/.claude/projects/*/memory/` — map each mangled dir name to its repo (one per git root; the workspace parent has its own).
- Adjacent sources to flag but not restructure unless asked: `.claude/skills`, `commands`, `agents`, hooks — they often duplicate or contradict CLAUDE.md.
- Note per file: line count, and **tracked in git (public!) vs local**.

## 2. Audit every entry

Classify: duplicate / contradiction / stale / valid. Verification tactics:

- "Parked / pending / not merged" claims → check `git log --grep`, merged PRs, and the actual file state. Features ship while notes sleep.
- Documented commands → **run the safe read-only ones** to validate; never run mutations or commands a note itself flags as dangerous.
- Documented policy vs actual practice → sample real history (trailers in `git log --format=%B`, PR body format via `gh pr view --json body` on merged PRs).
- Dangling references → existence-check every file, agent, and skill a note points to.
- Line-number citations → spot-check; code moves.

**List contradictions to the user BEFORE resolving them — the user decides.** Present the evidence for each side.

## 3. Restructure by loading mechanics

- Stable instructions/conventions → the repo's CLAUDE.md (loaded whole; keep it ≤300 lines, imperative, dense).
- Cross-repo/workspace-wide rules → the workspace root CLAUDE.md.
- Machine-specific commands, credentials, personal workflow → `CLAUDE.local.md` (gitignored) or auto-memory — **never in a tracked CLAUDE.md**.
- Learnings, history, open questions → auto-memory as thematic files (`projects.md`, `patterns.md`, `debugging.md`) with `MEMORY.md` as a concise index (only the beginning is loaded — keep it short, content lives in the files).
- One fact lives in exactly one place; other levels point to it.
- Resolved incidents: delete, or compress to the durable lesson; point to the backup for archaeology.

## 4. Report

- Deleted entries, each with the reason and the verification evidence.
- Moved entries (from → to).
- Uncertainty zones left unverified (and why).
- The backup path.
- Remind the user which modified files are git-tracked and uncommitted — committing is their call.
