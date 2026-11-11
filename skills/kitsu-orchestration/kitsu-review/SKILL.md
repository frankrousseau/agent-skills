---
name: kitsu-review
description: Use when acting as an independent review agent for development work tracked in Kitsu via the kitsu CLI — reviewing deliverables that are waiting for approval and posting concise approve-or-retake verdicts. Triggers include reviewing Kitsu tasks in "waiting for approval" (wfa), independent spec/code review in Kitsu, gating a dogfooded dev pipeline.
---

# kitsu-review — concise independent review of Kitsu dev tasks

## Overview
You are a **separate review agent** (a distinct Kitsu identity from the worker, so the review is genuinely independent). You pick up tasks waiting for approval, read the actual deliverable from the git repo, and post a **concise, actionable** verdict: `done` or `retake`. The worker ([kitsu-work]) loops on your `retake` notes; the human owns the final `Final Review`.

**Conventions (non-negotiable):**
- **Write everything posted to Kitsu in English.**
- Positive verdict status is **`done`** — never `approved` (that status is reserved for concepts in Kitsu).
- Status short names vary per instance (e.g. wfa may be `toreview`, ready may be `READY`): check `kitsu --format json project task-status list "<Project>"` first instead of assuming.
- **Every review comment ends with a `Model: <model-id>` line** (the orchestrator passes you the exact string — don't guess).
- **After posting the verdict, add your own token consumption to the reviewed preview file** (additive — preview counters accumulate worker + reviewer) and to the asset aggregate. Zou exposes native `token_in`/`token_out` fields on preview files; use the project's helper if present (e.g. `scripts/log_tokens.py <preview-id> <asset-id> <in> <out> --token-line <your-line>`), else `gazu.client.put` on `data/preview-files/<id>` and the asset `data`.

**REQUIRED BACKGROUND:** board created by [kitsu-plan]; rationale in `kitsu-cli/specs/2026-05-31-kitsu-agent-dev-pipeline-skills-design.md`. For deeper code-review judgement on `Implement`, use **/code-review** — but keep the posted comment short.

## Prerequisites
```bash
export KITSU_HOST="https://<instance>/api"
export KITSU_TOKEN="<reviewer token>"        # NOT the worker's token
kitsu --format json auth status
```
Conventions: **global options go BEFORE the subcommand** (`kitsu --format json task list`, not `kitsu task list --format json` → "No such option"); UUIDs for writes / names for reads.

## Workflow

1. **Find work awaiting review**
```bash
kitsu --format json task list --project "<Project>" --task-status wfa
kitsu --format json studio tasks-requiring-feedback   # alternative, if subscribed
```

2. **Read the deliverable** — get the last comment, extract its `Commit:` SHA, read the files/diff in the code repo at that commit.
```bash
kitsu --format json task comment last "<task-id>"     # contains the footer with the SHA
( cd ../<repo> && git show <sha> --stat && git show <sha> )
```

3. **Evaluate against the step's rubric** (3–6 points max, no padding):

| Step | Check |
|------|-------|
| Specs | Complete? Clear? Ambiguities? Edge cases named? |
| Plan | Feasible? Covers the specs? Risks called out? |
| Unit Tests | Meaningful (not tautological)? Cover the specs? Valid TDD (written before code)? |
| Implement | Tests pass? Correct? Matches spec & plan? Quality? |
| Functional Tests | Real end-to-end against Kitsu? No mocks hiding integration gaps? |
| Final Review | Holistic coherence — pre-digest for the human gate. |

4. **Post the verdict.** Verdict first, then a short bullet list of specific, actionable items, then the mandatory `Model:` line. In English.
```bash
# Approve (positive verdict = done, NOT approved)
kitsu -q task comment add "<task-id>" --status done -m "$(printf 'DONE. <one line why>\n\nModel: <model-id>')"

# Retake
kitsu -q task comment add "<task-id>" --status retake -m "$(printf 'RETAKE.\n- %s\n- %s\n\nModel: <model-id>' \
  "<specific actionable item>" "<specific actionable item>")"
```

5. **Log your own tokens on the reviewed preview file** (additive) + asset aggregate — see Conventions above.

## Concise reviews — the core discipline
- **Verdict on the first line** (`DONE.` / `RETAKE.`).
- Retakes = a short bullet list of *specific, actionable* fixes. No essays, no restating the deliverable.
- Each bullet points to a concrete file/line/behavior the worker can act on.
- Approve when it meets the rubric; don't invent blockers.

## Common mistakes
| Mistake | Fix |
|---------|-----|
| Reviewing with the worker's token | Use a distinct reviewer identity — the review must be independent. |
| Reviewing the comment, not the code | Read the files at the `Commit:` SHA in the repo. |
| Verbose review comments | Verdict + short actionable bullets. Keep it scannable. |
| Approving without checking tests pass (`Implement`) | Confirm the unit/functional tests actually pass at that commit. |
| Blocking on the `Final Review` step | That's the human's gate; you pre-digest, you don't hard-block it. |
| Using `approved` as positive verdict | Use `done` — `approved` is reserved for concepts. |
| Posting reviews in the project's spoken language | Kitsu interactions are in English. |
| Forgetting the `Model:` footer or your token logging | Both are mandatory on every review. |
