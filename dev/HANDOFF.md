# Handoff · 2026-09-19 14:23 · main

## State
- No code exists for v2 yet — this session was pure context-building (`/context-builder`), no implementation.
- Old prototype (git-tracked at `snntopo/`, `scripts/`, `docs/`, `results/`) has already been moved to `prototype/` (untracked) by a prior action, with the original tracked paths showing as deleted in `git status`. Nothing has been committed reflecting this move yet.
- `dev/context/` is complete: `requirements.md`, `research.md`, `decisions.md` (D1–D10), `agent-team.md` — ready to hand to `project-builder-helper`.
- IBL ONE API auth is live and verified: `one.search(project='brainwide', limit=3)` → returned real session UUIDs, in `~/Code/python_venv_01_main`.

## In flight
- Nothing half-done. Git working tree has the prototype-move (deletions + untracked `prototype/`) uncommitted — not committed this session since it wasn't asked for.
- `.nodeterm/` also untracked (not inspected — likely canvas state from a prior nodeterm session).

## Next
1. Decide whether/how to commit the `prototype/` move (git status shows 57 deletions + untracked `prototype/` — currently uncommitted).
2. Hand `dev/context/` to `project-builder-helper` to start the v2 build.
3. Build team follows `dev/context/agent-team.md`: opusplan orchestrator lands interfaces first, then Codex + spawned Claude agents fan out per workstream in worktrees.
4. **Build-vs-run boundary is load-bearing** — the build only does smoke tests + small mini-experiments; the full wall-clock-capped search suite runs later, separately, user-initiated.

## Traps
- IBL public access needs *no* personal registration — `username='intbrainlab', password='international'` against `https://openalyx.internationalbrainlab.org` works directly. Don't waste time on OAuth/signup flows.
- `prototype/` is frozen reference material by its own reports' convention — read from it, never edit it.
- No `.venv` in this project dir; per user's global CLAUDE.md, `~/Code/python_venv_01_main` is the fallback and is what was used for the ONE-api install.
- The prototype's own findings (3 experiments) consistently showed the H0 gap *widening* as the SNN got more bio-realistic (recurrence, scale, criticality) while H1 stayed flat — this is why v2 adds a modular/multi-population model family (D3) instead of just tuning the existing recurrent model further.

## Pointers
- `dev/context/requirements.md` — Done-when checklist, scope in/out, explicit build-vs-run split.
- `dev/context/research.md` — full prototype-findings summary + bio dataset notes + IBL auth setup steps.
- `dev/context/decisions.md` — D1–D10, all ADRs from this session.
- `dev/context/agent-team.md` — build-team structure, roles, worktree/review-gate boundaries.
- `prototype/docs/*.md` — original prototype reports (source material for research.md).

handoff written. Safe to /clear.
