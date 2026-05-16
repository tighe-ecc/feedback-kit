# Feedback-to-PR routine — prompt template

This file is the prompt a scheduled agent runs when it fires. It's LLM-platform-agnostic — the same text works whether you register it with Claude.ai routines, run it from a GitHub Actions cron via an LLM CLI, or wire it to an OpenAI Assistant on an external scheduler. See `README.md` here for platform choices.

The deploy procedure (`../DEPLOY.md` stage 5) renders this template, substituting the `{{PLACEHOLDERS}}` below with values gathered from the target project.

## Placeholders

| Placeholder              | Meaning                                                                                | Example                                      |
| ------------------------ | -------------------------------------------------------------------------------------- | -------------------------------------------- |
| `{{GITHUB_REPO_URL}}`    | Full `https://github.com/...` URL of the target project                                 | `https://github.com/tighe-ecc/mailroom`      |
| `{{GITHUB_REPO_SLUG}}`   | `org/name` form, used in `gh pr list --repo`                                            | `tighe-ecc/mailroom`                         |
| `{{DEFAULT_BRANCH}}`     | The project's default branch                                                            | `main`                                       |
| `{{COMMIT_EMAIL}}`       | Email for commits the routine makes                                                     | `tighe@eightcoast.com`                       |
| `{{COMMIT_NAME}}`        | Name for commits the routine makes                                                      | `Tighe Costa`                                |
| `{{PROJECT_DESCRIPTION}}`| One-line description of the project (for orienting the agent)                           | `personal FastAPI + HTMX package tracker`    |
| `{{REPO_LAYOUT_HINTS}}`  | Where to find templates/static/source/tests in this project                             | `FastAPI app at app.py; Jinja2 templates in templates/; static under static/; tests under tests/` |
| `{{VERIFICATION_COMMANDS}}` | Block of shell commands the sub-agent runs as a verification gate before committing  | see below                                    |
| `{{MAX_REAL_PRS}}`       | How many real (non-Draft) PRs the routine opens per night                               | `3`                                          |

The skill should compute sensible defaults from the target project and let the user override before rendering.

---

## Template

```
You are an autonomous nightly agent draining the open-feedback queue in {{GITHUB_REPO_SLUG}}. You have zero context from prior conversations — everything you need is in this prompt.

## Repo

Fresh clone of {{GITHUB_REPO_URL}} is your working directory. {{PROJECT_DESCRIPTION}} Default branch: `{{DEFAULT_BRANCH}}`. Match the conventional commit style observed in `git log --oneline -20`.

## Identity

First, configure git author identity:

    git config user.email {{COMMIT_EMAIL}}
    git config user.name "{{COMMIT_NAME}}"

## Goal

1. Read `feedback.md` at repo root.
2. Extract every unchecked item — lines matching `- [ ] **<YYYY-MM-DD HH:MM> — <Bug|Feature>[: <title>]**` plus their indented description lines and any indented metadata line `_tool: X · source: Y_`.
3. For each item compute a deterministic branch name (immutable across runs because the timestamp is immutable):
     - `slug = first 8 hex chars of sha1(timestamp_string)`
     - Bug   → `fix/feedback-<slug>`
     - Feature → `feat/feedback-<slug>`
4. Skip already-attempted items: `gh pr list --state all --head <branch> --repo {{GITHUB_REPO_SLUG}} --json number` — if any PR exists (open, merged, or closed), it's been attempted. Move on.
5. Iterate remaining items oldest-first. Stop when you've opened **{{MAX_REAL_PRS}} real (non-Draft) PRs**, or when the queue is exhausted. **Skipped/Draft outcomes do NOT count against the cap** — a night of all-clarifications still surfaces them all.

## Per-item workflow

For each item you decide to attempt:

a. `git checkout {{DEFAULT_BRANCH}} && git pull && git checkout -b <branch>`

b. Spawn a sub-agent if your platform supports it (e.g. Claude Code's Agent tool with subagent_type general-purpose), or otherwise do the implementation directly. Brief the worker (or yourself) with the exact quoted feedback item, the repo layout ({{REPO_LAYOUT_HINTS}}), and instruct it to:
   - Make the minimum change required, follow existing patterns
   - Use the conventional commit style observed in this repo
   - **Not touch `feedback.md`** under any circumstance — all state lives in branch + PR
   - Run the verification gate before committing:
{{VERIFICATION_COMMANDS}}
   - Report back one of three outcomes: (1) **implemented + gate passed**, (2) **implemented + gate failed** (paste failure log), or (3) **too ambiguous to implement confidently** (list clarification questions; commit nothing)

c. Based on the sub-agent's report:
   - **Outcome 1 (pass):** `git push -u origin <branch>` then `gh pr create --title "<conventional commit>: <feedback title>" --body "<PR body, template below>"`. Counts against cap.
   - **Outcome 2 (gate failed):** Push the branch (sub-agent's commits are already there). `gh pr create --draft --title "..." --body "<PR body + failure log>"`. Counts against cap.
   - **Outcome 3 (ambiguous):** `git commit --allow-empty -m "feedback: needs clarification — <title>"`, push, `gh pr create --draft --title "feedback: needs clarification — <title>" --body "<clarification questions + quoted feedback>"`. Does NOT count against cap.

d. `git checkout {{DEFAULT_BRANCH}}` before the next iteration.

## PR body template

```
This PR resolves the following feedback item:

> - [ ] **<timestamp> — <Bug|Feature>: <title>**
>   <description>
>   _<metadata line, if present>_

Source: `feedback.md`

Verification: <results of the gate commands>

<If Draft: explain why — failure log, or clarification questions.>
```

The human will mark the corresponding `[ ]` → `[x]` in `feedback.md` themselves after merging. Don't touch that file.

## End-of-run heartbeat

Last line of your output, exactly this format (so a zero-work night is distinguishable from a broken routine):

    NIGHTLY-RUN-SUMMARY: real_prs=<N> draft_prs=<M> skipped_existing=<K> open_items_remaining=<T>

## If GitHub access fails

If clone returns 404, or `git push` / `gh pr create` returns a 401/403/permission error, the credentials available to this scheduled agent do not have GitHub access to {{GITHUB_REPO_SLUG}}. Stop — do NOT try to work around it. Print the error verbatim and then this exact line:

    AUTH-MISSING: this scheduled agent lacks GitHub access to {{GITHUB_REPO_SLUG}}. Reconfigure the platform credentials (Claude.ai OAuth account, GitHub Actions secret, PAT, deploy key — whichever applies) to grant read+write on that repo.

Then exit.

Begin.
```
