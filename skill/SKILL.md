---
name: feedback-framework
description: Drop a portable in-app feedback collection framework into a web project. Installs feedback.py (stdlib Python library that appends entries to feedback.md), feedback-button.js (self-contained floating-button + modal UI), a POST /feedback endpoint matched to the project's web framework (FastAPI / Flask / Express), and wires the script into the base template. Idempotent. Use when the user wants to add a "click button → write to feedback.md" loop to a web app, or asks to install the feedback-kit.
user-invocable: true
---

# /feedback-framework

Install the canonical feedback collection framework into the current project.

## What gets installed

1. **`feedback.py`** at the repo root — stdlib-only Python library; `note(description, type, title, tool, url)` appends to `feedback.md`. Auto-resolves target `feedback.md` by walking up from caller `__file__`.
2. **`feedback-button.js`** under the project's static dir — shadow-DOM floating button + modal; POSTs JSON to `/feedback`.
3. **A `POST /feedback` endpoint** in the project's app file, in the matching web framework.
4. **A `<script type="module">` tag** in the project's base HTML template that imports `feedback-button.js` and calls `initFeedback({ endpoint: '/feedback', toolName: '<project-name>' })`.
5. **A seeded `feedback.md`** at the repo root if absent.

After install, the user submits feedback from any page of the running app via the floating "Feedback" button; entries land in `feedback.md` as a Markdown checklist.

## Fixed context

- **Kit source:** `tighe-ecc/feedback-kit` (public). Files fetched via `https://raw.githubusercontent.com/tighe-ecc/feedback-kit/<KIT_REF>/<path>`.
- **`KIT_REF` (pin):** `main`
  - Bump this to a tag or SHA when the kit changes — don't trust `main` forever. The downstream installs see whatever this points at, so the pin is the version contract.
- **Mailroom is the originating copy.** Any tweak to `feedback.py` / `feedback-button.js` in `/Users/tighe.costa/personal/mailroom` MUST be upstreamed to `tighe-ecc/feedback-kit` and a new `KIT_REF` cut here. No automation catches this.

## Two phases

**Phase 1 (always):** install the framework into the current project — files copied/patched, no commit. End-state: the user can run their app and the floating Feedback button writes to `feedback.md`.

**Phase 2 (optional):** offer to register a **nightly remote routine** that scans the project's `feedback.md` and opens PRs for unchecked items overnight. The routine is per-project and runs on the user's own Claude.ai account against their own GitHub identity. If the user declines, Phase 1 still works exactly as before — Phase 2 can be added later by re-invoking the skill.

## Phase 1 — Install the framework

### 1. Verify state

- `git status` clean is preferred but not required (the install adds new files + light edits; the user should review the diff before committing).
- If the project doesn't look like a web app at all (no `pyproject.toml`/`requirements*.txt`/`package.json`, or none mention a recognized framework), **stop and ask** the user where to install. Don't guess.

### 2. Detect the web framework

Check in order:

```bash
grep -l 'fastapi' pyproject.toml requirements*.txt 2>/dev/null    # → FastAPI
grep -l 'flask'   pyproject.toml requirements*.txt 2>/dev/null    # → Flask
grep -l '"express"' package.json 2>/dev/null                      # → Express
```

If multiple match (rare — usually a monorepo), ask the user which one.
If none match, ask the user which framework, and offer to skip the endpoint step (so they can wire it manually with one of the snippets).

### 3. Detect the target app file

```bash
# Python:
grep -rn -E 'FastAPI\(|Flask\(__name__\)' --include='*.py' .
# JavaScript:
grep -rn -E '\bexpress\(\)' --include='*.js' .
```

- Exactly 1 hit → use that file.
- 2+ hits → ask the user to pick. **Do not auto-pick.**
- 0 hits → ask the user for the path.

### 4. Detect the static dir and base template

**FastAPI:** look for `app.mount("/static"` in the target file. The path argument tells you the static dir. Common: `static/`. If absent, ask the user.

**Flask:** Flask's default `static_folder` is `static/` (sibling to the app file or under `src/<pkg>/`). Look for `Flask(__name__, static_folder=...)` for overrides. Default if not overridden.

**Express:** look for `express.static(` in the target file (or any file). The first argument is the static dir.

**Base template:** ask the user. Typical guesses:
- `templates/base.html` / `templates/_base.html` (Jinja2/Flask)
- `templates/layout.html` (Jinja2)
- For HTMX-style apps without a base layout: paste the snippet into the main page template that renders on first visit.
- Express + EJS: `views/layout.ejs` or the page-level template.

If unsure: `find . -path ./node_modules -prune -o \( -name '*.html' -o -name '*.ejs' -o -name '*.jinja' \) -print 2>/dev/null | head -20` and ask.

### 5. Fetch kit files

Set `KIT_REF` from the constant above (currently `main`). Then:

```bash
KIT_REF="main"
BASE="https://raw.githubusercontent.com/tighe-ecc/feedback-kit/${KIT_REF}"
curl -fsSL "${BASE}/feedback.py"          -o feedback.py
curl -fsSL "${BASE}/feedback-button.js"   -o <static-dir>/feedback-button.js
curl -fsSL "${BASE}/endpoints/<fw>.<ext>" -o /tmp/feedback-endpoint-snippet
```

Where `<fw>.<ext>` is `fastapi.py`, `flask.py`, or `express.js`. The endpoint snippet is a paste fragment — not directly importable; just read it and inline its content.

### 6. Patch the app file (idempotent)

Search for the sentinel `--- feedback endpoint` in the target file. If present, skip step 6 entirely — the endpoint is already installed.

Otherwise, append the snippet from `/tmp/feedback-endpoint-snippet` to the bottom of the target file. The sentinel comments in the snippet make re-runs safe.

### 7. Patch the base template (idempotent)

Search the base template for the string `feedback-button.js`. If present, skip step 7.

Otherwise, insert this near the closing `</body>`:

```html
<script type="module">
  import { initFeedback } from '/<static-mount>/feedback-button.js';
  initFeedback({ endpoint: '/feedback', toolName: '<project-slug>' });
</script>
```

Use the static mount path discovered in step 4 (typically `/static`). Use the project's directory basename for `toolName`.

### 8. Seed `feedback.md`

```bash
test -f feedback.md || printf '# Feedback\n\n' > feedback.md
```

### 9. Show the diff and stop

Run `git status` and `git diff` (for the patched files). **Do not commit.** Let the user review.

Print a brief summary:

- Files added: `feedback.py`, `<static-dir>/feedback-button.js`, `feedback.md` (if newly seeded).
- Files patched: `<app-file>` (endpoint), `<template>` (script tag).
- Next: start the app, click the floating "Feedback" button, submit a test entry, confirm it appears in `feedback.md`.

## Phase 2 — Offer optional nightly automation

After Phase 1 succeeds (or if invoked on a project where Phase 1 was already done), ask the user:

> Want to set up a nightly remote agent that scans `feedback.md` for new items, implements them on branches, and opens PRs against your default branch?
> - **yes** — register the routine now
> - **no** — skip; you can run `/feedback-framework` again later to add it
> - **show** — render the prompt and the exact `/schedule` invocation without registering anything

If `no` or `show`, stop after that. Phase 1 is unaffected.

If `yes`, walk through these steps:

### P2.1 Surface the auth caveat **before** doing anything else

The remote routine clones the project via the *current Claude.ai account's* GitHub OAuth. There is no per-routine secret. If the user is signed into Claude Code under a work / shared account that doesn't have access to the target repo's GitHub owner, the routine will 404 on clone and `AUTH-MISSING:` will appear in the run log.

Print this explicitly to the user. Ask them to confirm:

> "This routine will run as the GitHub identity that **{{their current Claude.ai account}}** has authorized. The target repo is **<owner>/<name>**. Is that the right account, or should you switch Claude Code to a different login first?"

If they need to switch, stop — they can re-invoke the skill once they've `/login`-ed to the right account.

### P2.2 Gather routine parameters

Defaults to compute; ask the user to confirm/override before submitting:

| Parameter                | Default                                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------------------- |
| `GITHUB_REPO_URL`        | `git remote get-url origin` → normalize to `https://github.com/...` form (strip `.git`, swap SSH → HTTPS)     |
| `GITHUB_REPO_SLUG`       | `org/name` form derived from the URL                                                                          |
| `DEFAULT_BRANCH`         | `git symbolic-ref refs/remotes/origin/HEAD` → `main` if unknown                                                |
| `COMMIT_EMAIL`           | `git config user.email`                                                                                       |
| `COMMIT_NAME`            | `git config user.name`                                                                                        |
| `PROJECT_DESCRIPTION`    | first non-blank line of README.md, trimmed; or one sentence the user provides                                 |
| `REPO_LAYOUT_HINTS`      | a short string the skill composes from the detected layout (e.g. `FastAPI app at app.py; templates/; static/; tests/`) |
| `VERIFICATION_COMMANDS`  | python projects: `python -c "import <root-module>"` and `pytest -x --timeout=60` (only the import check if `tests/` is absent). Node/Express: `node -e "require('./<entry>')"`. Let the user override. |
| `MAX_REAL_PRS`           | `3`                                                                                                            |
| `CRON_EXPRESSION` (UTC)  | `0 10 * * *` (≈ 03:00 PT). Ask for time zone; compute UTC.                                                     |

### P2.3 Render the prompt

Fetch the template:

```bash
curl -fsSL "https://raw.githubusercontent.com/tighe-ecc/feedback-kit/${KIT_REF}/skill/routine-prompt.template.md" \
  | sed -n '/^## Template$/,/^## /{/^## Template$/d;/^## /d;p}'
```

Substitute all `{{PLACEHOLDER}}`s with the values from P2.2.

### P2.4 Register the routine

Hand the rendered prompt to the `schedule` skill — invoke it with `create` and a fully-specified body: `cron_expression`, `name` (suggest `<project-slug>-nightly-feedback-drain`), `enabled: true`, `session_context.sources` set to the target repo URL, `model: claude-sonnet-4-6`, `allowed_tools: ["Bash","Read","Write","Edit","Glob","Grep","Agent","TaskCreate","TaskUpdate","TaskList"]`, and the event message set to the rendered prompt.

### P2.5 Verify with a manual fire

Immediately run the new routine on-demand (`RemoteTrigger action=run`) and ask the user to check the run history at `https://claude.ai/code/routines/<id>`. Look for one of:

- `NIGHTLY-RUN-SUMMARY: real_prs=… draft_prs=… skipped_existing=… open_items_remaining=…` → auth works, the routine is live.
- `AUTH-MISSING: this routine's Claude.ai account lacks GitHub access to <slug>.` → the OAuth grant is wrong for this account; user fixes at `https://claude.ai/settings/integrations`, then re-fires the routine.

Print the routine URL one last time so the user can bookmark it.

## Re-running the skill

Safe. Sentinels in the endpoint snippet and a check for `feedback-button.js` in the template make all Phase 1 patches idempotent. File fetches overwrite — that's how kit updates propagate. If the user has hand-edited `feedback.py` or `feedback-button.js` locally, warn before overwriting.

Phase 2 is also re-invocable: if the user previously chose `no`, running the skill again gives them another chance to opt in. If a routine already exists for this project (name match on `<project-slug>-nightly-feedback-drain` in `RemoteTrigger list`), skip the create step and just show the URL — don't make duplicates.

## When to refuse / escalate

- Project has no recognizable web framework → ask, don't guess.
- Multiple plausible app files / templates → ask, don't auto-pick.
- User wants a database-backed feedback queue, not flat-file Markdown → out of scope; point at the kit's README for the design rationale, suggest they fork.
