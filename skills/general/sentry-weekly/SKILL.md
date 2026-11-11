---
name: sentry-weekly
description: Use when the user asks for a Sentry analysis of the last 7 days ("analyse Sentry de la semaine", "bilan Sentry 7 jours", "sentry weekly", "what broke this week"). Read-only report: error volume and trend against the previous week, top, new and regressed issues, slow transactions, and what to triage first. Writes .audit/sentry-weekly-<date>.md.
---

# Sentry weekly analysis

Read-only: never resolve, assign, ignore or comment on an issue. The output
is a report and a short list of issues to hand to `/sentry-triage`.

## 0. Setup

- Load the Sentry MCP tools: `ToolSearch` with query `+sentry`. If none
  show up, say the Sentry MCP server is not configured for this project
  and stop.
- Organization and project: take them from the user, or from project
  memory. Otherwise list them (`find_organizations`, `find_projects`) and
  ask which one.
- Window: the last 7 days (`statsPeriod: 7d`), compared with the 7 days
  before (days -14 to -7). Use UTC dates in the report.

## 1. What was deployed

List the releases (`find_releases`) and note which one was live on each
day of the window. Sentry only sees deployed code: never credit a drop to
a fix, or blame a spike on a commit, before checking that the release
carrying it was live. If you cannot tell what is deployed, say so and ask
the user.

## 2. Collect

Run these with `search_events` and `search_issues`. They take natural
language queries; read back the query each tool generated and check it
used the right project and period.

1. **Volume**: error events per day over 14 days, and unique users
   affected, this week vs. the previous one.
2. **Top issues**: the 10 unresolved issues with the most events in the
   last 7 days: short ID, title, culprit, events, users, first seen, last
   seen, and the trend against the previous week.
3. **New issues**: first seen in the last 7 days, sorted by events.
4. **Regressions**: issues marked regressed, or resolved issues seen again
   this week.
5. **Gone quiet**: issues in last week's top 10 with no event this week.
   Match them with a release from step 1 before calling them fixed.
6. **Performance**: transactions with the worst p95 and the most total
   time (p95 × throughput), plus performance issues (N+1, slow DB query,
   consecutive DB calls) seen this week.

For the 3 to 5 issues that matter most, open them (`get_issue_details`,
or `get_sentry_resource` depending on the server version) to read the
stacktrace and the tags (route, release, environment, user role). Map the
top frame to a file in the current repo when you can.

## 3. Report

Write `.audit/sentry-weekly-<YYYY-MM-DD>.md` (`mkdir -p .audit`, suffix
`-2`, `-3`… if it exists) and show the summary in the chat:

```markdown
# Sentry weekly, <org>/<project>, <start> to <end> (UTC)

## Summary
3 to 5 lines: overall trend, the issue that matters most, what changed
since last week, which release was live.

## Numbers
| | this week | previous week | delta |
| errors | | | |
| users affected | | | |
| new issues | | | |
| regressions | | | |

## Top issues
| issue | title | events | users | trend | first seen | code |

## New issues
## Regressions
## Gone quiet (and the release that explains it, if any)
## Performance
| transaction | p95 | throughput | total time | note |

## Triage next
Ranked list of 3 to 5 issues, each with one line on why it comes first
(users hit, growth, new in a release, data at risk). Each is a candidate
for /sentry-triage.
```

Match the user's language. Mark anything you could not verify (a query
that came back empty or odd, a release you could not date) instead of
guessing.

## Rules

- Rank by users affected and growth, not by raw event count alone: one
  noisy client can flood an issue.
- Separate environments (production vs. staging) if the project has
  several. Default to production.
- A 7-day window cuts weekly cycles in half: compare with the previous 7
  days, never with a shorter period.
- Never paste tokens, user emails or IP addresses from events into the
  report.
