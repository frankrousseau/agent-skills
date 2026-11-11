# agent-skills

The agent skills I use regularly.

## general

| Skill | Purpose |
|---|---|
| [audit-checklist](skills/general/audit-checklist/SKILL.md) | Turn an audit report into checklists, fix the picked items |
| [code-audit](skills/general/code-audit/SKILL.md) | Phased, read-only audit of a whole repo |
| [elixir-cleanup-pass](skills/general/elixir-cleanup-pass/SKILL.md) | Simplify recent Elixir code, no behavior change |
| [memory-audit](skills/general/memory-audit/SKILL.md) | Verify and consolidate agent memory and CLAUDE.md |
| [pushpr](skills/general/pushpr/SKILL.md) | Draft a Problem/Solution PR, push after approval |
| [python-check-docstrings-and-comments](skills/general/python-check-docstrings-and-comments/SKILL.md) | Docstrings match the code, useful comments, ASD-STE100 |
| [python-check-tests](skills/general/python-check-tests/SKILL.md) | Coverage, useless and over-zealous tests for one file |
| [rust-cleanup-pass](skills/general/rust-cleanup-pass/SKILL.md) | Simplify recent Rust code, no behavior change |
| [sentry-triage](skills/general/sentry-triage/SKILL.md) | Sentry issue to root cause, fix and regression test |
| [sentry-weekly](skills/general/sentry-weekly/SKILL.md) | Last 7 days of Sentry against the week before |
| [servant-memory](skills/general/servant-memory/SKILL.md) | Sync memory and skills between machines via Servant |

## kitsu

| Skill | Purpose |
|---|---|
| [cleanup-pass](skills/kitsu/cleanup-pass/SKILL.md) | Simplify recent Kitsu (Vue) code, no behavior change |
| [contract-audit](skills/kitsu/contract-audit/SKILL.md) | Check that kitsu, gazu and docs only use real zou routes and events |

## kitsu-orchestration

Agents that develop software tracked in [Kitsu](https://github.com/cgwire/kitsu) through the kitsu CLI.

| Skill | Purpose |
|---|---|
| [kitsu-plan](skills/kitsu-orchestration/kitsu-plan/SKILL.md) | Scaffold the board: modules, features, pipeline tasks |
| [kitsu-work](skills/kitsu-orchestration/kitsu-work/SKILL.md) | Worker: do tasks, publish for review, loop on retakes |
| [kitsu-review](skills/kitsu-orchestration/kitsu-review/SKILL.md) | Reviewer: post done or retake verdicts |
| [kitsu-loop](skills/kitsu-orchestration/kitsu-loop/SKILL.md) | Follow a project's news feed and act on changes |

## zou

Skills for [zou](https://github.com/cgwire/zou), Kitsu's API.

| Skill | Purpose |
|---|---|
| [migration-replay-audit](skills/zou/migration-replay-audit/SKILL.md) | Replay migrations up, down, up; flag lying downgrades |
| [new-endpoint](skills/zou/new-endpoint/SKILL.md) | Scaffold a REST endpoint with schema and tests |
| [new-model](skills/zou/new-model/SKILL.md) | Scaffold a model, migration, CRUD routes and tests |
| [zou-blueprint-cleanup-pass](skills/zou/zou-blueprint-cleanup-pass/SKILL.md) | Simplify recent blueprints, no behavior change |
| [zou-service-cleanup-pass](skills/zou/zou-service-cleanup-pass/SKILL.md) | Simplify recent services, no behavior change |
| [zou-util-cleanup-pass](skills/zou/zou-util-cleanup-pass/SKILL.md) | Simplify recent utils, no behavior change |

## gazu

Skills for [gazu](https://github.com/cgwire/gazu), Kitsu's Python client.

| Skill | Purpose |
|---|---|
| [gazu-module-cleanup-pass](skills/gazu/gazu-module-cleanup-pass/SKILL.md) | Simplify recent modules, public API untouched |

## Install

Copy a skill folder into `~/.claude/skills/`, or into a repo's `.claude/skills/` for the project ones.

MIT licensed.
