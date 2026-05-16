# Pattern: local dev server

The simplest case, and the one the `reference/` implementation is built for.

## When this applies

- The web app runs on your local machine (e.g., `uvicorn`, `flask run`, `npm run dev`).
- The project's git working tree is on the same machine the app process can see.
- You can `git push` from a terminal on that machine without prompts (SSH keys or stored creds).
- One developer (or a tight team) using the running app.

## What the kit looks like in this shape

Identical to the reference. Use `reference/feedback.py`, `reference/feedback-button.js`, and the matching endpoint snippet verbatim.

## Phase 1 checklist

1. Copy `reference/feedback.py` → `<repo>/feedback.py`.
2. Copy `reference/feedback-button.js` → `<repo>/<static-dir>/feedback-button.js` (typically `static/`).
3. Paste `reference/endpoints/<fastapi|flask|express>.<py|js>` into the app file (the one with `app = FastAPI(...)` / `Flask(__name__)` / `express()`).
4. Insert near `</body>` in the base template:
   ```html
   <script type="module">
     import { initFeedback } from '/static/feedback-button.js';
     initFeedback({ endpoint: '/feedback', toolName: '<project-slug>' });
   </script>
   ```
5. `test -f feedback.md || printf '# Feedback\n\n' > feedback.md`

## Phase 2 wiring

The reference endpoint already handles the expedite trigger via the `FEEDBACK_ROUTINE_ID` / `FEEDBACK_ROUTINE_TOKEN` env vars. After `automation/` produces a routine ID:

1. Add the two env vars to whatever sources your shell config / `.env`.
2. Restart the app.
3. Submit a test entry with Expedite checked — confirm the routine fires by checking `https://claude.ai/code/routines/<id>` for a new run.

## Gotchas

- **Background tasks block app shutdown briefly.** The FastAPI git-sync runs in `BackgroundTasks`; if you `Ctrl-C` mid-push, the entry is on disk but not on the remote. Re-running submit re-appends — manually clean up `feedback.md` if a partial run left it duplicated.
- **`git push` prompts.** If your terminal prompts for a passphrase or 2FA token, the endpoint's git push silently fails (logs only). Use a key-based SSH config or a credential helper.
- **`feedback.md` conflicts.** If you've edited `feedback.md` on another branch and merge later, the auto-pushes can conflict. Resolve manually; nothing in the kit is designed for that case.
