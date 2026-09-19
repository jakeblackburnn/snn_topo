# Handoff · 2026-09-19 15:33 · main
## State
- v2 build (`/project-builder`, orchestrated on nodeterm) is 4/5 merged into main: interface phase (0372605) + ws-topology, ws-search, ws-reports, ws-data.
- `pytest -q` → 31 passed; `pytest -m data` → 7 passed (data tests are opt-in).
- `snntopo snn --task steinmetz_2afc --n-hidden 128 --n-updates 100` → status ok, acc 0.90, objective 0.17, 30 distance rows, 48 s.
- `snntopo bio --dataset {steinmetz,ibl,allen}` → 5 bio entries ok (Steinmetz 11; IBL ×3; Allen 719161530). IBL 120 s, Allen 43 s.
- Only model that builds on main: recurrent/lif/random (interface placeholder `snntopo/models/prototype_rlif.py`). A `snntopo search` on main would mark every other family "failed".
## In flight
- **ws-models** (worktree `../snn_topo.worktrees/ws-models`, Claude node "SNN model registry across four axes") had NOT committed at 15:33. Uncommitted: models/{connectivity,networks,neurons}.py, tests/test_models.py, prototype_rlif.py deleted, models/__init__.py + cli.py modified. Its last note: modular M=2 learns in 60–160 updates, M=4 in ~500–800. It was doing final GPU timings.
- `.nodeterm/` untracked (canvas state; left alone).
## Next
1. Read the ws-models worker's final message (`get-linked-context` on node term-mu8qktti-4bea1351), then review `git diff main...ws-models` against `snntopo/contracts.py` (ModelConfig forward contract; any new fields must have defaults).
2. Merge ws-models. Then replace `search.model_families()` (snntopo/search.py) with the model registry's own valid-triples function, so the rule lives in one place.
3. Mini-run the search per matched task (NOT the full suite): `snntopo search --task steinmetz_2afc --budget-hours 0.25 --out <scratch>` and the same for ibl_2afc and nback. Then `snntopo report --run ... --out ...`.
4. Tick off the Done-when list in dev/context/requirements.md against real command output.
5. Write dev/SPEC.md from requirements.md. Append dev/context/decisions.md D1–D10 plus the kickoff decisions (see Pointers) into a new dev/DECISIONS.md. Leave dev/context/ untouched.
6. Close the worktrees: nodeterm `close-worktree`, or `git worktree remove`.
## Traps
- nodeterm `send`/`notify` → "Agent messaging refused" even after the user toggled the setting. Use `write --node <id> --text "...\n"` instead (one confirm dialog per message). The user said to just use write.
- stats.py runs a forkserver process pool, so callers need an `if __name__ == "__main__"` guard. The CLI already has one.
- The IBL choice sign is derived from the trials table (+1 = left-correct choice), NOT choice==-1. It's cached in each npz (`left_choice`/`right_choice`); stale caches re-process automatically.
- ONE 3.5 `load_dataset`/`load_object` can't see the BWM-tagged records, so the loader uses `one.alyx.download_file` (documented in data/ibl.py).
- Data caches live under data/raw/{steinmetz,ibl(3.1 GB),allen}, moved from the ws-data worktree. Worktrees don't share data/ (gitignored). Hardlink or move caches instead of re-downloading.
- Significance power (topology/stats.py docstring): effects ≲2× the null mean are often missed at n_resamples=50. TopoConfig.n_resamples default was lowered 100 → 50 for cost (~43 s/entry with 3 refs).
- Venv: ~/Code/python_venv_01_main (py3.14). allensdk doesn't support 3.14, so Allen is read via DANDI 000021 with h5py+remfile.
## Pointers
- snntopo/contracts.py: the frozen interfaces. snntopo/atlas.py: `snn_entry`/`bio_entry`, storage layout.
- snntopo/topology/stats.py: module docstring explains the null design.
- snntopo/search.py: docstring maps each trial status to what Optuna is told.
- Worker briefs: /tmp/claude-1000/-home-jake-Code-main-experiments-snn-topo/ab326d01-fa17-42f3-9f34-72c8e054a397/scratchpad/briefs/ (ephemeral).
- Decisions made this session, not yet in DECISIONS.md: diameter-normalized point clouds; Allen is bio-only; nodeterm team; trial-matched split-half null (stats.py); n_resamples=50. Recorded in dev/context/requirements.md "Resolved at build kickoff". Offer `/decide`.
