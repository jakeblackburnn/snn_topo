# Journal · 2026-09-27 13:24 · main · 25c78e2
## Start
**State:** E12-E15 done. The null is valid (0/40). The Steinmetz engaged-vs-passive H1 contrast
clears the matched-noise floor (3.07 vs 1.09) and replicates in 11/12 sessions. D28 reframes D20;
the `steinmetz_2afc` search block still stands. 128 tests pass (rerun this session, after the
migration below).
**Since:** Nothing committed since `25c78e2`. This session migrated `dev/` to the human/agent split:
`journal.md`, `DECISIONS.md` → `decisions.md`, `SPEC.md` → `spec.md` and `experiments.md` moved
under `dev/agents/`; `context/` and the poster report moved to `dev/agents/project/`, all via
`git mv`. `dev/` path references were updated in README, `snntopo/{objective,contracts,topology/stats}.py`
(comments only), the moved docs and `brainstorm/`. Past journal Close entries and the frozen
`project/context/` keep their old paths. The user's `dev/main.md` and `dev/journal.md` don't
exist yet; they're the user's to write.
**Next:** (no user tasks yet)
1. Preregister E16: active no-go vs passive, contrast-matched, Steinmetz sessions 0-12. No-go
   trials (`response == 0`, 56-155/session) are the only engaged-without-movement set. Add a
   `nogo` contrast to `scripts/engagement_contrast.py`, then rerun the E14 floor scan at the no-go
   null scale.
2. Stress-test the floor (D28 revisit): latent shape, embedding dimension, firing rate at fixed
   null_mean.
3. Re-derive SNN-vs-bio against a matched-noise floor, with a preregistered criterion, before
   unblocking the search.
4. Rerun the D19 controls (untrained/shuffled); their run directory is gone.
**Traps:**
- Never compare a `distance/null_mean` ratio to a bar measured at a different null_mean (the same
  difference reads 115, 35 or 2.8). Scan `split_half_null` on `circle(seed=500)` to match noise;
  matching H0 needs a higher noise than matching H1.
- Generators with different `seed` also differ in embedding. For a null pair, share `mixing_seed`.
- `compare` tests "same signature", and signatures include geometry: significant ≠ different topology.
- `results/` is gitignored; CSVs regenerate from the scripts (commands in their docstrings and the E-entries).
- Stats code run from `python -` (stdin) falls back to serial with noisy tracebacks. Run a script file.
- Venv is `~/Code/python_venv_01_main`; bare `python3` has no numpy.
- Steinmetz passive `left`/`right` = stimulus side; use condition `all` for active-vs-passive.
  Active `all` = responded trials only (`snntopo/data/steinmetz.py:103`).
- `_CACHE_SIZE = 32` is still undersized for 20 references.
**Pointers:**
- `dev/agents/experiments.md:609` E12, `:664` E13, `:707` E14, `:750` E15.
- `dev/agents/decisions.md:455` D28.
- `snntopo/generators.py:25` `_activity`; `:46` `mixing_seed`.
- `scripts/null_calibration.py` (`--n-neurons --n-trials --runs A:x B:x C:x`);
  `scripts/engagement_contrast.py:49` block rule.
- `dev/agents/project/2026-09-22-poster-report.md` Panel 8 (d).

## Task: Reframe snntopo as a general SNN-TDA data-gathering platform, through to an implementation packet · 13:38
**Goal:** Turn snntopo from a D20-centred SNN-vs-bio search into an organized setup that gathers TDA results across many SNNs (and brain data) at scale. This session ends when the implementation packet for a separate nodeterm build session is ready.
**Now:**
- `dev/main.md` sets the new frame: a flexible workspace, a large TDA dataset over varied SNNs, brain signatures plus comparison metrics, and a poster.
- The code (~2.9k lines, `snntopo/`) is organized around search/objective (`search.py`, `objective.py`, D17/D18), with a matched-noise floor as yardstick (D28). `results/` is ad hoc per-run directories (gitignored).
- `dev/brainstorm/mega-forward-plan/` (09-23) already holds the data-platform schema, model zoo tiers, bio expansion and a codebase audit. Its index is D20-centred and partly stale (E12 retracted the anticonservative claim).
- `dev/agents/project/context/` holds the v1 build packet. Four merged worktrees are still checked out, and the dev/ path migration is uncommitted.
**Scope:** in: pre-flight commit → `/brainstorm` → `/consolidate` → `/context-builder` packet (including a nodeterm addendum) → worktree cleanup. out: any code change, any experiment (E16 and the D28 stress tests are paused), launching the build.
**Constraints:**
- `/brainstorm` goes in a new topic, `dev/brainstorm/snn-tda-dataset/`, with mega-forward-plan read as seed input. It doesn't extend that folder.
- `/context-builder` rewrites `dev/agents/project/context/` in place; git keeps v1 (last at `0374c27`). Assumption: this is fine even though D1-D10 cite it as a "frozen input", since the old pointers resolve through git.
- The agent-team addendum names nodeterm: a Claude orchestrator node that spawns subagents and leans on codex in permissive mode (sandbox off, which ripser's process pool needs; see mega index, forkserver trap).
- Carry forward: the preregistration discipline (never move a criterion after seeing a result), "never overwrite a measured number" (store raw + correction + construction id), the pair-policy wall (all-pairs is infeasible above ~10³ entries), and `SNNTOPO_DATA_DIR` (shared data across worktrees).
- Git: commit the dev/ path migration as its own commit before `/brainstorm`. Remove the four merged worktrees and their branches before any launch. Confirm each step with you first.
**Approach:**
1. Pre-flight: run `pytest -q` (expect 128 pass), then commit the uncommitted dev/ migration (README, 3 comment-only .py edits, moved docs).
2. Brainstorm + consolidate in one **general-purpose subagent**, to save context. `/brainstorm` is user-invoke-only, so the subagent reads `~/.claude/skills/brainstorm/SKILL.md` and `consolidate/SKILL.md` and follows them. It may fork per angle. The prompt hands it the topic, the seed files and the facets: dataset organization and schema, the pair/reference-panel policy, SNN breadth (model zoo), brain-signature extraction, run orchestration at scale, and what search/objective becomes. It must not ask questions or touch code. It returns index.md's recommendation plus open questions, and I relay them to you.
3. `/context-builder` stays in the main session, since its interview needs you: interview, then write requirements, research, decisions, design (milestones with runnable checks) and agent-team with the nodeterm addendum, then `/consolidate` it.
4. Hygiene: remove the four merged worktrees and branches. Leave you a one-paragraph launch note: open a Claude node, `/project-builder`.
**Risks:**
- The brainstorm rediscovers the 09-23 work. To catch it, the new index should cite mega's files rather than restate them.
- The subagent's work is invisible until it reports. To catch problems, I read its index.md before relaying it; the facet files I only spot-check.
- Scope creep into running science. The guard is that no `results/` writes happen this session.
- project-builder says it's "not for incremental features on an already-built project". This reorg is big enough, but the packet's design must name what survives from v1, or the builder will one-shot over working code.
- Codex in permissive mode touches shared data. The packet sets which paths each role may write.
**Done when:**
- `git status` is clean apart from this session's dev/ docs, the migration is its own commit, and `git worktree list` shows only main.
- `dev/brainstorm/snn-tda-dataset/index.md` exists, links every facet file, and gives a recommendation.
- `dev/agents/project/context/` has requirements.md (Done-when list, sandbox), research.md, decisions.md, design.md (milestones, each with a runnable check), and agent-team.md with a nodeterm/codex addendum. No blocking open question remains.
- design.md's acceptance includes: E15 reproduces through the new pipeline, the existing tests pass, and E16 is runnable as the first experiment on the new setup.
**Open:** none blocking. Pause/resume of E16 and the stop point are decided (above).

## Progress · 13:54
- Pre-flight: 128 passed. Path migration committed `5d91f47`. Four merged worktrees and branches removed, and `snn_topo.worktrees/` rmdir'd.
- Brainstorm (subagent): `dev/brainstorm/snn-tda-dataset/` committed `479b25d` and `3fa110a`. Recommendation: the recipe-hashed activity is the unit of record, pairs are declared only, storage is jsonl plus a content-addressed store, search/objective are frozen, experiments are committed specs with prereg bound by blob hash, and v1 numerics are frozen behind golden checks G1-G7 (E15 string-identical).
- Verified by hand: E16 as framed is nearly empty. Passive has 0 zero-contrast trials, so contrast-matched no-go means misses only, with 14/14/9 in sessions 6/11/12 (`checks/e16_and_determinism.out`). Model built before seeding: `atlas.py:237` vs `training.py:32`.
- Next: `/context-builder`. The ranked open questions are in the subagent report and `snn-tda-dataset/index.md`.

## Progress · 14:49
- /context-builder: v3 packet written in `dev/agents/project/context/` (requirements, research, decisions D29-D38, design M1-M9, agent-team + nodeterm addendum). Consolidated by subagent: `afd2d9d`, `f0006e1`.
- User calls: freeze search; jsonl storage; declared pairs only; no old-results oracle, validated by a known-answer spec instead (D33); fresh dataset with v1 kept parallel; specs at root binding PREREG+verdict; new families smoke-gated into zoo v1; E15 fresh + E16 skeleton; team and gates as drafted.
- After consolidate, fixed design gaps: Steinmetz trial arrays moved to M2 (the bio producer and E16 --mini need them); ModelConfig fields moved to M8; file-ownership section added; E16 uses `PREREG = None` so the binding can't lock it by accident; SNNTOPO_WORKERS 6/5/5 across tracks. Uncommitted, for /devlog.
- Stale cite outside the packet: `snn-tda-dataset/experiments-and-prereg.md` §5 has `steinmetz.py:121-135`, which should be about 103-117.
- Next: the user starts the build session (nodeterm orchestrator node → `/project-builder`).

## Close · 2026-09-27 15:08 · 0374c27..07c6eae
- **changed:** dev/ split: agent docs moved under `dev/agents/`, path refs updated (README, 3 comment-only .py edits)
- **changed:** `dev/brainstorm/snn-tda-dataset/`: new brainstorm (schema, pair policy, SNN breadth, brain signatures, orchestration, prereg, v1 survival, checks/)
- **changed:** `dev/agents/project/context/`: v3 build packet (requirements, research, D29-D38, design M1-M9, agent-team + nodeterm addendum), rewritten in place over v1
- **why:** reframe snntopo per `dev/main.md` from a D20-centred search into a general SNN-TDA data-gathering platform; the packet is the input for `/project-builder`
- **verified:** `pytest -q` → 128 passed (13:54, before the migration commit). No code change after that. Packet fixes post-consolidate are docs only
- **by:** pair
- `07c6eae` notes: SNN-TDA reframe (main.md) and 09-27 session plan
- `f0006e1` consolidate: v3 context packet, fix stale path:line citations, dedupe validation facts
- `afd2d9d` journal: snapshot before consolidate
- `3fa110a` consolidate: snn-tda-dataset brainstorm, dedupe no-go check, fix cross-file facts
- `479b25d` journal: snapshot before consolidate
- `5d91f47` dev: update path references after agent-docs move
- 36 files, +2078 −419 (excl. journal)
- ⚠ uncommitted: `.nodeterm/` (canvas state, not project code)

### Next
1. `/project-builder` from the nodeterm orchestrator node in the main checkout. It reads the packet and shows the phase-1 plan for a go-ahead (checkpoint 1, `agent-team.md`)
2. Before any codex node: add an explicit permission rule for codex permissive mode (see Traps)
3. E16 population (misses vs zero-contrast withholds, `snn-tda-dataset/experiments-and-prereg.md` §5) is the user's call. It blocks only E16's PREREG commit
4. Paused science (after the build): D28 floor stress tests, SNN-vs-bio against a matched floor, D19 controls rerun
### Traps
- E16 as first framed is nearly empty: passive has 0 zero-contrast trials, so contrast-matched no-go = misses only, 14/14/9 trials in sessions 6/11/12 (`dev/brainstorm/snn-tda-dataset/checks/e16_and_determinism.out`)
- SNN model is built before seeding (`atlas.py:237` vs `training.py:32`); the M2 seeding fix covers it
- Worktrees branch from HEAD: commit packet edits before spawning workers, or they build on the old design
### Pointers
- `dev/agents/project/context/design.md` milestones table (M1-M9 checks), "File ownership"; `agent-team.md` Addendum: nodeterm, Checkpoints
- `dev/brainstorm/snn-tda-dataset/index.md`: recommendation + links to all facets
- `dev/agents/experiments.md:750` E15 (must reproduce through the new pipeline, design.md acceptance)

## M2 · 2026-09-27 15:55 EDT
**Built:** `producers.py` for bio, synthetic, control, and existing SNN recipes; deterministic pre-build SNN seeding; grouped training/checkpoint evaluation; content-addressed activity and optional weight storage; and failed-row handling. Added measurement signature/null/comparison rows with diagrams, R2 H1 presence, R4 anchors, and stated construction IDs. Added explicit `h`, seed, and per-side null means to stats results; training snapshots; and Steinmetz full-trial selector arrays.

**Gate fixes:** controls now read SNN and promoted source fields from their unwrapped recipes; SNN degeneracy uses `compute_signature` skip semantics (including zero diameter); skipped signature rows have no diagram pointer and `diagram_key` was removed; duplicate training-key calculation was collapsed; explicit oversized-`h` raises are covered; and this journal was restored from `v3-build` before appending this entry.

**Checks:**
- `pytest -q` → `150 passed, 1 skipped, 11 deselected, 2 warnings in 41.62s`.
- `pytest -m data tests/test_producers.py -q` → `2 passed, 9 deselected in 5.19s`.

**CUDA determinism:** small SNN recipe twice on CUDA and once on CPU: `cuda_cuda_bit_identical True`; `cuda_cpu_bit_identical True`. Set `PERSIST_DEFAULT = dict(spikes="none", weights=False)`.

**v1 test edits:** none. **Cross-module gaps:** none encountered.

## M3 · 2026-09-27 16:24 EDT
**Built:**
- `snntopo/runner.py`: spec loading by path (importlib, registered in `sys.modules`), `expand` (pair sides added to the activities; pairs gain `a_id`/`b_id`/`pair_key`), anti-join resume over every shard's files, stable sha256 shard hash (phase 1 by `training_key` or `activity_id`, phase 2 by `pair_key`), `run.json` with git state, `--dry-run` counts and cost, `status`.
- `snntopo/cli.py`: `run <spec> [--out] [--shard i/N] [--mini] [--dry-run] [--retry-failed]` and `status <run_dir>`. The 8 v1 subcommands are unchanged.
- `snntopo/topology/stats.py`:
  - `SNNTOPO_WORKERS`, read per call: `max_workers=min(workers, len(halves1))`.
  - The serial fallback logs one loud line per process (`_SERIAL_WARNED`).
  - Disk layer: `DISK_CACHE` module flag, off by default; `runner.run` sets it and restores it in `finally`. Lookup goes memory -> `store/halves/<key>.npz` -> compute. Computed entries are written through `dataset.store_put_npz` (tmp + `os.replace`, write-once).
  - Disk key = `short_hash(content_hash, sha256(mask), h, n_resamples, seed, topo_id, cmp_id)`. `dataset` and `producers.content_hash` are imported at call time to avoid the import cycle (dataset imports `STATS_VERSION`).
  - The forkserver preloads `snntopo.topology.stats`. Under `python -m` and pytest, `__main__` isn't preloaded (forkserver passes only `main_path`), so every new pool's workers re-imported stats + torch, about 1.3 s per `_split_halves` call. The full suite went from 41 s to 31 s. Numbers are unchanged: `_half_pair` is the same function in the same order.
- `tests/test_runner.py` (11 tests) and `tests/specs/tiny.py`: 6 circles, a 2-update SNN trained once for checkpoints 0 and 2, a failing recipe, and 5 pairs (a side outside the recipes, `first_half`, 2 seeds, one blocked by h, SNN-vs-SNN).

**Runner semantics (the reviewer should check these):**
- **Phase-1 write order: spikes blob -> signature rows -> self-null rows -> activity row *last*.** The brief listed the activity row first. It is last because the activity row is the commit marker. If an ok/degenerate activity row exists, all of that activity's signature and self-null rows exist too. So resume never has to guess an activity's conditions, and another shard's phase 2 never sees an activity whose signature rows are half written. A kill before the marker means the activity is produced again; rows already on disk are skipped by key. The row set is the same as with the brief's order.
- Self-null expected keys (status/dry-run) come from the signature rows: `n_trials // 2`, seed 0, each condition with `skipped is None`. That matches `measure.null_rows(h=None)`.
- Pair nulls are computed on an `Activity` restricted to the pair's condition. `measure.null_rows` with an explicit h runs every usable condition, and raises when h is too big for one of the others. They hit the in-memory halves compare just filled.
- A pair is `waiting` (a side has no row yet; a later run picks it up) or `blocked`: a side failed, the condition is missing or skipped, or 2h > n_trials, all read from the signature rows. Blocked pairs are logged and never computed.
- Phase-2 sides come from, in order: an in-process LRU (16), `store/spikes/<content_hash>` if persisted, or `produce` again (both sides in one call, so SNN checkpoints share one training). A regenerated side must reproduce its recorded `content_hash`; otherwise the pair is blocked with a "persist its spikes" message.
- A run dir holds one (spec path, topo_id, cmp_id, mini). Resuming with a different one is refused ("Use a new --out"). Otherwise a TOPO change would leave activity rows marked done without signatures at the new topo_id.
- Crash/concurrency safety:
  - Each shard has its own jsonl files and its own `run[.sIofN].json` = `{"invocations": [...]}`, replaced via tmp + `os.replace`.
  - Each shard holds a non-blocking `flock` on `.lock[.sIofN]`, so a second process on the same shard is refused.
  - `--shard` requires `--out`.
  - New run dirs are made with an atomic `mkdir` loop (`-2`, `-3`, … on collision).
- An invocation record holds spec, `code_rev`, `spec_blob` (`git hash-object`), `spec_tracked`, `clean`, argv, host, shard, mini, `exploratory`, `retry_failed`, topo_id, cmp_id, persist, start/end, status (`running|done|incomplete|failed`) and summary. A killed run stays `running`.
  - `clean` = `status --porcelain --untracked-files=no` is empty in both the code checkout and the spec's repo, and the spec is tracked and matches HEAD.
  - `is_experiment` = the spec's parent dir is named `experiments`. It can't test for "experiments" anywhere in the path, because this repo itself lives under `~/Code/main/experiments/`.
  - `exploratory` = `--mini` or not under `experiments/`.
  - Track A adds `prereg_hash`/`verdict_hash` to the record and `verdict`. The `PREREG is None -> --mini only` rule isn't built (M5 binding).
- The PERSIST spikes rule counts an activity as SNN when its base kind is `snn`, controls of one included: `"all"` covers every SNN activity, `"paired"` covers SNN pair sides. Weights go through `produce(persist_weights=True)`.
- `--dry-run` cost model (orchestration.md): produce 1 s synthetic / 5 s bio / 1 s per SNN eval; train 5 + 0.05·n_updates s per training key; measure 12 s per activity; compare 3 s per (pair, seed). Measure and compare scale by n_resamples/50. The estimate adds an upper bound for SNN sides retrained in phase 2 when their spikes aren't persisted.

**Checks:**
- `pytest -q` → `161 passed, 1 skipped, 11 deselected, 2 warnings in 31.37s`.
- `pytest -q tests/test_runner.py` → `11 passed in 15.96s`.
  - Kill-and-resume: a subprocess is SIGKILLed once the second activity's signature rows exist. In 4/4 manual tries that was `acts 1 sigs 12 nulls 6`, i.e. signatures written, nulls and the marker not. A torn fragment is then appended, and the rerun gives the same row set as the uninterrupted run. The kill test passed 6/6 repeats.
  - Shards 0/2 + 1/2, then a second pass of each, give the one-shard row set, with one store shared by all shards.
  - Pooled = serial = disk-written = disk-read: diagrams, within arrays and compare/null results are bitwise equal, dtype included. The disk-read pass monkeypatches `build_trajectories`/`_half_pair` to raise.
  - The dirty-tree refusal uses a tmp git repo: an untracked or modified spec is refused, an untracked other file doesn't make the tree dirty, and `--mini` runs labelled exploratory.
  - Also covered: rerun is a byte-level no-op, `--retry-failed`, the construction-mismatch/lock/`--shard`-needs-`--out` refusals, dry-run writes nothing, run-dir collisions, the `SNNTOPO_WORKERS` cap, and the serial warning logged once.
- `pytest -q -m data tests/test_producers.py` → `2 passed, 9 deselected in 5.23s`.
- `snntopo run tests/specs/tiny.py --dry-run` (run as `python -m snntopo.cli` from the worktree; the venv's `snntopo` script points at the main checkout):
```
spec .../tests/specs/tiny.py | shard all | run dir (new)
topo_id d8c80deadabf2a4f | cmp_id b2af5b74ed7d9f5c | persist {'spikes': 'none', 'weights': False}
activities   expanded 10 | done 0 | failed 0 (not retried without --retry-failed) | to do 10
signatures   rows done 0 | to do: every row of the 10 activities to produce (conditions known after produce)
nulls        rows done 0 of 24 known (self + pair) | + self-nulls of the 10 activities to produce
comparisons  rows done 0 of 12 | pairs: 0 done, 0 ready, 5 waiting on activities, 0 blocked
cost         ~0.5 min serial (produce 10 s, train 1x 5 s, measure 10x 10 s, compare 6x 1 s, phase-2 SNN retrain <= 1x 5 s); rough, from orchestration.md's cost model, assumes a 16-core pool
```
- `snntopo status` after `run --shard 0/2`, `1/2`, `0/2`, `1/2` into one `--out`. First-pass logs: shard 0 `2 waiting`, shard 1 `0 waiting`; second pass: shard 0 `1 pairs compared, 1 blocked`.
```
run /tmp/tmp.czGWy8xi6l/runs/sharded
shard 0/2: done (last of 2 invocations, 2026-09-27T16:23:57-0400 -> 2026-09-27T16:23:57-0400, code_rev d27af89-dirty, clean False, exploratory)
shard 1/2: done (last of 2 invocations, 2026-09-27T16:23:59-0400 -> 2026-09-27T16:23:59-0400, code_rev d27af89-dirty, clean False, exploratory)
rows per file:
  activities.s0of2.jsonl           5
  activities.s1of2.jsonl           5
  signatures.s0of2.jsonl           24
  signatures.s1of2.jsonl           30
  nulls.s0of2.jsonl                24
  nulls.s1of2.jsonl                38
  comparisons.s0of2.jsonl          4
  comparisons.s1of2.jsonl          6
failed activities (1): 641baf1d8f355d51
vs expansion of .../tests/specs/tiny.py:
  activities   expanded 10 | done 9 | failed 1 (not retried without --retry-failed) | to do 0
  signatures   rows done 54 | to do: every row of the 0 activities to produce (conditions known after produce)
  nulls        rows done 62 of 62 known (self + pair) | + self-nulls of the 0 activities to produce
  comparisons  rows done 10 of 10 (+2 blocked) | pairs: 4 done, 0 ready, 0 waiting on activities, 1 blocked
  cost         ~0.0 min serial (produce 0 s, train 0x 0 s, measure 0x 0 s, compare 0x 0 s); rough, from orchestration.md's cost model, assumes a 16-core pool
  blocked: too-big: h=7 needs 14 trials; activity 7a0fc3b828c807cb 'all' has 12
```
- design.md's M3 check `snntopo run sweeps/validate_instrument.py --mini --dry-run` moves to M4, because that file is Track A's. The same check ran above on `tests/specs/tiny.py`.

**v1 test edits:** `tests/test_topology.py::test_split_halves_serial_fallback_is_bitwise_identical_to_pool` gains `monkeypatch.setattr(stats, "_SERIAL_WARNED", False)`, since the fallback now logs once per process (intended change). The message keeps "computing topology serially".

**Cross-module gaps (not changed; for the orchestrator):**
1. **`--retry-failed` is shadowed in `dataset.load`.** `load` dedups activities first-seen-wins, so a retried activity's new ok row stays hidden behind its earlier `failed` row. The runner's own anti-join treats "any ok/degenerate row" as done, so resume and phase 2 are right; downstream `load` users are not. Proposed fix in `dataset.load`: for activities, prefer an ok/degenerate row over a failed one (e.g. a stable sort on `status == "failed"` before `drop_duplicates`). That's M1's module, so I didn't touch it.
2. With `PERSIST_DEFAULT = spikes "none"` (M2), an SNN-vs-SNN pair whose sides aren't in the in-process cache (another shard, a later invocation, >16 sides) retrains in phase 2. It's correct, and the content_hash is checked, but slow at zoo scale. Specs with SNN pairs should set `PERSIST spikes="paired"`.
3. The halves disk cache stores SNN activities too, about 0.1-0.2 MB per (activity, condition, h, seed): roughly 0.5 GB for zoo v0's ~970 activities × 3 conditions. orchestration.md suggests skipping non-persisted SNNs. That needs activity kind inside stats, so it's left as is.
4. A measurement exception on a produced activity (a bug in measure/stats) stops the run with `run.json` status `failed`, and the resume retries that activity. It isn't turned into a row.

## Orchestrator · 2026-09-27 16:50 EDT · phase 1 integration
- M1 `e7ef821` (mine). M2 merged `d27af89` after a gate fix pass (`3520de8`: controls of SNN recipes all failed with `KeyError: 'task'`; bio controls lost session/independence_group; degenerate check narrower than v1; dangling diagram pointer on skipped rows). M3 merged `c75aff7`, reviewer verdict merge.
- `917a8b8` `dataset.load`: an activity's ok/degenerate row beats an earlier `failed` one (M3 gap 1, `--retry-failed`).
- `producers.produce` trained every model before yielding any row (a zoo shard would hold all models and lose all training on a kill); now trains lazily in recipe order and frees each model after its last recipe. SNN training was hard-coded to CPU; now `producers.DEVICE` = `SNNTOPO_DEVICE` or cuda-if-available, and `tests/conftest.py` pins tests to CPU. Replaced M2's `training_key`-call-count test with one on train/yield interleaving.
- CUDA determinism, re-measured (M2's probe was untrained-size): recurrent LIF n_hidden 256, 200 updates, CUDA twice → identical content_hash `c90a816209ced3d3` both times. CUDA vs CPU at 20 updates: checkpoint 0 identical, trained checkpoint differs. So `PERSIST_DEFAULT spikes="none"` holds per device; regenerating on another device is caught by the runner's content_hash check (pair blocked with "persist its spikes").
- Known, not fixed: resuming one `--out` with a different shard N repartitions work (duplicate compute, no bad rows; M3 review #2). The halves disk cache also stores SNN halves (~0.5 GB for zoo v0; M3 gap 3). M3 check `validate_instrument --mini --dry-run` moved to M4 (the file is Track A's).

## Track B · 2026-09-27 16:52 EDT

**Built:** Atomic Steinmetz part download: each fetch now writes a unique sibling temporary
file, fsyncs it, and publishes with `os.replace`; a failed transfer removes its temporary
file and cannot leave a final partial archive. Added `sweeps/bio_core.py`, an exploratory
resolved-data spec for part0's 13 sessions. It has active responded, passive, and active
no-go for every whole session and each non-`root` region with >=50 units, plus two seeded,
disjoint neuron halves and an `all` comparison for each region/selection. `CMP` is
`("wasserstein", "bottleneck")`, 50 resamples, so R1 integration reads each H1 signature
diagram row and its matching `nulls` bottleneck `null_q95` (same activity/condition/topo/cmp,
self-null `h=n_trials//2`, seed 0). The neuron-split `comparisons` are the stated-h control,
not R1's threshold source.

**Counts:** real expansion found the inventory's 77 region populations. Thus 3 selections ×
`(13 whole + 77 regional + 2*77 split-half)` = **732 activities**; 3 × 77 = **231 pairs**;
each pair has 2 metrics × H0/H1 = **924 comparison rows**. The planned signature total is
732 × 3 conditions × 2 dimensions = **4,392**. With responded/passive's three usable
conditions and no-go's `all` condition, self-null rows are
244 × (12 + 12 + 4) = **6,832**; pair `h` equals the same selection's self-null `h`, so
those null keys deduplicate rather than add rows.

**Checks:**

```text
$ python -m pytest -q tests/test_steinmetz_download.py tests/test_bio_core.py
3 passed in 0.95s

$ python -m snntopo.cli run sweeps/bio_core.py --dry-run
activities   expanded 732 | done 0 | failed 0 (not retried without --retry-failed) | to do 732
signatures   rows done 0 | to do: every row of the 732 activities to produce (conditions known after produce)
nulls        rows done 0 of 1848 known (self + pair) | + self-nulls of the 732 activities to produce
comparisons  rows done 0 of 924 | pairs: 0 done, 0 ready, 231 waiting on activities, 0 blocked
cost         ~218.9 min serial (produce 3660 s, train 0x 0 s, measure 732x 8784 s, compare 231x 693 s); rough, from orchestration.md's cost model, assumes a 16-core pool

$ python -m pytest -q
165 passed, 1 skipped, 11 deselected, 2 warnings in 42.89s
```

**Timing/run:** mini (session 0) run
`/home/jake/Code/main/experiments/snn_topo/results/runs/20260927-1645-bio_core` took
4m05s (16:45:49–16:49:54), with 57 activities and 18 pairs. Its completed status was:

```text
rows per file:
  activities.jsonl                 57
  signatures.jsonl                 342
  nulls.jsonl                      532
  comparisons.jsonl                72
failed activities (0): -
activities   expanded 57 | done 57 | failed 0 (not retried without --retry-failed) | to do 0
signatures   rows done 342 | to do: every row of the 0 activities to produce (conditions known after produce)
nulls        rows done 532 of 532 known (self + pair) | + self-nulls of the 0 activities to produce
comparisons  rows done 72 of 72 | pairs: 18 done, 0 ready, 0 waiting on activities, 0 blocked
```

Extrapolating by 732/57 gives **~52.3 minutes**. Per the 30-minute rule, the full run was
not launched; it needs orchestrator/user approval to resume. I inspected the other processed
download paths: Allen and IBL both still write `np.savez_compressed` directly to their final
cache paths, so they are not concurrent-download atomic; they are outside this track's file
scope and were not changed.
## Track C · 2026-09-27 17:12 EDT
**M7 built:** `sweeps/measure_gpu.py` and `sweeps/zoo_v0.py`. Zoo v0 is exactly
27 valid triples × 2 hidden sizes × 3 seeds × 3 checkpoints × 2 regimes = **972**
activities, all self-null only (no declared pairs). Its MINI is six existing triples,
one seed, task regime, checkpoint 200, trained for 200 updates.

**GPU measurement:** Before the clean run, `nvidia-smi` showed only nodeterm's Wayland
renderer (242 MiB); no other compute app. Each cell is 200 recurrent-LIF/random updates,
with `peak_mib` from `torch.cuda.max_memory_allocated()`, then mean/max `nvidia-smi`
utilization and max observed total GPU memory.

| hidden | trainers | wall s | updates/s/trainer | total updates/s | peak MiB | util mean/max % | total GPU MiB max |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 64 | 1 | 11.13 | 22.14 | 17.97 | 76.3 | 30.6/50 | 1662 |
| 64 | 2 | 16.51 | 15.62 | 24.23 | 76.3 | 51.6/97 | 2150 |
| 64 | 4 | 20.98 | 11.76 | 38.13 | 76.3 | 68.6/99 | 3539 |
| 256 | 1 | 20.43 | 13.40 | 9.79 | 113.4 | 21.3/45 | 2028 |
| 256 | 2 | 22.34 | 12.39 | 17.90 | 113.4 | 41.5/90 | 2770 |
| 256 | 4 | 33.68 | 8.74 | 23.75 | 113.4 | 55.1/98 | 3393 |
| 1024 | 1 | 60.05 | 8.58 | 3.33 | 286.0 | 17.7/79 | 2551 |
| 1024 | 2 | 65.52 | 10.26 | 6.10 | 286.0 | 28.7/99 | 3291 |
| 1024 | 4 | 89.83 | 6.51 | 8.91 | 286.0 | 39.0/100 | 4529 |

**N = 2 zoo shards.** Four trainers maximized raw GPU throughput, but at 256–1024 it
reduced per-trainer throughput sharply and its gain over two was modest; with the two other
topology tracks each capped at five workers, two zoo shards retain useful CPU headroom.

**M7 check:** `python -m snntopo.cli run sweeps/zoo_v0.py --mini` → run
`results/runs/20260927-1659-zoo_v0`, 6/6 activities, 36 signatures, 36 self-null rows,
0 failed/missing; `summarize_smoke.py` → 0/6 degenerate, all six accuracy 1.0. `zoo_v0
--dry-run` reported 972 activities; no real zoo run was launched.

**M8 built:** deterministic per-neuron beta spread (`beta + spread*linspace(-1,1,n)`,
clamped to `(0,1]`), Dale recurrent columns (last rounded `frac_inhibitory*n` columns
inhibitory; effective recurrent weights use `abs(raw) * sign * mask` every forward), rate CTRNN
with count-valued Poisson sampling at recipe gain, and balanced three-action
`steinmetz_nogo` (`left`, `right`, `nogo`). `frac_inhibitory` is rejected unless Dale is on;
Dale is rejected for feedforward networks. The rate policy uses the passing 200-update
large-batch/low-learning-rate settings. `zoo_v1.py` contains v0 plus the eight passing configs
over the standard grid: 1,260 activities in `--dry-run` (no real run).

**Smoke checks (all `status` 0 missing):**
- tau spread: `results/runs/20260927-1701-smoke_tau_spread`, 0/2 degenerate; accuracies 1.0,
  1.0; PASS.
- Dale: `results/runs/20260927-1702-smoke_dale`, 0/2 degenerate; accuracies 1.0, 1.0; PASS.
- rate: final passing run `results/runs/20260927-1707-smoke_rate`, 0/2 degenerate; accuracies
  1.0, 1.0; PASS. Earlier `1702`, `1703`, `1704`, `1705`, `1706` exploratory attempts record
  the rejected small-batch rate configuration (and one implementation-fix failure) rather than
  overwrite any measurement.
- Steinmetz no-go: final passing run `results/runs/20260927-1709-smoke_steinmetz_nogo`, 0/2
  degenerate; accuracies 0.9896, 1.0; PASS at chance 1/3. The preceding `1708` run recorded the
  unbalanced-sampler failure (2/2 degenerate); balancing the three classes fixed it.

**Verification:** targeted Track-C tests → `87 passed, 2 deselected in 4.90s`; full suite
`pytest -q` → `175 passed, 1 skipped, 11 deselected, 2 warnings in 61.63s`. New tests cover
CPU recipe determinism for tau/rate, Dale signs after optimizer steps, no-go shapes/targets,
and sweep expansion counts. **Gaps:** none.

## Orchestrator · 2026-09-27 18:00 EDT · phase 2 integration, paused
- Merged into v3-build: Track B (M6, `8dac864`), Track C (M7+M8, `8ad1b48`). Reviewers: ship for both. `pytest -q` at 8ad1b48: 179 passed, 11 deselected.
- bio_core full run: `results/runs/20260927-1703-bio_core`, 16 min wall (Track B's mini extrapolated 52), `status`: 732/732 activities, 6832 nulls, 924 comparisons, 0 missing, 0 failed. No R1 derived rows yet (see below).
- User decision (derived rows): optional spec hook `derive(activity_id, activity)`, called in phase 1 before the activity row; no new subcommand. Per activity, not over tables, because R1 needs the activity's diagrams and halves. Built in `85dee0e`; recorded in design.md "Spec interface"/"Runner" and requirements.md open questions.
- Track C notes accepted: producers.py `training_key`/`_model_and_train` also changed for the rate family (needed); `nogo` action has no bio condition of that name; `validate()` hard-codes 0.2; `tau_spread` unbounded (clamped).
- Track A resumed as a new node (A2) after the first hit the usage limit; brief-a2 answers its gaps: validation run OK (<=60 min); gap 1 (synthetic halves cost) left; gap 2 -> derive hook; gap 3 accepted (library numerics versioned by PIPELINE/STATS_VERSION); gap 4 is the user's E16 call.
- Orchestrator error: brief-a2 gave `--out` as a relative path, so the resume started an empty run dir inside the v3-a worktree; A2 killed and removed it (user approved) and reran against the shared dir.

**To resume (in order):**
1. CHECKPOINT 3: relay Track A2's scan table, chosen noise and intended PREREG to the user; on approval, a new Claude node in the Track A group commits PREREG, runs E15 (arms + contrasts), `snntopo verdict`, E-entry.
2. Gate Track A (floor/binding/verdict/E15/E16): run checks, `pytest -q`, reviewer; merge `--no-ff`.
3. `sweeps/bio_core.py`: add `derive()` calling `floor.robust_count_rows`; drop the dead `TOPO.metrics`; rerun into a new dir (~16 min) so every activity has R1 rows.
4. M9 docs: README, docs/architecture.md, dev/agents/spec.md (v3, replacing v1's), D29-D38 appended to dev/agents/decisions.md (continues from D28, no renumber), CLAUDE.md (sandbox from requirements.md, commands used, layout). `snntopo --help` lists 11 subcommands.
5. Check every requirements.md Done-when item with a real command. 6. CHECKPOINT 4: user OK to merge v3-build to main.

## Close · 2026-09-27 18:19 · b13e52b..ac1ba4a
- **changed:** snntopo v3 M1-M3 (dataset.py rows/ids/store, producers.py + measure.py, runner.py `run`/`status` with shards/resume/halves disk cache), merged on `v3-build`
- **changed:** M6 (atomic Steinmetz download, `sweeps/bio_core.py`) and M7+M8 (GPU measurement N=2, `sweeps/zoo_v0.py`/`zoo_v1.py`, `tau_spread`, Dale, rate family, `steinmetz_nogo`), merged on `v3-build`
- **changed:** runner: optional spec `derive(activity_id, activity)` hook for derived rows (user decision; design.md "Spec interface"/"Runner")
- **changed:** Track A (M4 floor.py + validate_instrument, M5 PREREG binding + `snntopo verdict`, E15 spec, E16 skeleton) is on `v3-a`, NOT merged (+1283 −3, 11 files)
- **why:** build the v3 dataset workspace from `dev/agents/project/context/` (`/project-builder`, nodeterm orchestrator + codex/claude tracks)
- **verified:** `pytest -q` on v3-build at 8ad1b48 → 179 passed, 11 deselected; `snntopo status results/runs/20260927-1703-bio_core` → 732/732 activities, 924/924 comparisons, 0 missing; `zoo_v0`/`zoo_v1 --dry-run` → 972/1260 activities; Track A2 (v3-a): `snntopo verdict sweeps/validate_instrument.py` → PASS 8/8 (E17), `pytest -q` → 174 passed, 1 skipped, `-m data` → 13 passed
- **by:** claude
- `ac1ba4a` journal: phase 2 integration and resume list
- `8ad1b48` Merge M7+M8 (Track C): GPU measurement (N=2), zoo_v0/v1, tau_spread, Dale, rate family, steinmetz_nogo
- `85dee0e` runner: optional spec derive(activity_id, activity) writes derived rows in phase 1
- `99cba89` design: derived rows come from an optional spec derive(tables) hook (user decision)
- `2c4103a` M8 add gated model axes and families
- `6d6dd02` M7 measure GPU and define zoo v0
- `8dac864` Merge M6 (Track B): atomic Steinmetz download, sweeps/bio_core.py
- `a7e4aad` Add atomic Steinmetz download and bio core sweep
- `f6bf95b` producers: train lazily per training key, GPU when available; journal phase 1
- `c75aff7` Merge M3: runner run/status, shards, resume, SNNTOPO_WORKERS, halves disk cache
- `917a8b8` dataset.load: a retried activity's success beats its earlier failed row
- `1342fc9` M3: runner (run/status), shards, SNNTOPO_WORKERS, disk halves cache
- `d27af89` Merge M2: producers, measure, stats h/seed, checkpoints, Steinmetz trial arrays
- `3520de8` Fix M2 producer and measurement gate findings
- `d139afb` M2: add activity producers and measurement rows
- `e7ef821` M1: dataset.py (ids, RunWriter, store, load) + PIPELINE/STATS_VERSION
- 38 files, +3212 −36

### Next
1. CHECKPOINT 3 (user): approve E15's PREREG. Track A2's report is the `## Track A (cont.)` section of `dev/agents/journal.md` on `v3-a` (`git show v3-a:dev/agents/journal.md`): scale 1026×110, blind target H1 null_mean 0.06644, scan 12 → 0.0581, 16 → 0.0756, chosen noise 12. The user had typed (unsent) "add 14 to the scan and rerun it" into A2: do that first (`python experiments/e15_engagement.py scan` in the v3-a worktree, add level 14), then show the table + intended PREREG.
2. On approval: commit PREREG on v3-a, run E15 (arms + contrasts, ~30+ min), `snntopo verdict experiments/e15_engagement.py`, new E-entry; run `snntopo run experiments/e16_nogo.py --mini` for real.
3. Gate v3-a: `pytest -q`, reviewer agent on `git diff v3-build...v3-a` (check `runner.load_spec` compile-from-source change and the binding tests), merge `--no-ff` (journal conflict: keep both sections).
4. `sweeps/bio_core.py`: add `derive()` calling `floor.robust_count_rows(aid, activity, TOPO, CMP)`, drop dead `TOPO.metrics=`; rerun into a new dir (~16 min) so every activity has R1 rows.
5. M9 docs (README, `docs/architecture.md`, v3 `dev/agents/spec.md` replacing v1's, D29-D38 appended to `dev/agents/decisions.md` (continues after D28), root `CLAUDE.md` with Agent sandbox from requirements.md); `snntopo --help` lists 11 subcommands; check every requirements.md Done-when item by command; CHECKPOINT 4: user OK to merge `v3-build` → main.
### Traps
- `snntopo run --out` with a relative path resolves against cwd, so from a worktree it starts a new run in the worktree. Pass `$SNNTOPO_RESULTS_DIR/runs/<id>`.
- nodeterm `send`/`settings` answer "Agent messaging refused." even with messaging switched on: a follow-up to a track means a new node in its group (`open-agent --group <group-id> --prompt-file`).
- nodeterm lists working codex nodes as "AGENT STATUS UNCONFIRMED"; read panes with `tmux -L node-terminal capture-pane -p -t nt-<node-id>`. A Claude pane's busy marker is the `…(Nm Ns` spinner, not "esc to interrupt".
- Three tracks sharing the 16 cores slowed topology ~3× (validation 10-16 s/activity loaded, 3-5 s quiet); bio_core took 16 min quiet vs a 52 min loaded extrapolation.
- Codex workers overwrote `dev/agents/journal.md` once; briefs must say APPEND, never rewrite.
### Pointers
- Build packet: `dev/agents/project/context/{requirements,design,decisions,agent-team}.md`; derived-rows decision in design.md "Spec interface"/"Runner".
- Briefs (session scratchpad, gone after reboot): brief-a.md / brief-a2.md contents are summarized in Track A sections of the journal on v3-a.
- Worktrees: `../snn_topo.worktrees/v3-{a,b,c,m2,m3}`; only v3-a is unmerged. nodeterm groups: Track A `group-mukacave-5de15e30`.
- Runs: `results/runs/20260927-1703-bio_core` (full), `results/runs/20260927-1703-validate_instrument` (E17).
- Runner phase 1 / derive hook: `snntopo/runner.py:447-495`; R1: `floor.robust_count_rows` (v3-a `snntopo/floor.py:258`).
