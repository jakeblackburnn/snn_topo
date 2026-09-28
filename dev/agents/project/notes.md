# Durable notes

## Env
- Venv: `~/Code/python_venv_01_main`; bare `python3` has no numpy.
- `results/` is gitignored; CSVs regenerate from scripts (commands in docstrings and E-entries).
- Stats code run from `python -` (stdin) falls back to serial with noisy tracebacks: run a script file.
- `python -m pytest` in a worktree needs `PYTHONPATH=.` (editable install resolves to the main checkout); prefer `python -m snntopo.cli` over the console script there.
- `SNNTOPO_DATA_DIR` shares raw data across worktrees.
- The `snntopo` console script doesn't put the repo root on sys.path: a spec that reuses another spec loads it with `runner.load_spec(path)`, never `from sweeps.x import`.
- `-m data` tests aren't in the default `pytest -q`; run them before a merge (M8's `steinmetz_nogo` broke one unseen).
- `snntopo run --out` resolves a relative path against cwd: from a worktree, pass `$SNNTOPO_RESULTS_DIR/runs/<id>`.
- SNN training device: `producers.DEVICE` (`SNNTOPO_DEVICE`, else cuda). CUDA re-runs are bit-identical; trained CUDA vs CPU spikes differ. Tests pin CPU (`tests/conftest.py`).

## Codex / sandbox
- ripser's forkserver pool needs AF_UNIX: codex `--sandbox workspace-write` blocks it, so no topology can be computed (serial fallback is too slow). It also can't `git commit` in a worktree (`.git/worktrees/<name>/index.lock` read-only).
- Claude Code's auto-mode classifier refuses `codex --dangerously-bypass-approvals-and-sandbox`; it needs an explicit Bash permission rule.
- `du -sh` per worktree double-counts hardlinked git objects.
- nodeterm: `send`/`settings` refused ("Agent messaging refused.") even with messaging on; follow-ups = a new node in the group. Codex nodes read "AGENT STATUS UNCONFIRMED" while working: watch panes via `tmux -L node-terminal capture-pane -p -t nt-<node-id>`.
- Agent briefs must say APPEND to `dev/agents/journal.md`; a codex worker once rewrote it.

## Zoo launch (zoo_v1 complete 2026-09-28 18:21, `results/runs/20260928-1502-zoo_v1`)
- GPU measurement (M7, 200 updates, `sweeps/measure_gpu.py`): N = 2 concurrent trainers. 4 maximizes raw throughput but at n_hidden 256-1024 cuts per-trainer speed sharply for a modest total gain (1024: 3.3 / 6.1 / 8.9 updates/s total at 1 / 2 / 4). Peak 286 MiB per trainer at 1024.
- Launch zoo_v1 only: it is a superset of v0 (same recipe ids) and a run dir holds one spec. 1260 activities = 210 training groups (one training, 3 checkpoints x 2 regimes). Self-nulls only, no pairs. Expand order is seed-major, so a block that stops early leaves every config at the same seeds.
- Run dir: `results/runs/20260928-1502-zoo_v1`. It binds the spec path, so always launch from the main checkout (not a worktree). One block = both shards, same budget, same dir; rerun the same lines for the next block:
  `D=$PWD/results/runs/20260928-1502-zoo_v1; for i in 0 1; do SNNTOPO_WORKERS=8 snntopo run sweeps/zoo_v1.py --out $D --shard $i/2 --budget 65 > $D/logs/block-$(date +%H%M).s$i.out 2>&1 & done; wait`
  `--budget MIN` starts no new group after MIN minutes (overrun <= one group, ~1.5 min) and records status `budget`; `snntopo status $D` shows what is left.
- Calibration (20-min block, 2026-09-28 15:02): 15 groups per shard in 20.4/20.7 min = 82 s/group per shard wall (train ~55 s median), vs the cost model's ~158 s serial. All 30 groups were v0 existing triples at seed 0, n 128 and 512 alike (izhikevich trains slowest, ~80 s). 0 failed, 31/180 degenerate. The v1 families (tau_spread, Dale, rate at batch 256, no-go) are not timed yet.
- Block 2 (15:31, `--budget 65`): 48/50 groups per shard in 65.3 min = 82/78 s/group, 0 failed. The v1 families train no slower (median 47-53 s vs v0 56 s). After it: 768/1260 done, all of seed 0 (70 groups) plus 58 of seed 1's 70; 42 + 40 groups left, then a `--budget 35` block and a final unbudgeted ~19-min block finished it: 1260/1260, 0 failed, ~3 h wall over 4 blocks.
- The dry-run budget line uses the uncalibrated cost model and undercounts a block ~2x for the zoo (60 min -> "~23 groups"; measured ~45).

## Science
- Never compare a `distance/null_mean` ratio to a bar measured at a different null_mean. Match noise by scanning `split_half_null` on `circle(seed=500)`; matching H0 needs higher noise than H1.
- Generators with different `seed` differ in embedding too; null pairs share `mixing_seed` (`snntopo/generators.py:46`).
- `compare` tests "same signature" and signatures include geometry: significant ≠ different topology.
- Steinmetz passive `left`/`right` = stimulus side; use `all` for active-vs-passive. Active `all` = responded trials only (`snntopo/data/steinmetz.py:103-118`).
- `_CACHE_SIZE = 32` in stats is undersized for 20 references (needs ~60).
- Verify agent-reported numbers by computing them; prose-reasoned numbers have been wrong.
