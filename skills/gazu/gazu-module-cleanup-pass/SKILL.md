---
name: gazu-module-cleanup-pass
description: Use when asked to re-read, clean up or simplify gazu code (gazu/<entity>.py modules, client.py, aio.py, helpers) that was just written or heavily changed ("relis le module", "clean", "simplifie", "passe de nettoyage", "cleanup pass"), typically after adding wrappers, a series of fixes, or before opening a PR.
---

# Gazu module cleanup pass

## Overview

Re-read recently changed gazu code and make it smaller and more
conventional **without changing what it does**. Every public function of
gazu is an API that studio scripts call: a name, a parameter, a default or
a return shape that moves breaks code you will never see. Report those,
never apply them silently.

## Scope

1. Perimeter, in this order: files named by the user, else commits named by
   the user, else `git diff origin/main...HEAD --stat` plus the working
   tree, limited to `gazu/`.
2. Every file in the perimeter is reviewed in full, with its test file
   `tests/test_<module>.py`. Carried-over code is in scope: tag its
   findings `(pre-existing)`.
3. Read `git diff` for each file to tell new code from carried-over code.
   Other modules are out of scope even when a finding points at them:
   mention them in the report.

## Checklist

Walk each file top to bottom against these, in order. Apply what is a pure
cleanup; list the rest.

**Dead code**
- Private helpers (`_name`) nobody calls, imports and locals nobody reads.
- Public functions are never dead: users call them. An unused public
  function is at most a deprecation proposal.

**Wrapper conventions** (`CLAUDE.md`, `add-wrapper` skill)
- Verb set: `all_*` / `get_*` / `get_*_by_name` / `new_*` / `update_*` /
  `remove_*`, plus helpers. No new prefix.
- `client: KitsuClient = default` is the last keyword argument of every
  function that reaches the API, and is passed down to every `raw.*` call
  (a call without `client=client` silently hits the default instance: a
  real bug, list it and fix it only if the user agrees).
- Entity inputs go through `normalize_model_parameter`, so an id and a dict
  both work.
- `@cache` only on read functions (`all_*`, `get_*`), never on writes.
- HTTP only through `raw.fetch_all` / `fetch_one` / `fetch_first` /
  `get` / `post` / `put` / `delete` / `upload` / `download`, never
  `requests` directly.
- Lists sorted with `sort_by_name` where the neighbours do it.
- Google-style docstrings (`Args:` / `Returns:`) on every public function,
  matching the actual parameters and return type.
- Type hints with `from __future__ import annotations` at the top.

**Compatibility** (gazu targets Python 3.7+)
- A "simplification" must run on 3.7: no walrus `:=`, no positional-only
  `/`, no `match`, no `str.removeprefix`, no `dict | dict`, no
  `functools.cache`, no parenthesized context managers. PEP 604 unions
  only in annotations (thanks to `__future__`), never at runtime
  (`isinstance(x, str | dict)`).

**Sync and async**
- A low-level primitive changed in `client.py` has its twin in `aio.py`
  (and the reverse). A drift is a finding.

**Python style**
- f-strings for paths (`f"data/projects/{project['id']}/assets"`).
- Imperative loops that are a comprehension, `any`/`all` or a dict build.
- Helpers return new values, arguments are never mutated (a dict passed by
  the user stays untouched).
- Comments that restate the code: delete. Comments that explain a
  non-obvious why: keep.

## Cleanup versus behavior change

| Looks like cleanup, is a behavior change | Do instead |
|---|---|
| Renaming a public function, a parameter or changing a default | Out of scope: user scripts break. Propose a deprecation alias at most |
| Changing a route path or an HTTP method | Report it, check it against zou (`tests/test_zou_routes.py`) |
| Adding or removing `@cache` | Report it: users get stale or fresh data |
| Removing or adding `sort_by_name` | Report it: result order changes |
| Returning `None` instead of raising, or the reverse | Report it |
| Building the request body differently (keys, `None` values sent or dropped) | Report it: zou may read the missing key as a reset |

Rule: if a test, a user script or a zou request log could tell the before
from the after, it is not cleanup.

## Verify

On every touched file, before reporting:

```bash
black --check <files>
py.test tests/test_<module>.py tests/test_zou_routes.py -q
```

A passing mocked test proves nothing about the route: the contract gate
(`tests/test_zou_routes.py`) does.

## Report

Three lists, in this order, one line per item with `file:line`, and
`(pre-existing)` when the code predates the diff:

1. **Applied**: cleanups done, grouped by file.
2. **Proposed**: behavior changes worth making, each with the observable
   difference for a user script.
3. **Checked, unchanged**: what was reviewed and found conventional.

Do not commit. The user tests first and asks for the commit.
