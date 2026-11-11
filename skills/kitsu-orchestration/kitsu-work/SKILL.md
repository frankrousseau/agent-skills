---
name: kitsu-work
description: Use when doing development work that must be tracked in Kitsu via the kitsu CLI — picking up assigned tasks, reporting progress, submitting deliverables for review, and incorporating retake feedback. Triggers include an agent working Kitsu dev tasks, dogfooding development tracked in Kitsu, reporting progress to Kitsu, handling a "retake".
---

# kitsu-work — do dev work and report it into Kitsu

## Overview
You are a **worker agent**. You pick up `ready` tasks from a Kitsu board, do the work, report progress, submit each deliverable for review (waiting-for-approval), and loop on `retake` feedback **until done — with no cap on retakes**. Everything goes through the `kitsu` CLI. Reviews are done by a separate agent — see [kitsu-review].

**Conventions (non-negotiable):**
- **Ask your questions in Kitsu**: a question about a task (scope, retake, open point) is a comment on that task, not a chat message. Record in Kitsu any decision taken elsewhere. Then wait for the answer in Kitsu.
- **Write everything posted to Kitsu in English** (specs, plans, comments, footers), whatever language the conversation uses. **File and directory names are English-only too** (translate feature names: demarrage → startup), even when board asset names are in another language.
- The positive end-of-review status is **`done`** — never `approved` (reserved for concepts in Kitsu).
- **Status short names vary per instance** (wfa may be `toreview`, ready may be `READY`): run `kitsu --format json project task-status list "<Project>"` first and use the instance's short names everywhere below.
- Prefer **gazu** (`gazu.client.get/put/post`) over raw curl for any direct Zou API call or bug workaround. When the CLI lacks a feature, add it to the kitsu-cli repo with a test instead of keeping a one-off script.

**REQUIRED BACKGROUND:** the board is created by [kitsu-plan]; rationale in `kitsu-cli/specs/2026-05-31-kitsu-agent-dev-pipeline-skills-design.md`.

## Prerequisites
```bash
export KITSU_HOST="https://<instance>/api"
export KITSU_TOKEN="<worker token>"
kitsu --format json auth status
```
Code lives in a sibling git repo. Conventions: **global options go BEFORE the subcommand** (`kitsu --format json task list`, not `kitsu task list --format json` → "No such option"); **UUIDs for writes / names for reads**; **1 publish = 1 git commit**. Subcommand options (`--status`, `--file`, `-m`, `--interval`…) stay after the subcommand as usual.

## Pipeline gating
Steps run in order `Specs → Plan → Unit Tests → Implement → Functional Tests → Final Review`. When you move `Final Review` to waiting-for-approval, post a **pre-digest for the human**: pipeline recap, what exists now, retake/flag history, **and a "How to test" section** (exact commands: unit suite, functional suite, manual server run, real-client connection) — the human must be able to verify without asking anything. **Wrap every command in markdown code fences (```)** — Kitsu renders comments as markdown. TDD: an `Implement` task only goes `ready` once its `Unit Tests` task is `done`; your code must make those tests pass. If implementing reveals a reviewed test was wrong, **reopen the Unit Tests task** (set it back to `wip`, publish the test delta) rather than working around it. The `Final Review` task stays at the waiting-for-approval status — it is the human's gate.

## Per-task loop

0. **Read the project news FIRST** — before picking new work, read what changed on the board since your last check: statuses, retakes, human comments, tasks set to ready, including on tasks already `done`. The news feed shows every change, also on tasks you do not watch:
```bash
kitsu --format json news list --project "<Project>" --after "<last check, 2026-10-08T12:20:00>" --details --limit 50
```
`--details` adds the task type name, the status short name and the comment text. A human comment is an implicit retake: reopen (`wip`), address it, re-submit, get re-reviewed. Never let a human comment sit unanswered through a cycle. (`studio notifications` is refused for a bot token.)

1. **Find work**: tasks set to `ready`, or your assigned to-dos.
```bash
kitsu --format json task list --project "<Project>" --task-status ready
kitsu --format json studio todo                       # your to-do tasks (notifications: kitsu --format json studio notifications)
# To grab a specific task (e.g. Parser's Specs task) by asset + step:
kitsu --format json task get-by-entity "<asset-name>" --task-type "Specs" --project "<Project>"   # or an asset UUID without --project
```

2. **Start** → status `wip`, with a progress note (`-m` is required), and **assign yourself** (Zou's bot guard refuses time logging on tasks the bot is not assigned to):
```bash
kitsu -q task start "<task-id>"
kitsu -q task comment add "<task-id>" --status wip -m "Starting <step> for <module>"
kitsu -q task assign "<task-id>" --person "<your-person-uuid>"
```

3. **Produce the deliverable** for the step. Layout: `specs/<m>.md`, `plans/<m>.md`, `tests/test_<m>.py`, `tests/functional/test_<m>.py`, `src/.../<m>.py`. For `Implement`/test steps, run tests locally and make them pass before publishing.

4. **Commit** (one commit per publish) and capture the short SHA:
```bash
sha=$(cd ../<repo> && git add -A && git commit -q -m "<step>: <module>" && git rev-parse --short HEAD)
```

5. **Submit for review** → `wfa`, attaching the deliverable, with the mandatory footer. Redirect output to a temp file before parsing (multiline comments break inline JSON pipes):
```bash
kitsu task preview publish "<task-id>" --status wfa --file ../<repo>/<deliverable> \
  -m "$(printf '%s\n\nModel: %s\nCommit: %s\nTokens: %s in / %s out' \
        "<what was done>" "<model-id>" "$sha" "<in>" "<out>")" > /tmp/pub.json
```
If the preview extension is rejected (`.py`/`.txt`), publish a unified diff instead (`diff -u /dev/null file > file.diff`) and attach it: `kitsu task preview add "<task-id>" "$(jq -r .comment.id /tmp/pub.json)" --file file.diff`.
⚠️ **Verify the .diff is a REAL unified diff before publishing** — local command proxies (e.g. token-optimizing wrappers like rtk) may intercept `diff`/`git diff` and write a pretty-printed summary instead, which renders BLANK in Kitsu's diff viewer. Check the first line and regenerate bypassing the proxy if needed:
```bash
head -1 file.diff | grep -qE "^(diff --git|--- )" || rtk proxy git diff … > file.diff
```

6. **Wait for the verdict**, then act on it. Use the CLI's built-in poll:
```bash
kitsu task await "<task-id>" --status done --interval 30   # --status is the TARGET status to wait for
```
On **retake**: read the reviewer's note, fix, re-submit for review, repeat. **No retake limit — loop until `done`.**
```bash
kitsu --format json task comment last "<task-id>"   # reviewer feedback
# fix → new commit → preview publish --status wfa (diff prev-vs-current if extension-restricted)
```

7. **Log time** — pass your own person **id**, not your email (emails can collide with a human). Get it from `kitsu --format json auth status` (the `id` field):
```bash
MY_ID=$(kitsu --format json auth status | jq -r .id)
kitsu task time add "<task-id>" --person "$MY_ID" --date <YYYY-MM-DD> --duration <minutes>
```

8. **Log token counters** after each publish — Zou exposes native `token_in`/`token_out` fields on **preview files**: fill them at upload (your consumption for that iteration), and accumulate the same numbers (additive) into the asset `data` (`token_in`/`token_out`) so the asset stays the sum of its previews. One command does both:
```bash
kitsu --format json task preview tokens "<preview-file-id>" --in <in> --out <out>
```
(The reviewer adds its own consumption to the same preview fields afterwards — see [kitsu-review].)

## Comment footer (mandatory on every review submission, in English)
```
<what was done>

Model: <model-id>
Commit: <short-sha>
Tokens: <in> in / <out> out
```

## Common mistakes
| Mistake | Fix |
|---------|-----|
| `--format`/`-q` after the subcommand | Global options go BEFORE it: `kitsu --format json task list`. Otherwise "No such option", exit 2. |
| `comment add` without `--status` | `--status` is the required option (`-m`/message is optional but always include it). |
| Parsing `preview publish` JSON inline | Redirect to `/tmp/pub.json`, then `jq`. Multiline comments break pipes. |
| Logging time with `--person <email>` | Use your person `id` from `auth status`; email may resolve to the human. |
| Capping retakes | There is no cap — loop until `done`. |
| Using `approved` as the positive status | Use `done` — `approved` is reserved for concepts. |
| Posting Kitsu content in another language | Kitsu interactions are in English. |
| Assuming status short names (`wfa`, `ready`) | Check `project task-status list` — instances customize them (`toreview`, `READY`…). |
| Implementing around a wrong reviewed test | Reopen the Unit Tests task and fix the test. |
| Bot can't be assigned / log time | The project needs agent collaboration enabled: `kitsu -q project update "<Project>" --bot-collaboration` ([kitsu-plan] step 2b). Requires Zou's bot-collaboration support. |
| `kitsu task assign` crashes (gazu bug) | Fixed in kitsu-cli (branch `feature/agent-workflow-gaps`, 2026-10-08): the CLI calls the Zou route itself. Update the CLI. |
