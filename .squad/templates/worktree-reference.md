# Worktree Reference — Full Details

## Worktree Awareness

All `.squad/` paths MUST be resolved relative to a known **team root**, never assumed from CWD.

### Resolution Strategies

| Strategy | Team root | State scope | When to use |
|----------|-----------|-------------|-------------|
| **worktree-local** | Current worktree root | Branch-local | Feature branches needing isolated state |
| **main-checkout** | Main working tree root | Shared | Single source of truth across branches |

### How the Coordinator Resolves Team Root (every session start)

1. `git rev-parse --show-toplevel` → current worktree root
2. Check if `.squad/` exists at that root (fall back to `.ai-team/`)
   - Yes → **worktree-local**. Team root = current root.
   - No → **main-checkout**. Discover via `git worktree list --porcelain` (first `worktree` line = main).
3. User may override at any time.

### Passing to Agents
- Include `TEAM_ROOT: {resolved_path}` in every spawn prompt
- Agents resolve ALL `.squad/` paths from provided team root
- Agents never discover team root themselves

### Cross-Worktree: worktree-local (recommended)
- `.squad/` files are branch-local. Independent, no races.
- State merges through normal git merge / PR workflow.
- `merge=union` driver in `.gitattributes` auto-resolves append-only files.
- Scribe commits `.squad/` changes to worktree's branch.

### Cross-Worktree: main-checkout
- All worktrees share same `.squad/` state on disk.
- **Not safe for concurrent sessions.** Use for solo work only.

## Worktree Lifecycle Management

### Activation
- Explicit: `worktrees: true` in project config
- Environment: `SQUAD_WORKTREES=1`
- Default: `false`

### Creating Worktrees
- One worktree per issue number, shared by agents on same issue
- Path: `{repo-parent}/{repo-name}-{issue-number}`
- Branch: `squad/{issue-number}-{kebab-case-slug}` from base branch

### Dependency Management
- Link `node_modules` from main repo:
  - Windows: `cmd /c "mklink /J {worktree}\node_modules {main-repo}\node_modules"`
  - Unix: `ln -s {main-repo}/node_modules {worktree}/node_modules`
- If linking fails, fall back to `npm install`

### Reusing Worktrees
- Check `git worktree list` before creating
- If found: reuse (cd, verify branch, `git pull`)

### Cleanup
- After PR merged: `git worktree remove {path}` + `git branch -d {branch}`
- Ralph heartbeat can trigger cleanup checks

## Pre-Spawn Worktree Setup

### 1. Check worktree mode
- `SQUAD_WORKTREES=1` in env? Or `worktrees: true` in config?
- If neither: skip → agent works in main repo

### 2. If worktrees enabled
a. Determine path: `{repo-parent}/{repo-name}-{issue-number}`
b. Check if exists (`git worktree list`). If yes: reuse, verify branch, pull, skip to (e).
c. Create: `git worktree add {path} -b {branch} {baseBranch}`
d. Set up dependencies (link node_modules or npm install)
e. Include in spawn: `WORKTREE_PATH`, `WORKTREE_MODE: true`

### 3. If disabled
- `WORKTREE_PATH: "n/a"`, `WORKTREE_MODE: false`
- Use existing `git checkout -b` flow
