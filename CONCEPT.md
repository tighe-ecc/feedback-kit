# Concept

In-app feedback button writes to `feedback.md` at the repo root; an optional scheduled agent reads the queue and opens PRs against the default branch.

## Components

1. **Capture button.** Floating button in the running app. Modal fields: type (Bug/Feature), title, description, optional Expedite checkbox. Submit appends to `feedback.md`. Provenance (timestamp, page URL, tool name) is auto-captured.
2. **Queue file.** `feedback.md` at the repo root. Markdown checklist. `- [ ]` open, `- [x]` resolved. Diff-friendly, version-controlled with the code.
3. **Scheduled agent (optional).** Clones the repo, reads `feedback.md`, picks unchecked items, implements each on its own branch, runs the project's verification gate, opens a PR. Never edits `feedback.md`. The human merges PRs and flips checkboxes.

## Two halves install separately

- **Capture** (components 1 + 2). Standalone-useful as a complaint board with provenance.
- **Agent loop** (component 3). Adds autonomous PR drafting. Can be wired later without changes to Capture.

## Trigger surfaces (Agent loop)

| Trigger      | Latency      | Use when                                                                       |
| ------------ | ------------ | ------------------------------------------------------------------------------ |
| Nightly cron | up to 24 h   | Default. Queue accumulates, drains overnight.                                  |
| On-submit    | seconds      | Every entry kicks the agent. Low-volume projects wanting fast turnaround.      |
| Expedite     | seconds      | Per-entry opt-in via the modal checkbox. Compatible with nightly as baseline.  |

On-submit and Expedite both wire the submit endpoint to fire the scheduled agent's "run now" endpoint after writing the entry.

## Platform-agnostic

The Agent loop prompt (`automation/routine-prompt.template.md`) runs on any LLM platform that supports a scheduled agent:

- Claude.ai routines (registered via the `schedule` skill in Claude Code).
- GitHub Actions cron + an LLM CLI (`claude`, `codex`, etc.) inside the workflow.
- OpenAI Assistant + an external scheduler (Vercel cron, Cloudflare cron, cron-job.org).
- Self-hosted cron + LLM CLI.

The reference and the [`tighe-ecc/mailroom`](https://github.com/tighe-ecc/mailroom) example both use Claude.ai routines.

## In scope

- Personal one-shot tools, internal team tools, vibe-coded apps with small user bases.
- Apps where the human submitting feedback is — directly or via review — the engineer fixing it.

## Out of scope

- Public bug trackers with many reporters (no triage / dedup).
- Feedback that cannot live in source control (PII, support tickets, customer-confidential).
- Auto-merge — kit always opens PRs; humans merge.
- Workflows needing assignees, statuses, labels, SLAs.

## Invariants

Any deployment must preserve:

1. Queue is `<repo>/feedback.md`, Markdown checklist, exact entry format (see `DEPLOY.md` "Format reference"). The agent parses by regex.
2. Submit appends; never mutates existing entries. State changes (`[ ]` → `[x]`) come from human edits or git only.
3. Scheduled agent never edits `feedback.md`.
4. Entries carry provenance: timestamp, page URL, tool name. Optional `expedited` marker on the metadata line.
5. Scheduled agent opens PRs, not direct commits.
6. `feedback.py` is stdlib-only.

## Customization

`DEPLOY.md` includes an explicit step for capturing kit-level customizations after the adaptation pattern is picked. Customizations within scope (examples):

- Hide the Expedite checkbox (nightly cron only).
- Rename Bug/Feature labels.
- Move `feedback.md` to a non-root path.
- Disable auto-commit and push of `feedback.md`.
- Override the default cron expression / time zone.
- Change the button label or placement.

Customizations that break the invariants above are out of scope and should be refused.

## What the kit provides

| Path                                  | Purpose                                                                              |
| ------------------------------------- | ------------------------------------------------------------------------------------ |
| `reference/`                          | End-to-end implementation for FastAPI/Flask/Express, locally hosted. One valid path. |
| `adaptations/`                        | Pattern docs for hosting/stack shapes the reference doesn't cover.                   |
| `automation/routine-prompt.template.md` | Scheduled-agent prompt, platform-agnostic.                                         |
| `DEPLOY.md`                           | Procedure the installing agent follows.                                              |

## Deploy

Read `DEPLOY.md`.
