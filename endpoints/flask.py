# --- feedback endpoint (Flask) ---------------------------------------------
# Paste into your Flask app file (the one that has `app = Flask(__name__)`).
# Requires feedback.py at the project root or anywhere on sys.path.

from flask import request, jsonify
from feedback import note as _feedback_note


@app.post("/feedback")
def feedback():
    payload = request.get_json(force=True, silent=True) or {}
    _feedback_note(
        payload.get("description", ""),
        type=payload.get("type", "bug"),
        title=payload.get("title") or None,
        tool=payload.get("tool") or None,
        url=payload.get("url") or None,
    )
    return jsonify({"ok": True})
# --- end feedback endpoint -------------------------------------------------
