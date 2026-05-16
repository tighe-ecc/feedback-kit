# Concept

This kit packages one idea: **put the human on taste and opinion, put the machine on mechanical implementation, and close the feedback → fix loop without context-switching.**

You build a piece of idiosyncratic software — a one-shot app, an internal tool, something vibe-coded for a specific purpose — and you ship it. Users use it and find rough edges. Normally, sustaining that software means *you* drop what you're doing, read the user's bug report, reproduce, write the fix, test it, deploy. The kit replaces that loop with this one:

1. A user inside the running app clicks a "Feedback" button, picks Bug or Feature, types two sentences, and submits. (Or hits **Expedite** if they want it actioned now.)
2. A scheduled agent — on whatever LLM platform you prefer — reads the queue and attempts each item: writes the fix on its own branch, runs your verification gate, opens a PR.
3. You wake up to a list of candidate fixes. Review, merge the good ones, close the bad ones, ask for clarification on the ambiguous ones.

You stay in the loop where you should be — judging whether each fix is right, has the shape you want, reflects the product's character. The agent handles the parts that don't need taste.

## The loop, mechanically

```
   ┌─────────────┐         ┌──────────────┐         ┌──────────────────┐
   │ in-app      │ submit  │ feedback.md  │ trigger │ scheduled agent  │
   │ Feedback    ├────────►│ in repo      ├────────►│ implements + PRs │
   │ + Expedite  │         │ (the queue)  │         │ against default  │
   └─────────────┘         └──────────────┘         └──────────────────┘
```

Three pieces:

1. **Capture in the app.** A floating button on every page of the running app opens a modal: type (bug/feature), title, description, and an Expedite checkbox. Submit appends to `feedback.md` at the repo root. Provenance (timestamp, page URL, tool name) is auto-captured.

2. **A Markdown queue in the repo.** `feedback.md` is a plain Markdown checklist. Open items are `- [ ]`, resolved are `- [x]`. Human-readable, diff-friendly, version-controlled with the code it's about. The format is chosen specifically so any LLM agent can parse it deterministically.

3. **A scheduled agent drains the queue.** Cloned the repo, read `feedback.md`, pick unchecked items, spawn implementation sub-agents, run the project's verification gate, open PRs. The human reviews and merges. The agent never edits `feedback.md` — checkbox flips are a human signal that a PR was accepted.

The kit installs in two halves: **Capture** (pieces 1 and 2) and **the Agent loop** (piece 3). Capture stands on its own as a structured complaint board with provenance; the Agent loop is what turns it into autonomous sustaining engineering. You can ship Capture today and wire the Agent loop next week.

## Trigger surfaces

The Agent loop can be invoked three ways. Pick one or more per project:

| Trigger          | Latency        | When to use                                                                                          |
| ---------------- | -------------- | ---------------------------------------------------------------------------------------------------- |
| **Nightly cron** | up to 24 h     | Default. Fine for personal tools; the queue accumulates, gets drained while you sleep.              |
| **On-submit**    | seconds–minutes| Every new feedback entry kicks the agent. Right for projects where you want quick turnaround.       |
| **Expedite**     | seconds–minutes| Per-entry opt-in. The user ticks the Expedite box on Submit; that specific entry triggers a run.    |

On-submit and Expedite both come down to the same thing: the submit endpoint, in addition to appending to `feedback.md`, kicks the scheduled agent. The difference is whether every submit triggers (on-submit) or only flagged ones (expedite). A project can have both — nightly as the default sweep, Expedite as the "do this now" override.

## Platform-agnostic

The agent doesn't care what LLM platform it runs on, and neither does the kit. The prompt under `automation/routine-prompt.template.md` works wherever you can run a scheduled agent — Claude.ai routines, an OpenAI Assistant on a Vercel cron, a GitHub Actions workflow that shells out to an LLM CLI, a self-hosted cron on your own VPS. Pick whatever you're already using.

The reference implementation under `reference/` and the running example at [`tighe-ecc/mailroom`](https://github.com/tighe-ecc/mailroom) both happen to use Claude.ai routines — that's *one* place to run the agent, not the *only* one.

## Why this shape

| Choice                                  | Why                                                                                                                                                                                                                                                  |
| --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **The queue is the spec.**              | The agent reads `feedback.md` and does what it says. There's no separate ticket system, no triage step, no "I need to write up the bug properly." If the human can describe it in two sentences from the running app, the agent can attempt it.   |
| **Markdown, not a database.**           | The agent's input is `cat feedback.md`. Reviewing what landed is `git diff`. Triaging is editing a text file. Zero infrastructure: no schema, no admin UI, no separate auth.                                                                       |
| **In the repo, not a service.**         | The feedback ships with the code it describes. A six-month-old bug report next to a six-month-old commit. Rolling back a branch rolls back its feedback. Forking the project forks the queue.                                                       |
| **Checklist as state machine.**         | `[ ]` / `[x]` is the entire state. The agent only reads `[ ]`. The human only flips to `[x]` after merging. No labels, no statuses, no assignees — if you need those, you've outgrown the kit.                                                    |
| **Capture and Agent loop install separately.** | The capture half is useful on its own (complaint board with provenance). The Agent loop is the value multiplier. Bundling them would force users to wire scheduled-agent infrastructure before they can collect a single piece of feedback. |
| **Remote agent, not a local hook.**     | The agent runs on someone else's compute, authenticated as your GitHub identity. Your laptop can be off. The app can be hosted anywhere. The agent only needs the repo URL and credentials.                                                          |
| **Three trigger options, not one.**     | Different projects need different responsiveness. Nightly is fine for a personal tracker; a tool you're actively using might want Expedite. The kit doesn't force a choice — wire whichever surface you need.                                       |
| **Human-in-the-loop on the output.**    | The agent opens **PRs**, not commits. You review, you merge. The kit's role ends at "here is a candidate fix"; accepting it is yours. Draft PRs surface ambiguous cases for clarification without claiming a fix.                                   |

## Who this is for

- Custom personal tools built in a one-shot by an LLM, where the human doesn't want to context-switch to fix every small bug.
- Internal tools at a small team where the user filing the feedback is also the engineer (or has one nearby) who'd otherwise fix it.
- Vibe-coded apps shipped to a small audience where the cost of "I'll fix this later" is high enough to want the loop closed automatically.
- Any app where you'd rather your role be reviewer than implementer.

## Who this is *not* for

- Public-facing bug trackers with many reporters (the queue isn't designed for triage or dedup).
- Anything where the feedback shouldn't be in source control (PII, support tickets, customer-confidential).
- Projects where the agent can't safely auto-PR — heavily regulated codebases, anything where a bad PR is dangerous to even open. (The agent is supervised, but only by PR review; if PR review is too late, this kit isn't safe.)
- Apps that need assignees, SLAs, labels, or status workflows beyond open/closed. Use Linear / GitHub Issues / etc.

## Invariants (don't break these when adapting)

Any deployment of this concept should preserve:

1. **The queue is a Markdown checklist in `<repo>/feedback.md`.** The format `- [ ] **<YYYY-MM-DD HH:MM> — <Bug|Feature>[: <title>]**` is the agent's input contract. Don't switch to JSON, don't move it, don't nest it.
2. **Entries are append-only at write time.** State changes (`[ ]` → `[x]`) come from human edits or git, never from the submit path. A submission must never mutate or delete existing entries.
3. **The agent never edits `feedback.md`.** It reads, it implements, it opens PRs. The human flips checkboxes after merging.
4. **Each entry carries its provenance.** Timestamp, the page URL the user was on, the tool name. The agent uses these to disambiguate; the human uses them to remember context.
5. **The agent opens PRs, not direct commits.** Even when high-confidence. Even when single-author. Human review is the safety layer.
6. **The library is stdlib-only.** `feedback.py` has no dependencies. If your adaptation can't avoid a dep, document why.

## What the kit gives you

- **A reference implementation** under `reference/` — `feedback.py` (the library), `feedback-button.js` (the UI, with Submit + Expedite), and three HTTP-endpoint snippets (FastAPI / Flask / Express). This is one valid path, designed for a locally-hosted Python or Node web app with git push access. It's not the only path.
- **A set of adaptation patterns** under `adaptations/` — short notes on how to deploy the concept when your constraints differ from the reference (remote host, no backend, an exotic stack, etc.).
- **The agent prompt** under `automation/routine-prompt.template.md` — the prompt a scheduled agent runs, with `{{PLACEHOLDERS}}` for project-specific values. Works on any LLM platform; pick whichever scheduler you already use.
- **A deployment guide** at `DEPLOY.md` — the procedure a code-generation agent follows when a user points it at this repo and says "implement this."

## How to deploy it

Read `DEPLOY.md`. Whether you're a human installing it manually or an agent installing it on behalf of a user, the procedure is the same: confirm the concept, discover the project, present a concrete plan, install Capture, verify, then optionally wire the Agent loop on the user's chosen platform.
