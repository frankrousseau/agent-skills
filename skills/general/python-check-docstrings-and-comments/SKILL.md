---
name: python-check-docstrings-and-comments
description: Use when asked to check that the docstrings of Python code match what the code does, that the inline comments are useful, and that both are written in ASD-STE100 Simplified Technical English ("vérifie les docstrings", "relis les commentaires", "docstrings à jour ?", "check docstrings", "STE", "ASD-STE100"). Typically on a diff before a PR, or on one module.
---

# Python docstrings and comments check

Three questions, for each docstring and comment in the perimeter:

1. Does it say what the code does now?
2. Is it useful to a reader of the code?
3. Is it written in ASD-STE100 Simplified Technical English?

Only text changes. If a code change looks necessary (a docstring describes
the right behavior and the code does not), report it, do not apply it.

## Scope

1. Perimeter, in this order: files named by the user, else commits named by
   the user, else `git diff origin/main...HEAD --stat` plus the working
   tree, limited to `*.py`.
2. In each file, check every docstring and comment, carried-over ones
   included: tag their findings `(pre-existing)`. On a large carried-over
   file, ask before rewriting all of it.
3. Read the project's conventions first (`CLAUDE.md`, linter config):
   docstring format (Google `Args:`, NumPy, reST, plain), the position of
   the `"""` quotes, the mood of the first line. The project format wins
   over this skill. STE applies to the words, not to the layout.

## 1. Docstrings match the code

Run the mechanical check first:

```bash
python ~/.claude/skills/python-check-docstrings-and-comments/scripts/check_docstrings.py \
    [--ignore client] <files or directories>
```

It reports parameters documented but not in the signature, parameters not
documented in a docstring that has a parameter section, and a `Returns`
section on a function that returns nothing. Use `--ignore` for parameters
the project never documents on purpose (gazu: `client`). Exit code 1 means
findings.

Then read each function against its docstring. The script cannot see
these:

- The summary describes what the function did before a change (another
  return value, another side effect, a removed branch).
- Types in the docstring differ from the annotations or the real values
  (`dict` vs ORM object, `str` vs `UUID`, `list` vs generator).
- Default values written in the text differ from the signature.
- `Raises:` names an exception that is not raised any more, or omits one
  the function raises itself.
- Side effects not stated: database write, cache invalidation, event,
  file write, network call, mutation of an argument.
- Class and module docstrings that describe attributes or functions that
  no longer exist.

A public function without a docstring, where the neighbours have one, is a
finding. A private helper with an obvious name does not need one.

## 2. Inline comments are useful

Keep a comment that says what the code cannot say:

- why the code is like this (a constraint, a bug in a dependency, a
  performance reason, a decision);
- an invariant or a precondition the reader must not break;
- a warning (order of calls, thread safety, security);
- units, formats and references (issue number, RFC, spec section);
- a `shortcut:` comment that records a known limit.

Remove or rewrite:

| Comment | Do |
|---|---|
| Says again what the next line does (`# increment i`) | Delete |
| Contradicts the code (stale) | Rewrite to match, or delete |
| Code in comments | Delete (git keeps the history) |
| History ("changed by X", "before we used Y") | Delete, it belongs to the commit message |
| `TODO` / `FIXME` without an issue or a reason | Report it, do not delete |
| A long comment that explains a hard block | Propose a better name or a small function only in the report |

## 3. ASD-STE100 rules

Write docstrings and comments in English, with the STE rules that apply
to short technical text. Code identifiers, type names and product names
are technical names: keep them as they are, in backticks if the project
does so.

**Words**
- Use simple, common words, with one meaning each. Use the same word for
  the same thing everywhere in the module.
- Use these words, not the words in parentheses: make sure (ensure),
  use (utilize, leverage), before (prior to), after (following,
  subsequent to), to (in order to), get (obtain, retrieve, fetch when it
  is not a technical name), start (initiate, commence), stop (terminate),
  enough (sufficient), about (approximately), more or other (additional),
  help (facilitate), show (indicate, display when it is not a technical
  name), with or through (via).
- No phrasal verbs (set up, carry out, look up, find out, figure out):
  use one verb (configure, do, find, examine).
- No slang, jargon or contractions (`don't`, `it's`).

**Verbs**
- Active voice: "The function deletes the task", not "The task is deleted
  by the function".
- Simple tenses only: present, past, future. No `-ing` form as a verb
  ("Returns the tasks, sorting them by name" becomes "Sorts the tasks by
  name and returns them").
- Instructions (what the caller must do) use the imperative: "Call
  `open()` first."

**Sentences**
- Descriptive sentences: 25 words maximum. Instructions: 20 words maximum.
  One instruction per sentence.
- Do not omit articles and verbs to make text short: "Returns the task or
  None", not "Task or None".
- Noun clusters: 3 words maximum. "The status of the preview file
  upload", not "preview file upload status".
- Put a condition first: "If the task does not exist, raises
  `TaskNotFoundException`."
- Use vertical lists for 3 items or more, or for steps.
- Warnings start with the command: "Do not call this inside a memoized
  function. The cache keys on the arguments only."

## Machine-read docstrings

Some docstrings are not only for humans. Report changes to these, do not
apply them without the user's agreement:

- doctest examples (`>>>`): a change changes a test;
- click or argparse commands: the docstring is the `--help` text;
- docstrings that OpenAPI, Sphinx or a plugin system read (check how the
  project builds its docs).

## Verify

```bash
python ~/.claude/skills/python-check-docstrings-and-comments/scripts/check_docstrings.py <files>
<the project's formatter and linter on the touched files>
```

If the project runs doctests, run them on the touched modules.

## Report

Three lists, in this order, one line per item with `file:line`, and
`(pre-existing)` when the text predates the diff:

1. **Applied**: docstrings and comments rewritten or deleted, grouped by
   file.
2. **Proposed**: code changes the check revealed, and changes to
   machine-read docstrings.
3. **Checked, unchanged**: what was correct already.

Do not commit. The user reads the result and asks for the commit.
