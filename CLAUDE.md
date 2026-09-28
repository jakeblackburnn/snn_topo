# snntopo: agent sandbox

Read `dev/` first (see the global CLAUDE.md); the workflow is in `README.md` and
`docs/architecture.md`, the agent's reading of the project in `dev/agents/spec.md`.

## Sandbox
- **Writes:** anywhere in the repo, except the user's `dev/` root files (`main.md`, `journal.md`,
  `spec.md`, `decisions.md`) and existing run dirs under `results/runs/`. New run dirs under
  `results/runs/` and blobs in `results/store/` are fine.
- **Commands:** `pytest`, `snntopo`, and the venv python (`~/Code/python_venv_01_main`).
  Runs up to 30 min are free; longer runs or overnight sweeps (zoo v0/v1) need the user's OK first.
- **Git:** commit on feature branches and worktrees. Merge to main or delete branches only with
  the user's OK. Never push.

## Rules
- Experiments (`experiments/`) run only from a clean tree; `--mini` runs are exploratory.
- Never edit a committed PREREG after its first run; a new criterion is a new experiment.
- Never overwrite a measured number: corrections are `derived` rows.
- Analysis never pools rows across `topo_id`/`cmp_id`.
- Bump `PIPELINE_VERSION`/`STATS_VERSION` by hand whenever numerics change.

## Traps
- `snntopo run --out` with a relative path resolves against cwd; from a worktree pass
  `$SNNTOPO_RESULTS_DIR/runs/<id>`. Worktrees export `SNNTOPO_DATA_DIR` and `SNNTOPO_RESULTS_DIR`
  pointing at the main checkout, and `PYTHONPATH=<worktree>` (the venv's editable install
  points at the main checkout).
- The ripser pool uses forkserver, which needs AF_UNIX sockets: a sandboxed shell falls back to
  serial (one loud log line). Cap it with `SNNTOPO_WORKERS` when runs share the 16 cores.
- Stats code run from `python -` (stdin) falls back to serial; run a script file.
