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
- Steinmetz passive `left`/`right` = stimulus side; use `all` for active-vs-passive. Active `all` = responded trials only (`snntopo/data/steinmetz.py:143-171`).
- `_CACHE_SIZE = 32` in stats is undersized for 20 references (needs ~60).
- Verify agent-reported numbers by computing them; prose-reasoned numbers have been wrong.
- Total H0 persistence (Rips) is the minimum-spanning-tree length, so at most the trajectory's length in diameters (`trajectory_length / raw_diameter`); measured 95-99% of it. It is a path-smoothness number. Pure noise (trials shuffled in time) gives about 26 at any trial count; a straight path gives 1. Fitting it on split-half `null_mean` is partly circular (both come from H0 diagrams). `scripts/topo_or_noise.py`, `docs/poster/results.md` section 6.

## Zoo vs bio comparability (found 2026-09-29, not fixed)
- `zoo_v1` and `bio_core` are not comparable as run. `cmp_id` hashes metrics + n_resamples (`snntopo/dataset.py:81`) and `dataset.load` needs one `cmp_id`, so the two can't be loaded together: zoo `3fed78af4c11ac97` (wasserstein only), bio_core `539728d0ec6e8f09` (wasserstein + bottleneck). `topo_id` matches (`70aaac6c2b35a7ff`).
- The zoo has no `derive()`, so no R1 robust-count rows (bio's headline measure). `TOPO`/`CMP`/`derive` are copied per spec (`sweeps/bio_core.py:19,90`, `sweeps/zoo_v0.py:6`), so they can drift.
- Scale differs: `null_mean` depends on unit and trial count. Bio sessions have varied unit counts; the zoo has 128/512 units and 340 eval trials. Ratios are comparable only at matched null_mean (spec.md Validity).
- Proposed fix (user wants comparability by construction, not patched rows): one shared measurement file (`TOPO`, `CMP`, `h` rule, `derive`) loaded by path by both specs, a test that both resolve to the same `topo_id`/`cmp_id`, then a zoo rerun (~3 h in blocks, needs the user's OK; keep the old dir). Open: subsample both sides to common (units x trials) scales, or keep native scales with null_mean as a covariate. Settle the full measurement list first so the zoo reruns once.
- Zoo splits: 3 seeds per config, self-nulls only, no pairs. The training seed is the unit for any test, not the activity.
- 2026-10-09: the fix is coded on branch `grid-measure` (`e88be9e`: `snntopo/grid.py`, recipe `subsample`, `sweeps/bio_grid.py`, `sweeps/zoo_grid.py`, `scripts/snn_vs_bio.py`) but never run and not merged. Parked until the project reframe.
- 2026-10-13: fixed. `grid-measure` merged to `main` (`43c0393`) and both specs run: `results/runs/20261013-1300-bio_grid` (361 activities, ~12 min, CPU) and `results/runs/20261013-1300-zoo_grid` (1260 activities, 0 failed, ~2 h over two `--budget 65` blocks, 2 shards x `SNNTOPO_WORKERS=8`, ~70 s/group per shard). Both `cmp_id 539728d0ec6e8f09`. The cells (50x56, 128x100) and the single subsample draw are still the branch's assumption, never a recorded decision.

## Poster analysis (2026-10-13)
- Rebuild commands are in each script's docstring: `scripts/zoo_overview.py` (zoo_v1), `scripts/bio_overview.py` (bio_core + E18), `scripts/snn_vs_bio.py` (the two grid runs). Outputs go to `results/analysis/` (gitignored).
- Zoo status `degenerate` means a `left`/`right`/`nogo` condition had < 5 trials, i.e. the network never picks that action: all 210 at checkpoint 0, 13 of 210 at 1500 (did not learn). Their `all` signature still exists; summaries filter on `status == "ok"`, not on `skipped`.
- Steinmetz window: `WINDOW = slice(50, 200)` is 0 to 1.5 s from stimulus onset (`stim_onset` = 0.5 s in the archive, checked on session 11). The comment at `snntopo/data/steinmetz.py:32` ("0.5--2.0 s after the stimulus") is wrong and unfixed.
- In `snn_vs_bio` tables bio `select == "all"` is the passive block and `"responded"` is the engaged one. Pooling them hides the engaged/passive gap (robust loops 8/39 vs 1/39 at 128x100).
- Wiring names are random, small_world, scale_free, modular_hub; "modular" alone is an architecture.

## Poster writing (2026-10-13)
- `docs/snn_topo.md` is Jake's poster doc. Never edit it; suggested wording goes in chat or agent files. The agent's vetting of it is `dev/agents/project/2026-10-13-doc-response.md`.
- `pull.rebase=true` here: a pull refuses over any uncommitted file. With Jake's `dev/journal.md` dirty, `git checkout main` also fails when the branches differ in it; merge in a throwaway `git worktree` instead.
- Reading papers: nature.com redirects WebFetch to a login; bioRxiv rate-limits (HTTP 429). Europe PMC full text works with curl: `https://www.ebi.ac.uk/europepmc/webservices/rest/<PMCID>/fullTextXML`. WebFetch returns a small model's summary, so it does not count as reading a paper.
- Reference checks record the page each entry was checked against: `dev/workshop/poster-references.md`.

## Poster figures (2026-10-13)
- `scripts/poster_figures.py` builds every poster figure into `docs/poster/figures/` (PDF and 300 dpi PNG) from `results/analysis/*/activities.csv`, the E18 run and the two grid runs. All sizes hang off `COLUMN_IN` (14.5 in: 48x36 in landscape, three columns). `docs/poster/plan.md` maps panels to figures, `docs/poster/narrative.md` gives the story and a layout proposal; the poster uses `results`, `table`, `trajectories`, `engagement`, `pipeline`, `rips`.
- The venv's editable install of `snntopo` points at `/home/jake/Code/main/experiments/snn_topo`, which no longer exists: `import snntopo` fails outside pytest. Run scripts with `PYTHONPATH=<repo>`. Not fixed (Jake's venv).
- No run stores activities, point clouds or weights (`results/store/` has `diagrams` and `halves` only). `poster_figures.cloud()` rebuilds a cloud from its recipe and checks it against the stored diagram to 1e-9; a model is retrained (about a minute, reproduces exactly on the GPU). Cache: `results/analysis/poster_figures/clouds/` (gitignored).
- `poster_figures.py <name> ...` builds only the named figures (rebuilding all rewrites every PDF). `noise` and `results` need `PYTHONPATH=. python scripts/topo_or_noise.py` first; `table` prints its cells for checking against `results.md`; its brain trial sweep (~35 s, 16 cores) is cached in `results/analysis/topo_or_noise/sweep.csv`: delete it to recompute.
- Grid runs are sharded: files are `activities.s0of2.jsonl` etc., not `activities.jsonl`. SNN labels are not unique; select by `activity_id`.
- The two-choice group in `snn_vs_bio` (n = 189) includes 12 rate networks (`family == "rate"`, `arch` and `neuron` empty), though figures and the table label it "spiking models".
- `docs/poster/poster.md` (2026-10-15) is the poster copy Jake lays out from in Canva: his six sections plus Conclusions, about 800 words, captions and figure edit notes, three columns about 13 / 18 / 13 in. Structure: `dev/workshop/poster-structure.md`. The figure edit notes in it are not yet applied to `scripts/poster_figures.py`.
- `docs/poster/draft.md` is the agent's test draft of Jake's poster doc: each number carries its source line in an HTML comment (`<!-- results.md:84 -->`), so a number check is "does the value appear in the cited lines". `docs/poster/results.md` is the number source; `core-summary.md` is a summary of it and has been wrong once (loop counts swapped, fixed 2026-10-13).

## Clique probe (2026-10-16, branch `clique-topology`)
- `docs/poster/` on this branch holds only `references.md`, `headline.md`, the `torus`, `rips` and `pipeline` figures, and the four `clique_*` figures. `poster.md`, `results.md`, `draft.md` and `scripts/poster_figures.py` figures other than those three live on main only. The notes above that cite them describe main.
- `snntopo/pugavko.py` ports Pugavko et al. 2023 (AdEx, 12 Yang-style tasks, their regularized recipe), without norse.
  - Speed: the step loop is overhead-bound, so G nets run side by side for about the cost of one: 10 nets × 512 units take 3.6 s/epoch, 3 h for 3000 epochs, peak 3 GB GPU.
  - Never index `x[t]` inside an autograd time loop: each index's backward writes a full-size zero tensor, O(T²). Use `unbind`.
  - The input projection is computed inside each checkpointed chunk; a full (T, G, B, N) tensor is 4 GB.
  - Training has no resume.
- REINFORCE on our own tasks (`training.py`) never learned DMS, 2-back, or a 4-task mix at 2048 units (0.45-0.50 flat). Supervised surrogate-gradient training with the published recipe learned 12 tasks within 250 epochs.
- `clique.betti_curves` with H2 takes ~8 s per probe at k = 128 and <0.5 s at k = 50.
- The cloned paper code (`cgtasknet`, `multy_task`) was in the session scratchpad: github.com/Pugavkom/{cgtasknet,multy_task}. The regularized settings come from `multy_task/server/mean_fr_filter_bigger_tau_a_less/mean_fr_filtertau_a_less.ipynb`.
- Projecting out top principal components before clique topology overshoots far above random, even for place cells (2.8-8x); use `clique.demean_trials` (per-trial mean removal) for slow drift. Population regression overshoots slightly (1.09-1.26x on synthetic data).
- Poster figures for this result: `scripts/poster_figures.py clique_method clique_model clique_results clique_table` (~5 s, needs `PYTHONPATH=.`; it imports `scripts.clique_probe`). They read `results/analysis/clique_probe/`; `clique_method` is synthetic. `clique_model` redraws the first k = 50 probe of `multitask-0` and asserts that it equals its `probes.csv` row. `clique_table` prints its cells as markdown.
- In this shell, `pkill -f <pattern>` matches the calling Bash command's own command line and kills it; use `pgrep` and kill by PID.
