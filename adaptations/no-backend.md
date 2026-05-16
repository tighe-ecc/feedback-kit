# Pattern: no backend

There is no server-side endpoint to POST to. This is the case for:

- Pure static sites (GitHub Pages, Netlify deploys with no functions, S3+CloudFront, etc.)
- Mobile apps (no shared backend service for feedback specifically)
- Desktop / CLI tools that aren't running in a browser
- Libraries used as dependencies in other people's projects

You still want the **agent loop** — that's the value. You just need a different shape for the capture half.

## Pick a sub-pattern

Three options, in increasing order of friction:

### Option A: GitHub Issues as the queue

Don't use `feedback.md` at all. Use GitHub Issues with a specific label as the queue. The capture surface is a deep link to the new-issue form pre-filled with a template.

**Phase 1:** No backend needed. `feedback-button.js` opens `https://github.com/<owner>/<repo>/issues/new?labels=feedback&template=feedback.md&title=...` in a new tab.

**Phase 2:** The agent reads `gh issue list --label feedback --state open` instead of `feedback.md`. PRs reference the issue number; merging closes the issue. The routine prompt template needs adjustment — see "Adjusting the agent prompt" below.

**Trade-offs:** Requires the user to be logged into GitHub to submit. Provenance comes from GitHub's issue metadata, not your app's URL. The agent prompt is more complex (more GitHub API calls), but it works for fully-static deploys and mobile apps. **The Expedite affordance still works** — the submit flow can also hit a webhook trigger.

### Option B: Form-service intermediary

Use a generic form-to-something service (Formspree, Web3Forms, a Cloudflare Worker you wrote in 10 lines) as the receive endpoint. The service writes to GitHub via the Contents API (same as `remote-host-github-api.md`).

**Phase 1:** `feedback-button.js` POSTs to the form service URL. The form service does the GitHub commit. From the app's perspective there's no backend.

**Trade-offs:** You now own the form service (or trust a SaaS). For personal projects this is fine; for anything bigger you've added a dependency.

### Option C: `feedback.py` as a CLI on the user's machine

For CLI tools or libraries where the user is a developer with the repo cloned, ship `feedback.py` as part of the tool. Provide a command:

```bash
mytool feedback "the thing that's broken" --type bug --title "Title"
```

…which calls `feedback.note(...)` and writes to `<repo>/feedback.md` locally. The user `git commit && git push` themselves. The agent loop runs from there as normal.

**Trade-offs:** Friction at submit time. No in-app button. Right for tools where the user is technical enough that "type two commands" isn't a barrier.

## Adjusting the agent prompt

If you go with Option A (GitHub Issues queue), the routine prompt in `automation/routine-prompt.template.md` needs changes:

- Replace "Read `feedback.md` at repo root" → "Run `gh issue list --label feedback --state open --json number,title,body,createdAt` and parse the response."
- Replace the deterministic branch-name slug computation to use the issue number: `fix/feedback-<issue-number>` instead of the SHA1 slug.
- Replace the skip check (`gh pr list --head <branch>`) — same shape, just keyed on the new branch name.
- The PR body template should reference the issue (`Closes #<n>`) so merging auto-closes it.

If you go with Option B or C, no prompt changes — `feedback.md` is still the source of truth, you just got it there a different way.

## Phase 2 trigger options

- **Nightly cron:** Works for all three sub-patterns. No app involvement needed.
- **On-submit / Expedite:** Works for A (the form-submit step can also hit the routine's run endpoint) and B (the form service does it). Doesn't work for C unless the CLI command also fires the trigger, which it can.

## When to use which sub-pattern

| Situation                                                        | Pick     |
| --------------------------------------------------------------- | -------- |
| Public static site; users may not have GitHub accounts          | B        |
| Static site; users are developers who have GitHub accounts      | A        |
| Mobile app; users have GitHub accounts                          | A        |
| Mobile app; users do not                                        | B        |
| CLI tool / library; users are devs cloning the repo             | C        |
| You want the smallest possible thing                            | A        |
