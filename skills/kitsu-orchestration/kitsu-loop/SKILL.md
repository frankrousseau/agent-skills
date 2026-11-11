---
name: kitsu-loop
description: Use when the user asks to connect to Kitsu and follow the changes of a project board ("reconnecte toi à Kitsu", "suis les changements", "lance la boucle Kitsu", /kitsu-loop). Starts the self-paced loop that reads the news feed of the project and does the work through kitsu-work.
---

# kitsu-loop: follow a Kitsu project board

Kitsu drives the work: a READY task, a retake or a human comment is an
order. Do it in the same turn, answer in Kitsu comments, not in the chat.
Load `kitsu-work` first: this skill only adds the connection and the loop.

Replace `<Project>`, `<project>`, `<instance>`, `<token file>` and
`<kitsu-cli>` below with your own values.

## 1. Connect

```bash
export KITSU_HOST=https://<instance>/api
export KITSU_TOKEN=$(tr -d '\n' < <token file>)
K=<kitsu-cli>/.venv/bin/kitsu
$K --format json auth status | python3 -c "import json,sys;d=json.load(sys.stdin);print(d['id'],d['role'])"
```

- Note the bot's person id from `auth status`. Never print the token.
- `ModuleNotFoundError: kitsu_cli` means the venv is stale (system Python
  update): `cd <kitsu-cli> && uv venv --clear .venv && uv pip install -e . --group dev`.
- Global options go before the subcommand (`kitsu --format json task list`).
- Check the status short names of the instance
  (`kitsu --format json project task-status list "<Project>"`). Below they
  are `todo`, `READY`, `wip`, `toreview`, `retake`, `done`.

## 2. Cursor

The cursor is the UTC time of the last news read, in
`~/.claude/kitsu-loop/<project>-news-cursor` (format `2026-10-27T12:21:26`).
It survives a restart. If the file is absent, create it with
`date -u +%Y-%m-%dT%H:%M:%S`.

After each publish or comment of your own, set the cursor to now: the
Monitor must not wake you on your own news.

## 3. Cycle (each tick)

```bash
S=~/.claude/kitsu-loop
$K --format json news list --project "<Project>" --after "$(cat $S/<project>-news-cursor)" --details --limit 50
$K --format json task list --project "<Project>" --task-status READY
$K --format json task list --project "<Project>" --task-status retake
```

For each change, follow `kitsu-work`: start (`wip`, assign the bot),
one commit per publish on a feature branch, `preview publish --status
toreview` with a real unified diff (`/usr/bin/git diff`, not a proxy), the
footer (Model, Commit, Tokens), `task preview tokens`, `task time add`.
Do not set a `Final Review` to `done`. Then write the cursor.

## 4. Watch and self-pace

Arm a Monitor (`timeout_ms: 1800000`, re-arm at each expiry):

```bash
export KITSU_HOST=https://<instance>/api; export KITSU_TOKEN=$(tr -d '\n' < <token file>)
K=<kitsu-cli>/.venv/bin/kitsu; S=~/.claude/kitsu-loop
while true; do
  $K --format json news list --project "<Project>" --after "$(cat $S/<project>-news-cursor)" --details --limit 50 2>/dev/null | python3 -c "
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
items=d if isinstance(d,list) else d.get('data',d)
for n in items: print('NEWS',n.get('created_at'),'|',n.get('full_entity_name') or n.get('entity_name'),'|',n.get('task_type_name'),'|',n.get('task_status_short_name') or n.get('task_status_name'),'|',(n.get('comment_text') or '')[:160].replace(chr(10),' '))
" || true
  sleep 60
done
```

Then run the `/loop` skill in dynamic mode with this prompt, and keep it
as the `ScheduleWakeup` prompt (1800 s fallback, `noop: true` on a quiet
tick):

```
/loop Read the Kitsu news of the project <Project> since the cursor in ~/.claude/kitsu-loop/<project>-news-cursor (kitsu-work step 0), act on each change (READY tasks, retakes, human comments) through the kitsu-work skill, then update the cursor.
```

A Monitor event is a news line: handle it, then re-schedule the wakeup.
A Monitor expiry: re-arm it. Stop the loop only when the user asks.
