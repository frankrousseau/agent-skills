# agent-skills

The agent skills I use regularly.

## general

- [code-audit](skills/general/code-audit/SKILL.md): phased, read-only audit of a whole repo, written to `.audit/`.
- [audit-checklist](skills/general/audit-checklist/SKILL.md): turns an audit report into checklists and implements the items you pick.
- [elixir-cleanup-pass](skills/general/elixir-cleanup-pass/SKILL.md): re-reads recently changed Elixir/Phoenix code and simplifies it without changing behavior; JSON shapes, PubSub topics and stored strings are treated as contracts.
- [memory-audit](skills/general/memory-audit/SKILL.md): audits and consolidates agent memory and CLAUDE.md files, checking each entry against code and git.
- [pushpr](skills/general/pushpr/SKILL.md): drafts a pull request (C4 **Problem** / **Solution** body), waits for approval, then pushes to the personal fork and opens the PR upstream. Invoked by hand (`/pushpr`).
- [python-check-docstrings-and-comments](skills/general/python-check-docstrings-and-comments/SKILL.md): checks that docstrings match the code (with a script for parameters and returns), that inline comments are useful, and rewrites both in ASD-STE100 Simplified Technical English.
- [python-check-tests](skills/general/python-check-tests/SKILL.md): for one Python file, measures branch coverage, maps behaviors to assertions, and lists missing, useless and over-zealous tests.
- [rust-cleanup-pass](skills/general/rust-cleanup-pass/SKILL.md): re-reads recently changed Rust code and simplifies it without changing behavior; Tauri commands, serde names and events are treated as contracts.
- [sentry-triage](skills/general/sentry-triage/SKILL.md): takes a Sentry issue from stacktrace to root cause, minimal fix and regression test, then stops before committing (written for zou).
- [sentry-weekly](skills/general/sentry-weekly/SKILL.md): read-only analysis of the last 7 days in Sentry against the previous week: volume, top, new and regressed issues, slow transactions, what to triage first.
- [servant-memory](skills/general/servant-memory/SKILL.md): syncs agent memory, skills and Cursor rules between machines through a Servant server (pull at session start, push after each write).

## kitsu

- [cleanup-pass](skills/kitsu/cleanup-pass/SKILL.md): re-reads recently changed Kitsu (Vue) code and simplifies it without changing behavior: dead code, house conventions, CSS tokens, i18n; behavior changes are reported, not applied.
- [contract-audit](skills/kitsu/contract-audit/SKILL.md): checks that kitsu, gazu and the docs only call routes and listen to events that zou really has.

## kitsu-orchestration

Agents developing software tracked in [Kitsu](https://github.com/cgwire/kitsu) through the kitsu CLI.

- [kitsu-plan](skills/kitsu-orchestration/kitsu-plan/SKILL.md): scaffolds the board (modules, features, dev-pipeline tasks).
- [kitsu-work](skills/kitsu-orchestration/kitsu-work/SKILL.md): worker agent: picks up tasks, publishes deliverables for review, loops on retakes.
- [kitsu-review](skills/kitsu-orchestration/kitsu-review/SKILL.md): independent reviewer agent: posts done or retake verdicts.
- [kitsu-loop](skills/kitsu-orchestration/kitsu-loop/SKILL.md): follows a project's news feed and acts on each change through kitsu-work.

## zou

Skills for [zou](https://github.com/cgwire/zou), Kitsu's API. Install them in the zou repo's `.claude/skills/`.

- [migration-replay-audit](skills/zou/migration-replay-audit/SKILL.md): replays every migration up, down and up again on a throwaway database, and flags downgrades that do not restore the schema.
- [new-endpoint](skills/zou/new-endpoint/SKILL.md): new REST endpoint (blueprint, Pydantic schema, tests).
- [new-model](skills/zou/new-model/SKILL.md): new SQLAlchemy model with migration, CRUD blueprint, routes and tests.
- [zou-blueprint-cleanup-pass](skills/zou/zou-blueprint-cleanup-pass/SKILL.md): re-reads recently changed blueprints (resources, schemas, routes, OpenAPI) and simplifies them without changing behavior.
- [zou-service-cleanup-pass](skills/zou/zou-service-cleanup-pass/SKILL.md): same for services: dead code, conventions, cache invalidation, events, N+1 queries.
- [zou-util-cleanup-pass](skills/zou/zou-util-cleanup-pass/SKILL.md): same for utils: layering, stdlib duplicates, security-sensitive helpers.

## gazu

Skills for [gazu](https://github.com/cgwire/gazu), the Python client of Kitsu. Install them in the gazu repo's `.claude/skills/`.

- [gazu-module-cleanup-pass](skills/gazu/gazu-module-cleanup-pass/SKILL.md): re-reads recently changed gazu modules and simplifies them without changing the public API: wrapper conventions, Python 3.7 compatibility, sync/async parity.

Install: copy a skill folder into `~/.claude/skills/` (or a repo's `.claude/skills/`).

MIT licensed.
