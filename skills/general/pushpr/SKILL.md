---
name: pushpr
description: Create a pull request from the personal fork to the upstream main, with a C4 **Problem** / **Solution** body. Drafts the title and body, waits for approval, then pushes and opens the PR.
disable-model-invocation: true
---

Create a Pull Request targeting upstream main, following the C4 **Problem**/**Solution** format. Ask me to validate before creating anything.

## Steps

1. **Gather context** — Run these commands to understand the current state:
   - `git status` to see uncommitted changes (warn me if there are any)
   - `git branch --show-current` to get the current branch name. Being on `main` is fine: a PR from the fork's `main` to upstream `main` is a normal workflow here — compare against `origin/main`, never the literal local branch.
   - `git log origin/main..HEAD --oneline` to see all commits to include
   - `git diff origin/main...HEAD --stat` to see the full diff summary

2. **Draft the PR** — Based on ALL commits (not just the latest), draft:
   - A **title**: short (under 70 chars), imperative, prefixed with the domain in brackets if applicable (e.g. `[feature] Add project template wrappers`)
   - A **body** using this exact format (bold headers, no `##` sections):

   ```
   **Problem**

   - concise bullet point describing each problem addressed

   **Solution**

   - concise bullet point describing each fix or change applied
   ```

   Keep bullet points short and factual. One bullet per distinct issue/fix. Do NOT add any extra sections, attribution, or boilerplate beyond Problem and Solution.

3. **Ask for validation** — Show me the title and body clearly formatted, then ask: "Is this good? You can ask me to change the title, body, or both before I create the PR."

   Wait for my explicit approval. Do NOT proceed until I say yes.

4. **Push and create** — Only after I approve:
   - Push to the personal fork, **never to `origin`** (upstream): `git push -u <fork-remote> HEAD`
   - Create the PR from the fork: `gh pr create --repo cgwire/<repo> --base main --head <github-user>:<branch> --title "..." --body "..."`
   - If `gh pr` fails with a `projectCards` GraphQL error, fall back to `gh api`
   - Show me the PR URL when done

$ARGUMENTS
