# --- feedback endpoint (FastAPI) -------------------------------------------
# Paste into your FastAPI app file (the one that has `app = FastAPI(...)`).
# Requires feedback.py at the project root or anywhere on sys.path.
#
# Phase 2 trigger: set FEEDBACK_ROUTINE_ID and FEEDBACK_ROUTINE_TOKEN env vars
# after registering the routine (see DEPLOY.md step 4d). With them unset the
# endpoint still writes feedback.md and git-syncs; only the expedite trigger
# is no-op'd.

import logging
import os
import subprocess
from pathlib import Path

from fastapi import BackgroundTasks, Request
from feedback import note as _feedback_note

_FEEDBACK_LOG = logging.getLogger(__name__)

CLAUDE_ROUTINE_ID = os.environ.get("FEEDBACK_ROUTINE_ID")
CLAUDE_API_TOKEN = os.environ.get("FEEDBACK_ROUTINE_TOKEN")


def _git_sync_feedback() -> None:
    repo = str(Path(__file__).resolve().parent)
    try:
        subprocess.run(["git", "-C", repo, "add", "feedback.md"], check=True, capture_output=True, text=True, timeout=10)
        if subprocess.run(["git", "-C", repo, "diff", "--cached", "--quiet"], timeout=10).returncode == 0:
            return
        subprocess.run(["git", "-C", repo, "commit", "-m", "feedback: sync new entry"], check=True, capture_output=True, text=True, timeout=10)
        subprocess.run(["git", "-C", repo, "push"], check=True, capture_output=True, text=True, timeout=30)
    except subprocess.CalledProcessError as exc:
        _FEEDBACK_LOG.warning("feedback git-sync failed: %s\n%s", exc, exc.stderr)
    except Exception as exc:
        _FEEDBACK_LOG.warning("feedback git-sync error: %s", exc)


def _expedite_routine() -> None:
    """Kick the remote Claude routine to drain feedback.md immediately."""
    if not (CLAUDE_ROUTINE_ID and CLAUDE_API_TOKEN):
        _FEEDBACK_LOG.info("expedite requested but no routine configured")
        return
    try:
        import urllib.request
        req = urllib.request.Request(
            f"https://claude.ai/api/routines/{CLAUDE_ROUTINE_ID}/run",
            method="POST",
            headers={
                "Authorization": f"Bearer {CLAUDE_API_TOKEN}",
                "Content-Type": "application/json",
            },
            data=b"{}",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            _FEEDBACK_LOG.info("expedite trigger: %s", resp.status)
    except Exception as exc:
        _FEEDBACK_LOG.warning("expedite trigger failed: %s", exc)


@app.post("/feedback")
async def feedback(request: Request, background_tasks: BackgroundTasks) -> dict[str, bool]:
    payload = await request.json()
    expedited = bool(payload.get("expedite"))
    _feedback_note(
        payload.get("description", ""),
        type=payload.get("type", "bug"),
        title=payload.get("title") or None,
        tool=payload.get("tool") or None,
        url=payload.get("url") or None,
        expedited=expedited,
    )
    background_tasks.add_task(_git_sync_feedback)
    if expedited:
        background_tasks.add_task(_expedite_routine)
    return {"ok": True}
# --- end feedback endpoint -------------------------------------------------
