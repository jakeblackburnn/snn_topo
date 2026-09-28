# snntopo

snntopo accumulates a dataset of topological data analysis (TDA) results over spiking
neural networks and brain recordings. The unit of record is an *activity* (neurons × trials
× time bins), identified by the resolved recipe that produces it. Every activity gets
persistence signatures, split-half nulls and descriptors; comparisons exist only where a
spec declares them. Design: `docs/architecture.md`. The agent's reading of the project:
`dev/agents/spec.md`.

## Install

```sh
pip install -e .[test]
```

Biological data is cached under `data/raw/` and results under `results/`. Set
`SNNTOPO_DATA_DIR` / `SNNTOPO_RESULTS_DIR` to share them across worktrees, and
`SNNTOPO_WORKERS` to cap the ripser process pool.

## Quickstart

```sh
snntopo run sweeps/validate_instrument.py --mini --dry-run   # counts and a cost estimate
snntopo run sweeps/validate_instrument.py --mini             # a small real run -> results/runs/<id>/
snntopo status results/runs/<id>                             # done / missing / failed per record type
snntopo verdict sweeps/validate_instrument.py                # read the runs through the spec's verdict()
```

```python
from snntopo import dataset, runner
spec = runner.load_spec("sweeps/validate_instrument.py")
tables = dataset.load(["results/runs/<id>"], dataset.topo_id(spec.TOPO),
                      dataset.cmp_id(spec.CMP["metrics"], spec.CMP["n_resamples"]))
tables["signatures"].head()
```

## Specs

A spec is a Python file that declares what to measure; `snntopo run <spec>` produces and
measures whatever its run dir is still missing, so a killed run resumes where it stopped.

- `sweeps/*.py` are exploratory: `validate_instrument` (known-answer check of the instrument),
  `bio_core` (Steinmetz part 0 atlas), `zoo_v0`/`zoo_v1` (SNN zoo), `smoke_*` (200-update
  gates for new model families).
- `experiments/eNN_*.py` are preregistered: a `PREREG` literal and a `verdict(tables)` bound at
  the first commit that sets PREREG. They run only from a clean tree (or `--mini`, which is
  exploratory), and `snntopo verdict` counts only runs whose recorded hashes match that commit.

A spec defines `TOPO` (a `TopoConfig`), `CMP` (`metrics`, `n_resamples`), `PERSIST`, and
`expand(mini) -> (recipes, pairs)`; optionally `derive(activity_id, activity)` for
per-activity derived rows, and, for experiments, `PREREG` and `verdict`.

Scale by shards: run `snntopo run <spec> --out <dir> --shard i/N` in N shells.

## Results layout

```
results/runs/<YYYYMMDD-HHMM>-<spec>/run.json            provenance: spec blob, code_rev, clean, prereg/verdict hashes
results/runs/<id>/{activities,signatures,nulls,comparisons,derived}[.sIofN].jsonl
results/store/{diagrams,halves,spikes,weights}/<hash>   write-once blobs, shared by runs
```

Rows are append-only. A correction is a `derived` row, never an edit.

## Legacy (v1)

The eight v1 subcommands (`bio`, `baseline`, `snn`, `control`, `synthetic`, `search`,
`report`, `rescore`) and their atlas run dirs still work, but the v3 dataset doesn't read them.

## Tests

`python -m pytest -q` runs the fast suite. `-m data` adds the tests that read the Steinmetz data.
