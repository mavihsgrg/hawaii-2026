---
name: trip-commit-push
description: Commit all pending changes in the Hawaii trip repo and push them straight to origin/main in one go. Use whenever the user asks to commit, push, save, or sync the trip docs, or after editing any .md file in this repo.
---

# Hawaii trip: commit and push to main

This repo uses a single branch, `main`. Never create other branches, never force-push, never merge, and never delete branches unless the user explicitly asks.

## Steps

1. **Check the branch.** Run `git branch --show-current`. If it is not `main`, stop and ask the user before doing anything else. (A worktree session shows its own `worktree-*` branch; in that case, push with `git push origin HEAD:main` after confirming the commit is a fast-forward of `origin/main`.)
2. **Look at what changed.** Run `git status --short` and `git diff --stat`. If nothing changed, say so and stop.
3. **Stage everything except local-only files.** Run `git add -A`, then unstage local settings with `git reset -q -- .claude/settings.local.json` and anything else that is local-only. Never stage passport or ID scans (`docs/` is set up in `.gitignore` for these). Confirm with `git diff --cached --stat`.
4. **Write the commit message.** One short imperative line that says what changed, for example `Add Maui hotel shortlist` or `Update budget after Aston quote`. If several unrelated things changed, add a short body with one line per change. End the message with this exact trailer, after a blank line:

   `Co-Authored-By: Claude Haiku 5.5 <noreply@anthropic.com>`

5. **Commit.** Write the message to a file in `$CLAUDE_JOB_DIR/tmp`, then run `git commit -q -F <file>` so the trailer and quotes survive.
6. **Push.** Run `git push origin main` (or `git push origin HEAD:main` from a worktree). If the push is rejected because the remote moved, run `git pull --ff-only origin main` and push again. Never rebase or force. If the fast-forward pull fails, stop and report the conflict.
7. **Report.** Give the commit short hash, the one-line message, and the files changed. Confirm with `git status -sb` that `main` matches `origin/main`.

## Notes
- Small, frequent commits keep the history readable. If there are many unrelated edits, offer to split them, but default to one commit.
- The repo is private, but keep passport scans, full card numbers, and similar secrets out of commits. Confirmation numbers are fine.
