# --- feedback endpoint (FastAPI) -------------------------------------------
# Paste into your FastAPI app file (the one that has `app = FastAPI(...)`).
# Requires feedback.py at the project root or anywhere on sys.path.

from fastapi import Request
from feedback import note as _feedback_note


@app.post("/feedback")
async def feedback(request: Request) -> dict[str, bool]:
    payload = await request.json()
    _feedback_note(
        payload.get("description", ""),
        type=payload.get("type", "bug"),
        title=payload.get("title") or None,
        tool=payload.get("tool") or None,
        url=payload.get("url") or None,
    )
    return {"ok": True}
# --- end feedback endpoint -------------------------------------------------
