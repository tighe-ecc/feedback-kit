# Pattern: remote host with direct git access

The app runs on a host you control (VPS, container with persistent storage, bare metal), and the process can `git push` because you've set up credentials there.

## When this applies

- App is deployed beyond your laptop.
- The host has the project as a real git working tree (not just built artifacts).
- You've put SSH keys or a credential helper on the host that lets `git push` work non-interactively.
- The host filesystem is writable — `feedback.md` can be appended to and the working tree can advance.

## What changes vs the reference

Almost nothing. The reference endpoint's `_git_sync_feedback()` already does the right thing — it runs `git add / commit / push` on the directory containing the app file. As long as:

- The app process's CWD or `__file__` resolves to a directory inside the git working tree, **and**
- The credentials for `git push` are wired into the deploy environment

…the reference works as-is.

## Phase 1 checklist

Same as `local-dev-server.md`. The only differences are in the host setup:

1. On the host: clone the repo to a real working tree (e.g. `/srv/<project>`). Don't run from an extracted tarball.
2. Configure git credentials for the user the app runs as:
   - **SSH keys:** `ssh-keygen -t ed25519`, add the public key as a deploy key on the GitHub repo (with write access).
   - **PAT:** `git config --global credential.helper store` and a one-time `git push` that caches the token.
3. Configure git identity for that user: `git config --global user.name "<app-deploy>"` and `user.email`.
4. Verify: `cd /srv/<project> && git pull` and `git push --dry-run` both succeed without prompts.
5. Install the kit files (same five steps as local-dev-server).
6. Restart the app process.

## Phase 2 wiring

Same as local-dev-server. Set `FEEDBACK_ROUTINE_ID` and `FEEDBACK_ROUTINE_TOKEN` in the host's environment (e.g. systemd unit `Environment=` or `.env` if your loader picks it up). Restart.

## Gotchas

- **Container restarts wipe the working tree.** If you're running in Docker or similar, the git working tree must live on a persistent volume — otherwise `feedback.md` resets on every restart and pushes are noisy. Mount `/srv/<project>` to a real volume.
- **Read-only filesystem on the container.** If you can't write `feedback.md` at all (some hardened base images), you're in the `remote-host-github-api.md` case instead. Switch patterns.
- **Branch protection.** If the host's account can't push to the default branch (because of branch protection rules), the auto-sync will fail. Either relax protection for that identity, or push to a side branch like `feedback/inbox` and have a GH Action merge into main. (See the `remote-host-github-api.md` pattern for a GH Action sketch.)
- **Multiple replicas writing.** If your host runs N replicas all writing to the same `feedback.md`, they'll race the git push. Either pin the submit endpoint to a single replica, or use the GitHub API pattern.
