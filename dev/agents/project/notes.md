# Durable notes

## Env
- Venv: `~/Code/python_venv_01_main`; bare `python3` has no numpy.
- `results/` is gitignored; CSVs regenerate from scripts (commands in docstrings and E-entries).
- Stats code run from `python -` (stdin) falls back to serial with noisy tracebacks: run a script file.
- `python -m pytest` in a worktree needs `PYTHONPATH=.` (editable install resolves to the main checkout); prefer `python -m snntopo.cli` over the console script there.
- `SNNTOPO_DATA_DIR` shares raw data across worktrees.
- `snntopo run --out` resolves a relative path against cwd: from a worktree, pass `$SNNTOPO_RESULTS_DIR/runs/<id>`.
- SNN training device: `producers.DEVICE` (`SNNTOPO_DEVICE`, else cuda). CUDA re-runs are bit-identical; trained CUDA vs CPU spikes differ. Tests pin CPU (`tests/conftest.py`).

## Codex / sandbox
- ripser's forkserver pool needs AF_UNIX: codex `--sandbox workspace-write` blocks it, so no topology can be computed (serial fallback is too slow). It also can't `git commit` in a worktree (`.git/worktrees/<name>/index.lock` read-only).
- Claude Code's auto-mode classifier refuses `codex --dangerously-bypass-approvals-and-sandbox`; it needs an explicit Bash permission rule.
- `du -sh` per worktree double-counts hardlinked git objects.
- nodeterm: `send`/`settings` refused ("Agent messaging refused.") even with messaging on; follow-ups = a new node in the group. Codex nodes read "AGENT STATUS UNCONFIRMED" while working: watch panes via `tmux -L node-terminal capture-pane -p -t nt-<node-id>`.
- Agent briefs must say APPEND to `dev/agents/journal.md`; a codex worker once rewrote it.

## Zoo launch (not yet run; needs the user's OK)
- GPU measurement (M7, 200 updates, `sweeps/measure_gpu.py`): N = 2 concurrent trainers. 4 maximizes raw throughput but at n_hidden 256-1024 cuts per-trainer speed sharply for a modest total gain (1024: 3.3 / 6.1 / 8.9 updates/s total at 1 / 2 / 4). Peak 286 MiB per trainer at 1024.
- So: `snntopo run sweeps/zoo_v0.py --out <dir> --shard i/2` for i in 0, 1, with `SNNTOPO_WORKERS=8` each. zoo_v0 = 972 activities (27 triples x {128, 512} x 3 seeds x {0, 300, 1500} x {task, spontaneous}); zoo_v1 = v0 + 8 smoke-passing configs = 1260, a superset of v0 (same recipe ids). A run dir holds one spec, so launching v1 alone covers v0; running both recomputes v0. Self-nulls only, no pairs. Cost-model estimate: v0 ~7 h, v1 ~9 h serial.

## Science
- Never compare a `distance/null_mean` ratio to a bar measured at a different null_mean. Match noise by scanning `split_half_null` on `circle(seed=500)`; matching H0 needs higher noise than H1.
- Generators with different `seed` differ in embedding too; null pairs share `mixing_seed` (`snntopo/generators.py:46`).
- `compare` tests "same signature" and signatures include geometry: significant ≠ different topology.
- Steinmetz passive `left`/`right` = stimulus side; use `all` for active-vs-passive. Active `all` = responded trials only (`snntopo/data/steinmetz.py:103-118`).
- `_CACHE_SIZE = 32` in stats is undersized for 20 references (needs ~60).
- Verify agent-reported numbers by computing them; prose-reasoned numbers have been wrong.
