# feedback-kit

Drop an **agentically-actioned feedback button** into any web app. Users submit bugs and feature requests in-app; a scheduled agent reads the queue and opens PRs against your repo; you stay focused on review, taste, and opinion — not triage and mechanical implementation.

This repo is built to be deployed by a code-generation agent, not by hand.

## How to install it

In the repository that contains *your* application — whether it's locally hosted, on a VPS, on a managed platform, anywhere — launch your coding agent (Claude Code, Codex, Cursor, Aider, whatever) and tell it:

> Implement this: `https://github.com/tighe-ecc/feedback-kit`

That's the whole interaction. The agent will:

1. **Read** every document in this repo to understand the concept.
2. **Explore** your project to understand its stack, hosting model, and structure.
3. **Plan** a concrete installation tailored to your project's idiosyncrasies, and present it to you for sign-off.
4. **Implement** the in-app capture pieces (the floating Feedback button with Bug/Feature options and an Expedite checkbox, the receive endpoint, the Markdown queue file) once you approve the plan.
5. **Walk you through** setting up the optional remote agent on your preferred platform — Claude.ai routines, an OpenAI scheduled job, a GitHub Actions cron, whatever you already use — so it can drain the feedback queue into PRs autonomously.

You stay in the loop only where you should be: reviewing the plan up front, reviewing each PR before merge.

## What the user-facing surface looks like

A floating "Feedback" button on every page of your app. Click it, and a small modal opens:

- **Type:** Bug or Feature
- **Title** + **Description**
- **Expedite** (optional checkbox): trigger the remote agent immediately instead of waiting for the next nightly run

Submit appends a Markdown entry to `feedback.md` at the repo root. That file is the queue, the spec, and the audit log — diff-friendly, version-controlled with the code it's about, and formatted so an agent can parse it deterministically.

## What the agentic loop gives you

The pitch in one line: **ship idiosyncratic, one-shot software with confidence, because its sustaining engineering happens without you.**

You build something custom — vibe-coded, AI-assisted, a one-off internal tool — and deploy it. Users use it and find bugs. Instead of you sifting through their reports and writing fixes:

- They click Feedback, type two sentences, hit Submit (or Expedite if they need it now).
- A scheduled agent reads the queue, implements each item on its own branch, runs your verification gate, and opens a PR.
- You wake up to a list of candidate fixes. Review them. Merge the good ones. Close the bad ones. The agent's never edits to `feedback.md` itself — closing the loop is your call.

The human stays in the loop on **taste and opinion**. The machine handles **mechanical implementation**.

## What's in this repo

Designed to be read by an agent in this order:

| File / dir                          | What it's for                                                                                                                                                                                              |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`CONCEPT.md`](CONCEPT.md)          | The concept: what this kit is, why it's shaped the way it is, and the invariants any deployment must preserve.                                                                                            |
| [`DEPLOY.md`](DEPLOY.md)            | The procedure an agent follows when a user points it at this repo. Discovery → plan → present → implement → verify → optional remote-agent setup.                                                          |
| [`reference/`](reference/)          | One end-to-end implementation of the kit (FastAPI/Flask/Express, locally hosted). Treat as *example*, not prescription.                                                                                    |
| [`adaptations/`](adaptations/)      | Short pattern docs for everything the reference doesn't cover: remote hosting, no backend, exotic stacks, etc. Each says when to pick it and what changes vs the reference.                                |
| [`automation/`](automation/)        | The optional remote-agent half. Includes a prompt template that works on any agent platform — Claude.ai routines, OpenAI assistants, a self-hosted cron + LLM, etc. Mailroom uses Claude.ai routines.     |
| [`skill/`](skill/)                  | An optional preinstalled Claude Code skill that maps `/feedback-framework` to "read DEPLOY.md and proceed." You don't need it; the paste-the-URL workflow works without any skill preinstalled.            |

There's also a working example: [`tighe-ecc/mailroom`](https://github.com/tighe-ecc/mailroom) is a personal app that uses this kit end-to-end (capture + Claude.ai routine). When the agent needs a real-world reference, point it there.

## Manual install (humans who want to skip the agent)

If you'd rather install by hand, read `DEPLOY.md` and apply each step yourself, picking the right adaptation from `adaptations/`. The files in `reference/` are copyable as-is for FastAPI/Flask/Express. Everything else is in the text.

## Drift discipline

If you customize the reference files in a downstream project and the changes would be useful for everyone, send a PR back here and cut a new tag. Downstream installs pin to a kit ref; bumping that ref is the only way changes propagate.
