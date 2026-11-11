---
name: zou-blueprint-cleanup-pass
description: Use when asked to re-read, clean up or simplify zou blueprint code (resources.py, schemas.py, routes __init__.py, openapi.yml, crud/*.py) that was just written or heavily changed ("relis le blueprint", "clean", "simplifie", "passe de nettoyage", "cleanup pass"), typically after a series of new routes, a migration to Pydantic, or before opening a PR.
---

# Zou blueprint cleanup pass

## Overview

Re-read recently changed blueprint code and make it smaller and more
conventional **without changing what it does**. In zou, a blueprint change
is almost always a behavior change for someone (status code, permission,
response shape, OpenAPI contract): when in doubt, report it, never apply it
silently.

## Scope

1. Perimeter, in this order: files named by the user, else commits named by
   the user, else `git diff origin/main...HEAD --stat` plus the working
   tree, limited to `zou/app/blueprints/`.
2. Every file in the perimeter is reviewed in full, with its sibling
   `schemas.py`, `openapi.yml` and `__init__.py`. Carried-over code is in
   scope: tag its findings `(pre-existing)`.
3. Read `git diff` for each file to tell new code from carried-over code.
   Services, utils and models are out of scope even when a finding points
   at them: mention them in the report (see `zou-service-cleanup-pass`,
   `zou-util-cleanup-pass`).

## Checklist

Walk each file top to bottom against these, in order. Apply what is a pure
cleanup; list the rest.

**Dead code**
- Resource classes not listed in the `routes` of `__init__.py`, routes
  pointing at a missing class, schemas no resource validates.
- `openapi.yml` entries no `swag_from(SPECS[...])` reads, and the reverse.
- Imports, `ArgsMixin` parents and locals nobody uses.

**Layering** (`CLAUDE.md`, Services)
- A resource never builds an ORM query, calls a model (`Task.get`,
  `.query`) or touches `db.session`: list it, with the service function it
  should call.
- Business logic (loops over rows, computations) belongs in a service;
  caller-dependent shaping (role-based serialization, vendor filtering)
  stays in the resource.
- Every `<x>_service.<name>()` called must exist
  (`tests/misc/test_route_service_calls.py` checks it).

**Resource conventions**
- Plain `MethodView` (+ `ArgsMixin` only when query parameters are read).
- Decorator order as in the surrounding file: `@jwt_required()`, then the
  permission decorator, then `@swag_from(SPECS[...])`.
- Request bodies through `validation.validate_request_body(Schema)`, never
  `request.json` read by hand. Query parameters through `ArgsMixin`
  (`get_text_parameter`, `get_bool_parameter`…).
- Path ids checked (`self.check_id_parameter`) like the neighbour routes.
- Status codes explicit (`return result, 201`).

**Schemas** (Pydantic v2)
- `BaseSchema` subclasses, `Field(...)` for required fields,
  `Optional[X] = None` for optional ones.
- A cross-field check raised in the resource or service belongs in a
  `@model_validator(mode="after")`; repeated `Field` constraints become a
  shared `Annotated` type. Moving a check changes the error message: list
  it unless the message is identical.

**Python style** (`CLAUDE.md`)
- f-strings in new or edited lines; imports sorted inside parenthesized
  blocks; `"""` on their own lines; no parentheses around returned tuples;
  no leading underscore on a name another module uses.
- Comments that restate the code: delete. Comments that explain a
  non-obvious why: keep.

## Cleanup versus behavior change

| Looks like cleanup, is a behavior change | Do instead |
|---|---|
| Reordering a permission check before or after `check_project_access` | Report it: the project role is resolved by that call (`CLAUDE.md`, Permissions) |
| Merging two routes' guards, or a list and a single route that serve the same data | Report it: one data path, one policy |
| Replacing a `has_*` boolean with a `check_*` call | Report it: the status code or the branch changes |
| Changing a status code, a response key, a schema field, a route path | Out of scope |
| Moving a validation from the service into the schema | Report it unless the error message stays the same |
| Editing `openapi.yml` beyond removing an unused entry | Report it: `tests/misc/test_openapi_*` and the docs read it |

Rule: if a test, a client (kitsu, gazu) or the OpenAPI spec could tell the
before from the after, it is not cleanup.

## Verify

On every touched file, before reporting:

```bash
pre-commit run --files <files>
DB_DATABASE=zoudb-test python -m pytest tests/blueprints/<matching dir> tests/misc -q
```

Use the project's virtualenv (see `CLAUDE.local.md`).

## Report

Three lists, in this order, one line per item with `file:line`, and
`(pre-existing)` when the code predates the diff:

1. **Applied**: cleanups done, grouped by file.
2. **Proposed**: behavior changes worth making, each with the observable
   difference (status code, response, permission).
3. **Checked, unchanged**: what was reviewed and found conventional.

Do not commit. The user tests first and asks for the commit.
