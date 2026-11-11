---
name: zou-service-cleanup-pass
description: Use when asked to re-read, clean up or simplify zou service code (zou/app/services/*_service.py) that was just written or heavily changed ("relis le service", "clean", "simplifie", "passe de nettoyage", "cleanup pass"), typically after a long series of additions, a function moved between services, or before opening a PR.
---

# Zou service cleanup pass

## Overview

Re-read recently changed service code and make it smaller and more
conventional **without changing what it does**. Services hold the queries,
the cache and the events: a change in any of them is a behavior change.
Report those, never apply them silently.

## Scope

1. Perimeter, in this order: files named by the user, else commits named by
   the user, else `git diff origin/main...HEAD --stat` plus the working
   tree, limited to `zou/app/services/`.
2. Every file in the perimeter is reviewed in full, with its test file
   `tests/services/test_<x>_service.py`. Carried-over code is in scope: tag
   its findings `(pre-existing)`.
3. Read `git diff` for each file to tell new code from carried-over code.
   Blueprints and utils are out of scope even when a finding points at
   them: mention them in the report (see `zou-blueprint-cleanup-pass`,
   `zou-util-cleanup-pass`).

## Checklist

Walk each file top to bottom against these, in order. Apply what is a pure
cleanup; list the rest.

**Dead code**
- Functions nobody calls: grep the name across `zou/`, `tests/`, plugins
  and the CLI (`zou/cli.py`, `zou/remote/`) before calling it dead. A
  public service function may be used by plugins: list it, do not delete.
- Imports, locals and parameters nobody reads.
- `get_x_raw()` / `get_x()` pairs where one side is unused.

**Service conventions** (`CLAUDE.md`, Services and Naming)
- Module-level functions, no classes. Verb-first names (`get_`, `create_`,
  `update_`, `remove_`). `get_x_raw()` returns the ORM object, `get_x()`
  the serialized dict.
- Domain exceptions from `zou/app/exceptions.py`, never a bare
  `Exception`, never a `None` the caller has to test when the neighbours
  raise `XNotFoundException`.
- No leading underscore on a function another module calls
  (`other_service._helper()`): make it public.
- Imports between services at module level; a deferred import inside a
  function needs a one-line reason (circular import),
  `tests/misc/test_service_imports.py` checks them.
- One service, one test file: a function that moves takes its tests along.

**Cache and events**
- Every `@cache.memoize_function` getter has a matching
  `cache.cache.delete_memoized(...)` in each mutation of the same rows:
  a missing one is a finding (list it, run the
  `cache-invalidation-reviewer` agent if available).
- No caller-dependent filter (`g.project_role`, `get_current_user()`)
  inside a memoized function: the cache keys on arguments only. List it.
- Every mutation emits `events.emit("<table>:<action>", ...,
  project_id=...)` like its neighbours.

**Queries**
- A loop that runs a query per row (N+1): list it with the single query
  that replaces it.
- `.all()` followed by a Python filter that the query could do: list it.
- Duplicate query-building blocks across functions: extract one helper
  if the result is identical.

**Python style** (`CLAUDE.md`)
- f-strings in new or edited lines; imports sorted inside parenthesized
  blocks; `"""` on their own lines; no parentheses around returned tuples.
- Imperative loops that are a comprehension, `any`/`all` or a dict build.
- Helpers return new values, arguments are never mutated.
- Comments that restate the code: delete. Comments that explain a
  non-obvious why: keep.

## Cleanup versus behavior change

| Looks like cleanup, is a behavior change | Do instead |
|---|---|
| Rewriting a query (join, filter order, `.first()` vs `.one()`, ordering) | Report it: result order and exceptions change |
| Adding, removing or moving a `delete_memoized` or a memoize TTL | Report it |
| Adding, renaming or removing an `events.emit` | Report it: kitsu and plugins listen (run `contract-audit` if available) |
| Returning `get_x()` instead of `get_x_raw()`, or the reverse | Report it: callers get a dict instead of an ORM object |
| Raising instead of returning `None` | Report it: the route answers 404 instead of 200 |
| Renaming a public function | Out of scope: plugins and gazu-side scripts may import it |

Rule: if a test, a cached reader, an event listener or a plugin could tell
the before from the after, it is not cleanup.

## Verify

On every touched file, before reporting:

```bash
pre-commit run --files <files>
DB_DATABASE=zoudb-test python -m pytest tests/services/test_<x>_service.py tests/misc -q
```

Use the project's virtualenv (see `CLAUDE.local.md`). If the service is
reached by routes you know, run their blueprint tests too.

## Report

Three lists, in this order, one line per item with `file:line`, and
`(pre-existing)` when the code predates the diff:

1. **Applied**: cleanups done, grouped by file.
2. **Proposed**: behavior changes worth making, each with the observable
   difference (query result, cache, event, exception).
3. **Checked, unchanged**: what was reviewed and found conventional.

Do not commit. The user tests first and asks for the commit.
