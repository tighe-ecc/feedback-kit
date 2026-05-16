# Deploy

This file is the procedure a code-generation agent (Claude Code, Codex, Cursor, Aider, anything similar) follows when a user points it at this repo and says "implement this in my project."

**Audience: the agent.** A human can read it as a checklist, but it's written assuming the reader is doing the install autonomously, in the user's project as the working directory.

Read `CONCEPT.md` first. The invariants at the bottom of that file are non-negotiable; everything below assumes you're preserving them.

## The two halves of the kit

The kit has two installable halves:

- **Capture** — the in-app Feedback button (Bug/Feature/Expedite), the receive endpoint, and the `feedback.md` queue at the repo root.
- **Agent loop** — a scheduled remote agent that drains `feedback.md` into PRs against the user's default branch.

The pitch — autonomous sustaining engineering — depends on both. But they ship independently. **Install Capture first, verify it works, then offer the Agent loop as an optional second step.** A user with no remote-agent infrastructure can still get value from Capture as a structured complaint board with provenance; they can wire the loop later when they're ready.

## Workflow

Five stages. Don't skip stages, and especially don't skip Plan.

1. **Confirm the concept.** Restate it back to the user. Catch wrong-fit cases now.
2. **Discover.** Read this repo end-to-end. Read the user's project end-to-end. Pick an adaptation pattern that matches.
3. **Plan.** Build a concrete plan — exact file paths, exact patches, framework-specific details — and present it to the user. Wait for sign-off before touching anything.
4. **Implement Capture.** Apply the plan idempotently. Show the diff. Have the user verify the button works end-to-end before continuing.
5. **Offer the Agent loop.** Walk the user through registering a scheduled agent on their preferred platform. They can decline; Capture stands on its own.

---

## Stage 1 — Confirm the concept

Restate the concept back to the user in plain English:

> This kit installs a "Feedback" button in your running app. Users submit bugs and feature requests (with an optional "Expedite" checkbox); submissions append to `feedback.md` at your repo root. Optionally, a scheduled agent — running on whatever LLM platform you prefer — drains that queue into PRs against your default branch. You stay focused on reviewing the PRs; the agent handles the mechanical implementation.
>
> Is that the shape you want?

Stop and recommend something else if:

- They want a real ticket system with assignees, statuses, labels → GitHub Issues / Linear.
- They want feedback to be private, not in git → out of scope; the queue is in the repo by design.
- They want the agent to merge its own PRs → out of scope; human review is the safety layer.
- They want feedback collection but explicitly *no* agentic implementation, even later → Capture still works for them, but they're not getting the kit's headline value. Confirm they understand and continue.

Green light? Move on.

## Stage 2 — Discover

You can't plan without knowing constraints. Two parallel investigations:

### 2a — Read this repo

If you haven't already, fetch the kit's docs in this order:

1. `README.md` (orientation)
2. `CONCEPT.md` (invariants — anything you plan must respect these)
3. `DEPLOY.md` (this file)
4. `reference/README.md` and the files under `reference/` (the example end-to-end)
5. `adaptations/README.md` (index) and skim every pattern in `adaptations/`
6. `automation/README.md` and `automation/routine-prompt.template.md`

If you can `git clone` the kit to a temp dir, do that — much faster than fetching docs one-at-a-time over HTTP.

### 2b — Read the user's project

Find out, by inspection where possible:

- **What is the project?** Web app / CLI / library / mobile / static site / mixed.
- **What stack?** Read `pyproject.toml`, `package.json`, `Gemfile`, `go.mod`, etc.
- **What's the entry point?** The file with `app = FastAPI(...)` / `Flask(__name__)` / `express()` / equivalent.
- **Where do templates and static assets live?** Look for `app.mount("/static"`, `express.static(...)`, Flask defaults, etc.
- **Where does the app run?** Local dev box / VPS / managed platform (Vercel/Lambda/etc.) / static. If the project has `Dockerfile` / `vercel.json` / `render.yaml` / `fly.toml` / `wrangler.toml`, infer from that.
- **Is the project a git repo with a GitHub remote?** `git remote -v`. Phase 2 needs this; Capture works without.

**Don't ask the user questions whose answers are already in their repo.** Only ask when inspection genuinely can't tell you — e.g., "this looks like it deploys to a VPS, but can the running process `git push` from there?"

### 2c — Pick an adaptation

`adaptations/` has one short doc per shape:

| Situation                                                                                       | Adaptation                                                                                                  |
| ----------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| FastAPI / Flask / Express, locally hosted, has `git push` access                                | `adaptations/local-dev-server.md` (matches `reference/`)                                                    |
| Same stack, deployed on a VPS / container where the process can `git push`                      | `adaptations/remote-host-direct-git.md`                                                                     |
| Same stack, managed platform with read-only filesystem (Vercel / Lambda / etc.)                 | `adaptations/remote-host-github-api.md`                                                                     |
| No backend (static site, mobile app, CLI tool, library)                                         | `adaptations/no-backend.md`                                                                                  |
| Stack not in the reference (Django, Rails, Next.js, Go, Rust)                                   | `adaptations/novel-stack.md`                                                                                |

If none fit cleanly, plan a custom approach that preserves the invariants. Don't silently invent a shape.

## Stage 3 — Plan (present to user, wait for sign-off)

This stage is non-negotiable. Do not edit any of the user's files until they've approved the plan.

Produce a written plan with these sections, all populated with concrete values from your discovery:

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

### Files to add (Capture)
- <path> ← reference/feedback.py
- <path> ← reference/feedback-button.js
- <path> ← seed feedback.md (`# Feedback\n\n`) if absent

### Files to patch (Capture)
- <app file>: insert POST /feedback endpoint (sentinel-wrapped, idempotent)
- <base template>: insert <script type="module"> calling initFeedback()

### Capture verification
- Start the app, click Feedback, submit a test entry, confirm it lands in feedback.md.

### Optional agent loop
- Will offer Phase 2 after Capture is verified. Platforms the user mentioned/uses: <list>.
- Recommended trigger surfaces: nightly + Expedite (default).
- If declined, Capture stands on its own.

### Risks / open questions for you to answer
- <e.g. "Your render.yaml builds from /app — is /app on a persistent volume? If not, git push won't survive restart.">
- <e.g. "Multiple plausible app files; please confirm which one is the FastAPI entry point.">
```

Then explicitly: **"Does this plan look right? Any changes before I implement?"** Wait for the answer. If the user redirects, revise the plan and present again.

## Stage 4 — Implement Capture

Once the user approves the plan, apply it. The shared shape across adaptations:

1. **Place `feedback.py`.** Drop the library where the server-side code can import it. Reference path is the repo root.
2. **Place `feedback-button.js`.** Where the browser can fetch it — usually the project's static dir.
3. **Wire the receive path.** For HTTP backends: a `POST /feedback` endpoint calling `feedback.note(...)`. Use the matching snippet from `reference/endpoints/`. For non-HTTP shapes, see the adaptation.
4. **Add the script tag** near `</body>` in the base template:
   ```html
   <script type="module">
     import { initFeedback } from '/<static-mount>/feedback-button.js';
     initFeedback({
       endpoint: '/feedback',
       toolName: '<project-slug>',
       expedite: true,  // show the Expedite checkbox; default true
     });
   </script>
   ```
5. **Seed `feedback.md`.** `# Feedback\n\n` at the repo root if absent.

**Idempotency requirements:**

- The endpoint snippet is delimited by `# --- feedback endpoint ---` / `# --- end feedback endpoint ---` (Python) or `//`-style sentinels (JS). Re-runs detect the sentinel and skip.
- The script tag is detected by searching for `feedback-button.js` in the template.
- `feedback.md` is only seeded if absent.
- `feedback.py` and `feedback-button.js` overwrite on re-run — that's how kit updates propagate. **Warn before overwriting if the user has hand-edited either.**

After implementing, show `git status` and `git diff`. **Do not commit** — the user reviews and commits themselves.

### Verify Capture end-to-end

Don't claim success without a live test. Ask the user to:

1. Start the app (or open the static page).
2. Click the floating "Feedback" button (bottom-right).
3. Submit a test entry — type bug, give it a title, a one-line description, leave Expedite unchecked.
4. Confirm a new `- [ ]` entry appeared at the bottom of `feedback.md`.
5. Confirm the metadata line includes `source: <the URL the user was on>`.

If 4 fails, debug the endpoint. If 5 fails, debug the JS payload. Don't move to Stage 5 until both pass.

## Stage 5 — Offer the Agent loop (optional)

After Capture is verified, ask:

> The kit's full pitch is autonomous sustaining engineering — a scheduled agent that drains `feedback.md` into PRs while you sleep. Want to set that up now, or skip and run with Capture-only for a while?

If they decline, **stop here**. Capture works perfectly on its own; they can come back to this later.

If they accept, walk through the loop setup. The loop is **LLM-platform-agnostic** — the same prompt works wherever you can run a scheduled agent. Mailroom uses Claude.ai routines as a working example. Other options:

- **Claude.ai routines** (`schedule` skill on Claude Code) — simplest if the user is already in the Claude ecosystem. Single command to register.
- **OpenAI Assistants + scheduler** — Assistant with the right tools (shell, gh CLI), triggered by Vercel cron / GitHub Actions / Cloudflare cron.
- **A GitHub Actions cron** that shells out to an LLM CLI (`claude`, `codex`, etc.) inside the action and passes the rendered prompt.
- **A self-hosted cron** on the user's VPS that runs an LLM CLI with the prompt.

Pick the platform that matches the user's existing infrastructure. Don't insist on Claude.ai routines if the user is an OpenAI shop. Ask if you're unsure.

### Step 5a — Surface the auth caveat

Whichever platform: the scheduled agent will clone the user's repo and push branches. It needs:

- Read+write GitHub access to the target repo, as some identity that's allowed to push and open PRs.
- A way to invoke `gh pr create` (or the GitHub API equivalent).

For **Claude.ai routines** specifically: the routine runs as the GitHub identity that the *current Claude.ai account* is OAuthed to. If the user is signed into Claude Code on a work account that can't reach their personal repo, the routine 404s on clone. Make them confirm the right account before registering. They can switch with `/login` on Claude Code.

For other platforms, the equivalent: confirm the credentials the scheduled job will use can push to the target repo. Test with `git push --dry-run` on the host (or a one-off run of the workflow).

### Step 5b — Gather routine parameters

Compute defaults from the project; let the user override before submitting:

| Parameter                | Default                                                                                                                                                                            |
| ------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `GITHUB_REPO_URL`        | `git remote get-url origin` → normalized to `https://github.com/...`                                                                                                               |
| `GITHUB_REPO_SLUG`       | `org/name` form derived from the URL                                                                                                                                               |
| `DEFAULT_BRANCH`         | `git symbolic-ref refs/remotes/origin/HEAD` → `main` if unknown                                                                                                                    |
| `COMMIT_EMAIL`           | `git config user.email`                                                                                                                                                            |
| `COMMIT_NAME`            | `git config user.name`                                                                                                                                                             |
| `PROJECT_DESCRIPTION`    | First non-blank line of `README.md`, trimmed; or one sentence the user provides                                                                                                    |
| `REPO_LAYOUT_HINTS`      | A short string you compose from the detected layout (e.g. `FastAPI app at app.py; templates/; static/; tests/`)                                                                    |
| `VERIFICATION_COMMANDS`  | Python: `python -c "import <root-module>"` and `pytest -x --timeout=60` (skip pytest if no `tests/`). Node/Express: `node -e "require('./<entry>')"`. Let the user override.       |
| `MAX_REAL_PRS`           | `3` (per-run cap on non-Draft PRs to prevent runaway runs)                                                                                                                         |
| `CRON_EXPRESSION` (UTC)  | `0 10 * * *` (≈ 03:00 PT). Ask for time zone; compute UTC.                                                                                                                          |

### Step 5c — Render the prompt

Fetch `automation/routine-prompt.template.md` and substitute every `{{PLACEHOLDER}}` with the values from 5b. The template's content section (between the `## Template` `````s) is what you'll feed to the platform.

### Step 5d — Register on the chosen platform

Platform-specific:

- **Claude.ai routines:** hand the rendered prompt to the `schedule` skill. `create`, fully specified: `cron_expression`, `name` = `<project-slug>-feedback-drain`, `enabled: true`, `session_context.sources` = the target repo URL, `model: claude-sonnet-4-6`, `allowed_tools` covering Bash/Read/Write/Edit/Glob/Grep/Agent.
- **GitHub Actions:** add a `.github/workflows/feedback-drain.yml` that runs on cron and `workflow_dispatch`. Inside, `pip install` (or `npm install -g`) the user's chosen LLM CLI, then pipe the rendered prompt into it. Make sure the workflow has the secrets it needs (GitHub token with PR-write scope, plus the LLM API key).
- **Other:** the prompt is just text — wherever you can run an LLM agent on a cron, you can register this. Be specific to the platform when documenting steps for the user.

### Step 5e — Wire the Expedite / on-submit trigger

If the user wants Expedite or on-submit, the submit endpoint kicks the scheduled agent in addition to writing `feedback.md`. The reference endpoints have this as commented-out scaffolding controlled by `FEEDBACK_ROUTINE_ID` / `FEEDBACK_ROUTINE_TOKEN` env vars (Claude.ai routines shape). For other platforms, replace those env vars with whatever your platform exposes — a `workflow_dispatch` POST to GitHub's API, a Cloudflare Workers trigger URL, an OpenAI Assistant run create, etc.

If the user said "nightly only," skip this step.

### Step 5f — Verify the loop

Two checks:

1. **Manual fire.** Trigger the scheduled agent on-demand and watch its run log. Expect either:
   - `NIGHTLY-RUN-SUMMARY: real_prs=… draft_prs=… skipped_existing=… open_items_remaining=…` → the loop works.
   - `AUTH-MISSING: …` → credentials don't reach the target repo. Fix and re-fire.
2. **End-to-end via Expedite.** Submit a tiny test entry (e.g. "Bug: add a comment to README saying 'Hello from feedback-kit'") with Expedite checked. Within a few minutes, a PR should appear. Confirm with the user.

Print the agent's URL/dashboard one last time so they can bookmark it.

## Stage 6 — Wrap up

Print a short summary of what landed:

```
Installed (Capture):
  - <library path> (feedback.py)
  - <static path>/feedback-button.js
  - feedback.md (seeded)
Patched (Capture):
  - <app file>      (POST /feedback)
  - <base template> (initFeedback script tag)

Registered (Agent loop):
  - Platform: <Claude.ai routines | GitHub Actions | …>
  - Cron: <expression> UTC
  - Triggers: nightly + <on-submit | expedite | none>
  - Dashboard: <url>

Next:
  - git add -p <files> && git commit
  - Watch for the first agent-opened PR.
```

If the user skipped the Agent loop, omit the second block and end with:

```
Capture is live. Re-invoke me later when you're ready to wire up the optional agent loop.
```

## Where to fetch the kit files from

When implementing, you need to put `feedback.py` and `feedback-button.js` into the user's project. Two equally-good ways:

- **Copy from the cloned kit.** If you `git clone`'d the kit to read these docs, you already have the files locally. `cp` them.
- **Curl from GitHub raw.** Useful if you only fetched docs via web fetch:

  ```bash
  KIT_REF=main   # bump to a tag/SHA in production
  BASE="https://raw.githubusercontent.com/tighe-ecc/feedback-kit/${KIT_REF}"
  curl -fsSL "${BASE}/reference/feedback.py"        -o feedback.py
  curl -fsSL "${BASE}/reference/feedback-button.js" -o <static-dir>/feedback-button.js
  ```

  The endpoint snippets at `reference/endpoints/<fw>.<ext>` are paste-fragments — read them and inline their content, don't ship them as files.

If the user wants to pin to a kit version, bump `KIT_REF` to a tag or SHA. The kit's `main` is the trunk; it can change.

## When to refuse or escalate

- **No recognizable project structure** — no `package.json`, `pyproject.toml`, etc. Ask. Don't guess.
- **Multiple plausible app files.** Ask which one. Don't auto-pick.
- **Hosting shape the user can't describe.** Walk them through it (`ssh in, git config --list, git push --dry-run`). Don't assume.
- **They want the kit but with one invariant broken** ("use JSON not Markdown", "let the agent merge directly"). Push back hard. Most invariants exist for a specific reason in the agent prompt; quietly breaking one breaks Phase 2.
- **Phase 2 can't work** (no GitHub repo, no credentials they can wire). Install Capture, document the gap, leave the loop unwired with a clear note.

## Format reference

For agents reading or writing `feedback.md`:

```markdown
# Feedback

- [ ] **YYYY-MM-DD HH:MM — Bug: Title here**
  Optional description, possibly multi-line.
  Each line indented two spaces.
  _tool: my-app · source: http://localhost:8000/page · expedited_

- [x] **YYYY-MM-DD HH:MM — Feature: A resolved feature request**
  _tool: my-app · source: Manual input_
```

- The checkbox state (`[ ]` / `[x]`) is the entire status.
- `Bug` and `Feature` are the only two types.
- `: Title` is optional; if absent the headline is just `<ts> — <type>`.
- The trailing `_..._` metadata line is optional. Recognized keys: `tool`, `source`, `expedited` (presence-only marker that the entry was expedited at submit time).
- All other lines under the bullet are part of the description.
