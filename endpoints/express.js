// --- feedback endpoint (Express) ------------------------------------------
// Paste into your Express app file (the one that has `const app = express()`).
// Requires `app.use(express.json())` (or body-parser) earlier in the file.

const fs = require('fs');
const path = require('path');

const FEEDBACK_FILE = path.join(__dirname, 'feedback.md');

function appendFeedback({ description, type = 'bug', title, tool, url }) {
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
  if (meta.length) lines.push(`  _${meta.join(' · ')}_`);
  if (!fs.existsSync(FEEDBACK_FILE)) {
    fs.writeFileSync(FEEDBACK_FILE, '# Feedback\n\n');
  }
  fs.appendFileSync(FEEDBACK_FILE, lines.join('\n') + '\n');
}

app.post('/feedback', (req, res) => {
  try {
    appendFeedback(req.body || {});
    res.json({ ok: true });
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});
// --- end feedback endpoint ------------------------------------------------
