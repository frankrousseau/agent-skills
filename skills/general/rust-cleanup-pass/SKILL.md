---
name: rust-cleanup-pass
description: Use when asked to re-read, clean up or simplify Rust code that was just written or heavily changed ("relis le Rust", "clean", "simplifie", "passe de nettoyage", "cleanup pass"), typically after a series of additions, a new Tauri command, or before opening a PR.
---

# Rust cleanup pass

## Overview

Re-read recently changed Rust code and make it smaller and more
conventional **without changing what it does**. Behavior changes are
reported, never applied silently. In a Tauri app, a name or a field that
looks internal is often read by the JS side, a plugin or another process:
treat every serialized name as a contract.

## Scope

1. Perimeter, in this order: files named by the user, else commits named by
   the user, else `git diff origin/main...HEAD --stat` plus the working
   tree, limited to `*.rs` and the `Cargo.toml` files.
2. Every file in the perimeter is reviewed in full, its `#[cfg(test)]`
   module included. Carried-over code is in scope: tag its findings
   `(pre-existing)`.
3. Read `git diff` for each file to tell new code from carried-over code.
   Files outside the perimeter are out of scope: mention them in the
   report.
4. Read the project rules first: `CLAUDE.md`, `[workspace.lints]` in
   `Cargo.toml`, `clippy.toml`, `rustfmt.toml`. The project rules win over
   this checklist.

## Checklist

Walk each file top to bottom against these, in order. Apply what is a pure
cleanup; list the rest.

**Dead code**
- Items, imports, fields, enum variants and `pub` items nobody uses (grep
  the workspace and the JS side for command names).
- A `Result` return type on a function that cannot fail: list it if the
  function is a command or a public API, apply it otherwise.
- Leftover debug: `dbg!`, `println!`, `eprintln!`, temporary `#[ignore]`
  tests, commented-out code.

**Layout**
- Domain logic in domain modules, which do not import `tauri`. A command
  only validates its arguments, calls a domain function and converts the
  result. Logic inside a command is a finding.
- `mod.rs` holds only `mod` and `use` lines.
- A type sits right before its `impl` blocks. Public items come before the
  private helpers. Module constants at the top, each with a doc comment
  that explains the value.
- Keep the visibility style of the crate: do not churn `pub` into
  `pub(crate)` in private modules.

**Errors**
- One `thiserror` enum per domain; no `anyhow`, no `Result<T, String>`,
  no `map_err(|e| e.to_string())`.
- Variant fields: `reason` for a text, `source` for a wrapped error.
- Messages: lowercase, "cannot ...", without secrets or absolute user
  paths.
- No `unwrap`, `expect`, `panic!`, `todo!`, `unimplemented!` outside tests,
  `build.rs` and the app `run()`. Use `?`, `ok_or(...)?`, `let ... else`.
- An exception is `#[expect(lint, reason = "...")]`, never `#[allow]`.
- `let _ = ...;` always has a comment that gives the reason.

**Style** (what rustfmt does not enforce)
- Imports in 3 blocks: `std`, external crates, `crate`/`super`/`self`. No
  `*` import except `use super::*` in tests. Do not import enum variants.
- Inline format args: `format!("{path}")`.
- `Self` in impls; field-init shorthand; `.collect()` not `from_iter`;
  `Vec::new()` not `vec![]`; no `let x;` without a value.
- One `#[derive]`, ordered: `Copy`, then std traits A to Z, then the other
  traits A to Z. No `Debug` on a type that holds a secret.
- Names: one name per concept, no type in a name (`path`, not `path_str`),
  booleans as `is_*` / `has_*`, one-letter generic parameters, `Foo<'_>`.
- Iterator chains over index juggling (`remove(1)`, manual counters).
- A duplicated block (two copies of the same `format!` and parse) becomes
  one helper. Do not replace two clear copies with a macro.
- `checked_*` / `saturating_*` on values that come from outside (headers,
  arguments, sizes).
- Paths with `Path` / `PathBuf` and `join`, never string concatenation.
- `std::process::Command` with separate arguments, never a shell string.
- `log::info!` / `warn!` / `error!`, never a token, a password or file
  contents in a log.

**Docs and comments**
- `//!` header in each file. The first doc sentence says when to use the
  item, 2 lines maximum.
- Comments give the reason only (a library limit, an order, a data
  format). Delete comments that restate the code.
- Keep `// shortcut: <limit>, <when to change>` comments and `// SAFETY:`
  comments.
- If the project writes in ASD-STE100, keep to it (`python-check-docstrings-and-comments`
  has the rules).

**Async and state** (report, see the table below)
- A `std::sync::Mutex` guard held across `.await`.
- Blocking file system or CPU work in an async command without
  `spawn_blocking`.
- Shared state through globals instead of `app.manage` and `State`.

## Cleanup versus behavior change

| Looks like cleanup, is a behavior change | Do instead |
|---|---|
| Renaming a `#[tauri::command]`, one of its parameters, or turning parameters into a struct | Out of scope: the JS `invoke` keys, `build.rs` `COMMANDS`, `generate_handler!`, permissions and capabilities all depend on it |
| Changing `#[serde(...)]` attributes, field names, or the `kind()` strings of an error | Out of scope: the frontend and its i18n keys read them. Rewording `message` is safe |
| Renaming an event name or its payload | Out of scope |
| Changing a key of a file another process reads (session files, plugin configs), a keychain service or account name | Out of scope: users lose data or sessions |
| Removing a check that looks redundant (lexical and canonical path checks, header allowlists, size limits) | Report it: each one closes a different attack |
| Removing `let _ = child.wait()` or another "useless" call | Read `git log -S` first: it may reap a process or flush a state |
| Holding a lock instead of cloning a value out of it | Report it: the clone releases the lock before slow work |
| Changing the order of side effects (state set before a directory is made) | Report it |
| Switching sync to async or the reverse, or `+` to `saturating_add` on a value the code relies on to overflow-check | Report it |
| Adding or removing a crate feature | Report it: TLS, cookies or the runtime change |

Rule: if a test, the frontend, another process or a user's stored data
could tell the before from the after, it is not cleanup.

## Verify

At the workspace root, on every pass:

```bash
cargo fmt --all --check
cargo clippy --workspace --all-targets -- -D warnings
cargo test --workspace
```

If cargo is not on `PATH`, `source ~/.cargo/env` first. If a command
proxy rewrites shell output, run cargo through the raw command. When a
change touches a command, a serde type or an event, also run the JS unit
tests and the end-to-end tests: a passing Rust unit test does not prove
the app works.

## Report

Three lists, in this order, one line per item with `file:line`, and
`(pre-existing)` when the code predates the diff:

1. **Applied**: cleanups done, grouped by file.
2. **Proposed**: behavior changes worth making, each with the observable
   difference.
3. **Checked, unchanged**: what was reviewed and found conventional.

Do not commit unless the project rules say so. Never use `git stash`,
`git reset --hard` or `git checkout --` on the user's tree: it may hold
work in progress.
