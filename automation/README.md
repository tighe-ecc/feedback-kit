# Automation

This directory holds the agent half of the loop — the value multiplier on top of Capture. The prompt template here is **the most important file in the kit's optional half** — it's the agent the user is actually buying when they choose to wire up autonomous sustaining.

## What the agent does

On its trigger (cron, on-submit webhook, or Expedite click), the agent:

1. Clones the target repo fresh.
2. Reads `feedback.md`.
3. Picks unchecked items, oldest first.
4. For each item: branches, spawns a sub-agent to implement, runs the project's verification gate, opens a PR (Draft if gate failed or item was too ambiguous to attempt with confidence).
5. Stops at the per-run real-PR cap (default 3). Skipped/Draft outcomes don't count.
6. Emits a structured summary line: `NIGHTLY-RUN-SUMMARY: real_prs=… draft_prs=… skipped_existing=… open_items_remaining=…`.

The agent **never edits `feedback.md`**. Checkbox flips (`[ ]` → `[x]`) happen when the human merges a PR and decides the item is resolved. This separation is load-bearing: the human's edit is the only "resolved" signal; PR-merge events are not.

## Platform-agnostic — pick your runtime

The prompt under `routine-prompt.template.md` is plain text instructions for an LLM agent. It assumes nothing about the platform — only that the agent has a shell, git, the GitHub CLI (or REST), and can spawn sub-agents (or do the implementation work itself).

Options for where to run it, roughly in order of how easy they are to set up:

| Platform                                | How                                                                                                                                                                                                                       |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Claude.ai routines**                  | The `schedule` skill in Claude Code can register the rendered prompt as a cron-scheduled remote routine. Single command, runs on Anthropic's compute. This is what the example below ([`tighe-ecc/mailroom`](https://github.com/tighe-ecc/mailroom)) uses. |
| **GitHub Actions cron**                 | A `.github/workflows/feedback-drain.yml` on cron + `workflow_dispatch`. Inside the action, install an LLM CLI (`claude`, `codex`, etc.) and pipe the rendered prompt into it. Free for public repos, plenty of free minutes for private ones.   |
| **OpenAI Assistants + an external scheduler** | Create an Assistant with tool access (shell + gh), and trigger it from a Vercel cron / Cloudflare Worker cron / cron-job.org / etc.                                                                                       |
| **Self-hosted cron on your VPS**        | A bare crontab + an LLM CLI is the most flexible option. No platform lock-in. You handle uptime.                                                                                                                          |

Whichever you pick, the prompt template is unchanged. The integration is purely about *how to invoke an agent on a schedule with these instructions*; the instructions themselves are stable.

## Triggers

The same prompt runs regardless of trigger. The three triggers wire to:

- **Nightly cron:** whatever scheduler you picked fires the prompt at the cron time. Default `0 10 * * *` UTC ≈ 03:00 PT.
- **On-submit:** the submit endpoint, after writing the entry, POSTs to the platform's "run now" endpoint (Claude routines `/run`, GitHub `workflow_dispatch`, OpenAI Assistant run create, etc.).
- **Expedite:** same as on-submit, but only fires when the user's submit payload had `expedite: true`.

The reference endpoints (FastAPI / Flask / Express) implement the Expedite trigger inline for the **Claude.ai routines** shape — fill in `FEEDBACK_ROUTINE_ID` and `FEEDBACK_ROUTINE_TOKEN` env vars and you're done. For other platforms, swap the trigger call in the endpoint for whatever your platform exposes.

## Auth caveat (read this before registering anything)

Whichever platform you pick, the scheduled agent will:

- Clone the user's GitHub repo.
- Push branches.
- Open PRs.

It needs some GitHub identity, and that identity needs write access to the target repo. The shape varies by platform:

- **Claude.ai routines:** the routine clones via the *current Claude.ai account's GitHub OAuth*. There is no per-routine secret. If the account doing the registration isn't the one with GitHub access to the target repo, the routine 404s on clone and prints `AUTH-MISSING:`. Switch Claude.ai accounts with `/login` before registering if needed.
- **GitHub Actions:** the workflow runs with `GITHUB_TOKEN` (read+write on the repo it's in by default) — usually fine. For cross-repo PRs, add a fine-grained PAT as a secret.
- **OpenAI / self-hosted:** the agent uses a GitHub PAT or deploy key you provide. Make it a fine-grained PAT scoped to one repo.

Whatever you choose, **verify auth with a manual fire of the agent before relying on the cron.** A first run that prints `AUTH-MISSING:` (or the platform's equivalent) is the cheapest way to find this out.

## Files here

- `routine-prompt.template.md` — the prompt the scheduled agent runs. `{{PLACEHOLDERS}}` get substituted at registration time. See the table at the top of that file for the substitution list.

## Registering the agent

The deploy procedure (`../DEPLOY.md` stage 5) walks through registration end-to-end. The short version:

1. Render the template with your project's values.
2. Hand it to whichever scheduler/agent platform you chose (see the table above).
3. Immediately fire it once on-demand to verify auth + permissions work.

After it runs, look for either the `NIGHTLY-RUN-SUMMARY:` line (working) or `AUTH-MISSING:` / platform-specific error (broken). Fix any auth issues, then trust the cron.

## Iterating on the prompt

The prompt is a stable interface — downstream installs render it and run it as-is, so changing it has blast radius. When you do edit it:

- Preserve the placeholders and their meanings. Existing deploys reference the template's structure via the deploy procedure.
- Preserve the `NIGHTLY-RUN-SUMMARY:` and `AUTH-MISSING:` sentinel lines — they're how the user (and any monitoring) distinguishes a quiet-night run from a broken agent.
- Test changes against a real `feedback.md` before pushing. The prompt is easy to get wrong in ways that only show up at run time.
- The prompt is LLM-platform-agnostic, but different agents have different tool surfaces. If you reference a tool name (e.g. "the Agent tool" for Claude Code sub-agents), keep it generic enough that a Codex/Cursor/etc. agent can do the equivalent.
