---
name: kitsu-plan
description: Use when setting up a software-development project to be tracked inside Kitsu via the kitsu CLI — defining functional Modules and server Features as assets and creating their dev-pipeline tasks. Triggers include "plan the Kitsu board", "create the project structure in Kitsu", dogfooding development in Kitsu, scaffolding a Kitsu dev project.
---

# kitsu-plan — scaffold a dev project board in Kitsu

## Overview
Turn a project intent into a ready-to-work Kitsu board: a project, `Module`/`Feature` assets, the dev pipeline as task types, and one task per (asset × step). Drives the [kitsu-work] and [kitsu-review] skills. All actions go through the `kitsu` CLI (CGWire's kitsu-cli, built on gazu).

**REQUIRED BACKGROUND:** read the design doc at `kitsu-cli/specs/2026-05-31-kitsu-agent-dev-pipeline-skills-design.md` for the rationale.

## Prerequisites
```bash
export KITSU_HOST="https://<instance>/api"   # or pass --host
export KITSU_TOKEN="<token>"                 # or pass --token
kitsu --format json auth status              # exit 0 = authenticated
```
Conventions: **global options go BEFORE the subcommand** — `--format`/`-q`/`--host`/`--token` live on the root command, so write `kitsu --format json task list`, NOT `kitsu task list --format json` (the latter fails with "No such option"). **UUIDs for writes / names for reads.**

## Data model
- **Asset type `Module`** — a functional coverage area (à la gazu/kitsu-cli groups): Projects, Assets, Shots, Tasks, Casting, Playlists, Files, Persons, Edits, Search…
- **Asset type `Feature`** — a cross-cutting server concern: Startup, Deployment, Auth, Transport, Commands, Config.
- **Pipeline (task types)** on every asset: `Specs`, `Plan`, `Unit Tests`, `Implement`, `Functional Tests`, `Final Review`.
- **Statuses**: `todo`, `ready`, `wip`, waiting-for-approval, `retake`, `done`. ⚠️ Do NOT use `approved` (reserved for concepts in Kitsu) — `done` is the positive review verdict. Short names vary per instance (wfa may be `toreview`, ready may be `READY`): reuse what exists, record the mapping for [kitsu-work]/[kitsu-review].
- **Language**: everything written into Kitsu (project, assets, comments) is in English.

## Workflow

1. **Scope with the user**: list the Modules and Features before creating anything. Confirm.

2. **Create the project**
```bash
kitsu -q --format id-only project create "<Project Name>"
```

2b. **Enable agent collaboration** so the worker bot can be assigned tasks and log time on this project (without it, Zou rejects bot assignment / time logs). Requires Zou's bot-collaboration support on the instance.
```bash
kitsu -q project update "<Project Name>" --bot-collaboration
```

3. **Ensure asset types** (idempotent — check first, create if missing)
```bash
kitsu --format json asset type list            # look for Module / Feature
kitsu asset type create "Module"
kitsu asset type create "Feature"
```

4. **Ensure pipeline task types**, then attach them to the project. `--for-entity asset` scopes them to assets.
```bash
kitsu --format json task type list             # check existing
for tt in "Specs" "Plan" "Unit Tests" "Implement" "Functional Tests" "Final Review"; do
  kitsu task type create "$tt" --for-entity Asset      # capital A; choices: Asset|Shot|Sequence|Episode|Edit
  kitsu project task-type add "<Project Name>" "$tt"
done
```

5. **Ensure statuses** — check the **studio-level** list first (`kitsu --format json task status list`) and reuse existing statuses rather than creating near-duplicates (instances customize short names: `toreview`, `READY`…). Kitsu ships Todo/WIP/Waiting For Approval/Retake/Done; typically only `ready` is missing. Then attach the project's missing ones.
```bash
kitsu --format json task status list                          # studio level — reuse first
kitsu --format json project task-status list "<Project Name>" # what the project already has
kitsu task status create "Ready" --short-name ready --color "#9b59b6"        # only if truly missing; --color required
kitsu project task-status add "<Project Name>" "Ready"
kitsu project task-status add "<Project Name>" "Done"          # done = positive review verdict (NOT approved)
```

6. **Create assets** (one per module/feature)
```bash
ASSET=$(kitsu -q --format id-only asset create --project "<Project Name>" --type Module "Tasks")
```

7. **Create one task per (asset × step) in a loop.** ⚠️ Do NOT use `asset create --with-tasks` (gazu bug → `MethodNotAllowedException`). Loop instead:
```bash
for step in "Specs" "Plan" "Unit Tests" "Implement" "Functional Tests" "Final Review"; do
  kitsu -q --format id-only task create "$ASSET" --task-type "$step"
done
```

8. **Report the board**: print the assets × steps grid with task IDs so the user can hand off to [kitsu-work].

## Common mistakes
| Mistake | Fix |
|---------|-----|
| `asset create --with-tasks` | Broken (gazu). Create tasks in a loop (step 7). |
| Assuming statuses exist | Check studio + project status lists; reuse existing ones (short names vary per instance), create only what's truly missing. |
| Using `approved` in the pipeline | `approved` is reserved for concepts — the positive verdict status is `done`. |
| Writing Kitsu content in another language | Kitsu interactions are in English. |
| Creating tasks before the task type is on the project | Run step 4 (attach via `project task-type add`) first. |
| Passing names to write ops that need IDs | Use `--format id-only` captures; UUIDs for writes. |

## Next
Hand the board to **[kitsu-work]** (do the work + report) and **[kitsu-review]** (independent review).
