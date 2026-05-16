---
name: feedback-framework
description: Install the feedback-kit (agentic in-app feedback button + optional remote agent that drains feedback.md into PRs) into the current project. Reads the kit's repo for concept and procedure; interviews the user about hosting and stack; presents a plan; implements idempotently. Use when the user wants to drop the feedback-kit into a web app, or invokes /feedback-framework.
user-invocable: true
---

# /feedback-framework

This skill is a convenience entry point for users who've preinstalled it. It exists so that `/feedback-framework` in any project does the same thing as pasting the kit's URL and saying "implement this." Either path works; the skill just saves the user a typed sentence.

## What to do when invoked

1. **Fetch the kit's `DEPLOY.md`** from `https://raw.githubusercontent.com/tighe-ecc/feedback-kit/${KIT_REF}/DEPLOY.md` (default `KIT_REF=main`; bump to a tag/SHA in production).
2. **Read `DEPLOY.md` and follow it.** Everything you need is there — discovery, plan, present-to-user, implement, optional agent loop.
3. **Pin the kit ref.** When fetching `feedback.py` / `feedback-button.js` / endpoint snippets, use the same `KIT_REF` as step 1. Don't mix versions across files.

`DEPLOY.md` is the source of truth. If anything here drifts from it, trust `DEPLOY.md`.

## One-time install of the skill itself

```bash
mkdir -p ~/.claude/skills/feedback-framework
curl -fsSL https://raw.githubusercontent.com/tighe-ecc/feedback-kit/main/skill/SKILL.md \
  -o ~/.claude/skills/feedback-framework/SKILL.md
```

## Drift discipline

If you tweak the kit's behavior, edit `DEPLOY.md` in the kit — not this skill file. This file is a thin pointer on purpose; the more it knows, the more it can disagree with the kit.
