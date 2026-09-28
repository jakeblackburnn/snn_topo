# SPEC

> [!NOTE] the following is written by AI following a conversation - AI's ideas are not to be taken as ground-truth
> everything in '> [!NOTE]' blocks in this file are created by human

(v3, 2026-09-28. The v1 atlas/search spec is in git at `e007cc9:dev/agents/spec.md`.)

## Intent

My reading of `dev/main.md`: snntopo is an exploratory workspace that accumulates a large,
organized dataset of topological data analysis (TDA) results over many kinds of spiking
neural networks, extracts the same signatures from animal recordings, and compares the two.
The end products are the dataset, concrete TDA results on brain topology with comparison
metrics, and a poster.

So the product is **the dataset**, not a search for the most bio-like SNN (D29; `search.py`
and `objective.py` are frozen). The unit of record is an *activity* (neurons × trials × time
bins) identified by the resolved recipe that produces it (D30). Every activity gets
persistence signatures, split-half nulls at a stated `h`, and descriptors. Comparisons exist
only where a spec declares them (D32). Workflow and module map: `README.md`,
`docs/architecture.md`.

## What exists

| spec | kind | what it is | state |
|---|---|---|---|
| `sweeps/validate_instrument.py` | sweep | known-answer arms A/B/C × 40 at two scales (D33) | E17: PASS 8/8 |
| `experiments/e15_engagement.py` | experiment | engaged vs passive on fixed Steinmetz units, 13 sessions, own matched floor (D37) | see experiments.md, E18 |
| `experiments/e16_nogo.py` | experiment | no-go vs passive; population is the user's call, `PREREG = None` | `--mini` only |
| `sweeps/bio_core.py` | sweep | Steinmetz part 0: 13 sessions × {active responded, passive, no-go} × whole + regions with ≥ 50 units, neuron-split region controls, R1 derived rows | run |
| `sweeps/zoo_v0.py` | sweep | 27 existing SNN triples × {128, 512} × 3 seeds × checkpoints {0, 300, 1500} × {task, spontaneous} = 972 activities (D36) | smoke only; full run needs the user's OK |
| `sweeps/zoo_v1.py` | sweep | zoo v0 + the 8 smoke-passing new configs (τ spread, Dale, rate/CTRNN, `steinmetz_nogo`) = 1260 | dry-run only |
| `sweeps/smoke_*.py` | sweep | 200-update gates for the new families | all 4 PASS |

## Validity

- **Yardstick (D28):** a `compare` ratio is judged against synthetic arms at the *same*
  split-half null_mean as the data: A true null, B same shape / different embedding (geometry),
  C circle vs figure-8 (topology). Ratios measured at different noise aren't comparable.
- **Instrument (E17):** the v3 pipeline reproduces the known answers at E12's and E14's scales.
- **Significant ≠ different topology:** signatures include geometry. A ratio inside the B band
  is a geometry-sized change; only the band position against C says "topology-sized".
- **SNN vs bio** stays descriptive until a matched floor exists for it (their noise sources
  differ).
- **Preregistration (D35):** an experiment's PREREG and `verdict()` are bound at their first
  commit; `snntopo verdict` counts only clean runs whose hashes match.

## Out of scope for now

The overnight zoo runs (needs the user's OK; launch facts in `project/notes.md`, "Zoo launch").
E16's population. The D28 floor stress tests (latent shape, embedding dimension, rate). New bio
downloads (Gardner, MC_Maze, Steinmetz parts 1-2). Retiring v1. Dashboards.

## Known limits

- Synthetic recipes always add `first_half`/`second_half` conditions, which triples the cost of
  floor arms. A recipe option for `all` only would cut it by ~2/3.
- Code outside a spec (e.g. `floor.py`) isn't bound by PREREG. A numerics change there must
  bump `PIPELINE_VERSION`/`STATS_VERSION`.
- Significance power: effects below ~2× the null mean are often missed at `n_resamples=50`.
- `derive()` rows are written only for activities produced after the spec gained `derive`; to
  add them to an existing run, rerun it into a new dir.
