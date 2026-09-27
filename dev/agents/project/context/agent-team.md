# snn_topo v2 — agent team

**Scope of this team: build only.** It scaffolds and implements the framework
(data loaders, model registry, search harness, topology/stats, tests, docs). Once
built, the actual multi-objective search runs (per task, wall-clock-capped) happen
afterward as normal sequential jobs on the one shared 16GB GPU — this team does not
run or schedule those. See decisions.md D9.

**Explicitly in bounds for validation**: smoke tests (each registry entry
constructs and runs one step without error) and small mini-experiments (a
handful of search trials / a few minutes of training, enough to prove the
pipeline works end-to-end). **Explicitly out of bounds**: running the full
experiment suite — the complete wall-clock-capped search across all bio
datasets/model axes/tasks. If a worker finishes a workstream and is tempted to
"just kick off the real run to check it" — that's the line; don't cross it.

## Coordination pattern: hierarchical, interfaces-first, then parallel fan-out

Two phases:

1. **Interface phase (sequential, orchestrator-only).** The opusplan Claude
   orchestrator designs and lands the shared contracts before anyone else starts:
   - Bio-dataset registry interface (what a dataset loader must expose: trial-
     aligned spike arrays, condition splits, metadata — the shape
     `prototype/snntopo/data/steinmetz.py` already establishes for one dataset).
   - SNN model registry interface (how architecture family × neuron model ×
     connectivity structure × scale compose into a buildable model config).
   - Task registry interface (matched vs. generic tasks, what a task must expose
     to both the training loop and the search harness).
   - Atlas record schema (what one row of the atlas contains — model config,
     task, accuracy, topology signature, distance + significance test result
     where applicable).

   This phase exists because every downstream workstream needs to code against
   these shapes; skipping straight to parallel work risks five agents inventing
   five incompatible interfaces.

2. **Parallel fan-out (worktree-per-agent).** Once interfaces are landed, workers
   start in parallel, each in its own git worktree, against the frozen interface
   contracts:

   | Workstream | Owner | Why this split |
   |---|---|---|
   | Bio data loaders (Steinmetz refactor, IBL + ONE API auth, Allen) | Codex | Largely mechanical: each is "fetch, align to schema" against an already-working Steinmetz reference implementation in `prototype/`. |
   | CSV/report/logging utilities | Codex | Direct generalization of `prototype/snntopo/io_utils.py` / `logging_utils.py` — established pattern, low design risk. |
   | Test scaffolding + package infra (installable package, CI-ish checks) | Codex | Mechanical once interfaces exist; benefits from a dedicated owner so it isn't an afterthought on other workstreams. |
   | SNN model registry (4 axes: architecture × neuron model × connectivity × scale) | spawned Claude agent | Design-sensitive — this is the axis the prototype's own findings (D3) point at; needs judgment about how axes compose, not just plumbing. |
   | Multi-objective search harness (accuracy vs. bio-topology-distance, wall-clock budget, degenerate-run handling) | spawned Claude agent | Design-sensitive — owns the actual research mechanism (D3, D5); needs to correctly implement the prototype's learned lesson about treating degenerate policy collapse as a routine outcome, not an exception. |
   | Topology/stats module extension (H0/H1/H2, Wasserstein + bottleneck, permutation/bootstrap significance) | spawned Claude agent | Design-sensitive — extends validated prototype code (`prototype/snntopo/topology/`); correctness here underpins every atlas entry, warrants a focused owner rather than being bolted onto another workstream. |

   Task-suite work (matched 2AFC-family tasks per bio dataset + generic tasks)
   splits across whichever workstream it's closest to: bio-matched task variants
   ride with the relevant data-loader worker; generic tasks (N-back, delayed
   match-to-sample) ride with the search-harness worker, since they're primarily
   exercised by the search.

## Boundaries

- Each parallel worker operates in its own git worktree off the interface-phase
  commit — no shared branch during fan-out, to avoid merge conflicts between
  agents editing adjacent code.
- The orchestrator reviews each workstream's output against the frozen interfaces
  before merging — a review/merge gate, not a rubber stamp. Interface violations
  get sent back to the worker, not silently patched by the orchestrator.
- `prototype/` is read-only reference material during the build (already frozen
  by convention per its own reports) — workers read it for validated logic to
  port/extend, never edit it.
- Model tier: orchestrator runs opusplan (planning-grade model) since it owns
  architecture and integration judgment; Codex and spawned Claude agents run at
  whatever tier is standard for mechanical vs. design-sensitive work respectively
  — no specific tier constraint beyond that split.

## Tool-agnostic note

Described here in terms of roles and coordination, not a specific tool — this
shape works whether driven via nodeterm (as planned — opusplan orchestrator node,
a Codex node, spawned Claude agent nodes, worktree-per-node), a background
worktree loop, or a plain sequential session working through the same phases one
at a time. The nodeterm-specific execution (which nodes, which links, canvas
layout) is a `manage-nodeterm-canvas` concern at build-kickoff time, not fixed
here.
