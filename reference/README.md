# Reference implementation

This is the canonical end-to-end implementation of the kit's concept. It's also the implementation running in [`tighe-ecc/mailroom`](https://github.com/tighe-ecc/mailroom).

**This is one valid path, not the only one.** It assumes the user's project is:

- A web app (FastAPI, Flask, or Express)
- Locally hosted, on the same machine as the project's git working tree
- Configured with `git push` access to the repo from that machine

If any of those don't match, see `../adaptations/` for the right pattern.

## Files

| File                              | Purpose                                                                                                                                                                                                          |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `feedback.py`                     | stdlib-only library. `note(description, type, title, tool, url, expedited)` appends an entry to `feedback.md` at the project root. Also runnable as a CLI: `python -m feedback "..." --type bug`.                |
| `feedback-button.js`              | Floating button + modal, shadow-DOM isolated. Posts JSON to a configurable endpoint. Includes a Submit/Expedite UX; Expedite is opt-in per entry.                                                                |
| `endpoints/fastapi.py`            | Paste-fragment for FastAPI apps. POST `/feedback` → `feedback.note(...)`, background-task git sync, optional expedite trigger.                                                                                   |
| `endpoints/flask.py`              | Same shape as the FastAPI snippet, for Flask.                                                                                                                                                                    |
| `endpoints/express.js`            | Same shape, for Express. Note: Express snippet has its own inline formatter — it doesn't share `feedback.py`. Kept in sync manually.                                                                              |

## What it does, end to end

1. User loads the app in a browser. `feedback-button.js` mounts a floating "Feedback" button.
2. User clicks it, fills in the modal (type / title / description / optional Expedite checkbox), clicks Submit.
3. Browser POSTs JSON to `/feedback`.
4. Endpoint calls `feedback.note(...)`, which appends a `- [ ] **...**` entry to `feedback.md` at the project root.
5. Endpoint kicks off a background `git add feedback.md && git commit && git push` so the entry lands on the default branch within seconds.
6. If `expedite` was true, endpoint additionally POSTs to the Claude routine's run endpoint, kicking the agent immediately.
7. The remote agent (see `../automation/`) clones the repo, drains unchecked entries, opens PRs.

## Drift discipline

If you tweak `feedback.py` or `feedback-button.js` in a downstream project (e.g. mailroom), **upstream the change here** and cut a new tag/SHA. The deploy procedure pins to a `KIT_REF`; bumping that is the only way downstream installs pick up the change.
