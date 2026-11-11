---
name: python-check-tests
description: Use when asked to check the tests of a Python file ("vérifie les tests de ce fichier", "les tests sont bons ?", "couverture de X", "tests inutiles", "trop de tests", "check tests", "test review"). For one .py source file: is its behavior covered, which tests are useless, which tests are over-zealous. Read-only report, then fixes only on request.
---

# Python tests check

For one source file, answer three questions:

1. **Coverage**: is every behavior that matters tested, with an assertion
   on its result?
2. **Useless tests**: which tests prove nothing, or prove the same thing
   twice?
3. **Zeal**: which tests do more than the behavior needs, and so cost
   time and break on every refactor?

Read-only until the user chooses what to fix. The goal is not 100 %: it
is a test for each behavior a user or a caller depends on, and nothing
more.

## 1. Find the tests

- Read the project conventions (`CLAUDE.md`, `pytest.ini`,
  `pyproject.toml`, `conftest.py`): test layout, base classes, how to run
  them (virtualenv, test database, environment variables).
- Find the tests of the file: the conventional path
  (`tests/test_<module>.py`, `tests/<package>/test_<module>.py`), then
  grep `tests/` for imports of the module and calls of its public
  functions. Note tests in other files that reach the code through a
  higher layer (a route test that goes through a service).
- If no test exists, say so, and go to step 3 with an empty list.

## 2. Measure

Run the tests of the file with branch coverage, limited to the file:

```bash
python -m pytest <test files> --cov=<dotted.module> --cov-branch --cov-report=term-missing -q
# without pytest-cov:
python -m coverage run --branch -m pytest <test files> -q
python -m coverage report -m --include=<path/to/file.py>
```

Do not install packages without asking. If the tests cannot run (no
virtualenv, no database), say so in the report and do a static review.
Note failing or skipped tests: they cover nothing.

Coverage only says a line ran. A line can run in a test that asserts
nothing about it. The next step checks the assertions.

## 3. Map behaviors to tests

List the behaviors of the file: for each public function or method, its
normal result, each branch, each error path, each side effect (database
write, event, cache invalidation, file, network), and the edge inputs it
handles on purpose (empty, `None`, zero, limit, unicode, duplicate).

For each behavior, find the test that asserts it. Then rank what is
missing by risk:

1. **High**: error handling that prevents data loss, permissions and
   access checks, money, deletion, data migration, security checks,
   bugs fixed before (grep the git log for `fix` on the file: each fix
   needs a regression test).
2. **Medium**: branches a caller depends on, side effects other code
   reads (events, cache).
3. **Low**: logging, formatting of messages, trivial getters. Usually not
   worth a test: say so instead of proposing one.

## 4. Useless tests

A test is useless when it can pass with the behavior broken:

- No assertion, or only "it does not raise" on code that cannot raise.
- Tautology: the test mocks a function to return X, then asserts X.
- It tests the mock, the framework, the standard library or the ORM, not
  the code of the file.
- A duplicate: same path, same assertions as another test (different
  input values that take the same branch are duplicates too).
- It tests a function that no longer exists or a branch that cannot run.

For a doubtful test, check it: break the line it claims to cover (negate
a condition, return early), run the test, then restore the line with
`git diff` empty for that file. Do this only on a file with no
uncommitted changes. If the test still passes, it is useless.

## 5. Zeal

A test is over-zealous when it does more than its behavior needs:

- It asserts every field of a large result when one field is the
  behavior.
- It asserts private helpers, call counts, call order or internal state
  that a refactor changes without changing the behavior.
- It mocks so much that it tests the mocks (a mock of the code under
  test, or of a fast local dependency).
- It covers the same behavior again at each layer (service test, route
  test and end-to-end test for one branch): keep the cheapest layer that
  proves it, plus one test at the boundary.
- Many parametrized inputs that all take the same branch.
- It tests states the code prevents elsewhere (impossible inputs), or
  messages of log lines.
- Heavy setup: fixtures that build far more data than the test reads.
- It depends on time, order, network or `sleep`: flaky.

## Report

Start with the numbers: line and branch coverage of the file, number of
tests, run time, failing or skipped tests.

Then four lists, one line per item, with `test_file:line` or
`source_file:line`:

1. **Missing** (ranked high, medium, low): the behavior, why it matters,
   the test to add in one line.
2. **Useless**: the test, why it proves nothing, delete or rewrite.
3. **Zeal**: the test, what is too much, the simpler version.
4. **Good**: the tests that do their job, in one line, so the user knows
   what to keep.

End with the smallest set of changes that gives correct coverage. Ask
which items to apply. When you apply: follow the project's test patterns,
run the tests, make sure a new test fails without the code it covers,
and do not commit.
