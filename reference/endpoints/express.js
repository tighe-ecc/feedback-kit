// --- feedback endpoint (Express) ------------------------------------------
// Paste into your Express app file (the one that has `const app = express()`).
// Requires `app.use(express.json())` (or body-parser) earlier in the file.
//
// Phase 2 trigger: set FEEDBACK_ROUTINE_ID and FEEDBACK_ROUTINE_TOKEN env vars
// after registering the routine (see DEPLOY.md step 4d). With them unset the
// endpoint still writes feedback.md; only the expedite trigger is no-op'd.

const fs = require('fs');
const path = require('path');

const FEEDBACK_FILE = path.join(__dirname, 'feedback.md');
const CLAUDE_ROUTINE_ID = process.env.FEEDBACK_ROUTINE_ID;
const CLAUDE_API_TOKEN = process.env.FEEDBACK_ROUTINE_TOKEN;

function appendFeedback({ description, type = 'bug', title, tool, url, expedited = false }) {
  if (!description || !description.trim()) {
    throw new Error('description is required');
  }
  const ts = new Date().toISOString().slice(0, 16).replace('T', ' ');
  const label = type === 'feature' ? 'Feature' : 'Bug';
  const headline = title ? `${ts} — ${label}: ${title}` : `${ts} — ${label}`;
  const lines = [`- [ ] **${headline}**`];
  for (const line of description.trim().split('\n')) {
    lines.push(`  ${line}`.replace(/\s+$/, ''));
  }
  const meta = [];
  if (tool) meta.push(`tool: ${tool}`);
  if (url) meta.push(`source: ${url}`);
  if (expedited) meta.push('expedited');
  if (meta.length) lines.push(`  _${meta.join(' · ')}_`);
  if (!fs.existsSync(FEEDBACK_FILE)) {
    fs.writeFileSync(FEEDBACK_FILE, '# Feedback\n\n');
  }
  fs.appendFileSync(FEEDBACK_FILE, lines.join('\n') + '\n');
}

async function expediteRoutine() {
  if (!CLAUDE_ROUTINE_ID || !CLAUDE_API_TOKEN) {
    console.info('expedite requested but no routine configured');
    return;
  }
  try {
    const res = await fetch(`https://claude.ai/api/routines/${CLAUDE_ROUTINE_ID}/run`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${CLAUDE_API_TOKEN}`,
        'Content-Type': 'application/json',
      },
      body: '{}',
    });
    console.info(`expedite trigger: ${res.status}`);
  } catch (err) {
    console.warn(`expedite trigger failed: ${err.message}`);
  }
}

app.post('/feedback', (req, res) => {
  try {
    const body = req.body || {};
    const expedited = Boolean(body.expedite);
    appendFeedback({ ...body, expedited });
    if (expedited) expediteRoutine();
    res.json({ ok: true });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});
// --- end feedback endpoint ------------------------------------------------
