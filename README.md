# feedback-kit

A minimal, framework-agnostic feedback collection drop-in. Three pieces:

1. **`feedback.py`** — stdlib-only Python library. `note(description, type, title, tool, url)` appends a structured entry to a project-local `feedback.md`. Also runnable as a CLI: `python -m feedback "..." --type bug`.
2. **`feedback-button.js`** — self-contained ES module. Floating button + modal, shadow-DOM isolated so it can't collide with your existing styles. POSTs JSON to a configurable endpoint.
3. **An endpoint** that bridges the JS POST → `feedback.note(...)`. Reference snippets for FastAPI, Flask, and Express are in `endpoints/`.

Feedback lives in a plain Markdown checklist (`feedback.md`) — open items are `- [ ]`, resolved are `- [x]`. Human-readable, diff-friendly, no database.

## Quick install (manual)

In the target project:

```bash
# 1. Drop the library at the project root
curl -O https://raw.githubusercontent.com/tighe-ecc/feedback-kit/main/feedback.py

# 2. Drop the UI into wherever you serve static assets
curl -o static/feedback-button.js https://raw.githubusercontent.com/tighe-ecc/feedback-kit/main/feedback-button.js

# 3. Seed the feedback file
echo "# Feedback" > feedback.md
```

Then paste the right `endpoints/*.{py,js}` snippet into your app file, and add this to your base HTML template:

```html
<script type="module">
  import { initFeedback } from '/static/feedback-button.js';
  initFeedback({ endpoint: '/feedback', toolName: 'my-app' });
</script>
```

## Automated install (Claude Code)

A companion Claude Code skill ships in this repo under [`skill/SKILL.md`](skill/SKILL.md). It detects your framework, picks the right endpoint snippet, copies files, and wires up the template — idempotent.

One-time install of the skill itself:

```bash
mkdir -p ~/.claude/skills/feedback-framework
curl -fsSL https://raw.githubusercontent.com/tighe-ecc/feedback-kit/main/skill/SKILL.md \
  -o ~/.claude/skills/feedback-framework/SKILL.md
```

Then in any target project: `/feedback-framework`.

## The entry format

`feedback.md` looks like this:

```markdown
# Feedback

- [ ] **2026-05-14 12:40 — Bug: Background updater not running**
  Not clear to me if background updates are not running or if the GUI just isn't updating?
  _tool: my-app · source: http://localhost:8000/_

- [x] **2026-05-11 09:11 — Feature: Add dark mode toggle**
  _tool: my-app · source: Manual input_
```

- `[ ]` = open, `[x]` = resolved (flip when done)
- Timestamp is local time, `YYYY-MM-DD HH:MM`
- `Bug` or `Feature` is required; `: Title` is optional
- Indented metadata line is optional (`_tool: X · source: URL_`)

## Drift discipline

If you tweak `feedback.py` or `feedback-button.js` in a downstream project, please upstream the change here and cut a new tag/SHA. The Claude skill pins to a `KIT_REF`; bumping that is the only way downstream installs pick up your changes.
