---
name: sentry-triage
description: Triage a Sentry issue for zou, from stacktrace to root cause, minimal fix and regression test. Stops before committing.
disable-model-invocation: true
---

# Sentry triage (zou)

Use this skill to investigate a production error or performance issue reported in Sentry and turn it into a reviewed fix.

## Inputs

Ask the user for the Sentry issue (URL, short ID, or a description to search for). If given a description, use the Sentry MCP tools (`search_issues`) to locate it. Load the MCP tool schemas via ToolSearch first if needed.

## Workflow

1. **Fetch the issue**: `get_sentry_resource` for the full event: stacktrace, culprit, tags (endpoint, user role), frequency, first/last seen. For gnarly ones, `analyze_issue_with_seer` can give a head start; treat its output as a hypothesis, not a conclusion.
2. **Map to code**: locate the frames inside `zou/app/`. Read the involved resource, service and model code fully before theorizing. Note the request context from tags (route, method) and find the matching blueprint.
3. **Root cause**: follow the systematic-debugging skill. Reproduce the failing condition mentally against the code path; check recent git history of the involved files (`git log -p --follow`) for the commit that introduced it. Common zou classes of failure worth checking early:
   - stale cache reads (`@cache.memoize_function` without matching `delete_memoized`)
   - `ObjectDeletedError` / race on concurrent delete
   - permission checks raising on edge-case roles
   - N+1 or unindexed queries for performance issues
4. **Minimal fix**: smallest change that removes the failure mode, following repo conventions (f-strings, domain exceptions from `services/exception.py`, 400 + message over bare 500).
5. **Regression test**: add a test in the matching `tests/` package inheriting `ApiDBTestCase`, using the fixture generators to recreate the failing state. The test must fail without the fix. Run it:
   ```bash
   DB_DATABASE=zoudb-test ~/.virtualenvs/zou/bin/python -m pytest tests/<path> -v
   ```
6. **Report and stop**: present root cause, the diff, and the test result. **Do not commit.** The user tests first and asks for the commit explicitly (one bug = one commit, `[domain] Imperative description`). Reference the Sentry issue short ID in the commit message body when the user does.

## Performance issues

For slow-transaction or N+1 issues rather than errors: pull the transaction spans via `search_events`, identify the dominant span, and check `EXPLAIN` via the postgres MCP tool against a realistic dataset before proposing an index or query change. An index proposal means a migration: run the migration-reviewer agent on it.

## Rules

- Never mark the Sentry issue resolved or assign it; only report. The user handles Sentry state after deploy.
- If the stacktrace points at a dependency rather than zou code, say so and stop: upgrading a dependency is a separate decision.
- If several Sentry issues share the root cause, list them so one fix can close all, but keep the fix scoped to one root cause.
