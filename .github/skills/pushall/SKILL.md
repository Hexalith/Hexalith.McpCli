---
name: pushall
description: Process every root-declared submodule in its own subagent, then commit, merge, push, and safely prune branches in the main repository after all subagents finish. Only invoke this directly with /pushall — never trigger it automatically.
disable-model-invocation: true
allowed-tools: Bash(git *) Bash(mktemp *) Bash(printf *) Bash(sed *) Bash(cmp *) Bash(run-with-temp python3 *)
---

# /pushall — sync, merge, and prune every branch

Runs the repo-sync procedure for every root-declared submodule in a dedicated subagent. After all
subagents finish, runs the procedure in the superproject so its commit picks up the updated
submodule pointers and its push happens last.

## Required preflight

Before running any Git command, read
`references/Hexalith.AI.Tools/hexalith-git-instructions.md` completely and follow it. Treat it as
authoritative. If it is unavailable, stop `/pushall` and report the missing instructions.

For every commit, write the full proposed Conventional Commit message to a temporary file and
validate that file with the owning repository's pinned commitlint CLI and configuration. Keep the
exact file and successful validation result with the run evidence. Revise rejected messages and
validate them again. If validation cannot run, record the exact failing command and stop that
commit. Use `git -C <dir> commit --cleanup=verbatim --file <message-file>` with the validated file.
Compare the resulting commit object's message bytes with the file before pushing.

For an adopted module, use the validator from its committed Builds release. When it supplies
`Github/lib/guard_tools.py`, run it with `run-with-temp python3`. Import `Tools` from that directory
and call `Tools(Path(os.environ["TMPDIR"])).lint_message(message, identity)` with the exact UTF-8
message read from the file. The guard installs and verifies the locked tooling. Record the Builds
revision, validator command and result. Follow the owning repository's instructions for other
validator installations.

Run the owning repository's required checks before pushing. Adopted modules require
`python3 references/Hexalith.Builds/check.py` from a clean standalone checkout of the exact commit
being pushed, with Builds at the committed direct gitlink and `origin/main` fetched.

## /pushall-specific rules (never deviate)

- Do not invoke `bmad-build` or any other BMad skill during `/pushall`; execute simple Git
  operations such as commits and pushes directly through this skill's procedure.
- Only delete local branches with `git branch -d` (safe delete, refuses non-merged branches).
  Never use `-D`.
- Only delete an `origin` remote branch after its fetched tip is merged into the default branch and
  that default branch has been pushed successfully. Never delete the remote default branch or
  `origin/HEAD`. Use `--delete` with an exact expected-OID lease so deletion fails if the branch
  moved after it was merged.
- Never merge or prune the remote name `origin`, `refs/remotes/origin`, `HEAD`, or
  `refs/remotes/origin/HEAD`. `%(refname:short)` abbreviates `refs/remotes/origin/HEAD` to `origin`;
  that name is the remote, not a branch. Symbolic refs are never merge or prune targets.
- On a merge conflict, inspect the base and both sides and try to resolve it while preserving the
  intent of both branches. Never auto-resolve with `-X ours`/`-X theirs` or blindly accept one
  complete side. If a safe resolution cannot be determined or validated, run `git merge --abort`,
  record that ref as skipped, do not prune it, and continue.
- If a repo has no remote, push fails, or the local default branch has diverged from
  `origin/<default-branch>` (fast-forward not possible), record it as skipped/failed and continue
  with the rest — never stop the whole run for one repo.
- End each completed repo on its default branch. If switching would overwrite working changes,
  preserve the current checkout and report the blocker.
- Give a one-line progress update per repo as you go, and a final consolidated report (per repo:
  local and remote branches merged, local and remote branches deleted, anything skipped/failed,
  push status).

## Subagent coordination

- Keep the calling agent as the coordinator. It owns only orchestration, the final superproject
  procedure, and the consolidated report.
- If subagents are unavailable, stop before modifying any repository and report that `/pushall`
  requires subagent support. Never fall back to processing submodules in the coordinator.
- Assign each root-declared submodule path to its own dedicated subagent. Run subagents concurrently
  up to the available concurrency limit; when capacity is limited, start the remaining dedicated
  subagents as slots become available.
- Give each subagent exactly one submodule path and the per-repo procedure below. Require it to read
  the Git instructions in the required preflight before running Git commands.
- Restrict each subagent to its assigned submodule repository. It must not run Git commands in the
  superproject or another submodule, and it must not initialize or process nested submodules.
- Require each subagent to return a structured result containing its path, default branch, merged
  refs, deleted local and remote branches, skipped or failed operations, final branch, and push
  status.
- Wait for every declared submodule's dedicated subagent to finish with a success, skipped, or
  failed result. Do not run, commit, or push the superproject while any submodule subagent remains
  active or unreported.
- If a subagent fails without a usable result, record that failure and ensure the subagent is no
  longer running before crossing the barrier. A failed submodule does not cancel the remaining
  subagents or permit an early superproject push.

## Per-repo procedure

Apply this to one repo directory `<dir>` at a time (a submodule path, or `.` for the superproject):

1. `git -C <dir> fetch --all --prune`
2. Determine the default branch: prefer `main`, else `master`, else
   `git -C <dir> remote show origin | sed -n 's/.*HEAD branch: //p'`.
3. Inspect `git -C <dir> status --porcelain=v1 --untracked-files=all`, the index and the working
   tree. If a Git operation is already in progress or the index contains changes outside the
   reviewed sync, leave the checkout intact and report it as blocked.
   - If `git -C <dir> symbolic-ref --quiet HEAD` reports detached HEAD, check whether the tip
     is already contained in the local default branch. If it is unmerged or there are reviewed
     changes to commit, create a fresh `pushall/recovery-<unique-suffix>` branch at the detached
     tip with `git -C <dir> switch -c <recovery-branch>` before committing or switching branches.
     If this fails, stop processing the repo. Include the branch in step 6.
   - For reviewed tracked files whose full changes are in scope, stage explicit leaf paths with
     `git -C <dir> --literal-pathspecs add -u -- <tracked-paths>`. Preserve partial staging when
     only the indexed changes are in scope. Stage an untracked file only when its exact path and
     content are reviewed and authorized, using `git -C <dir> --literal-pathspecs add -- <paths>`.
     Use these commands only with nonempty lists and check the final staged patch.
   - Follow the owning repository's submodule policy. Verify each allowed staged gitlink is
     available on its declared remote before committing pointer changes separately from ordinary
     files. Leave centrally owned gitlinks untouched.
   - Validate and commit each nonempty reviewed staged patch using the preflight procedure. Use a
     subject describing the reviewed changes. Give a separate gitlink commit its own message.
4. `git -C <dir> switch <default-branch>`. If the switch would overwrite working changes, keep
   them intact and report the repo as blocked.
5. Try `git -C <dir> merge --ff-only origin/<default-branch>` to catch up with the remote first.
   If this fails because local and remote diverged, record it and skip the rest of this repo.
6. Build the merge list from both kinds of refs. A merge target is a full ref under `refs/heads/`
   or `refs/remotes/origin/<branch>`. Never merge `origin`, `HEAD`, `refs/remotes/origin`, or
   `refs/remotes/origin/HEAD`.
   - Local branches: `git -C <dir> for-each-ref --format='%(refname)' refs/heads/`. Exclude exactly
     `refs/heads/<default-branch>`.
   - Remote branches: `git -C <dir> for-each-ref
     --format='%(refname) %(objectname) %(symref)' refs/remotes/origin/`. Drop every line whose
     symref field is non-empty, and drop `refs/remotes/origin/<default-branch>`. Each remaining ref
     must be exactly `refs/remotes/origin/<branch>`, where `<branch>` is non-empty and is not
     `HEAD`. Keep that full ref as the merge target. Keep `<branch>` and the fetched object ID for
     the deletion lease in step 10. Do not shorten the ref.
7. For every ref in the merge list (full local branch refs first, then full remote-tracking refs):
   - Skip a ref already contained in the destination. Prepare and validate a message with a short
     subject and a body identifying the source and destination tips by their full object IDs.
     Record the full refs in the run evidence. Run `git -C <dir> merge --no-ff --no-commit -- <ref>`.
     On success, commit the pending merge using the validated file.
   - On conflict, list unresolved paths with `git -C <dir> diff --name-only --diff-filter=U`, inspect
     the base and both sides, and edit the files to preserve compatible changes and intended
     behavior from both branches.
   - Stage the resolved paths, verify that no unresolved paths remain, run the repository's most
     relevant available validation, and complete the merge with the validated file. If the message
     changes, validate the entire revised file first.
   - If the conflict cannot be resolved safely, unresolved paths remain, or validation fails, run
     `git -C <dir> merge --abort`, record the ref as skipped, and continue to the next ref.
   - If another merge or commit error leaves a pending merge started by this run, abort it before
     continuing. If cleanup fails, stop processing the repo and report the pending state.
8. `git -C <dir> push origin <default-branch>`. Record failure and continue if it's rejected.
9. Delete local branches now fully merged into the default branch (excluding the default branch
   itself): `git -C <dir> branch --merged <default-branch>` minus the default branch, then
   `git -C <dir> branch -d <each>`.
10. Only if step 8 succeeded, prune each remote branch recorded in step 6 whose fetched object ID
    is an ancestor of the default branch. The branch name is the `<branch>` captured in step 6.
    Refuse `origin`, `HEAD`, an empty name, and the default branch:
    - Verify with `git -C <dir> merge-base --is-ancestor <fetched-object-id> <default-branch>`.
    - Delete with `git -C <dir> push
      --force-with-lease=refs/heads/<branch>:<fetched-object-id> origin --delete <branch>`.
    - If the lease or deletion fails, record the branch as not pruned and continue. Never retry
      without the exact lease.
11. `git -C <dir> fetch --all --prune` to remove deleted or otherwise stale remote-tracking refs.

## Execution order

1. Complete the required preflight.
2. Read the root `.gitmodules` for the declared submodule paths (`references/...`).
3. Spawn one dedicated subagent per declared submodule path as described in **Subagent
   coordination**. Queue launches only when the concurrency limit requires it; never assign two
   submodule paths to the same subagent.
4. Collect each finished subagent's structured result and launch queued subagents until every
   declared submodule has a terminal result.
5. After the last submodule subagent has finished, verify the required submodule commits, pushes,
   and remote availability. If any required action failed, report its blocker and stop before
   committing the superproject. Otherwise, run the per-repo procedure for the superproject (`.`).
   Its separate pointer commit records only allowed, verified root gitlinks. Push the main
   repository after that verification.
6. Print the consolidated report, including every subagent result and the superproject result.
