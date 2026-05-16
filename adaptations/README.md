# Adaptations

The reference implementation under `../reference/` makes a specific set of choices: FastAPI/Flask/Express, locally hosted, can `git push` directly. This directory is for everything else.

Each file is a short pattern: when it applies, what changes vs the reference, and a concrete starting point. They're not full implementations — they're the parts of the reference that need to be different, with the rest assumed to carry over.

## Index

| Pattern                              | Use when                                                                                                                                            |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`local-dev-server.md`](local-dev-server.md)             | FastAPI/Flask/Express on your local machine. *This is the reference; included as the pattern doc for completeness.* |
| [`remote-host-direct-git.md`](remote-host-direct-git.md) | Same stack, deployed to a VPS or container where the running process has `git push` credentials.                    |
| [`remote-host-github-api.md`](remote-host-github-api.md) | Same stack, deployed to a managed platform with read-only filesystem (Vercel, Lambda, Cloud Run, etc.).             |
| [`no-backend.md`](no-backend.md)                         | Pure static site, mobile app, CLI tool, or library — anywhere there's no server-side endpoint to POST to.            |
| [`novel-stack.md`](novel-stack.md)                       | Stack the reference doesn't cover (Django, Rails, Next.js API routes, Go, Rust, etc.). Recipe for inventing the endpoint.   |

## What every pattern preserves

Look at `../CONCEPT.md`'s invariants. Any pattern in this directory keeps:

- The queue is `feedback.md` at the repo root, Markdown checklist, exact format.
- Entries append-only on submit. State changes are human/git only.
- The agent (Phase 2) reads the file and opens PRs; never edits it.
- The library file is stdlib-only Python (when Python is in play).

If you find yourself needing to break one of these for a real project, write a new pattern doc here and flag the deviation prominently. Don't silently ship a one-off — the next install in a similar shape will benefit.
