# Pair and reference-panel policy

> Brainstorm notes, 2026-09-27. Nothing here is a decision. Options with a recommendation.
> Seed: `../mega-forward-plan/data-platform.md` "The wall" (the all-pairs cost table, still
> right) and `model-zoo.md` "Costs and gotchas" (the reference-set scaling). Not restated here.

## Where a comparison's cost actually goes (read from the code)

`compare(a, b, ...)` (`snntopo/topology/stats.py:215`) has two parts:

1. **Halves.** For each source × condition it draws `n_resamples` split-half pairs at
   `h = min(n_a, n_b) // 2` (`:222`) and runs 2 ripser calls per pair in the process pool
   (`:171`). They're cached in-process by (content, mask, h, topo, seed) (`:148`). Cost: about 4 s
   per (activity, condition, h) on the pool (the `stats.py` docstring gives about 13 s for 3
   conditions).
2. **Cross distances.** `n_resamples × 2 × (maxdim+1)` gudhi calls per condition, i.e. 200 at
   defaults, **run serially in the calling process** (`:229-233`), not in the pool. mega measured
   0.81 s per condition. That's the "2.44 s per pair" for 3 conditions.

Three consequences mega didn't draw out:
- **`h` breaks reuse.** A reference's halves can only be reused against partners with the same
  `min(n_a, n_b)`. Every new partner with fewer trials re-splits the reference. A fixed per-panel
  `h` makes reference halves computable once and persistable (`orchestration.md`, `store/halves`).
- **Seeds multiply halves, not just cross work.** E15's 5 compare seeds re-split every activity
  5 times, because the seed is in the cache key.
- **Cross work is single-core.** While one process computes cross distances, its 16-worker pool
  sits idle. Two number-preserving fixes: move `diagram_distance` for the cross pairs into the
  pool, or run several comparisons in parallel processes with a capped pool each. Both
  multiply panel throughput by several times without touching any number. The 1-D H0 DP (mega,
  5-10×) is a third option, later.

With halves persisted at a fixed `h`, the marginal cost of one more pair is about 0.8 s per
condition, and parallelizable.

## Policies

| policy | pairs for N activities | 10⁴ activities, 1 condition, 16 cores | what it answers |
|---|---|---|---|
| P0 all-pairs | N²/2 | ~2,120 wall-h (mega, 3 conditions) | everything; infeasible past ~10³ |
| **P1 none by default** | 0 | 0 (signatures and self-nulls only: ~4 s × N) | per-activity TDA: the bulk of "a huge set of topological data" |
| **P2 frozen bio panel, opt-in** | N × R | R=13: ~2.9 CPU-h ≈ 0.2 wall-h if parallelized (0.8 s × 13 × 10⁴ = 1.0e5 s) | distance from each SNN to a fixed set of brain signatures |
| P3 anchor panel (bio + synthetic shapes) | N × (R + S) | S≈5 adds ~40% | as P2, plus "which known shape is it nearest" with a built-in positive control |
| **P4 replicate pairs** | configs × k²/2 | 5 seeds: 10 pairs per config | the within-config spread (model-zoo §4), i.e. the model-side geometry floor |
| **P5 experiment-scoped** | declared by the spec | E15: 13 × 3 contrasts × 5 seeds = 195 compares | preregistered contrasts: the only pairs that carry verdicts |
| P6 vectorized screen | 0 exact pairs | O(N) features, then exact compare on a chosen subset | exploratory maps (embeddings, clustering) |

Cost figures assume halves are cached at a fixed `h` and cross work is parallel. Without either
fix, multiply P2 by about 10.

### Recommendation

**P1 + P5 by default. P2 and P4 opt-in per spec. P6 only for descriptive figures.**
- A sweep spec produces activities and their signatures and self-nulls, and **no pairs** unless
  it names a panel. That keeps dataset growth linear and puts pair cost where someone chose it.
- Experiments (P5) declare their pairs explicitly. That's what E12-E15 already did by hand.
- A panel (P2/P3) is a **frozen, versioned object**: `panel_id` = hash of (member activity_ids,
  condition(s), fixed `h`, topo_id, cmp_id). Changing any of these makes a new panel. Numbers from
  different panels are never pooled, like different `cmp_id`s.
- Panel comparisons are **descriptive until the floor is portable.** Under D28, a panel ratio
  means something only against a synthetic floor at that pair's own `null_mean`. Each pair has a
  different null scale. So panel results can't carry a "bio-like / not bio-like" call until
  `brain-signatures.md`'s calibration grid passes the D28 stress test. Until then they're
  labelled descriptive, and no search objective reads them. This is the D20/E2-E3 lesson, applied
  in advance.

### Panel v1 candidates (options, not a choice)

| panel | members | R | pros | cons |
|---|---|---|---|---|
| A. Steinmetz active, one per subject | 4 sessions (Cori, Forssmann, Hench, Lederberg) | 4 | cheap; one lab, so no cross-lab nuisance | one paradigm |
| B. A + their passive blocks | 8 | 8 | carries the engagement axis E15 established | passive has no choice conditions, so `all` only |
| C. B + 4 IBL + Allen | 13 | 13 | three labs, two paradigms | E4-E11 showed cross-lab nuisance dominates |
| D. all references (13 Steinmetz ×2 + 20 IBL + 1 Allen) | 47 | 47 | no selection judgment | 3.6× C's cost; independence groups heavily unequal |

Recommendation: **B for the first panel**, with `h` fixed at the smallest block it must serve.
It's the population E15 validated, it's within one lab (the nuisance D22-D27 couldn't beat), and
it answers the obvious first dataset question: "is a trained SNN's signature closer to engaged or
to passive cortex?" That question is still descriptive until the floor is portable. The choice of
`h` interacts with power: at `h`=55, E13's null_mean was 0.078 and the matched floor 1.09.
Smaller `h` raises the null and pushes all ratios toward 1.

### Conditions

Panel comparisons on `all` only. `left`/`right` mean choice in active blocks, stimulus side in
passive blocks, and argmax action in SNNs (`evaluate.py`). They aren't the same variable across
panel members (journal trap: passive left/right = stimulus side). That cuts panel cost 3× relative
to mega's 3-condition estimate.

## Open questions

- **Fixed `h` for panels.** Which value? It trades power (bigger `h`) against which activities can
  join (each needs ≥ 2h trials in the condition). SNNs evaluate 340 trials, so the binding
  constraint is the bio side (passive 110, i.e. `h` ≤ 55).
- Does `compare` gain an explicit `h` argument (additive, default = today's `min // 2`)? A panel
  needs it. The golden tests pin the default path.
- Should P4 replicate pairs be default-on for any config swept at ≥2 seeds? They're cheap and they
  are the model-side floor. The case against is that they grow with seeds² and nobody may read them.
- P6's vectorization (persistence images, Betti curves, summary vectors): which, if any, belongs in
  the signature record so it's computed once? This is a descriptor choice, so it's
  `brain-signatures.md`/`snn-breadth.md`'s call, not a pair-policy one.
