# Architecture

The package moves one common representation through both domains:

```text
bio loader / task + trained model / control -> Activity -> Signature -> DistanceResult -> AtlasRecord -> static report
```

Loaders turn recordings into `Activity`; trained models are evaluated into the same
neuron × trial × time-bin layout, while controls supply untrained-SNN or shuffled-bio
activity in that same layout. The topology pipeline makes a per-condition,
diameter-normalized persistence `Signature` (H0/H1 by default; H2 is opt-in with
`--maxdim 2`). Statistics compare signatures and emit significance-bearing
`DistanceResult` rows. `atlas` stores each bio session, evaluated SNN configuration, or
control as an append-only `AtlasRecord`; `search` and `objective` select and score model
configurations; `report` reads one or more run directories and writes tables, markdown,
and figures.

## Build versus run

The build supplies registries, contracts, topology, training, search machinery, and
fast smoke tests. It does not run the wall-clock-limited searches or long training
jobs. Those are a later user-initiated run: each evaluated configuration is appended to
its atlas directory as it finishes, so interrupted runs remain reportable.
