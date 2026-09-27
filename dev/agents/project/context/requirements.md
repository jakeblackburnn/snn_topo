# snn_topo v2 — requirements

**Intent**: The 2026-09-11/12 prototype (now archived at `prototype/`) built a one-shot
pipeline comparing the topological signature (persistent homology of population
trajectories) of one bio dataset (Steinmetz mouse 2AFC) against one SNN architecture
on one matched task, and found a large, direction-inconsistent gap (H0 got *worse*
as the SNN got more bio-like in scale/recurrence/criticality; H1 stayed flat
throughout). The leading unverified hypothesis from that work: the gap reflects a
single homogeneous neuron population vs. bio's real multi-region circuit, not a
tunable hyperparameter.

v2 turns this into a proper, extensible research package: a **topology atlas** —
characteristic topological signatures computed across multiple bio datasets and
across a broad, searched space of SNN models × tasks — with paired bio-vs-SNN
distance comparisons (now with significance testing) wherever a matched pair exists.
The SNN side is explored via a multi-objective search (task accuracy vs.
bio-topology-distance) rather than a fixed preset grid, so the atlas is populated by
the search's own evaluated population. Goal: find SNN configurations that are both
performant and topologically bio-like, and characterize how/where topology diverges
when they aren't the same configuration.

Built with a multi-agent nodeterm team (opusplan Claude orchestrator + delegated
Codex + spawned Claude agents) for the *build* phase only — see `agent-team.md`.

**Build vs. run, explicitly**: `project-builder-helper` and the build team build
and validate the framework — they do not execute the full multi-objective search
suite across all bio datasets and model axes as part of the build. Validation
during the build is limited to smoke tests (does each registry entry construct
and run one step without error) and small mini-experiments (a handful of search
trials / a few minutes of training, enough to prove the pipeline works
end-to-end) — never the wall-clock-capped full search described below, which is
a separate, later, user-initiated run.

**Done when**
- [ ] `snntopo` is an installable package with a bio-dataset registry (Steinmetz,
      IBL brain-wide map, Allen Visual Coding), an SNN model registry spanning
      architecture family × neuron model × connectivity structure × scale, and a
      task registry (matched 2AFC-family tasks per bio dataset + generic tasks
      with no bio pair, e.g. N-back, delayed match-to-sample)
- [ ] Topology module computes H0/H1/H2 persistence + both Wasserstein and
      bottleneck distance, reusing/extending `prototype/snntopo/topology/`
- [ ] Every bio dataset has a computed characteristic topological signature,
      stored as structured data (atlas entry)
- [ ] Multi-objective search harness (accuracy vs. bio-topology-distance, e.g.
      Optuna/NSGA-II) implemented and proven end-to-end via a mini-run (a handful
      of trials, not the full wall-clock budget) per matched task; every
      evaluated config becomes an atlas entry, not just the Pareto front. The
      full-budget search itself is run later, separately, by the user — not
      during the build.
- [ ] Generic (unmatched) tasks run single-objective (accuracy only); topology is
      still computed and recorded against the nearest bio signature for the atlas,
      but doesn't drive the search — same build-vs-run boundary as above
- [ ] Permutation or bootstrap significance testing backs every reported
      bio-vs-SNN and null-baseline distance (closes the gap flagged in all three
      prototype reports)
- [ ] Atlas is delivered as structured data (CSV/parquet/JSON per run) + generated
      markdown/figure reports, matching the prototype's existing artifact pattern
      — no interactive dashboard in this scope
- [x] IBL brain-wide map ONE API auth set up (2026-09-19, `~/Code/python_venv_01_main`
      — see research.md); build still needs the actual data-loader against it
- [ ] Codebase has tests, docs, and clear extension points (registries) so adding
      a new bio dataset, model family, or task later doesn't require touching
      unrelated code — this is explicitly meant to be maintained and extended,
      not another disposable prototype
- [ ] `dev/` populated (SPEC.md/DECISIONS.md/HANDOFF.md/devlog/experiments.md
      conventions) so future sessions have ground truth without re-deriving it

**Scope**
- In: Steinmetz + IBL + Allen bio datasets; SNN architecture/neuron/connectivity/
  scale search; H0/H1/H2 topology with two distance metrics; permutation
  significance testing; atlas as structured data + static reports; installable
  package with registries and tests.
- Out: interactive dashboard/viewer; **running the full experiment suite** —
  the complete wall-clock-capped multi-objective search across all bio
  datasets/model axes/tasks. The build validates the pipeline with smoke tests
  and small mini-experiments only; the full suite is a separate, later,
  user-initiated run (normal sequential jobs on the one shared GPU, not part of
  the build team's job — see agent-team.md); a 4th bio dataset (motor/reaching)
  — noted as a plausible future extension, not built now.

**Open questions**
- None blocking. Exact search library (Optuna vs. a hand-rolled NSGA-II) and exact
  wall-clock-per-task budget are implementation details left to
  `project-builder-helper` / the build team, not gating this packet.

**Resolved at build kickoff (2026-09-19, project-builder)**
- Point clouds are diameter-normalized before Rips (compare shape, not firing-rate
  scale — bio counts/10ms bin vs SNN 0/1 spikes/step inflated the prototype's H0
  gap). Raw diameter is still recorded per atlas entry.
- Allen Visual Coding is bio-only: atlas signature + a "nearest signature"
  candidate for generic tasks; no matched SNN task, no search objective.
- Build team driven via nodeterm canvas (Codex node + Claude nodes, one worktree each).
