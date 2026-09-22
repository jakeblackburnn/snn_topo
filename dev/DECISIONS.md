# Decisions

D1-D10 were taken while building the context packet and are copied from
`dev/context/decisions.md` (left untouched as the frozen input to the build). D11-D16
were taken during the build itself.

## D1 · 2026-09-19 · Atlas + paired comparison, not a pure hypothesis test or pure survey
**Decision:** The deliverable is a topology atlas (characteristic signature per bio
dataset, per SNN model×task) with paired bio-vs-SNN distance comparisons as one section
where a matched pair exists, plus a well-formed, reusable codebase for future experiments.
**Why:** A pure hypothesis-test scope would force every task to have a bio pair, losing the
value of generic SNN-only tasks (checking signature stability across tasks). A pure-survey
scope would drop the original cross-domain question the prototype was built to answer. The
atlas framing keeps both.
**Rejected:** hypothesis-test-only (loses generic tasks); survey-only (loses the
cross-domain comparison that motivated the project).
**Revisit if:** the atlas format turns out to add overhead without anyone actually querying
across runs — in that case collapse back to per-task reports.

## D2 · 2026-09-19 · Bio datasets: Steinmetz (existing) + IBL + Allen Visual Coding
**Decision:** Add IBL brain-wide map (same 2AFC task family as Steinmetz, many more
sessions) and Allen Visual Coding (passive-viewing, no choice/reward) as the two new bio
datasets. IBL auth (ONE API) is set up now, not deferred.
**Why:** IBL gives statistical power within the same task type Steinmetz already
established works well for this pipeline. Allen tests whether the topology signature tracks
decision structure specifically, by providing a same-species, same-recording-technology
dataset with no decision/reward structure at all.
**Rejected:** motor/reaching dataset (e.g. Churchland/Shenoy) — real task-type diversity
value, but more integration work than this build should take on at once; CRCNS pvc-* —
registration/DUA friction, redundant with Allen's role.
**Revisit if:** the H0/H1 pattern needs a motor-task data point to disambiguate (e.g. if
Allen's passive-viewing result is ambiguous about whether decision structure matters).

## D3 · 2026-09-19 · SNN model suite is searched, not preset, across 4 axes
**Decision:** SNN models vary across architecture family (feedforward / recurrent / modular
multi-population), neuron model (LIF / adaptive-LIF / Izhikevich-style), connectivity
structure (random / small-world / scale-free / modular-with-hub), and scale — explored via
multi-objective search (accuracy vs. bio-topology-distance) rather than a fixed grid.
**Why:** The prototype's three experiments each changed one architectural property and found
the H0 gap only widened — the honest conclusion is that a hand-picked sequence of configs
isn't finding whatever configuration (if any) narrows the gap. A search treats "find a
performant, bio-like SNN" as the actual objective instead of guessing configs one at a
time. The modular/multi-population architecture family exists specifically to test the
prototype's leading hypothesis (single homogeneous population vs. bio's multi-region
circuit).
**Rejected:** fixed factorial grid analyzed post-hoc — simpler infra, but doesn't target the
actual question ("can we find a config that's both good and bio-like") as directly, and the
config space (4 axes) is large enough that a full grid is wasteful compared to a search
that spends budget where it's informative.
**Revisit if:** search infra (Optuna/NSGA-II) proves to be more build overhead than the
payoff justifies — fall back to a curated grid per axis.

## D4 · 2026-09-19 · Generic (unmatched) tasks are single-objective (accuracy only)
**Decision:** Tasks with no matched bio dataset (e.g. N-back, delayed match-to-sample) run
accuracy-only search. Topology is still computed and recorded against the nearest bio
signature for atlas purposes, but doesn't drive the search objective.
**Why:** There's no principled "correct" bio target for a task with no bio counterpart —
using "nearest signature, any dataset" as a search objective would optimize toward an
arbitrary target dressed up as a real comparison.
**Rejected:** searching against nearest-any-dataset bio signature as a second objective —
rejected for the reason above.
**Revisit if:** a fourth bio dataset with a naturally-matching generic task appears (e.g. a
working-memory bio dataset paired with delayed match-to-sample).

## D5 · 2026-09-19 · Compute budget: wall-clock cap per task, short individual runs
**Decision:** Multi-objective search runs under a wall-clock budget per task (one shared
16GB GPU); individual training runs should target under 30 minutes each rather than a few
long expensive ones.
**Why:** Predictable total runtime on shared hardware; short runs let the search sample more
configs per unit time, which matters more than any single run being maximally converged
given this is an exploratory search over a 4-axis space.
**Rejected:** trial-count cap (unpredictable total runtime if expensive configs get
sampled); no fixed cap (fine for an interactive session, not for a build spec that needs to
be handed to a build team).
**Revisit if:** early search runs show 30 minutes is too short to get a meaningful accuracy
signal for larger-scale/modular configs.

## D6 · 2026-09-19 · Add H2 + bottleneck distance alongside H0/H1 + Wasserstein
**Decision:** Topology module computes H0, H1, *and* H2 persistence, and both Wasserstein
and bottleneck distance (prototype had H0/H1 + Wasserstein only).
**Why:** User's explicit call — the bigger project should capture a more complete
topological picture; the point-cloud scale (100-150 points) that made the prototype's Rips
computation cheap still holds, so the added compute is affordable.
**Rejected:** keeping method unchanged — considered (avoids changing two things at once —
method and scale), but user opted to extend the method now given the project's overall
scope is already expanding.
**Revisit if:** H2 turns out uninformative (e.g. near-zero/noise across every run) or
bottleneck distance never disagrees meaningfully with Wasserstein — drop the redundant one
later rather than carrying dead weight. **Status 2026-09-19:** H2 is empty for every bio
condition at `n_pca=10`; this is the first evidence toward that revisit. **Status
2026-09-20 (supersedes above):** the n_pca=10 emptiness was an artifact, not a property of
H2 itself — swept n_pca ∈ {10,20,30,50} on Steinmetz 11 + the 3 IBL sessions; at n_pca≥20,
5 of 12 session×condition cells go nonzero (1-3 features), matching SNN-scale sparsity, not
zero. **H2 stays; revisit not triggered.** The bottleneck half of the revisit condition is
trending the other way: H1 bottleneck detects only 2% of pairs at an effect size (ratio
2.31) where H1 wasserstein detects 96% (ratio 2.58) — consistent with a fat-tailed
max-statistic null rather than an n_resamples power problem. Worth a bottleneck-specific
revisit, separate from H2.

## D7 · 2026-09-19 · Add permutation/bootstrap significance testing
**Decision:** Every reported bio-vs-SNN and null-baseline distance gets a permutation or
bootstrap p-value/CI.
**Why:** Flagged as a limitation in all three prototype reports; the search producing many
runs per task (rather than one-off comparisons) makes proper null distributions cheap to
build where the prototype's single-run design couldn't.
**Rejected:** keeping eyeballed noise-floor ratios — was viable for a same-day prototype,
not for a package meant to support ongoing conclusions.
**Revisit if:** never — this is a strict improvement given the atlas's scale.

## D8 · 2026-09-19 · Atlas delivered as structured data + static reports, no dashboard
**Decision:** Atlas is CSV/parquet/JSON per run (matching the prototype's
`comparison_table.csv` pattern) plus generated markdown/figure reports. No interactive
dashboard in this build.
**Why:** Matches existing, working pattern; avoids building and maintaining extra infra
(e.g. Streamlit) for a project already expanding on several other axes at once.
**Rejected:** interactive dashboard — more useful for ad hoc exploration, but explicitly
deferred given the scope already includes a search harness, 3 bio datasets, and 4 model
axes.
**Revisit if:** the number of atlas entries grows large enough that static reports stop
being a usable way to explore results.

## D9 · 2026-09-19 · Multi-agent nodeterm team builds the codebase only
**Decision:** The opusplan-orchestrated multi-agent team (Codex delegate + spawned Claude
agents) is scoped to building the framework. The actual post-build search experiments run
afterward as normal sequential jobs on the one shared GPU — no agent-team
concurrency/scheduling story is needed.
**Why:** Avoids designing GPU-contention handling into the agent team's coordination
pattern for a problem (concurrent training jobs) that doesn't need to exist if experiments
run sequentially after the build is done.
**Rejected:** build-and-orchestrate-experiments — would require real GPU-scheduling
coordination between agents, unnecessary complexity for a single shared card.
**Revisit if:** experiment turnaround time becomes a bottleneck and concurrent (carefully
GPU-budgeted) runs become worth the coordination cost.

## D10 · 2026-09-19 · Build team: hierarchical, interfaces-first, worktree-per-agent
**Decision:** Opusplan orchestrator defines shared interfaces first (registries for bio
datasets / model families / tasks), then fans out to parallel workers per workstream (bio
loaders, model registry, task suite, topology+stats module, search harness, package/tests),
each in its own worktree, with an orchestrator review/merge gate before integration. Codex
takes mechanical/boilerplate workstreams; spawned Claude agents take design-sensitive ones.
Full detail in `dev/context/agent-team.md`.
**Why:** User confirmed as proposed. Defining interfaces before fanning out avoids
integration conflicts between parallel agents; worktree-per-agent keeps their changes
isolated until the review gate.
**Rejected:** fewer/broader workstreams (less parallelism, less coordination overhead) —
user picked the finer-grained split.
**Revisit if:** the review/merge gate becomes a bottleneck — collapse workstreams or loosen
the gate.

## D11 · 2026-09-19 · Point clouds are diameter-normalized before Rips
**Decision:** Each condition's PCA trajectory point cloud is rescaled to unit diameter
before persistence is computed. The raw diameter is recorded per atlas entry as its own
statistic.
**Why:** Bio spike counts per 10 ms bin and SNN 0/1 spikes per step live on different
scales, so the prototype's H0 gap partly measured firing-rate magnitude rather than
trajectory shape. Normalizing makes the diagrams comparable as shape; keeping raw diameter
means no information is lost, and a scale difference remains visible as a number instead of
contaminating every distance.
**Rejected:** comparing raw diagrams (what the prototype did — conflates scale and shape);
normalizing by a fixed global constant (arbitrary, and still scale-sensitive across
datasets).
**Revisit if:** two configurations with genuinely different dynamics normalize onto the
same signature — then scale carries real signal and belongs back in the distance.

## D12 · 2026-09-19 · Allen Visual Coding is bio-only
**Decision:** Allen contributes an atlas signature and serves as a nearest-signature
candidate for generic tasks. It gets no matched SNN task and no search objective.
**Why:** Allen is passive viewing with no choice or reward, so there is no action-condition
structure to match an SNN task against; inventing one would fabricate the pairing that D2
brought Allen in to act as a control for.
**Rejected:** building a matched orientation-discrimination task — would turn the passive
control into just another decision dataset, destroying its role.
**Revisit if:** a decision-making Allen dataset (e.g. Visual Behavior) is added — that one
could carry a matched task while Visual Coding stays the control.

## D13 · 2026-09-19 · Significance null is trial-matched split-half resampling
**Decision:** A cross-source distance is tested against a null built by repeatedly splitting
each source's trials in half and measuring within-source distances, pooled across sources
and matched on trial count. `p = (1 + #{null >= observed}) / (1 + n)`. `TopoConfig.n_resamples`
defaults to 50.
**Why:** The quantity of interest is "are these two populations further apart than the same
population is from itself", and trial count strongly affects diagram distance, so the null
has to hold it fixed. Pooling across both sources avoids privileging either one's internal
variability.
**Rejected:** permuting condition labels (tests a different question — whether conditions
differ — not whether sources do); a fixed analytic noise floor (the prototype's approach,
which all three of its reports flagged as inadequate).
**Revisit if:** power becomes the binding constraint — effects below roughly 2× the null
mean are often missed at 50 resamples, and raising it is a linear cost (~43 s per entry
against 3 references).

## D14 · 2026-09-19 · Every evaluated config becomes an atlas record, including failures
**Decision:** `snn_entry()` always appends a record with a status of `ok`, `degenerate`,
`failed` or `timeout`. Optuna is told the measured values for the first three and FAIL only
where nothing was measured.
**Why:** The atlas is meant to characterise the model space, and "this family collapses to a
one-action policy" is a finding about that space, not an error to discard. Degenerate runs
carry an honest near-chance accuracy, which keeps them off the useful end of the Pareto
front without inventing a penalty term.
**Rejected:** recording only successful trials (silently biases the atlas); penalty values
for failures (feeds the sampler a number nobody measured).
**Revisit if:** never expected to — but if failure records ever dominate the atlas by
volume, split them into their own table rather than dropping them.

## D15 · 2026-09-19 · Model validity lives in the registry; the search samples within it
**Decision:** `models.validate()` / `models.valid_triples()` are the single definition of
what is buildable. `search.sample_model()` samples the family as one categorical over
`valid_triples()` and bounds `n_layers` / `n_modules` by `n_hidden // MIN_POPULATION`.
**Why:** The search harness originally duplicated the validity rule, and its independent
ranges (`n_hidden` 64-1024 against `n_modules` 2-8) proposed configs the registry rejects.
A rejected config becomes a FAIL trial that teaches the sampler nothing and spends budget.
Sampling the family as a single always-present categorical also lets NSGA-II and TPE model
it, where conditional parameters would fall back to random sampling.
**Rejected:** clamping an out-of-range draw after sampling (many trials collapse onto the
same config and the sampler cannot tell); letting invalid configs fail as trials (wastes the
budget the wall-clock cap is there to protect).
**Revisit if:** a future axis makes validity depend on something the sampler cannot see
before building — then validity has to move into a pre-build filter instead.

## D16 · 2026-09-19 · Surrogate gradient dampened ×0.3 and readout zero-initialised
**Decision:** The ATan surrogate gradient is scaled by 0.3 (Bellec et al. 2018 dampening),
and output-layer weights start at zero.
**Why:** Undamped, gradients through 150 steps of recurrence at spectral radius 1 reach
norms around 1e12 against 1e3 at the readout, so a global-norm clip leaves the readout with
no effective step — 14 of 18 recurrent/modular mini-runs sat at chance undamped against 7
of 18 damped. With a random readout init, output spike counts differ by tens of spikes per
trial, making the softmax over counts near-deterministic and vanishing REINFORCE's log-prob
gradient before it can explore: 6 of 9 recurrent runs stuck at chance against 0 of 9 with a
zero init.
**Rejected:** per-layer gradient clipping (more machinery, treats the symptom); a smaller
spectral radius (would silently exclude the critical regime the search is meant to explore).
**Revisit if:** a neuron model is added whose gradient scale differs enough that one global
dampening factor no longer serves — then it becomes a per-neuron constant.

## D17 · 2026-09-20 · Amend D3: drop accuracy as a second search objective on matched tasks
**Decision:** Matched tasks (steinmetz_2afc, ibl_2afc) search single-objective (minimize
bio-topology-distance) with an accuracy-floor feasibility constraint (~0.7), not
multi-objective NSGA-II over (accuracy, distance).
**Why:** E1 (4h steinmetz_2afc search, 192 trials) found accuracy saturated — median 1.000,
min 0.956 — so the Pareto front was a single point and NSGA-II was effectively
single-objective the entire run; the second axis bought nothing. D14's rationale that
degenerate trials self-exclude via near-chance accuracy is preserved by the floor
constraint, not lost.
**Rejected:** keeping two objectives with a non-saturating second axis (e.g. `|accuracy-1|`)
— the same saturated quantity in different clothing, doesn't fix the underlying problem.
**Revisit if:** a task's accuracy stops saturating (e.g. nback once it trains above chance)
— then a real two-objective front may exist and multi-objective search is worth it again.

## D18 · 2026-09-20 · Report the bio-vs-bio distance distribution alongside SNN-vs-bio
**Decision:** Add each run's bio-vs-bio pairwise distances (where ≥2 bio references exist)
as a reported baseline next to SNN-vs-bio distances. D13's split-half significance test
stays as the "is this measured, not noise" check; it is not sufficient alone to claim an SNN
is *meaningfully* distinguishable from bio.
**Why:** E1 offline re-analysis (2026-09-20): pairwise `compare()` across the 3 cached IBL
reference sessions, same `TopoConfig` defaults as E1, gave H0 wasserstein ratio 4.3-4.7×
(6/6 pairs p<0.05) and H1 ratio ~2.5× (3/6 p<0.05) — as large as or larger than E1's median
SNN-vs-bio ratios (H0 4.59, H1 2.58), and E1's best config (t0153) sat *inside* the
bio-vs-bio range on both. The p<0.05 test alone can't separate "different animal" from
"different model class"; E1's "0/191 entries free of significant tests" measured mostly
normal between-animal variability, not an SNN-specific gap.
**Rejected:** replacing D13's null design — the split-half mechanics are fine and stay;
this only adds a second reported baseline for interpreting the distance, not a new test.
**Revisit if:** more bio reference sessions become available per dataset and the bio-vs-bio
distribution needs recomputing; or if bio-vs-bio distance turns out unstable enough (e.g.
new sessions land far outside the 3-session range) that it's not a reliable yardstick.
**Revisited 2026-09-22:** triggered — see D20.

## D19 · 2026-09-22 · Controls (untrained SNN, shuffled bio) are first-class atlas records
**Decision:** Add `snntopo/controls.py` (`untrained`, `shuffled`) and `atlas.control_entry()`,
using the same `measure_activity()` tail `snn_entry` uses, so a control's distances/objective
are computed identically to a real trial and land in the same `atlas.jsonl`/`entries.csv` with
`kind="control"`. `rescore()` still filters to `kind == "snn"` — controls are diagnostic floors,
not search trials, and don't get re-optimized.
**Why:** no experiment run so far (E1-E3) had measured a floor. E2/E3's headline claim — SNN
configs land inside the bio-vs-bio range — has no meaning without knowing whether *nothing*
(an untrained network, or bio with its own cross-neuron structure destroyed) also lands there.
It does (E4): untrained objective_distance 9.5-14.4 and shuffled-bio 5.3-10.8 both fall inside
E3's trained-SNN range (6.45-9.53 by arch median).
**Rejected:** computing controls ad hoc per analysis script instead of as atlas records — would
have made every future run redo this by hand instead of `snntopo control --kind ...` once.
**Revisit if:** the measurement is fixed per D20's Next steps and controls need re-running to
confirm the floor moves with it.

## D20 · 2026-09-22 · The bio-vs-bio range is not currently a valid yardstick (D18, revisited)
**Decision:** Do not treat "an SNN config's distance falls inside the bio-vs-bio range" as
supporting evidence until the measurement passes a discriminative-validity check. E2/E3's
"supported" conclusions stand as historical record but are **not** confirmation the SNN family
can produce bio-like topology — they're pending re-derivation.
**Why:** E4, preregistered before running: Allen Visual Coding (passive viewing, no
choice/reward, deliberately a different paradigm from 2AFC) was compared against Steinmetz/IBL
for the first time this session. Both Allen-vs-Steinmetz (H0 7.983, H1 2.052) and Allen-vs-IBL
(H0 mean 8.394, H1 mean 2.143) land entirely inside the within-IBL bio-vs-bio range (H0
0.851-15.402, H1 0.941-14.313, n=20 sessions) despite being individually significant against the
split-half null. Widening the IBL reference set 3->20 widened this range, not tightened it. D19's
controls corroborate: untrained and shuffled-bio both land in the same range trained SNNs do.
Three independent checks (Allen, untrained, shuffled) all say the same thing: this range doesn't
separate bio-like from not-bio-like at the current `n_pca`/metric/sample size.
**Rejected:** discarding the atlas/search infrastructure — the pipeline (contracts, registries,
significance testing, search harness) is sound; the specific distance range built on top of it
isn't validated yet. Also rejected: quietly re-deriving `structure_weight` or re-running the
search at higher budget before fixing this — either would produce a result this same gap makes
uninterpretable.
**Revisit if:** a candidate fix (tighter session matching, a less nuisance-dominated
metric/normalization, a power analysis at the current `n_resamples`) passes the same Allen
contrast E4 used, i.e. Allen lands **outside** the bio-vs-bio range on both H0 and H1.

## D21 · 2026-09-22 · Default `maxdim=1`, wasserstein-only metrics
**Decision:** `TopoConfig.maxdim` default 2 -> 1; new `TopoConfig.metrics` field defaults to
`("wasserstein",)`. Both remain overridable (`--maxdim 2`, `--metrics wasserstein bottleneck`).
**Why:** H2 is empty (`_H2_n == 0`) at every bio reference session measured at `n_pca=10` —
Steinmetz session 11 and all IBL references — so computing it (the most expensive dim, run on
every split-half resample) buys nothing for the bio comparison it exists to support. Bottleneck
distance was computed for every dim/resample but `objective.py`'s `METRIC` has only ever read
wasserstein, and bottleneck is underpowered where measured (E1: H1 bottleneck 2.31 ratio / 2%
significant vs. H1 wasserstein 2.58 / 96%). Measured effect: topology-only cost ~4-5x faster,
per-trial wall clock ~2.4-3x faster.
**Rejected:** deleting H2/bottleneck support entirely — D6's 2026-09-20 status found H2 goes
nonzero at `n_pca>=20` on some cells, so it's a default change for the package's `n_pca=10`
default, not a claim H2 is worthless in general.
**Revisit if:** a run at `n_pca>=20` (or a different bio dataset) shows H2 reliably nonzero and
informative enough to justify its cost as the default rather than an opt-in.
