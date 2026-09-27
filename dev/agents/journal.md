# Journal · 2026-09-27 15:24 · v3-m2 · e7ef821
## Start
**State:** M1 is committed on this branch: `snntopo/dataset.py` supplies stable IDs, JSONL writing, content-addressed storage, and loading. The v3 implementation packet defines M2 as producers, measurement rows, Steinmetz selectors, stats additions, training checkpoints, and seeding.
**Since:** `e7ef821` added M1 after the previous session's v3 packet; this worktree is otherwise clean.
**Next:** Implement and test M2's owned modules, run the complete suite plus targeted data/CUDA checks, journal the evidence, and commit the result for the orchestrator gate.
**Traps:** Seed before SNN model construction; statistics must be run from a file or pytest because stdin disables the intended forkserver execution; Steinmetz active `all` means responded trials only.
**Pointers:** `dev/agents/project/context/design.md` M2 and recipes/rows; `snntopo/dataset.py`; v1 `atlas.py`, `topology/stats.py`, and `data/steinmetz.py`.

## M2 · 2026-09-27 15:36 EDT
**Built:** `producers.py` for bio, synthetic, control, and existing SNN recipes; deterministic pre-build SNN seeding; grouped training/checkpoint evaluation; content-addressed activity and optional weight storage; and failed-row handling. Added measurement signature/null/comparison rows with diagrams, R2 H1 presence, R4 anchors, and stated construction IDs. Added explicit `h`, seed, and per-side null means to stats results; training snapshots; and Steinmetz full-trial selector arrays.

**Checks:**
- `pytest -m data tests/test_producers.py -q` → `1 passed, 4 deselected in 4.28s`.
- `pytest tests/test_producers.py tests/test_measure.py -m 'not data' -q` → `7 passed, 1 deselected in 4.72s`.
- `pytest -q` → `144 passed, 1 skipped, 10 deselected, 2 warnings in 42.73s`.

**CUDA determinism:** small SNN recipe twice on CUDA and once on CPU: `cuda_cuda_bit_identical True`; `cuda_cpu_bit_identical True`. Set `PERSIST_DEFAULT = dict(spikes="none", weights=False)`.

**v1 test edits:** none. **Cross-module gaps:** none encountered.
