---
name: elixir-cleanup-pass
description: Use when asked to re-read, clean up or simplify Elixir code that was just written or heavily changed ("relis l'Elixir", "clean", "simplifie", "passe de nettoyage", "cleanup pass", "tidy against the style rules"), typically after a series of additions, a new connector or context function, or before opening a PR.
---

# Elixir cleanup pass

## Overview

Re-read recently changed Elixir code and make it smaller and more
conventional **without changing what it does**. Behavior changes are
reported, never applied silently. In a Phoenix API, JSON keys, status
codes, PubSub topics, channel events and stored strings are contracts with
a frontend or with data on disk: treat them as such.

## Scope

1. Perimeter, in this order: files named by the user, else commits named by
   the user, else `git diff origin/main...HEAD --stat` plus the working
   tree, limited to `*.ex` and `*.exs`.
2. Every file in the perimeter is reviewed in full, with its test file.
   Carried-over code is in scope: tag its findings `(pre-existing)`.
3. Read `git diff` for each file to tell new code from carried-over code.
   Files outside the perimeter are out of scope: mention them in the
   report.
4. Read the project rules first: `AGENTS.md`, `CLAUDE.md`,
   `.formatter.exs`, the `mix.exs` aliases, and any open audit checklist in
   `.audit/`. The project rules win over this checklist. Run only the
   tools the project has (no Credo or Dialyzer if they are not deps).

## Checklist

Walk each file top to bottom against these, in order. Apply what is a pure
cleanup; list the rest.

**Dead code**
- Private functions, aliases, imports, module attributes and bindings
  nobody uses (`mix compile --warnings-as-errors` finds most of them).
- Public context functions nobody calls: grep `lib/`, `test/` and the
  frontend, then list them. Behaviour callbacks that look unused: list,
  never delete.
- Generator leftovers (comments about a database or a layer the project
  does not use), stale comments.

**Layering**
- Controllers and channels call contexts only: no `Repo.`, no
  `import Ecto.Query` in the web layer. A query in a controller is a
  finding.
- Every query on user data is scoped by the user (`user_id`): a missing
  scope is a security finding, report it.
- Specialised data goes through its own context when the project has one
  (for example notes, agent memory): a bypass is a finding.

**Module layout** (Elixir style guide, as the project applies it)
- `@moduledoc` right after `defmodule` (`@moduledoc false` if nothing to
  say). Then `@behaviour`, `use`, `import`, `require`, `alias`
  (alphabetical), module attributes, `defstruct`, `@type`, functions.
- `__MODULE__` for self-reference. An alias where a full module name is
  repeated.
- `@spec` right under `@doc`; main type named `t`. Do not add specs in
  bulk if the project does not.
- One module per file.

**Expressions**
- No single-pipe expressions (`x |> f()` becomes `f(x)`). A pipeline starts
  from a bare value, not a function call.
- `if` with `else`, never `unless ... else`. The last `cond` clause is
  `true ->`.
- Pattern matching in function heads over a `case` on the argument, when
  it reads better.
- `with` for chains of `{:ok, _}` steps, with an `else` that maps each
  error once.
- `Enum.flat_map` over `map |> filter |> map`, `Enum.reduce` over manual
  accumulation, no destructure-and-rebuild of the same map.
- Descriptive bindings, never one letter (`entry`, not `e`).
- Booleans end in `?`; `is_` only for guards. Exception modules end in
  `Error`, messages lowercase.
- Keyword literals, not lists of tuples. `defstruct` without brackets.
- No `String.to_atom` on input, no map access syntax on structs,
  `Enum.at` instead of `list[i]`.

**Duplicates**
- A helper copied in two modules goes to the shared module the project
  already has (a `Util` module, a `ChangesetHelpers` module, the single
  JSON serializer of a schema). Do not create a new shared module for one
  use.
- Atom-or-string key access reimplemented by hand
  (`Map.get(m, "x") || Map.get(m, :x)`): use the project helper.
- Repeated work: a lookup done twice, two retry ladders around the same
  call.

**Errors**
- Contexts return `{:ok, value}` / `{:error, changeset | atom}`.
- `{:ok, _} = fallible_call()` on a call that can fail at runtime is a
  crash: list it with the `case` that replaces it. Keep assertive matches
  where failure is impossible.
- Bang functions (`get_x!`) stay where the project uses them for 404s.

**Comments and docs**
- Comments give the reason only. Delete comments that restate the code.
- Annotations uppercase with a colon on the line above (`# TODO:`).
- Keep `# shortcut:` and `# ponytail:` comments: they record a deliberate
  limit.
- If the project writes in ASD-STE100 or bans em dashes, keep to it.

**Tests** (the test file of each changed module)
- `assert actual == expected`.
- No `Process.sleep`: `assert_receive`, `Process.monitor` and
  `start_supervised!` instead.
- HTTP stubbed the project's way (for example `Req.Test`), never a real
  call.
- `async: true` only where the database allows it (SQLite: concurrent
  writers collide).

## Cleanup versus behavior change

| Looks like cleanup, is a behavior change | Do instead |
|---|---|
| Changing a JSON key, the list envelope, an error shape (`error` vs `errors`), or a status code | Out of scope: the frontend and custom clients parse them |
| Renaming a PubSub topic, a channel event, an internal broadcast message, or emitting one broadcast per row instead of one per batch | Out of scope |
| Changing a stored string: a kind, a source, a connector id, a config key, a scope string, a token prefix | Out of scope: data on disk and tokens break |
| Editing an OpenAPI `operation` that a validation plug enforces | Report it: requests start or stop getting 422 |
| Changing a default (sort order, page size limits, date ranges) | Report it |
| Removing a `rescue` in a worker, a `restart:` option, or a cursor saved on error | Report it: a sync can stay stuck or loop |
| Editing an existing migration | Never: add a new one |
| Removing a legacy fallback (old data formats, old paths) | Report it: old records stop loading |
| Removing a guard that refuses an operation with a domain atom | Report it |
| Replacing `Repo.transaction(fn -> ... end)` with `Ecto.Multi` or the reverse | Report it, not a cleanup |

Rule: if a test, the frontend, a stored record or a running worker could
tell the before from the after, it is not cleanup.

## Verify

Fast loop while working, then the project gate:

```bash
mix compile --warnings-as-errors && mix format --check-formatted && mix test <test files>
mix precommit   # or the project's full check alias
```

If shell commands go through a proxy that rejects flags, use
`command git` / `command grep`.

## Report

Three lists, in this order, one line per item with `file:line`, and
`(pre-existing)` when the code predates the diff:

1. **Applied**: cleanups done, grouped by file.
2. **Proposed**: behavior changes worth making, each with the observable
   difference, and the audit item it closes if any.
3. **Checked, unchanged**: what was reviewed and found conventional.

Do not commit unless the user says so. Check `git status` first: other
sessions may have uncommitted work in the tree. Never `git reset --hard`
or `git stash` on the user's tree.
