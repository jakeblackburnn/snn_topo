# What's stale or wrong in `../mega-forward-plan/` (as of 2026-09-27)

> That folder is input only and is not edited here. This list is for whoever cites it next.
> Checked against `dev/agents/decisions.md` D28, `dev/agents/experiments.md` E12-E15, git log,
> and the code at `5d91f47`.

## Wrong (retracted or contradicted by later results)

| where | claim | now |
|---|---|---|
| `index.md` §4 "(ii)" and the bottom of §4 | the split-half null is anticonservative; circle vs circle p=0.030 is a false positive | **retracted by E12**: null valid, 1/40 H0 and 0/40 H1 (E14: 0/40 both). The seed-shared embedding made that pair a geometry difference, not a null pair (`generators.py:33-36`) |
| `index.md` §4 table, "a genuine topological difference looks like 108, not 2" | fixed ratio scales separate topology from bio | **artifact of mismatched noise** (E14/D28): circle vs figure-8 reads about 2.8 at E13's noise and 31-38 at IBL-matched noise. Ratios are comparable only at matched `null_mean` |
| `index.md` "best current explanation of D20": "no detectable topological difference between any of these recordings" | — | **rejected by D28**: E15 detects engaged-vs-passive on fixed neurons in 11/12 held-out sessions. The difference is in the signature; whether topology differs is not established |
| `scientific-reframe.md` prediction AUC ≈ 0.5 | — | already corrected inside mega (computed AUC 0.77). Still post hoc: never cite it as a result |

## Stale (done or overtaken)

| where | item | status |
|---|---|---|
| `index.md` "Recommendation" steps 1-3 | confound-free E4, synthetic positive control, preregister E12 | **done**: E13/E15, E12/E14, `755097e` |
| `index.md` "What is already in flight" | 4 codex branches | **merged**: `33d83a6`, `7dbef2f`, `89ecf03`, `2791165`. `git worktree list` still names all four, but their directories (`../snn_topo.worktrees/`) no longer exist, so `git worktree prune` plus deleting the branches is all that's left |
| `index.md` open Q3 "does E4 fail for power reasons?" | — | answered: E12-C/E14-C detect real H1 differences at matched noise, and D22 had a power check. D28 moved the question from power to noise scale |
| `index.md` open Q1 "what is the reference panel?" | — | still open, now reframed as opt-in, not mandatory (`pair-policy.md`) |
| `codebase-consolidation.md` F1, A5 | no `--residualize-raw-diameter` flag | **fixed** (`cli.py:220`) |
| F2, A6 | `kind` contract comment; reports drop controls | **fixed** (`contracts.py:158`, `report.py:111`) |
| F4, B1 | `distance` overwritten in place | **fixed**: `distance_residual` + `construction` (`contracts.py:147-150`, `stats.py:239-247`). `data-platform.md`'s "stats.py:209-212 overwrites distance" is stale |
| F5, B2 | fit hardcoded in source | **fixed**: `topology/raw_diameter_fit.json` + `scripts/refit_raw_diameter_fit.py` |
| F6, F7, F8, F10, A2 | dedup refs, dead code, `N_EVAL`, `SNNTOPO_DATA_DIR`, serial pool fallback | **fixed** (`123ad7d`, `d2fff47`) |
| F9 | README subcommands | mostly fixed. README still omits `synthetic` (8 subcommands now, `cli.py`) |
| F3, B3 | controls cited but not on disk | **still open**: 0 control records in any run dir (`checks/inventory.out` §1). Journal Next 4 |
| `data-platform.md`, `model-zoo.md` | `_CACHE_SIZE = 32` undersized | **still true** (`stats.py:111`) |
| `data-platform.md` | `h` pair-dependent and unrecorded | **still true** (`stats.py:222`; no `h` field on any stored row) |
| `model-zoo.md` §1 | synthetic generators | **built** (`generators.py`). Its proposed `snntopo/generators/` registry name now collides with it |
| `bio-data-expansion.md` 1a, 1b | passive block; 13 sessions | **built** (`steinmetz.py`), with region sub-sessions |
| `distance-construction.md` R1 (AUC / Steinmetz-vs-IBL criterion) | a re-designed D20 test | superseded as a direction: D28 retired the bio-vs-bio yardstick. The post-hoc AUC numbers stay post hoc |

## Still valid and load-bearing (cited, not restated, by this folder)

- The all-pairs cost wall and the measured gudhi timing (`data-platform.md`).
- "Never overwrite a measured number" and provenance hashing (`data-platform.md`).
- "`Activity` is the cheapest extension point" (`model-zoo.md`).
- The pseudo-replication trap for sub-session entries (`bio-data-expansion.md` §7-§9).
- H1 under-sampling at `n_pca=10`, and the non-TDA anchors (`distance-construction.md` §2).
- The taste audit's "don't do these" list (`codebase-consolidation.md` Part 4).
