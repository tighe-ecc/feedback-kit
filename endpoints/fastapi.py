# --- feedback endpoint (FastAPI) -------------------------------------------
# Paste into your FastAPI app file (the one that has `app = FastAPI(...)`).
# Requires feedback.py at the project root or anywhere on sys.path.

import logging
import subprocess
from pathlib import Path

from fastapi import BackgroundTasks, Request
from feedback import note as _feedback_note

_FEEDBACK_LOG = logging.getLogger(__name__)


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


@app.post("/feedback")
async def feedback(request: Request, background_tasks: BackgroundTasks) -> dict[str, bool]:
    payload = await request.json()
    _feedback_note(
        payload.get("description", ""),
        type=payload.get("type", "bug"),
        title=payload.get("title") or None,
        tool=payload.get("tool") or None,
        url=payload.get("url") or None,
    )
    background_tasks.add_task(_git_sync_feedback)
    return {"ok": True}
# --- end feedback endpoint -------------------------------------------------
