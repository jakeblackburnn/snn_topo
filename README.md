# snntopo

snntopo builds a topology atlas of biological and spiking-neural-network population
activity. It measures persistence signatures across datasets, model configurations,
and tasks, then records statistically tested distances in portable atlas artifacts.
The project specification is in `dev/SPEC.md`.

## Install

```sh
pip install -e .[test]
```

## CLI

```sh
snntopo bio --dataset steinmetz --out results/bio
snntopo snn --task steinmetz_2afc --out results/snn-mini
snntopo search --task T --budget-hours H --out DIR
snntopo report --run results/bio --run results/search-T --out results/report
```

`search` is the full atlas-population command; use `snn` only for a small single
configuration smoke run. The build does not launch a full search.

Each run directory contains `atlas.jsonl` (append-only records), `signatures/` NPZ
files, optional training `curves/`, and flattened `entries`/`distances` CSV and
Parquet tables. `report` combines any number of those runs into the same tables plus
a static `report.md` and PNG figures.

Run the default fast suite with `pytest`; tests marked `data` are skipped because
they fetch or read biological data. Run those explicitly with `pytest -m data`.

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
