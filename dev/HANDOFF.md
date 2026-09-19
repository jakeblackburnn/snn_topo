# Handoff · 2026-09-19 18:20 · main
## State
- v2 build complete and merged. All five workstreams are in main; the five worktrees and their branches are closed.
- `pytest -q` → 89 passed; `pytest -m data` → 7 passed (data tests are opt-in, `-m data`).
- Search mini-runs through the CLI (`--n-trials 4 --n-updates 300`): steinmetz_2afc 4 ok; ibl_2afc 3 ok + 1 degenerate; nback 1 ok + 3 degenerate with `nearest_bio` set. `snntopo report` over all three → 631-line report.md + 9 figures.
- `dev/SPEC.md` and `dev/DECISIONS.md` are written; the Done-when list in SPEC.md is ticked against real command output. `dev/context/` is untouched (frozen build input).
## Next
- **The full experiment suite is the user's to launch**, sequentially on the one GPU: `snntopo search --task <t> --budget-hours <h> --out <dir>` per task, then `snntopo report --run ... --out ...`. Rerunning the same command resumes a run directory.
- Before committing to a long run, see "Known limits" in SPEC.md: nback needs far more than 300 updates, H2 is empty at `n_pca=10`, and significance power is weak below ~2× the null mean at `n_resamples=50`.
- Budgeting: ~13 s per 300 updates plus ~40 s topology per trial → roughly 25-30 trials per hour on a matched task.
## Traps
- stats.py runs a forkserver process pool, so callers need an `if __name__ == "__main__"` guard. The CLI already has one.
- The IBL choice sign is derived from the trials table (+1 = left-correct choice), NOT choice==-1. It's cached in each npz (`left_choice`/`right_choice`); stale caches re-process automatically.
- ONE 3.5 `load_dataset`/`load_object` can't see the BWM-tagged records, so the loader uses `one.alyx.download_file` (documented in data/ibl.py).
- Data caches live under `data/raw/{steinmetz,ibl (4.3 GB),allen}` and are gitignored. If you make a new worktree, hardlink or move caches rather than re-downloading.
- Venv: `~/Code/python_venv_01_main` (py3.14). allensdk doesn't support 3.14, so Allen is read via DANDI 000021 with h5py+remfile.
- `models.validate()` is the only definition of a buildable config; `search.sample_model()` samples inside it (D15). If you add a model axis, extend `valid_triples()` rather than the sampler.
- `.nodeterm/` is untracked canvas state; left alone.
## Pointers
- `dev/SPEC.md` — intent, components, the verified Done-when list, known limits.
- `dev/DECISIONS.md` — D1-D10 from the context packet, D11-D16 taken during the build.
- `snntopo/contracts.py` — the frozen interfaces. `snntopo/atlas.py` — `snn_entry`/`bio_entry` and the storage layout.
- `snntopo/topology/stats.py` — module docstring explains the null design and its power.
- `snntopo/search.py` — docstring maps each trial status to what Optuna is told.
