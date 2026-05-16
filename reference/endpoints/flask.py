# --- feedback endpoint (Flask) ---------------------------------------------
# Paste into your Flask app file (the one that has `app = Flask(__name__)`).
# Requires feedback.py at the project root or anywhere on sys.path.
#
# Phase 2 trigger: set FEEDBACK_ROUTINE_ID and FEEDBACK_ROUTINE_TOKEN env vars
# after registering the routine (see DEPLOY.md step 4d). With them unset the
# endpoint still writes feedback.md; only the expedite trigger is no-op'd.

import logging
import os
import threading

from flask import request, jsonify
from feedback import note as _feedback_note

_FEEDBACK_LOG = logging.getLogger(__name__)

CLAUDE_ROUTINE_ID = os.environ.get("FEEDBACK_ROUTINE_ID")
CLAUDE_API_TOKEN = os.environ.get("FEEDBACK_ROUTINE_TOKEN")


def _expedite_routine() -> None:
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
def feedback():
    payload = request.get_json(force=True, silent=True) or {}
    expedited = bool(payload.get("expedite"))
    _feedback_note(
        payload.get("description", ""),
        type=payload.get("type", "bug"),
        title=payload.get("title") or None,
        tool=payload.get("tool") or None,
        url=payload.get("url") or None,
        expedited=expedited,
    )
    if expedited:
        threading.Thread(target=_expedite_routine, daemon=True).start()
    return jsonify({"ok": True})
# --- end feedback endpoint -------------------------------------------------
