# Pattern: novel stack

The reference covers FastAPI, Flask, and Express because that's what the kit was first built for. If you're on something else, you have to write the endpoint yourself — but everything else carries over.

## When this applies

You're installing into a project on, e.g.:

- Python: Django, Starlette, Sanic, Quart, aiohttp
- JavaScript/TypeScript: Next.js (App Router or Pages), Nuxt, SvelteKit, Hono, Fastify, Koa, Remix
- Go, Rust, Ruby (Rails / Sinatra), PHP (Laravel / Symfony), Java/Kotlin, C# (.NET), Elixir (Phoenix), etc.

## What you write

A single endpoint, `POST /feedback`, that does three things:

1. Parse a JSON body with these fields (only `type` and `description` are required, but plumb all of them through to the queue):
   ```json
   {
     "type": "bug" | "feature",
     "title": "<string>",
     "description": "<string>",
     "expedite": <bool>,
     "tool": "<string>",
     "url": "<string>",
     "userAgent": "<string>",
     "timestamp": "<ISO 8601>"
   }
   ```
2. Append a Markdown entry to `feedback.md` at the repo root. **Use the exact format from `CONCEPT.md` and `../reference/feedback.py:_format_entry`.** Don't invent a new format — the agent prompt parses it.
3. Get the entry committed to git (or fail loudly). Three sub-options, in rough order of preference:
   - **Local subprocess (most direct):** if your stack runs on a host with `git push` access (see `remote-host-direct-git.md`), shell out to `git add / commit / push`.
   - **GitHub Contents API:** if your stack is on a managed platform (see `remote-host-github-api.md`), use the API.
   - **Async sync process:** the endpoint writes to a queue or store; a separate process flushes to git. Heaviest, only worth it if you have high write volume.

Then, if `payload.expedite` is true, POST to the Claude routine's run endpoint (see the reference endpoints for the exact shape — `https://claude.ai/api/routines/<id>/run` with a Bearer token).

## The format you must produce

```
- [ ] **YYYY-MM-DD HH:MM — Bug: <title>**
  <description, with each line indented two spaces>
  _tool: <toolName> · source: <url> · expedited_
```

- Timestamp: local time, `YYYY-MM-DD HH:MM`. (The reference uses local time; if your stack is server-only and timezone is variable, use UTC and note it.)
- `Bug` or `Feature` — capitalize.
- `: <title>` is optional in the spec, but the form requires title, so always present in practice.
- The metadata line is optional in the spec — include it if you have any of tool/source/expedited.

Test by hand-crafting one entry, then running the agent prompt manually (`gh repo clone`, paste prompt into Claude Code) — it should parse cleanly. If it doesn't, your format is off.

## Copying the formatter

Easiest: in Python stacks, even non-FastAPI/Flask, import the kit's `feedback.note(...)` from `reference/feedback.py`. It works regardless of framework. In non-Python stacks, port `_format_entry` — it's 20 lines. The `reference/endpoints/express.js` has a JS port you can copy verbatim.

## Phase 2 wiring

Identical to other patterns. The agent doesn't care how `feedback.md` is being updated; it just reads the file.

For the Expedite trigger, follow the same pattern as the reference endpoints — `_expedite_routine()` is ~15 lines in any language. The reference has Python and JS versions; both are uncommented scaffolding once you fill in env vars.

## Gotchas

- **Don't auto-generate the format.** Resist the urge to use a templating library or LLM to render the entry — string-format it deterministically. The agent parses by regex.
- **Validate input.** `type` must be `"bug"` or `"feature"`. `description` must be non-empty. Refuse anything else with a 400. The reference does this; copy the validation.
- **Don't sanitize the URL.** `source: <url>` is provenance, not user input — it comes from `window.location.href`, not the form. Pass through as-is.
- **Idempotency on retries.** The browser might retry on transient failures. Duplicate entries are a human-cleanup problem; don't try to dedupe automatically.
