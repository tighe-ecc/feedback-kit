# Deploy

Procedure for the code-generation agent (Claude Code, Codex, Cursor, Aider, etc.) installing this kit into a user's project. Read `CONCEPT.md` first; the invariants at the bottom are non-negotiable.

## The two halves

- **Capture** — button + receive endpoint + `feedback.md`. Standalone-useful.
- **Agent loop** — scheduled remote agent that drains the queue into PRs. Optional.

Install Capture first, verify it works, then offer the Agent loop as an optional second step.

## Workflow

1. **Confirm concept.**
2. **Discover** — read the kit, inspect the project, pick an adaptation.
3. **Capture customizations** — ask the user what defaults to change.
4. **Plan** — present a written plan, including a tailored preview render. Wait for sign-off.
5. **Implement Capture** — idempotent edits, show diff, don't commit.
6. **Verify Capture** — live test submission.
7. **Offer Agent loop** — optional; register on the user's chosen platform.

---

## Stage 1 — Confirm concept

Restate the concept back to the user:

> This kit installs a "Feedback" button (Bug/Feature, optional Expedite) into your app. Submissions append to `feedback.md` at the repo root. An optional scheduled agent — on whatever LLM platform you prefer — drains the queue into PRs against the default branch.
>
> Is that the shape you want?

Stop and recommend something else if the user wants any of:

- Real ticket system with assignees, statuses, labels → GitHub Issues / Linear.
- Private feedback, not in source control → out of scope.
- Agent auto-merges PRs → out of scope.
- Feedback collection but explicitly no agent loop ever → Capture works; confirm they understand the kit's value is the loop.

## Stage 2 — Discover

### 2a — Read the kit

Fetch the kit's docs in this order. `git clone` to a temp dir is faster than individual fetches if the agent supports it.

1. `README.md`
2. `CONCEPT.md` (invariants)
3. `DEPLOY.md` (this file)
4. `reference/README.md` and the files under `reference/`
5. `adaptations/README.md` and every file in `adaptations/`
6. `automation/README.md` and `automation/routine-prompt.template.md`

### 2b — Read the user's project

Determine by inspection where possible:

- Project type — web app / CLI / library / mobile / static.
- Stack — from `pyproject.toml`, `package.json`, `Gemfile`, `go.mod`, etc.
- App entry point — file containing `app = FastAPI(...)` / `Flask(__name__)` / `express()` / equivalent.
- Templates dir and base template path.
- Static dir and its mount path.
- Hosting — local dev / VPS / managed platform / static. Use `Dockerfile`, `vercel.json`, `render.yaml`, `fly.toml`, `wrangler.toml` etc. as signals.
- GitHub remote — `git remote -v`.

Only ask questions that inspection cannot answer.

### 2c — Pick an adaptation

| Situation                                                                       | Adaptation                                                                  |
| ------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| FastAPI / Flask / Express, locally hosted, has `git push` access                | `adaptations/local-dev-server.md` (matches `reference/`)                    |
| Same stack, deployed on VPS / container where the process can `git push`        | `adaptations/remote-host-direct-git.md`                                     |
| Same stack, managed platform with read-only filesystem                          | `adaptations/remote-host-github-api.md`                                     |
| No backend (static site, mobile, CLI, library)                                  | `adaptations/no-backend.md`                                                  |
| Stack not in the reference (Django, Rails, Next.js, Go, Rust)                   | `adaptations/novel-stack.md`                                                |

If none fit, plan a custom approach that preserves the invariants.

## Stage 3 — Capture customizations

Ask the user what they want changed from the kit defaults. Surface the options explicitly; don't make the user guess what's customizable. Common ones:

| Customization                                  | Default                              | How to apply                                                                   |
| ---------------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------ |
| Hide the Expedite checkbox                     | Shown                                | `initFeedback({ ..., expedite: false })`                                       |
| Rename type labels (Bug/Feature)               | Bug / Feature                        | Edit the `<option>` labels and `_format_entry` label map in `feedback.py`     |
| Move `feedback.md`                             | Repo root                            | `feedback.note(..., path=...)` and update agent prompt's "Read `feedback.md`" |
| Disable auto-commit + push                     | Enabled in the FastAPI snippet       | Remove the `background_tasks.add_task(_git_sync_feedback)` line                |
| Different cron schedule / time zone            | `0 10 * * *` UTC                     | Adjust at routine registration                                                  |
| Different button label or placement            | "Feedback", bottom-right              | Edit `feedback-button.js` HTML / CSS                                            |
| Custom verification commands for the agent     | `pytest` / `node require()` defaults | Override `VERIFICATION_COMMANDS` at routine registration                       |

Customizations that break the invariants in `CONCEPT.md` are out of scope — refuse and explain why.

Record the user's choices; they feed Stages 4 and 5.

## Stage 4 — Plan

Do not edit any of the user's files until they've approved the plan.

Produce a written plan with these sections, populated with concrete values:

```
## Plan

### Detected
- Stack: <e.g. "FastAPI 0.110, Jinja2 templates">
- App file: <path>
- Templates dir: <path>; base template: <path>
- Static mount: <e.g. "/static" → ./static/>
- Hosting: <local dev | VPS w/ direct git | managed platform | static-only | …>
- GitHub remote: <slug or "none">

### Adaptation
<which adaptation file, and why>

### Customizations
<list of changes from defaults, per Stage 3>

### Files to add (Capture)
- <path> ← reference/feedback.py
- <path> ← reference/feedback-button.js
- <path> ← seed feedback.md ("# Feedback\n\n") if absent

### Files to patch (Capture)
- <app file>: insert POST /feedback endpoint (sentinel-wrapped, idempotent)
- <base template>: insert <script type="module"> calling initFeedback()

### Preview
- Tailored preview written to <path-in-user-repo>, e.g. `tmp/feedback-preview.html`.
- User opens it in a browser to see the modal as it'll appear after install.
- Re-render after any customization change.

### Capture verification
- Start the app, click Feedback, submit a test entry, confirm it lands in feedback.md.

### Optional Agent loop
- Will offer after Capture is verified. Platforms the user mentioned/uses: <list>.
- Recommended trigger surfaces: nightly + Expedite (default).
- If declined, Capture stands on its own.

### Risks / open questions
- <e.g. "render.yaml builds from /app — is that on a persistent volume? If not, git push won't survive restart.">
```

### Producing the preview

Copy `preview/index.html` from the kit into the user's project at a scratch path (e.g. `tmp/feedback-preview.html` or `.feedback-kit/preview.html`). Adjust:

- The `import` path so it resolves to wherever `feedback-button.js` will land after install — for the duration of the preview, point it at the kit's source via a relative path or a `raw.githubusercontent.com` URL.
- The `readConfig()` defaults so they reflect the customizations chosen in Stage 3 (Expedite on/off, toolName, etc.).
- If the user renamed Bug/Feature, also patch the `<option>` labels in the inlined `HTML` constant of the JS file you preview (or pre-patch the JS and reference the patched copy).

Tell the user the path. They open it in a browser and confirm the styling/behavior is what they want before sign-off. They can edit the preview file directly — those edits guide your Stage 5 implementation.

Then explicitly: **"Does this plan look right? Any changes before I implement?"** Wait for the answer. Revise and re-present if redirected.

## Stage 5 — Implement Capture

After plan sign-off:

1. **Place `feedback.py`** where the server-side code can import it.
2. **Place `feedback-button.js`** in the project's static dir (apply any customizations from Stage 3).
3. **Wire the receive path** — paste the matching `reference/endpoints/<fw>.<ext>` into the app file, apply customizations.
4. **Add the script tag** near `</body>`:
   ```html
   <script type="module">
     import { initFeedback } from '/<static-mount>/feedback-button.js';
     initFeedback({
       endpoint: '/feedback',
       toolName: '<project-slug>',
       expedite: <true|false per Stage 3>,
     });
   </script>
   ```
5. **Seed `feedback.md`** with `# Feedback\n\n` at the configured path if absent.
6. **Delete the preview scratch file** if you made one in Stage 4.

### Idempotency requirements

- The endpoint snippet is sentinel-wrapped (`# --- feedback endpoint ---` / `// ---`). Re-runs detect the sentinel and skip.
- The script tag is detected by searching for `feedback-button.js` in the base template.
- `feedback.md` is only seeded if absent.
- `feedback.py` and `feedback-button.js` are overwritten on re-run. Warn before overwriting if the user has hand-edited either.

Show `git status` and `git diff`. Do not commit — the user reviews and commits.

## Stage 6 — Verify Capture

Have the user:

1. Start the app.
2. Click the floating Feedback button.
3. Submit a test entry (type Bug, leave Expedite unchecked).
4. Confirm a new `- [ ]` entry appears at the bottom of `feedback.md`.
5. Confirm the metadata line includes `source: <page URL>`.

Don't move to Stage 7 until 4 and 5 both pass.

## Stage 7 — Offer Agent loop (optional)

Ask:

> Want to set up the optional scheduled agent now? It drains `feedback.md` into PRs against your default branch on whatever cadence you pick. Or skip and run Capture-only.

If declined, stop. Capture is fine on its own.

If accepted, pick a platform and register the agent. The prompt is the same; the wiring differs.

### Platform options

| Platform                    | Notes                                                                                                       |
| --------------------------- | ----------------------------------------------------------------------------------------------------------- |
| Claude.ai routines          | Register via the `schedule` skill in Claude Code. Auth = current Claude.ai account's GitHub OAuth.          |
| GitHub Actions cron         | `.github/workflows/feedback-drain.yml` on cron + `workflow_dispatch`. Install an LLM CLI inside the action. |
| OpenAI Assistant + scheduler| Assistant with shell + gh tools, triggered by Vercel cron / Cloudflare cron / cron-job.org / etc.           |
| Self-hosted cron            | Bare crontab + LLM CLI on a VPS.                                                                            |

### Step 7a — Surface the auth caveat

The agent will clone the user's repo, push branches, open PRs. It needs:

- Read+write GitHub access to the target repo via some identity.
- A way to invoke `gh pr create` (or the GitHub REST equivalent).

Platform specifics:

- **Claude.ai routines:** clones via the *current Claude.ai account's* GitHub OAuth. No per-routine secret. Account-switch with `/login` before registering if needed.
- **GitHub Actions:** uses `GITHUB_TOKEN` (read+write on the workflow's own repo) or a fine-grained PAT secret for cross-repo.
- **OpenAI / self-hosted:** GitHub PAT or deploy key you provide. Scope it to the one repo.

Verify auth with a manual fire before relying on the cron.

### Step 7b — Gather routine parameters

| Parameter                | Default                                                                                                                                                                          |
| ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GITHUB_REPO_URL`        | `git remote get-url origin` → normalized to `https://github.com/...`                                                                                                             |
| `GITHUB_REPO_SLUG`       | `org/name` form derived from the URL                                                                                                                                             |
| `DEFAULT_BRANCH`         | `git symbolic-ref refs/remotes/origin/HEAD` → `main` if unknown                                                                                                                  |
| `COMMIT_EMAIL`           | `git config user.email`                                                                                                                                                          |
| `COMMIT_NAME`            | `git config user.name`                                                                                                                                                           |
| `PROJECT_DESCRIPTION`    | First non-blank line of `README.md`, or one sentence from the user                                                                                                               |
| `REPO_LAYOUT_HINTS`      | Short string composed from the detected layout (e.g. `FastAPI app at app.py; templates/; static/; tests/`)                                                                       |
| `VERIFICATION_COMMANDS`  | Python: `python -c "import <root-module>"` and `pytest -x --timeout=60` (skip pytest if no `tests/`). Node/Express: `node -e "require('./<entry>')"`. Honor Stage 3 overrides. |
| `MAX_REAL_PRS`           | `3` per-run cap on non-Draft PRs                                                                                                                                                 |
| `CRON_EXPRESSION` (UTC)  | `0 10 * * *` UTC (≈ 03:00 PT). Ask for time zone; compute UTC. Honor Stage 3 overrides.                                                                                          |

### Step 7c — Render the prompt

Fetch `automation/routine-prompt.template.md` and substitute every `{{PLACEHOLDER}}` with the values from 7b. The template's content section between the `## Template` `````s is what feeds the platform.

### Step 7d — Register on the platform

- **Claude.ai routines:** hand the rendered prompt to the `schedule` skill — `create`, fully specified: `cron_expression`, `name = <project-slug>-feedback-drain`, `enabled: true`, `session_context.sources = <repo URL>`, `model: claude-sonnet-4-6`, `allowed_tools` covering Bash/Read/Write/Edit/Glob/Grep/Agent.
- **GitHub Actions:** add `.github/workflows/feedback-drain.yml`. Cron + `workflow_dispatch`. Install the chosen LLM CLI, pipe the rendered prompt into it. Set required secrets.
- **Other:** wherever the LLM agent runs on a cron, hand it the same rendered prompt.

### Step 7e — Wire the Expedite / on-submit trigger

If the user wants Expedite or on-submit, the submit endpoint kicks the scheduled agent. The reference endpoints have this as commented-out scaffolding controlled by `FEEDBACK_ROUTINE_ID` / `FEEDBACK_ROUTINE_TOKEN` env vars (Claude.ai routines shape). For other platforms, replace those calls with the platform's "run now" API (GitHub `workflow_dispatch`, OpenAI Assistant run create, Cloudflare Workers trigger URL, etc.).

Skip this step if the user opted for nightly only.

### Step 7f — Verify the loop

1. Manual fire of the scheduled agent. Watch the run log for `NIGHTLY-RUN-SUMMARY:` (working) or `AUTH-MISSING:` (broken).
2. End-to-end test: submit a tiny entry (e.g. `Bug: add a comment to README saying "Hello from feedback-kit"`) with Expedite checked. Within minutes, a PR should appear.

Print the agent's dashboard URL.

## Stage 8 — Wrap up

```
Installed (Capture):
  - <library path> (feedback.py)
  - <static path>/feedback-button.js
  - feedback.md (seeded)
Patched (Capture):
  - <app file>      (POST /feedback)
  - <base template> (initFeedback script tag)
Customizations applied:
  - <list>

Registered (Agent loop):
  - Platform: <…>
  - Cron: <expression> UTC
  - Triggers: nightly + <on-submit | expedite | none>
  - Dashboard: <url>

Next:
  - git add -p <files> && git commit
  - Submit a test entry; watch the first agent-opened PR.
```

If the Agent loop was skipped, omit the second block and add:

```
Capture is live. Re-invoke me later to wire up the optional agent loop.
```

## Where to fetch kit files from

Two options:

- **Copy from the cloned kit** if you `git clone`'d it.
- **Curl from GitHub raw:**

  ```bash
  KIT_REF=main   # bump to a tag/SHA in production
  BASE="https://raw.githubusercontent.com/tighe-ecc/feedback-kit/${KIT_REF}"
  curl -fsSL "${BASE}/reference/feedback.py"        -o feedback.py
  curl -fsSL "${BASE}/reference/feedback-button.js" -o <static-dir>/feedback-button.js
  ```

`reference/endpoints/<fw>.<ext>` are paste-fragments — read and inline, don't ship as files.

## When to refuse or escalate

- No recognizable project structure → ask, don't guess.
- Multiple plausible app files → ask which one; don't auto-pick.
- Hosting shape the user can't describe → walk them through `ssh in, git config --list, git push --dry-run`.
- Customization that breaks an invariant → refuse and explain which invariant.
- Agent loop can't work (no GitHub repo, no usable credentials) → install Capture, document the gap, leave the loop unwired.

## Format reference

```markdown
# Feedback

- [ ] **YYYY-MM-DD HH:MM — Bug: Title here**
  Optional description, possibly multi-line.
  Each line indented two spaces.
  _tool: my-app · source: http://localhost:8000/page · expedited_

- [x] **YYYY-MM-DD HH:MM — Feature: A resolved feature request**
  _tool: my-app · source: Manual input_
```

- Checkbox state (`[ ]` / `[x]`) is the entire status.
- `Bug` and `Feature` are the only two types (default; overridable per Stage 3).
- `: Title` is optional; if absent the headline is just `<ts> — <type>`.
- Metadata line is optional. Recognized keys: `tool`, `source`, `expedited`.
- All other indented lines under the bullet are part of the description.
