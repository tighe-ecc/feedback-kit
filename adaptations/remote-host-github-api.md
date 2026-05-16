# Pattern: remote host via GitHub Contents API

The app runs on a host without persistent local git — managed platforms like Vercel, Netlify, AWS Lambda, Cloud Run, Fly.io ephemeral instances, Cloudflare Workers, etc. The filesystem is read-only or wiped on cold start, so the reference's `git add / commit / push` shape doesn't work.

Instead, the submit endpoint commits `feedback.md` directly via the GitHub REST API.

## When this applies

- App is on a platform where the local filesystem is ephemeral or read-only.
- You can store a GitHub PAT (or fine-grained token) as a platform secret.
- The repo is on GitHub.

## What changes vs the reference

Replace `_git_sync_feedback()` with a function that:

1. `GET /repos/{owner}/{repo}/contents/feedback.md` → fetch current content + SHA
2. Decode, append the new entry
3. `PUT /repos/{owner}/{repo}/contents/feedback.md` with the new content, the SHA from step 1, a commit message, and author info

You also have to give up on `feedback.py`'s "find feedback.md by walking up from `__file__`" — there's no local file. The library can still format the entry; the endpoint just bypasses the local-write path.

## Phase 1 checklist

1. Decide on a token. Fine-grained PAT scoped to "this repo only, contents read+write" is recommended. Store as a platform secret (Vercel env var, Lambda environment, etc.) as `FEEDBACK_GITHUB_TOKEN`. Also set `FEEDBACK_GITHUB_REPO` to `<owner>/<repo>` and `FEEDBACK_GITHUB_BRANCH` (default `main`).
2. Use `reference/feedback.py`'s `_format_entry()` (call it directly via `feedback._format_entry(...)`) to render the entry — or copy the formatter inline if you'd rather not import a private function. **Do not call `feedback.note(...)`** in this pattern; it tries to write the file locally.
3. Replace the endpoint's persistence path with a GitHub Contents API call. Sketch (Python, urllib only — keep stdlib-only invariant):

   ```python
   import base64, json, os, urllib.request
   from feedback import _format_entry

   GH_TOKEN = os.environ["FEEDBACK_GITHUB_TOKEN"]
   GH_REPO = os.environ["FEEDBACK_GITHUB_REPO"]          # "owner/name"
   GH_BRANCH = os.environ.get("FEEDBACK_GITHUB_BRANCH", "main")

   def _append_via_api(*, description, type, title, tool, url, expedited):
       api = f"https://api.github.com/repos/{GH_REPO}/contents/feedback.md"
       hdr = {"Authorization": f"Bearer {GH_TOKEN}", "Accept": "application/vnd.github+json"}

       # 1. Fetch current
       req = urllib.request.Request(f"{api}?ref={GH_BRANCH}", headers=hdr)
       try:
           with urllib.request.urlopen(req, timeout=10) as r:
               cur = json.load(r)
           current = base64.b64decode(cur["content"]).decode("utf-8")
           sha = cur["sha"]
       except urllib.error.HTTPError as e:
           if e.code == 404:
               current = "# Feedback\n\n"
               sha = None
           else:
               raise

       # 2. Append
       entry = _format_entry(description=description, type=type, title=title,
                             tool=tool, url=url, expedited=expedited)
       updated = current + entry

       # 3. PUT
       payload = {
           "message": "feedback: sync new entry",
           "content": base64.b64encode(updated.encode("utf-8")).decode("ascii"),
           "branch": GH_BRANCH,
       }
       if sha:
           payload["sha"] = sha
       put = urllib.request.Request(api, method="PUT",
                                    headers={**hdr, "Content-Type": "application/json"},
                                    data=json.dumps(payload).encode("utf-8"))
       urllib.request.urlopen(put, timeout=15)
   ```

4. The Expedite trigger is unchanged — same `_expedite_routine()` as the reference.

## Phase 2 wiring

Identical to local-dev-server's Phase 2. The routine clones the repo via its own GitHub OAuth and reads the file from there — it doesn't care how the file got there.

## Gotchas

- **Concurrency / race on `feedback.md`.** Two submits within seconds will race: both fetch the same SHA, both `PUT` with that SHA, one wins, the loser gets a 409 Conflict and that entry is lost. Mitigations:
   - Accept it (low-volume personal projects rarely hit this).
   - Retry with backoff on 409: re-fetch, re-append, re-PUT.
   - Queue submits through a single-writer (a small Lambda with reserved concurrency 1, or a Cloudflare Durable Object).
- **Rate limits.** Authenticated GitHub API is 5000 req/hr. Plenty for feedback, unless you also use the token heavily elsewhere.
- **Token scope creep.** Use fine-grained tokens scoped to *one repo, contents only*. A classic PAT with `repo` scope is overkill and dangerous.
- **Branch protection.** A PUT to `main` will be rejected if the branch is protected. Either push to a side branch (`feedback/inbox`) and merge via PR (a GH Action can do this), or relax protection.
- **Commit author.** The Contents API commits as whichever GitHub identity owns the PAT. If you want a separate "feedback-bot" identity, mint the PAT from a bot account.
