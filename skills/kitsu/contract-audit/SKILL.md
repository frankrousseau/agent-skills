---
name: contract-audit
description: Use when the user asks for the cross-repo contract audit ("audit de contrat", "drift entre repos", "kitsu appelle des routes qui n'existent plus", "contract audit", "rejoue l'audit contrat"), and suggest it after renaming or removing zou routes or events, before a release, or after a large kitsu refactor of src/store/api. One-shot, writes a report to zou/.audit/, commits nothing.
---

# Cross-repo contract audit (zou ↔ kitsu, gazu, docs)

Builds the zou app to read its real `url_map` (no request, no DB query),
then checks what its consumers call and listen to. Covers what gazu's own
route gate (`gazu/tests/test_zou_routes.py`) does not: kitsu, the developer
docs, and events.

## Run

From the zou repo root, with `kitsu/`, `gazu/` and
`kitsu-developer-documentation/` next to it. Check out the branches you want
compared first (usually `main` everywhere).

```bash
SECRET_KEY=audit-only-key DB_DATABASE=zoudb-test CACHE_TYPE=simple \
    ~/.virtualenvs/zou/bin/python \
    ~/.claude/skills/contract-audit/scripts/contract_audit.py
```

`SECRET_KEY` is only there because zou refuses to start on the default one.
About 5 seconds. Writes `.audit/contract-<date>.md` and `.json`.

## What it reads

- **zou**: every rule of `url_map` with its methods; event names from the
  first argument of every `events.emit` (literals, and f-strings as
  wildcard patterns); generic CRUD events `<table>:new|update|delete`
  from the CRUD resources.
- **kitsu**: every `/api/...` literal in `src/` (`${...}` as a parameter,
  query string dropped), with the HTTP method when the literal sits right
  after `client.pget/ppost/pput/pdel(`; listeners from `socket.on('x:y')`
  and `socketEvents = { 'x:y': ... }` keys.
- **gazu**: paths from calls to its client helpers, with the `data/`
  prefix `fetch_*`, `create` and `update` add. Used only to know which zou
  routes have a caller.
- **docs**: route mentions in `docs/**/*.md` (`GET /data/...`,
  `/api/...`, `:id` and `{id}` as parameters).

## Read the report

| section | action |
|---------|--------|
| Kitsu calls a route zou does not have | real bug: fix kitsu or restore the route |
| Kitsu uses a method the zou route refuses | real bug |
| Kitsu listens to an event zou never emits | dead listener, or a renamed event |
| Docs mention a route / method zou does not have | fix the docs |
| Zou routes with no kitsu or gazu caller | candidates only: external scripts and the dynamic kitsu paths may use them |
| Zou events kitsu does not listen to | informational, gazu users and plugins listen too |
| Kitsu paths built dynamically | concatenations the audit cannot check; read them if a route was renamed |

To triage the "no caller" list, search each route's distinctive segments
(`extract-annotated-frame`, `shared-used`) across the whole workspace,
kitsu-client-js, plugins and ayon-kitsu included: most hits are paths
kitsu or gazu build dynamically. Only zero-hit routes are removal
candidates, and they still need a deprecation step for external scripts.

Before reporting a broken call, open the call site: a literal completed
later by concatenation is flagged as dynamic, but an unusual helper may
still slip through.

## Known limits

- An f-string event emitted with fully dynamic names (`f"{a}:{b}"`) is
  ignored, otherwise it would match every listener.
- Installed plugins and OpenAPI/static routes are left out of the
  "no caller" list.
- The docs have no HTTP reference: only routes cited in guides are checked.
