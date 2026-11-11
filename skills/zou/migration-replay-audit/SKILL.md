---
name: migration-replay-audit
description: Use when the user asks for the migration replay audit on zou ("rejoue les migrations", "audit des migrations", "downgrades qui mentent", "migration replay", "autogenerate vide ?"), and suggest it after adding or editing a migration, after a squash, or before a release. One-shot on a dedicated database, writes a report to zou/.audit/, commits nothing.
---

# Migration replay audit (zou)

On a dedicated empty database (`zoudb-migrations`, forced by the script,
its schema dropped at start), replays every migration in isolation:
down to its parent, upgrade, downgrade, upgrade again. Then, at head,
compares the schema with the models (what `zou migrate-db` would
autogenerate), and downgrades to base.

## Run

From the zou repo root (about a minute):

```bash
SECRET_KEY=audit-only-key CACHE_TYPE=simple \
    ~/.virtualenvs/zou/bin/python \
    ~/.claude/skills/migration-replay-audit/scripts/migration_replay.py
```

`SECRET_KEY` only because zou refuses the default one; `DB_DATABASE` is
ignored, the script always uses `zoudb-migrations`. Writes
`.audit/migration-replay-<date>.md` and `.json` (gitignored).

## How it decides

- Each revision is measured from its parent, not from the previous one of
  the walk: downgrading to a parent also unapplies a sibling branch.
- Merge revisions (several parents) are skipped, they carry no schema.
- Snapshot: tables, columns (type, nullability, default), primary key,
  foreign keys with their options (`ondelete`), indexes, unique and check
  constraints, enum types.
- A failed downgrade is recorded, the schema rebuilt up to that revision,
  and the replay goes on.
- Model drift ignores `plugin_*` tables: plugins installed in the venv ship
  their own migrations.

## Read the report

| section | action |
|---------|--------|
| Failed | the downgrade crashes: fix its `downgrade()` (unnamed constraint, drop order) |
| Downgrades that lie | the downgrade runs but does not restore the parent schema |
| Upgrade not repeatable | the upgrade depends on state it should create itself |
| Models vs schema at head | what `zou migrate-db` would generate on a clean tree: declare in the model what a migration created on purpose, or migrate what the model declares |
| Left after downgrade to base | objects no downgrade removes |

Before reporting a drift, query `pg_constraint` / `pg_indexes` on
`zoudb-migrations` (left at head or wherever the run stopped): a unique
constraint on the same columns as the primary key is merged into it by
PostgreSQL, which autogenerate reports as a missing constraint.

## Known limits

- Schema only: data migrations (backfills) are run, not checked.
- One PostgreSQL version, the local one.
