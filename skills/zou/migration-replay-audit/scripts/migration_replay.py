"""
Migration replay audit for zou.

On a dedicated empty database, applies every migration one at a time and,
after each, downgrades it and checks the schema is back to what it was
before, then upgrades again. At head, compares the schema with the models
(an alembic autogenerate that must be empty). Finally downgrades to base
and checks nothing is left.

Run from the zou repo root (see SKILL.md):

    SECRET_KEY=audit-only-key CACHE_TYPE=simple \
        ~/.virtualenvs/zou/bin/python \
        ~/.claude/skills/migration-replay-audit/scripts/migration_replay.py

Writes .audit/migration-replay-<date>.md and .json in the repo root.
"""

import datetime
import json
import logging
import os

# Never another database: the schema is dropped at start.
DATABASE = "zoudb-migrations"
os.environ["DB_DATABASE"] = DATABASE

import flask_migrate  # noqa: E402
from alembic.autogenerate import compare_metadata  # noqa: E402
from alembic.migration import MigrationContext  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402
from sqlalchemy import inspect, text  # noqa: E402
from sqlalchemy_utils import create_database, database_exists  # noqa: E402

from zou import __file__ as zou_root  # noqa: E402
from zou.app import app, db  # noqa: E402

MIGRATIONS = os.path.join(os.path.dirname(zou_root), "migrations")


def short(exception):
    message = str(exception).split("\n[SQL")[0].replace("\n", " ")
    return f"{type(exception).__name__}: {message}"[:400]


def reset_schema():
    if not database_exists(db.engine.url):
        create_database(db.engine.url)
    with db.engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))


def snapshot():
    """
    Everything a downgrade has to put back: tables, columns with type,
    nullability and default, keys, indexes, constraints, and enum types.
    """
    db.engine.dispose()
    inspector = inspect(db.engine)
    schema = {}
    for table in sorted(inspector.get_table_names()):
        if table == "alembic_version":
            continue
        schema[table] = {
            "columns": {
                c["name"]: [str(c["type"]), c["nullable"], str(c["default"])]
                for c in inspector.get_columns(table)
            },
            "pk": inspector.get_pk_constraint(table)["constrained_columns"],
            "fks": sorted(
                f"{fk['constrained_columns']}->{fk['referred_table']}"
                f"{fk['referred_columns']} {fk.get('options', {})}"
                for fk in inspector.get_foreign_keys(table)
            ),
            "indexes": sorted(
                f"{i['name']}{i['column_names']} unique={i['unique']}"
                for i in inspector.get_indexes(table)
            ),
            "uniques": sorted(
                f"{u['name']}{u['column_names']}"
                for u in inspector.get_unique_constraints(table)
            ),
            "checks": sorted(
                f"{c['name']}" for c in inspector.get_check_constraints(table)
            ),
        }
    with db.engine.connect() as connection:
        enums = connection.execute(
            text(
                "SELECT t.typname, string_agg(e.enumlabel, ',' "
                "ORDER BY e.enumsortorder) FROM pg_type t JOIN pg_enum e "
                "ON e.enumtypid = t.oid GROUP BY t.typname"
            )
        ).all()
    schema["__enums__"] = {name: labels for name, labels in enums}
    return schema


def diff(before, after):
    changes = []
    for table in sorted(set(before) | set(after)):
        if table not in after:
            changes.append(f"missing {table}")
        elif table not in before:
            changes.append(f"left over {table}")
        elif before[table] != after[table]:
            for key in before[table]:
                old, new = before[table][key], after[table][key]
                if old == new:
                    continue
                if isinstance(old, dict):
                    for name in sorted(set(old) | set(new)):
                        if old.get(name) != new.get(name):
                            changes.append(
                                f"{table}.{key}.{name}: {old.get(name)} -> "
                                f"{new.get(name)}"
                            )
                else:
                    for item in sorted(set(old) - set(new)):
                        changes.append(f"{table}.{key}: lost {item}")
                    for item in sorted(set(new) - set(old)):
                        changes.append(f"{table}.{key}: gained {item}")
    return changes


def model_drift():
    with db.engine.connect() as connection:
        context = MigrationContext.configure(
            connection,
            opts={
                "compare_type": True,
                "include_object": lambda obj, name, type_, reflected, _: (
                    type_ != "table"
                    or not reflected
                    or name in db.metadata.tables
                ),
            },
        )
        # Tables of the plugins installed in this venv come with their own
        # migrations, not zou's.
        return [
            str(change)
            for change in compare_metadata(context, db.metadata)
            if "plugin_" not in str(change)
        ]


def main():
    logging.getLogger("alembic").setLevel(logging.WARNING)
    script = ScriptDirectory(MIGRATIONS)
    revisions = list(reversed(list(script.walk_revisions())))
    results = {"steps": [], "head_drift": [], "base_left": [], "errors": []}

    with app.app_context():
        reset_schema()
        for revision in revisions:
            step = {"revision": revision.revision, "doc": revision.doc}
            results["steps"].append(step)
            if isinstance(revision.down_revision, tuple):
                step["skipped"] = "merge revision"
                continue
            parent = revision.down_revision or "base"
            try:
                flask_migrate.upgrade(MIGRATIONS, revision.revision)
            except Exception as exception:
                step["error"] = f"upgrade: {short(exception)}"
                results["errors"].append(revision.revision)
                break
            # Measured from the parent, not from the previous revision of
            # the walk: going down to the parent also unapplies a sibling
            # branch, which is alembic's doing, not this migration's.
            try:
                flask_migrate.downgrade(MIGRATIONS, parent)
                before = snapshot()
                flask_migrate.upgrade(MIGRATIONS, revision.revision)
                after = snapshot()
                flask_migrate.downgrade(MIGRATIONS, parent)
                step["downgrade_diff"] = diff(before, snapshot())
                flask_migrate.upgrade(MIGRATIONS, revision.revision)
                step["reupgrade_diff"] = diff(after, snapshot())
            except Exception as exception:
                # A failed downgrade leaves the schema half dropped: rebuild
                # it up to this revision and go on with the next ones.
                step["error"] = f"downgrade: {short(exception)}"
                reset_schema()
                flask_migrate.upgrade(MIGRATIONS, revision.revision)

        if not results["errors"]:
            flask_migrate.upgrade(MIGRATIONS, "heads")
            results["head_drift"] = model_drift()
            try:
                flask_migrate.downgrade(MIGRATIONS, "base")
                left = snapshot()
                results["base_left"] = sorted(
                    t for t in left if t != "__enums__"
                ) + sorted(left["__enums__"])
            except Exception as exception:
                results["errors"].append(
                    f"downgrade to base: {short(exception)}"
                )
    write_report(results, len(revisions))


def write_report(results, total):
    os.makedirs(".audit", exist_ok=True)
    stamp = datetime.date.today().isoformat()
    base = os.path.join(".audit", f"migration-replay-{stamp}")
    with open(f"{base}.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    lying = [s for s in results["steps"] if s.get("downgrade_diff")]
    unstable = [s for s in results["steps"] if s.get("reupgrade_diff")]
    failed = [s for s in results["steps"] if s.get("error")]
    skipped = [s for s in results["steps"] if s.get("skipped")]
    lines = [
        f"# Migration replay audit, {stamp}",
        "",
        f"{len(results['steps'])}/{total} migrations replayed on "
        f"`{DATABASE}`: from the parent, upgrade, downgrade, upgrade "
        f"again. Skipped: {', '.join(s['revision'] for s in skipped) or 'none'}"
        " (merge revisions).",
        "",
        f"## Failed ({len(failed)})",
        "",
    ]
    for step in failed:
        lines += [f"- `{step['revision']}` {step['doc']}: {step['error']}"]
    lines += ["", f"## Downgrades that lie ({len(lying)})", ""]
    for step in lying:
        lines.append(f"- `{step['revision']}` {step['doc']}")
        lines += [f"  - {change}" for change in step["downgrade_diff"]]
    lines += ["", f"## Upgrade not repeatable ({len(unstable)})", ""]
    for step in unstable:
        lines.append(f"- `{step['revision']}` {step['doc']}")
        lines += [f"  - {change}" for change in step["reupgrade_diff"]]
    lines += [
        "",
        f"## Models vs schema at head ({len(results['head_drift'])})",
        "",
    ]
    lines += [f"- {change}" for change in results["head_drift"]]
    lines += [
        "",
        f"## Left after downgrade to base ({len(results['base_left'])})",
        "",
    ]
    lines += [f"- {item}" for item in results["base_left"]]
    lines += [f"- error: {e}" for e in results["errors"] if " " in e]
    with open(f"{base}.md", "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Report: {base}.md")


if __name__ == "__main__":
    main()
