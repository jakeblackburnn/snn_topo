# snntopo

snntopo builds a topology atlas of biological and spiking-neural-network population
activity. It measures persistence signatures across datasets, model configurations,
and tasks, then records statistically tested distances in portable atlas artifacts.
The project specification is in `dev/agents/spec.md`.

## Install

```sh
pip install -e .[test]
```

By default, biological data is cached under `data/raw/` and command outputs under
`results/` in this checkout. Set `SNNTOPO_DATA_DIR` or `SNNTOPO_RESULTS_DIR` to
share those locations across worktrees.

## CLI

```sh
python -m snntopo.cli bio --dataset steinmetz --out results/bio
python -m snntopo.cli bio --dataset allen --compare-dataset steinmetz --compare-dataset ibl --out results/bio-allen
python -m snntopo.cli baseline --out results/baseline
python -m snntopo.cli snn --task steinmetz_2afc --out results/snn-mini
python -m snntopo.cli control --task steinmetz_2afc --kind untrained --n 5 --out results/control
python -m snntopo.cli search --task T --budget-hours H --out DIR
python -m snntopo.cli report --run results/bio --run results/search-T --out results/report
python -m snntopo.cli rescore --run results/search-T
```

`search` is the full atlas-population command; use `snn` only for a small single
configuration smoke run. The build does not launch a full search.

Each run directory contains `atlas.jsonl` (append-only records), `signatures/` NPZ
files, optional training `curves/`, and flattened `entries`/`distances` CSV and
Parquet tables. `report` combines any number of those runs into the same tables plus
a static `report.md` and PNG figures.

Run the default fast suite with `python -m pytest -q`; data-marked tests are skipped
because they fetch or read biological data.

## Extending

- **Bio dataset:** implement a loader returning `BioSession`/`Activity`, then add a
  `DatasetEntry` to `snntopo/data/__init__.py`. Its condition names form the matching
  contract with tasks, and its reference-session signatures become atlas bio rows.
- **Model axis value:** add the public value to the appropriate registry constant in
  `snntopo/models/__init__.py`, make `build_model` construct it from `ModelConfig`,
  and preserve the model forward contract: hidden and output spikes have `(T, B, N)`
  layout.
- **Task:** subclass `contracts.Task`, register an instance in
  `snntopo/tasks/__init__.py`, and implement `sample_batch`. A matched task sets
  `bio_match` to a `DATASETS` key and uses that dataset's condition names as
  `action_names`; a generic task sets `bio_match = None`.

The shared field definitions in `snntopo/contracts.py` are the compatibility boundary
for all three extension points.
