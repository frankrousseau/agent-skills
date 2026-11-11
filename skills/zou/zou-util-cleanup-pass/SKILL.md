---
name: zou-util-cleanup-pass
description: Use when asked to re-read, clean up or simplify zou utility code (zou/app/utils/*.py) that was just written or heavily changed ("relis les utils", "clean", "simplifie", "passe de nettoyage", "cleanup pass"), typically after adding a helper, moving code out of a service, or before opening a PR.
---

# Zou util cleanup pass

## Overview

Re-read recently changed utility code and make it smaller and more
conventional **without changing what it does**. Utils are imported
everywhere (services, blueprints, CLI, plugins): a signature or a return
value that moves breaks callers far away. Report those, never apply them
silently.

## Scope

1. Perimeter, in this order: files named by the user, else commits named by
   the user, else `git diff origin/main...HEAD --stat` plus the working
   tree, limited to `zou/app/utils/`.
2. Every file in the perimeter is reviewed in full, with its test file
   `tests/utils/test_<x>.py`. Carried-over code is in scope: tag its
   findings `(pre-existing)`.
3. Read `git diff` for each file to tell new code from carried-over code.
   Services and blueprints are out of scope even when a finding points at
   them: mention them in the report (see `zou-service-cleanup-pass`,
   `zou-blueprint-cleanup-pass`).

## Checklist

Walk each file top to bottom against these, in order. Apply what is a pure
cleanup; list the rest.

**Dead code**
- Functions nobody calls: grep the name across `zou/`, `tests/`, `zou/cli.py`
  and `zou/remote/`. Utils are a public surface for plugins: list unused
  public functions, do not delete them.
- Imports, locals, parameters and constants nobody reads.

**Where the code belongs**
- A util stays free of business rules and of database access: a query or a
  model import in `utils/` belongs in a service. List it.
- A util must not import from `zou.app.services` (import cycles, layering).
- A helper duplicated in two utils, or reimplementing the standard library
  (`os.path`, `itertools`, `datetime`, `secrets`, `hmac`), is a finding:
  replace it when the result is identical on every input.

**Security-sensitive utils** (`CLAUDE.md`, Security review rules)
- `fs.py` and anything building paths: no client string joined onto a
  path; `os.path.join` keeps `..` and drops the prefix on an absolute
  second argument.
- `email_i18n.py`, `emails.py`: values from requests are escaped before
  `str.format()` on HTML templates.
- `auth.py`, `permissions.py`, `socket_auth.py`, `oidc.py`, `saml.py`,
  `fido.py`: constant-time comparisons for secrets, no secret in logs
  (`string.mask_secret`). Any finding here is reported, never applied.

**Python style** (`CLAUDE.md`)
- f-strings in new or edited lines; imports sorted inside parenthesized
  blocks; `"""` on their own lines; no parentheses around returned tuples;
  no leading underscore on a name another module uses.
- Imperative loops that are a comprehension, `any`/`all` or a dict build.
- Helpers return new values, arguments are never mutated.
- Comments that restate the code: delete. Comments that explain a
  non-obvious why: keep.

## Cleanup versus behavior change

| Looks like cleanup, is a behavior change | Do instead |
|---|---|
| Changing a signature, a default argument or a return type | Report it: callers in services, CLI and plugins |
| Swapping a helper for a stdlib call that differs on an edge case (`None`, empty string, timezone, trailing slash) | Read the tests and callers first, report if any edge differs |
| Touching `permissions.py`, `auth.py` or `cache.py` logic | Report it |
| Changing a log message or level in `monitoring.py` | Report it: alerts may match on it |
| Renaming a public function | Out of scope |

Rule: if a test, a caller or a log reader could tell the before from the
after, it is not cleanup.

## Verify

On every touched file, before reporting:

```bash
pre-commit run --files <files>
DB_DATABASE=zoudb-test python -m pytest tests/utils/test_<x>.py -q
```

Use the project's virtualenv (see `CLAUDE.local.md`). Grep the callers of
every function you touched and run their tests too.

## Report

Three lists, in this order, one line per item with `file:line`, and
`(pre-existing)` when the code predates the diff:

1. **Applied**: cleanups done, grouped by file.
2. **Proposed**: behavior changes worth making, each with the observable
   difference.
3. **Checked, unchanged**: what was reviewed and found conventional.

Do not commit. The user tests first and asks for the commit.
