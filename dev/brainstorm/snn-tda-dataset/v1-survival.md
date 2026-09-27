# What survives from v1, what gets rewritten, and the guards for the builder

> Brainstorm notes, 2026-09-27. Nothing here is a decision. Options with a recommendation.
> Seed: `../mega-forward-plan/codebase-consolidation.md` (audit at `599eb25`; most of its Track A
> and B has since merged, see `seed-errata.md`). The worry this file answers: a later
> `/project-builder` run one-shots over working code.

## Principle

The measurement chain is validated and its numbers are cited in D22-D28 and E4-E15. **Nothing on
the path from `Activity` to `DistanceResult` changes a number.** New capability goes in around
that path: before it (recipes, producers), beside it (explicit `h`, per-side nulls, a disk cache),
and after it (records, runner, verdicts). The v1 code is about 2.9k lines, well documented, and
128 tests pass (journal Start). This is an extension with a new data layer, not a rewrite.

## Module map

| module | verdict | what changes | guard |
|---|---|---|---|
| `topology/pipeline.py` | **keep, frozen** | add a `PIPELINE_VERSION` constant only | G2, G3 bit-identical |
| `topology/stats.py` | **keep numerics; additive only** | optional explicit `h` in `compare` (default = today's `min//2`); return `h`, `seed`, per-side null means; `SNNTOPO_WORKERS` cap at `:171`; disk layer under `_CACHE` (memory → disk → compute); optionally cross distances into the pool; `STATS_VERSION` | G2, G3, G4, plus a pooled == serial == disk-cached equality test |
| `contracts.py` | keep; additive fields only (its own rule, `:4`) | `DistanceResult` gains `h`, `seed`, `null_mean_a/b` with defaults. The new record dataclasses live here too, keeping one home for interfaces | existing tests |
| `generators.py` | keep | wrapped by `synthetic_activity(recipe)` | `tests/test_generators.py` |
| `data/*` | keep | Steinmetz: a trial/condition selector for no-go and contrasts (`steinmetz.py:121-135`); atomic tmp+rename downloads (`orchestration.md`). IBL/Allen unchanged. `DATASETS` references unchanged (`data/__init__.py:6` TODO(human) is a scientific call) | `pytest -m data` |
| `models/`, `tasks/`, `training.py`, `evaluate.py` | keep | seed before `build_model` inside the new producer, not in `snn_entry` (`snn-breadth.md`); new regimes/tasks are additive | `tests/test_models.py`, `test_search.py` |
| `controls.py` | keep | wrapped as `control` recipes | `tests/test_controls.py` |
| `atlas.py` | **keep as the legacy path** | still serves the existing subcommands; gains a read-only legacy adapter to the new record types | `tests/test_atlas.py`; G5 |
| `search.py`, `objective.py` | **freeze** (`experiments-and-prereg.md` §1, S1) | none | `tests/test_search.py` |
| `report.py`, `figures.py` | keep for legacy run dirs | a new dataset report is new code, not an edit | `tests/test_report.py` |
| `cli.py` | keep all 8 subcommands | add `run`, `status`, `verdict` | `tests/test_cli.py` |
| `scripts/engagement_contrast.py`, `scripts/null_calibration.py` | **replace, then delete** | become `experiments/e12…e15` specs. Delete once G3/G4 pass (git keeps them; the user's taste is to delete dead code) | G3, G4 |
| `scripts/refit_raw_diameter_fit.py` | keep | reproduces D27's fit data | — |
| `prototype/` | untouched | — | — |
| **new** | write | `producers.py`, a dataset module (records, loader, legacy adapter), a runner, `experiments/`, `sweeps/`, derived metrics (floor multiple, band position, robust counts) | new tests |

## Golden checks (proposed acceptance for the build)

| id | check | cost | pass |
|---|---|---|---|
| G1 | `pytest -q` | ~1 min | all 128 existing pass **unmodified**, plus new ones |
| G2 | `snntopo baseline` into a scratch dir vs `results/baseline-wide/distances.csv` | ~12 min | bit-identical (mega Track B's harness) |
| G3 | E15 via `snntopo run experiments/e15_…` | ~6.4 min | 390 rows string-identical to `results/engagement-contrast-e15/contrasts.csv`; verdict prints REPLICATES 11/12 with floor 1.09 |
| G4 | E12 and E14 via specs | ~15 min | 320 and 240 rows identical to their `pairs.csv`; verdicts as in `experiments.md` |
| G5 | the legacy adapter loads all 16 `atlas.jsonl` run dirs | seconds | record counts match `checks/inventory.out` §1 (235 bio, 317 snn, 0 control) |
| G6 | E16 spec in mini mode (one session, one seed) | minutes | expands, runs, and `verdict()` executes on its rows. No verdict is claimed |
| G7 | SNN producer determinism: the same recipe twice on CUDA, once on CPU | minutes | `content_hash` equal. If not, persisting spikes becomes mandatory for paired SNNs |

G2-G4 are the "one-shot" guard. If a builder touches the numeric path, these fail on the first
run. G1's "unmodified" matters: an existing test edited to pass counts as a scope change, and it
needs the user's approval.

## Explicit non-goals for the build

- No change to any number the pipeline produces (G2-G4).
- No re-judging of past verdicts. A reproduced verdict that differs is a bug.
- No unblocking of the D20 search, and no revival of `objective.py` as a ranking.
- No new bio downloads. Gardner, MC_Maze and Steinmetz parts 1-2 are separate tasks.
- No running E16 for real. Its design is the user's call (`experiments-and-prereg.md` §5).
- No dashboards (D8 still holds).

## Open questions

- Should `atlas.py` eventually become a thin wrapper over the new records (single write path), or
  stay parallel until the legacy subcommands are retired? Parallel is safer for this build.
  Single-path is less code later.
- G2 costs 12 minutes per run. Should it be a build milestone check, or a pre-merge check only?
- Is 128 still the count at build time? The journal's Start says 128. Any tests added before the
  build shift the baseline.
