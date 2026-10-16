# SNN Topo Journal


I wanna restart from scratch almost, but not really.
develop a more concrete result for the poster. This will involve code changes.

use first principles thinking to develop a creative new idea about how to use topology on the data.
I wanna pick one model type to try, maybe test a few variables, but really just get good averages for the topologies
with a more comparable task complexity.

I was thinking that the neuropixels recordings are really a smattering of neurons throughout the mouse brain,
so a more comparable setting would be a huge snn trianed to do a lot of things, and picking a small random subset
of the neurons to monitor. Maybe thats a thread to pull in limitations

Intro
I - TDA
II - Experiments
  a) dataset
  b) models
  c) pipeline
III - Results
IV - Limitations
Conclusion

so I know I want this structure for the poster,
so we want to develop a headline for this, and quite frankly start a new branch and destroy all the previous docs for the poster
Then start a coding session

### 2026-10-16 09:55 (agent)
Clique topology of random 50/128-neuron probes: trained multitask AdEx nets (Pugavko 2023 port) sit between untrained nets and mouse brain (Betti 1 vs random 0.04 / 0.24 / 0.46). The gap survives drift removal (E19, E20); see docs/e2e.md and docs/poster/headline.md on branch clique-topology.
