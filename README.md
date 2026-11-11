# agent-skills

The agent skills I use regularly.

## general

- [code-audit](skills/general/code-audit/SKILL.md): phased, read-only audit of a whole repo, written to `.audit/`.
- [audit-checklist](skills/general/audit-checklist/SKILL.md): turns an audit report into checklists and implements the items you pick.
- [memory-audit](skills/general/memory-audit/SKILL.md): audits and consolidates agent memory and CLAUDE.md files, checking each entry against code and git.
- [sentry-triage](skills/general/sentry-triage/SKILL.md): takes a Sentry issue from stacktrace to root cause, minimal fix and regression test, then stops before committing (written for zou).
- [sentry-weekly](skills/general/sentry-weekly/SKILL.md): read-only analysis of the last 7 days in Sentry against the previous week: volume, top, new and regressed issues, slow transactions, what to triage first.
- [servant-memory](skills/general/servant-memory/SKILL.md): syncs agent memory, skills and Cursor rules between machines through a Servant server (pull at session start, push after each write).

## kitsu

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

Install: copy a skill folder into `~/.claude/skills/` (or a repo's `.claude/skills/`).

MIT licensed.
