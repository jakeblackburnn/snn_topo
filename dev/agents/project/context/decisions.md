# snn_topo v2 — decisions

## D1 · 2026-09-19 · Atlas + paired comparison, not a pure hypothesis test or pure survey
**Decision:** The deliverable is a topology atlas (characteristic signature per bio
dataset, per SNN model×task) with paired bio-vs-SNN distance comparisons as one
section where a matched pair exists, plus a well-formed, reusable codebase for
future experiments.
**Why:** A pure hypothesis-test scope would force every task to have a bio pair,
losing the value of generic SNN-only tasks (checking signature stability across
tasks). A pure-survey scope would drop the original cross-domain question the
prototype was built to answer. The atlas framing keeps both.
**Rejected:** hypothesis-test-only (loses generic tasks); survey-only (loses the
cross-domain comparison that motivated the project).
**Revisit if:** the atlas format turns out to add overhead without anyone
actually querying across runs — in that case collapse back to per-task reports.

## D2 · 2026-09-19 · Bio datasets: Steinmetz (existing) + IBL + Allen Visual Coding
**Decision:** Add IBL brain-wide map (same 2AFC task family as Steinmetz, many
more sessions) and Allen Visual Coding (passive-viewing, no choice/reward) as the
two new bio datasets. IBL auth (ONE API) is set up now, not deferred.
**Why:** IBL gives statistical power within the same task type Steinmetz already
established works well for this pipeline. Allen tests whether the topology
signature tracks decision structure specifically, by providing a same-species,
same-recording-technology dataset with no decision/reward structure at all.
**Rejected:** motor/reaching dataset (e.g. Churchland/Shenoy) — real task-type
diversity value, but more integration work than this build should take on at
once; CRCNS pvc-* — registration/DUA friction, redundant with Allen's role.
**Revisit if:** the H0/H1 pattern needs a motor-task data point to disambiguate
(e.g. if Allen's passive-viewing result is ambiguous about whether decision
structure matters).

## D3 · 2026-09-19 · SNN model suite is searched, not preset, across 4 axes
**Decision:** SNN models vary across architecture family (feedforward / recurrent
/ modular multi-population), neuron model (LIF / adaptive-LIF / Izhikevich-style),
connectivity structure (random / small-world / scale-free / modular-with-hub),
and scale — explored via multi-objective search (accuracy vs. bio-topology-
distance) rather than a fixed grid.
**Why:** The prototype's three experiments each changed one architectural
property and found the H0 gap only widened — the honest conclusion is that a
hand-picked sequence of configs isn't finding whatever configuration (if any)
narrows the gap. A search treats "find a performant, bio-like SNN" as the actual
objective instead of guessing configs one at a time. The modular/multi-population
architecture family exists specifically to test the prototype's leading
hypothesis (single homogeneous population vs. bio's multi-region circuit).
**Rejected:** fixed factorial grid analyzed post-hoc — simpler infra, but doesn't
target the actual question ("can we find a config that's both good and bio-like")
as directly, and the config space (4 axes) is large enough that a full grid is
wasteful compared to a search that spends budget where it's informative.
**Revisit if:** search infra (Optuna/NSGA-II) proves to be more build overhead
than the payoff justifies — fall back to a curated grid per axis.

## D4 · 2026-09-19 · Generic (unmatched) tasks are single-objective (accuracy only)
**Decision:** Tasks with no matched bio dataset (e.g. N-back, delayed
match-to-sample) run accuracy-only search. Topology is still computed and
recorded against the nearest bio signature for atlas purposes, but doesn't drive
the search objective.
**Why:** There's no principled "correct" bio target for a task with no bio
counterpart — using "nearest signature, any dataset" as a search objective would
optimize toward an arbitrary target dressed up as a real comparison.
**Rejected:** searching against nearest-any-dataset bio signature as a second
objective — rejected for the reason above.
**Revisit if:** a fourth bio dataset with a naturally-matching generic task
appears (e.g. a working-memory bio dataset paired with delayed match-to-sample).

## D5 · 2026-09-19 · Compute budget: wall-clock cap per task, short individual runs
**Decision:** Multi-objective search runs under a wall-clock budget per task (one
shared 16GB GPU); individual training runs should target under 30 minutes each
rather than a few long expensive ones.
**Why:** Predictable total runtime on shared hardware; short runs let the search
sample more configs per unit time, which matters more than any single run being
maximally converged given this is an exploratory search over a 4-axis space.
**Rejected:** trial-count cap (unpredictable total runtime if expensive configs
get sampled); no fixed cap (fine for an interactive session, not for a build
spec that needs to be handed to a build team).
**Revisit if:** early search runs show 30 minutes is too short to get a
meaningful accuracy signal for larger-scale/modular configs.

## D6 · 2026-09-19 · Add H2 + bottleneck distance alongside H0/H1 + Wasserstein
**Decision:** Topology module computes H0, H1, *and* H2 persistence, and both
Wasserstein and bottleneck distance (prototype had H0/H1 + Wasserstein only).
**Why:** User's explicit call — the bigger project should capture a more complete
topological picture; the point-cloud scale (100-150 points) that made the
prototype's Rips computation cheap still holds, so the added compute is
affordable.
**Rejected:** keeping method unchanged — considered (avoids changing two things
at once — method and scale), but user opted to extend the method now given the
project's overall scope is already expanding.
**Revisit if:** H2 turns out uninformative (e.g. near-zero/noise across every
run) or bottleneck distance never disagrees meaningfully with Wasserstein —
drop the redundant one later rather than carrying dead weight.

## D7 · 2026-09-19 · Add permutation/bootstrap significance testing
**Decision:** Every reported bio-vs-SNN and null-baseline distance gets a
permutation or bootstrap p-value/CI.
**Why:** Flagged as a limitation in all three prototype reports; the search
producing many runs per task (rather than one-off comparisons) makes proper null
distributions cheap to build where the prototype's single-run design couldn't.
**Rejected:** keeping eyeballed noise-floor ratios — was viable for a same-day
prototype, not for a package meant to support ongoing conclusions.
**Revisit if:** never — this is a strict improvement given the atlas's scale.

## D8 · 2026-09-19 · Atlas delivered as structured data + static reports, no dashboard
**Decision:** Atlas is CSV/parquet/JSON per run (matching the prototype's
`comparison_table.csv` pattern) plus generated markdown/figure reports. No
interactive dashboard in this build.
**Why:** Matches existing, working pattern; avoids building and maintaining
extra infra (e.g. Streamlit) for a project already expanding on several other
axes at once.
**Rejected:** interactive dashboard — more useful for ad hoc exploration, but
explicitly deferred given the scope already includes a search harness, 3 bio
datasets, and 4 model axes.
**Revisit if:** the number of atlas entries grows large enough that static
reports stop being a usable way to explore results.

## D9 · 2026-09-19 · Multi-agent nodeterm team builds the codebase only
**Decision:** The opusplan-orchestrated multi-agent team (Codex delegate +
spawned Claude agents) is scoped to building the framework. The actual
post-build search experiments run afterward as normal sequential jobs on the one
shared GPU — no agent-team concurrency/scheduling story is needed.
**Why:** Avoids designing GPU-contention handling into the agent team's
coordination pattern for a problem (concurrent training jobs) that doesn't need
to exist if experiments run sequentially after the build is done.
**Rejected:** build-and-orchestrate-experiments — would require real
GPU-scheduling coordination between agents, unnecessary complexity for a single
shared card.
**Revisit if:** experiment turnaround time becomes a bottleneck and concurrent
(carefully GPU-budgeted) runs become worth the coordination cost.

## D10 · 2026-09-19 · Build team: hierarchical, interfaces-first, worktree-per-agent
**Decision:** Opusplan orchestrator defines shared interfaces first (registries
for bio datasets / model families / tasks), then fans out to parallel workers per
workstream (bio loaders, model registry, task suite, topology+stats module,
search harness, package/tests), each in its own worktree, with an orchestrator
review/merge gate before integration. Codex takes mechanical/boilerplate
workstreams (data-loader plumbing, CSV/report utilities, test scaffolding);
spawned Claude agents take design-sensitive workstreams (model registry across 4
axes, search harness, topology/stats extension). Full detail in `agent-team.md`.
**Why:** User confirmed as proposed. Defining interfaces before fanning out
avoids integration conflicts between parallel agents; worktree-per-agent keeps
their changes isolated until the review gate.
**Rejected:** fewer/broader workstreams (less parallelism, less coordination
overhead) — user picked the finer-grained split.
**Revisit if:** the review/merge gate becomes a bottleneck — collapse
workstreams or loosen the gate.
