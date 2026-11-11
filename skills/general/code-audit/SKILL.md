---
name: code-audit
description: Use when the user asks for a full code review/audit of the whole project ("analyse complète du code", "audit du code", "full code analysis", "code audit", "état de santé du code"). Whole-repo and read-only — for reviewing only the current diff, /code-review is the lighter tool.
---

# Code audit — analyse complète, phase par phase

Goal: audit the codebase in the current working directory across **8 themes**, running **one phase at a time**. Each phase investigates its theme, presents its findings, then you move to the next. At the end, produce a single cross-cutting prioritized synthesis.

> **When to use this vs. related skills.** This is a whole-repo health check across 8 axes — reach for it periodically, or when the user wants broad coverage (security, dependencies, architecture, docs…). To review **only the current diff** before a merge (correctness + simplification, faster, can comment a PR or apply fixes), prefer the built-in **`/code-review`** instead. To **act on** this audit's findings, hand the report to **`/audit-checklist`**, which turns it into per-phase checklists and implements the items the user selects.

This skill is **read-only with respect to the audited code**: investigate and report, never edit source, run formatters, upgrade dependencies, or commit. The one thing it *does* write is its own **report file** (a separate artifact — see below). Fixes to the code happen only afterward, if the user asks, one at a time.

## The report file (persist as you go)

Findings must be written to a file, not just streamed to the chat — for two reasons: a long audit may have its context compacted before the final synthesis, so early phases would be lost; and the user keeps a durable, shareable deliverable.

- In **phase 0**, create the `.audit/` directory at the repo root (`mkdir -p .audit`) and start `.audit/code-audit-<YYYY-MM-DD>.md` (use today's date). Begin it with a title, the date, and the scope summary. If a report with today's date already exists, **read it first**: if it's an interrupted run (phases missing, no synthesis), offer to resume at the first missing phase instead of restarting; if it's a completed run, start a new file suffixed `-2`, `-3`, … rather than clobbering it.
- After **each** phase, **append** that phase's findings section to the file immediately — before moving to the next phase. This is what makes the audit crash- and compaction-safe. On a full-stack repo (see phase 0), keep **Backend** and **Frontend** findings under clearly separated headings.
- In the **final** step, insert the cross-cutting synthesis at the **top** of the file (Read it, then rewrite with the synthesis prepended) so the most important section is read first.
- Tell the user the report path, and suggest adding `.audit/` to `.gitignore` (or deleting it) since it's a generated artifact, not part of the codebase.

## Why phased (not all-parallel)

- **Digestibility** — theme-by-theme findings are far easier to absorb than one giant dump. The user can react (or say "stop, fix that first") between phases.
- **Phase 1 feeds the rest** — the architecture pass produces a *map* of the codebase (modules, layers, hot spots, key flows). Carry that map forward so every later phase is targeted instead of starting blind.

Stream each phase's findings as you finish it, then continue automatically to the next unless the user interrupts. Within a single heavy theme you may still fan out parallel sub-agents (`Agent` tool, `Explore`/`general-purpose` type) — the *phases* are sequential, the work inside one phase need not be.

## Phase 0 — Scope the codebase

Get your bearings (run together):

```bash
git rev-parse --show-toplevel 2>/dev/null    # repo root (fall back to CWD if not a repo)
git log --oneline -10 2>/dev/null            # recent activity / what's being worked on
ls -A                                         # top-level layout
```

Then, with the file tools, establish:
- **Languages & frameworks** — manifests (`package.json`, `requirements.txt`, `pyproject.toml`, `go.mod`, `Cargo.toml`, etc.).
- **Project conventions** — `CLAUDE.md`, `README`, linter/formatter config. Findings must respect the project's own idioms, not impose generic ones.
- **Rough size** — source file count and main directories, to decide how wide to fan out.

**Detect the stack shape.** Is this a single-stack project, or **full-stack** (a distinct backend and a distinct frontend living side by side — e.g. a Django/Rails/Node API plus a Nuxt/React/Vue SPA, often in separate sub-directories with separate manifests)? Identify each side's root directory and its toolchain (`pip`/`coverage`/`ruff` vs `npm`/`eslint`/`vitest`, etc.). You'll use this to decide between one pass and two.

If the directory is huge or a monorepo, ask the user whether to scope to a sub-path before starting.

## Single pass vs. two passes (backend / frontend)

- **Single-stack project** → run the 8 phases once over the whole codebase.
- **Full-stack project** → run the 8-phase sequence **twice**: a **Backend pass** first, then a **Frontend pass**. The two stacks have different concerns, tools, and idioms (backend security = SQL injection/authz; frontend security = XSS/CSP; deps = `pip` vs `npm`; performance = ORM N+1 vs bundle size), so auditing them together produces mushy, generic findings. Keep each pass self-contained: its own architecture map (phase 1) feeding its own later phases, its own toolchain, its own report headings.
- **Frontend-only themes.** In the Frontend pass, add **accessibility** (semantic markup, keyboard navigation, contrast, alt text, focus management) and **i18n** (hardcoded user-facing strings, locale/date/number handling) to the Clean code phase.
- **Mind the seam.** Add a short **Intégration front↔back** check (in the Backend architecture phase, or as a brief extra note): API contract consistency, request/response types, auth/session flow across the boundary, error handling end-to-end. Cross-boundary issues are exactly what a strict two-pass split tends to miss.
- The **final synthesis** spans both passes — one prioritized list across backend and frontend.

## Phases 1–8 — one theme at a time

Run these **in order** (and, on a full-stack repo, run the whole sequence once per pass — Backend then Frontend, per the section above). Phase 1 is first on purpose: keep its codebase map and reuse it in every later phase of that pass. For each phase, produce findings where every item has: **`file:line`, severity (critical/high/medium/low), the issue, why it matters, and a concrete suggested fix**. Present that phase's findings to the user **and append them to the report file** before starting the next phase.

1. **Architecture** *(do first — produces the map)* — module boundaries, layering, separation of concerns, coupling/cohesion, circular dependencies, duplication across modules, dead code, scalability bottlenecks, consistency of the chosen patterns. Is the structure coherent with how the project describes itself? Output a short map of the main modules and flows to carry forward.

2. **Bugs / debug (correctness)** — logic errors, unhandled edge cases, null/undefined and off-by-one risks, race conditions, resource leaks (unclosed files/connections), swallowed or mishandled exceptions, incorrect error handling. Include **observability**: logging quality (levels, noise, sensitive data logged, missing context on errors) and error reporting — ask "could an incident in production be diagnosed from these logs?".

3. **Tests & couverture** — coverage on the critical paths (identify them from the phase-1 map — e.g. auth, payments, data sync, whatever this project's core flows are), missing or weak tests, flaky/fragile patterns, tests asserting nothing, gaps where a bug from phase 2 would not be caught. Run the project's test/coverage tool **read-only** if cheap (e.g. `coverage report`, `pytest --collect-only`) — never write or commit. **First make the toolchain reachable**: the audit env often lacks the project's deps. Look for and activate a virtualenv before running anything (`.venv/`, `venv/`, `env/`, or `poetry env info -p`/`pipenv --venv`; for Node, ensure `node_modules` exists). If no env is available and installing is out of scope, don't silently skip — **state in the findings that test collection could not run and why**, and fall back to a static review of the test files.

4. **Security** — injection (SQL/command/template), authn/authz gaps, secrets/credentials in code, unsafe deserialization, SSRF/XSS/CSRF, IDOR, missing input validation, weak crypto, permissive CORS, exposed debug/admin endpoints, dependency CVEs. Emphasize exploitable issues over theoretical ones.

5. **Performance** — N+1 ORM queries, missing indexes, slow/unbounded queries, missing caching, sync work that should be async, frontend bundle size, lazy-loading, render bottlenecks. Tie findings to concrete hot paths from the phase-1 map.

6. **Clean code** — naming clarity, function/file size and complexity, simplicity vs over-engineering, leanness (premature abstraction, unused code, redundant layers), readability, comment quality, adherence to existing idioms. Flag both what's too complex and what's needlessly clever.

7. **Dépendances / mises à jour de libs** — outdated packages, known-vulnerable versions, deprecated APIs in use, unmaintained deps, version-pinning hygiene, unused dependencies. Run the ecosystem's audit tool **read-only** (`npm outdated`, `pip list --outdated`, `npm audit`, `pip-audit`) — never `install`/`update`/`upgrade`. **Caveat — installed tree vs. manifest:** these tools report what's *installed*, which can diverge wildly from the manifest (e.g. a stale `node_modules`/lockfile predating a major upgrade, or `pip list` reading the system Python instead of the project venv). Always cross-check the tool output against the actual manifest (`package.json`, `requirements/*.txt`), and when the installed tree looks stale or unrelated, **say so explicitly** and base findings on the manifest — don't report phantom vulns from an out-of-date install as if current.

8. **Documentation** — README accuracy, docstrings/comments on non-obvious code, API documentation, setup/onboarding instructions, and whether the docs still match the actual code. Flag drift between documented and real behavior.

## Final — cross-cutting synthesis

After phase 8, tie everything together (don't just repeat the per-phase lists). Deduplicate findings that span themes (a security issue may also be a bug), resolve contradictions, and write this synthesis at the **top** of the report file (as well as showing it in the chat):

- **Résumé exécutif** — 3-6 lines: overall health, biggest risks, recurring themes.
- **Top priorités** — a ranked shortlist (≈5-10) of what to fix first, across all themes, each with severity and a one-line rationale. The most important section.
- **Quick wins** — low-effort/high-value items worth doing immediately.

Match the user's language (request in French → report in French). Be honest about confidence: mark anything you couldn't fully verify rather than overstating it.

## Next steps

End by asking whether the user wants you to fix any specific finding or group. Only start editing once they choose — then tackle them one at a time, verifying as you go.
