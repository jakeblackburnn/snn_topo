# Mega brainstorm · taking snntopo forward · 2026-09-23

> Brainstorm notes. **Nothing here is a decision.** Options with recommendations, per `/brainstorm`.
> Six research agents fanned out on separate angles; this file is the synthesis. Every claim
> attributed to an agent below that carries a number was **re-verified by hand** against cached
> data before being written here — see "Verified this session".

## Files

| file | angle |
|---|---|
| [distance-construction.md](distance-construction.md) | alternative comparison statistics for D20 |
| [scientific-reframe.md](scientific-reframe.md) | is the target question itself changing shape? |
| [model-zoo.md](model-zoo.md) | model families and generative axes to add |
| [bio-data-expansion.md](bio-data-expansion.md) | more and better biological data |
| [data-platform.md](data-platform.md) | storing/querying topological data at 10⁴–10⁶ entries |
| [codebase-consolidation.md](codebase-consolidation.md) | file-by-file audit + ordered refactor |
| [verify_auc_criterion.py](verify_auc_criterion.py) | runnable check of the three headline numbers |

---

## Recommendation, up front

**The project's stated blocker may be substantially a property of its acceptance criterion rather
than of its instrument — and the one experiment that would settle it costs zero downloads and has
been sitting in a cached file the whole time.**

Sequenced:

1. **Run the confound-free E4** (`steinmetz:11` active vs `steinmetz:11/passive`). Zero download.
2. **Run the synthetic positive control** (circle vs figure-8 at project defaults). Zero download.
3. **Preregister a new criterion** (E12) *before* looking at any more numbers — see the warning
   below, which is the most important paragraph in this file.
4. Only then: scale the model sweep, expand the data platform, and revisit the search.

Both (1) and (2) are being implemented right now by codex stations on branches
`feat-steinmetz-passive` and `feat-synthetic-controls`.

---

## Verified this session

These were checked directly against `results/baseline-wide/` and `data/raw/steinmetz/`, not taken
on an agent's word. Two agents disagreed about the first one; the numbers below settle it.

### 1. Under a standard effect-size framing, the current statistic already separates Allen

E4's criterion is **max-exclusion**: Allen must exceed the *maximum* of 190 within-IBL pairs. The
max of 190 draws is the least stably estimated statistic in a sample. Under the standard form of
"does this measure discriminate?":

| | AUC | p (Mann–Whitney, one-sided) |
|---|---|---|
| H0 | **0.771** | 3.4e-05 |
| H1 | **0.766** | 4.7e-05 |

Allen-vs-IBL (n=20) against within-IBL (n=190), ratio = `distance/null_mean`, condition `all`.

So "the instrument cannot discriminate" is too strong a reading of E5–E11. What is true is that it
cannot discriminate *by max-exclusion*. This directly contradicts `scientific-reframe.md`'s
prediction that AUC ≈ 0.5 — that agent reasoned from E5's prose ("Allen lands mid-range") rather
than computing it. The computed value wins.

### 2. …but H1's apparent discriminability is probably an artifact, and H0's is probably real

The right control for Allen is not within-IBL (that is *within*-dataset). It is **Steinmetz-vs-IBL**
— also cross-dataset, differing only in paradigm. Paired over the same 20 IBL sessions:

| | Allen > Steinmetz | median Δ | Wilcoxon (two-sided) |
|---|---|---|---|
| H0 | **17 / 20** | +3.334 | p = 0.012 |
| H1 | **1 / 20** | −0.255 | p = 0.0007 |

**H1 is significantly *anti*-discriminative for paradigm.** Combined with:

- **6 of 22** bio sessions have **zero** H1 features; median H1 count is **1**;
- `spearman(raw_diameter, H1_n) = −0.562, p = 0.0065`

…the picture is that H1 distances are largely being computed between near-empty diagrams, and H1
feature count is driven by how *noisy* a session is: `unit_diameter` divides by signal, so a
low-SNR session grows spurious micro-loops. That is a **multiplicative** per-session noise effect.
**E11 fitted an additive linear offset** — which is why it could not have worked, and is a better
explanation of D27's failure than the one currently in `dev/agents/decisions.md`.

It also means the project has been requiring its yardstick to pass on a dimension that may carry no
biological signal at this construction. `H0_n` is identical (150) across all 22 sessions — the
hardcoded `WINDOW = slice(50, 200)` — so H0 count carries no information either; only H0 *distance*
does.

### 3. The confound-free E4 has been in a cached file the whole time

`data/raw/steinmetz/steinmetz_part0.npz` holds **13 sessions**, of which the code uses one. Session
11 contains:

- `spks` → **(698, 340, 250)** — the active 2AFC trials the project already uses
- `spks_passive` → **(698, 110, 250)** — the **same 698 neurons**, same animal, same probes, same
  session, passive stimulus presentation

E4 confounds lab, animal, probe placement, unit count, region set, firing-rate scale *and* paradigm,
so its failure cannot be attributed to any one of them. `steinmetz:11` vs `steinmetz:11/passive`
holds all of those fixed and varies **only task engagement**. Zero bytes downloaded.

If the pipeline separates active from passive here, D20's framing needs rewriting. If it does not,
that is a far cleaner negative result than E4 — because there is nothing left to blame.

---

### 4. The positive control now exists, and it reframes D20

Built this session on `feat-synthetic-controls` and **re-run independently** by claude at the
project's own defaults (`n_pca=10, smooth_win=5, maxdim=1, n_resamples=50`), 300 neurons × 340
trials × 150 bins — i.e. bio-comparable scale:

| comparison | H0 ratio | H1 ratio | H1 p |
|---|---|---|---|
| circle vs circle (**identical** topology, different draw) | 1.52 | **2.66** | 0.030 |
| circle vs figure-8 (**genuinely different** H1) | 43.72 | **108.24** | 0.0099 |

Two things follow, and the second is the important one.

**(i) The pipeline is not underpowered.** It detects a real H1 difference at ~100× the noise floor.
So E4's candidate (c) — the never-run power analysis — can be answered: lack of power is *not* why
E5–E11 failed. That closes an open question that has been live since D20.

**(ii) Every bio comparison the project has ever made sits in the false-positive regime.** Compare
the table above against the real data:

| | H0 ratio | H1 ratio |
|---|---|---|
| within-IBL (n=190) | 0.90 – 14.25 (mean 5.12) | 0.94 – 14.31 (mean 2.22) |
| Allen vs IBL (n=20) | 1.95 – 13.88 (mean 8.39) | 1.24 – 4.33 (mean 2.14) |
| **synthetic, same topology** | **1.52** | **2.66** |
| **synthetic, different topology** | **43.72** | **108.24** |

The bio H1 mean ratio (2.22 within-IBL, 2.14 Allen-vs-IBL) is *indistinguishable from the
same-topology synthetic control* (2.66). A genuine topological difference looks like 108, not 2.

And note the same-topology pair still came out "significant" at p = 0.030 — **a false positive on
two point clouds with identical topology.** `stats.py`'s docstring claims a false-positive rate of
0–8% at α = 0.05 from synthetic checks; this is direct evidence the split-half null is
anticonservative in exactly the regime all the bio comparisons live in.

**So the best current explanation of D20 is not "the instrument cannot discriminate."** It is:
*there is no detectable topological difference between any of these recordings at this
construction, and the observed distances are sampling noise whose null under-estimates it.* That
is a much stronger, much more defensible claim than five FAILs — and it is only sayable **because
the positive control exists**, which is precisely the argument `scientific-reframe.md` made.

**Caveat, stated plainly:** the synthetic noise model (Poisson at `noise_level=0.25`) is not
calibrated to bio SNR, so the ratio *scales* are not strictly comparable across the table. The
robust part is the ordering and the order of magnitude — a real topology change produces ~10²,
bio differences produce ~10⁰–10¹. Calibrating the generator's noise to match bio split-half null
magnitudes would make this quantitative, and is the obvious follow-up.

---

## ⚠ The preregistration warning — read before acting on any of the above

Sections 1 and 2 are **post-hoc**. They were computed after seeing five FAILs against a criterion
that was fixed in advance. Switching to AUC now, because AUC is the framing under which the
existing data passes, is precisely the move this project's discipline exists to prevent — and the
project's single greatest asset right now is that it has never once moved a criterion after seeing
a result.

So: do not record "E4 passes under AUC" anywhere as a result. The honest path is to preregister
E12 with the criterion, the dimension(s) and the control population fixed **before** computing,
and to test it on data the post-hoc analysis did not touch — which is exactly what the Steinmetz
passive contrast and the additional Steinmetz sessions provide.

`scientific-reframe.md` §3 proposes the right companion safeguard for any learned version: a
**nuisance-orthogonality condition** (`|r| < 0.3` of the score against `|Δraw_diameter|`) alongside
the discriminability bar, which makes the learned criterion *stricter* than the hand-built one
rather than looser.

---

## Where the six angles converged

Independently, and this is the strongest signal in the fan-out:

- **`distance-construction`**, **`scientific-reframe`**, **`model-zoo`** and **`bio-data-expansion`**
  all arrived at the same #1 priority by different routes: **the project has never established that
  its pipeline can detect a difference it should detect.** Until it has, D20 is ambiguous between
  "no topological difference exists at this construction" and "the instrument is broken", and every
  negative in `dev/agents/experiments.md` is uninterpretable. The three candidate positive controls are
  synthetic manifolds (`model-zoo` Tier 1), Steinmetz active-vs-passive (`bio-data-expansion` #1),
  and the Gardner grid-cell torus (`bio-data-expansion` #3, 320 MB, CC0, known answer β=(1,2,1)).
- **The cheapest extension point is `Activity`, not `ModelConfig`.** `atlas.measure_activity`
  accepts any `Activity`; `controls.py` already proves two unrelated mechanisms can feed it. Most of
  the model zoo, all synthetic generators, and the untrialed bio datasets reach the atlas through
  that one door without touching `models/`, `training.py`, `search.py` or `objective.py`.
- **n is the binding constraint, and it is a data-loading problem, not a compute one.** 22 bio
  sessions, Allen = **1**. Under any framing where Allen-vs-2AFC separability is the acceptance
  test, that is a 1-sample test forever. Arbitrarily large model-side data cannot substitute.

## Where they disagreed, and how it was resolved

- **AUC ≈ 0.5 vs AUC ≈ 0.77** — resolved by computing it (§1 above). `distance-construction` was
  right; `scientific-reframe` reasoned from prose.
- **Scale up IBL to 459 sessions?** `data-platform` wants more samples; `bio-data-expansion` ranks
  it **last** and makes the better argument: pairs go 231 → 105,111 (**455×**, ~91 h per baseline)
  for 459 more samples of the *same paradigm*, which is not what a yardstick short of contrast
  classes needs. 60–80 sessions is the sensible version. Contrast classes beat sample count here.
- **GPU/CPU overlap as the throughput lever** — `model-zoo` proposed it; `data-platform` measured
  it down to ~10% at the default `n_updates=3000` and proposed 4–8 concurrent training processes
  on the 16 GB card instead. The measured objection wins. Related: **the bottleneck is CPU ripser,
  not the GPU**, which contradicts D9's premise.

---

## Costs and traps that showed up across angles

- **All-pairs comparison is infeasible above N ≈ 10³.** Measured: 2.44 s per pair per condition.
  All-pairs at 10⁴ entries = ~2,120 wall-hours on 16 cores. A **pair policy** (compare against a
  fixed reference panel, not all-pairs) is mandatory before any mass sweep, not an optimization.
  "What is the panel?" is the biggest unanswered design question in this brainstorm.
- **`_CACHE_SIZE = 32` is now undersized.** 20 references × 3 conditions = 60, so it thrashes on
  every comparison since D20 widened the reference set 3 → 20. That widening also silently took
  per-entry topology from ~43 s to ~200+ s. Every dataset multiplier compounds it.
- **Never overwrite a measured number.** `stats.py:209-212` overwrites `distance` in place when
  residualization is on, and nothing in the schema records which construction produced a row. Store
  raw + correction + construction id, and a candidate normalization becomes a SQL view instead of a
  full re-run — turning D20 candidates #12–40 from hours into seconds.
- **`h` is pair-dependent and unrecorded.** `compare()` uses `h = min(n_a,n_b)//2`;
  `split_half_null` uses a different `h`; `DistanceResult` stores neither. `stats.py`'s own
  docstring argues trial count *systematically shifts* H0 bars — which is why it equalizes `h`
  within a pair — but across pairs `h` varies freely and nobody can check the heterogeneity.
- **12.7 GB of merged worktrees**, and 12.4 GB of that is bio data re-downloaded because
  `config.py:5` makes `DATA_DIR` package-relative. Every future agent worktree pays it again.
- **Zero `kind:"control"` records exist in any run directory**, yet `dev/agents/spec.md` and the poster
  both cite the D19 controls as corroborating D20. `dev/agents/experiments.md:307` says why — the numbers
  are logged but "no local raw data for that run". The evidence is not fabricated, it is
  **unreproducible**, and re-running it is cheap.
- **`forkserver` is hardcoded with no fallback** (`stats.py:150`), so in a sandboxed environment no
  topology can be computed at all. The `test_bio_entry_siblings_cross_compare` failure the journal
  records as "pre-existing" is confirmed sandbox-only — it passes in 7.5 s outside one.
- **E4's own candidate (c) — the power analysis at `n_resamples=50` — was never run.** D22–D27
  covered only candidates (a) and (b). The journal's "no lever is currently flagged as untested" is
  inaccurate.

---

## What is already in flight

Four codex stations, one worktree branch each, launched from this brainstorm:

| branch | scope |
|---|---|
| `refactor-cleanup` | Track A: `SNNTOPO_DATA_DIR`, dead code, de-dup refs loading, controls in reports, doc drift |
| `refactor-provenance` | Track B: serial pool fallback, missing `--residualize-raw-diameter` flag, stop overwriting `distance`, fit constants out of source |
| `feat-synthetic-controls` | `generators.py` + the circle-vs-figure-8 diagnostic at project defaults |
| `feat-steinmetz-passive` | `spks_passive` loader + all 13 cached sessions + region sub-sessions |

## Biggest open questions

1. **What is the reference panel?** Pair policy determines whether 10⁴ entries costs 9 hours or
   2,120. No angle could answer it alone.
2. **Should H1 remain in the acceptance criterion at all**, given §2? Dropping it must be
   preregistered with its rationale, not quietly done.
3. **Does E4 fail for power reasons?** Candidate (c) was never run, and the synthetic station's
   circle-vs-figure-8 result speaks directly to it.
4. **Does the project still want a search?** Several angles suggest the deliverable is becoming a
   characterized atlas plus a validated instrument, with search downstream of both.
