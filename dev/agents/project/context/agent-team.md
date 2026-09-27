# snntopo v3: agent team

**Scope: build only.** The team delivers design.md's M1-M9. It runs the validation sweep, E15, the
bio core, and smoke sweeps, because those are milestone checks. It never launches zoo v0/v1 for
real, never runs E16 beyond `--mini`, and never picks E16's population.

## Pattern: hierarchical; foundation sequential, then parallel fan-out

Everything depends on the row schema, recipe ids and the runner (M1-M3), so these land first,
one at a time. After M3 the remaining work splits into three independent tracks.

| phase | milestone | owner | why this owner |
|---|---|---|---|
| 1 | M1 `dataset.py`: ids, row keys, RunWriter, store, loader + tests | **orchestrator** (Claude) | this is the interface every other track codes against; keep it in one head |
| 1 | M2 producers, measure, the additive stats/contracts changes, the seeding fix, checkpoints | **codex** | mechanical against M1 plus existing v1 functions; the checks are unit tests |
| 1 | M3 runner: resume, shards, `SNNTOPO_WORKERS`, disk halves cache, `run`/`status` | **Claude subagent** | concurrency and crash-safety correctness is design-sensitive |
| 2 | Track A: M4 floor + validation → M5 prereg binding, `verdict`, E15, E16 skeleton | **Claude subagent** | owns the scientific safeguards (D28, D35); mistakes here are silent |
| 2 | Track B: M6 Steinmetz trial selectors, atomic download, `bio_core` sweep, R1/R2/R4 | **codex** | loader and spec plumbing against a settled recipe format |
| 2 | Track C: M7 GPU measurement, `zoo_v0` → M8 Dale/τ-spread, rate family, `steinmetz_nogo`, smoke sweeps, `zoo_v1` | **codex** | model code in established idioms (`build_model` dispatch), gated by smoke results |
| 3 | M9 docs: README, architecture, `dev/agents/spec.md`, `CLAUDE.md` | **codex** | mechanical once the code has settled |
| 3 | final: every requirements.md *Done when* checked against a real command | **orchestrator** | — |

## Boundaries

- **Branches.** The orchestrator creates the integration branch `v3-build` off main. Each worker
  gets its own worktree and branch off `v3-build` at the phase boundary it starts from. Nobody
  commits to main. At the end the orchestrator asks the user to merge `v3-build` to main.
- **Review/merge gate.** Before merging a worker branch into `v3-build`, the orchestrator runs that
  milestone's check from design.md, runs `pytest -q`, and has the `reviewer` agent read the diff
  against design.md and decisions.md. Anything that breaks an interface goes back to the worker;
  the orchestrator doesn't patch around it.
- **Shared data.** Every worktree exports `SNNTOPO_DATA_DIR=<main>/data/raw`. Real runs use
  `SNNTOPO_RESULTS_DIR=<main>/results` (run dirs are unique and `store/` is write-once). Tests use
  a tmp dir.
- **Compute.** Only Track C uses the GPU. Tracks A and B each set `SNNTOPO_WORKERS=8`, so two
  topology runs split the 16 cores. A single run over 30 min needs the orchestrator's OK. The
  orchestrator asks the user before anything over 1 h.
- **Ownership.** A worker writes only its track's files (design.md module table). A cross-track
  change (e.g. Track B needing a new row field) is raised in the worker's report and settled by
  the orchestrator in design.md. It is never made unilaterally.
- **Stop rule for workers.** Decide anything internal to your module. At a gap that crosses a
  module boundary or is hard to change later, stop and report.
- Workers never edit `dev/main.md`, `dev/journal.md`, `dev/agents/project/context/`, or existing
  `results/` run dirs. Each worker appends its milestone results to `dev/agents/journal.md` on its
  own branch, and the orchestrator reconciles those on merge.

## Checkpoints with the user

1. Before phase 1 (project-builder's go-ahead).
2. Before the phase 2 fan-out: M1-M3 merged and green.
3. Before E15's PREREG commit: the user sees the scanned noise and the criteria.
4. Before merging `v3-build` to main.

## Addendum: nodeterm

The user drives this through nodeterm (`manage-nodeterm-canvas` skill).
- **Orchestrator node:** Claude Code in the main checkout, running `/project-builder`. It owns the
  canvas: a group per phase-2 track, each group bound to that track's worktree, with a context
  link from each worker node back to the orchestrator so it can read their output.
- **Codex nodes (M2, Track B, Track C, M9):** codex in permissive mode (sandbox and approvals off,
  e.g. `--dangerously-bypass-approvals-and-sandbox`). This is required: the forkserver ripser pool
  needs AF_UNIX sockets (`stats.py:170-181`), and Track C needs the GPU. Each node's prompt is
  assembled from requirements.md, design.md (its milestones + the module table + recipe/row/spec
  interfaces) and decisions.md.
- **Claude subagent nodes (M3, Track A):** Claude Code nodes in their worktrees. The orchestrator
  may use in-process subagents instead when a node isn't worth a canvas slot (e.g. the `reviewer`
  gate).
- Kanban: one card per milestone. The orchestrator moves cards as gates pass.
