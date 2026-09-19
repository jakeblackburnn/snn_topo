# The two compared datasets — 2026-09-12

Background reference for [`experiment_report_2026-09-12.md`](experiment_report_2026-09-12.md)
and the 2026-09-11 prototype: what the bio recording actually is, and what the SNN
side actually is, side by side.

## Bio: Steinmetz et al. 2019 mouse Neuropixels recording

**Task**: head-fixed mouse faces two screens (left, right), each showing a sinusoidal
grating at one of four contrasts `{0, 0.25, 0.5, 1.0}`, independently per side. Mouse
turns a steering wheel with its front paws to bring the higher-contrast grating to
center; correct turn → water reward. Equal contrasts (including 0/0 ) → no-go trial
(reward for holding still). An auditory go-cue (mean ~0.6s post-stimulus in this
session) signals the response window is open.

**Recording technology**: Neuropixels probes — silicon microelectrode arrays with
hundreds of densely-spaced recording sites per shank, enabling simultaneous
extracellular recording of hundreds of single units across multiple brain regions in
one acute session. Spikes are sorted into single/multi-units (Kilosort-family spike
sorting) and each unit is assigned a brain-region label via histological
reconstruction of the probe track against the Allen Common Coordinate Framework.

**This specific session** (used throughout this project): mouse "Lederberg",
2017-12-05, session index 11 of the `part0` NMA-packaged release. 698 simultaneously
recorded units, 340 trials, spikes binned at 10ms over 250 bins/trial (2.5s), of
which analysis here uses bins 50-200 (0.5-2.0s post-stimulus, 150 bins). Trials:
135 left-choice, 141 right-choice, 64 no-go (excluded from analysis, mirroring the
SNN's exclusion of equal-contrast trials).

Recorded regions (unit counts) — a genuine cross-brain sample, not a single cortical
area:

| Region | Units | Region | Units |
|---|---|---|---|
| MD (mediodorsal thalamus) | 126 | LH (lateral hypothalamus) | 18 |
| SUB (subiculum) | 105 | ACA (anterior cingulate cortex) | 16 |
| root (unassigned/fiber tract) | 100 | LGd (dorsal lateral geniculate, thalamus) | 11 |
| VISam (visual cortex, anteromedial) | 79 | MOs (secondary motor cortex) | 6 |
| VISp (primary visual cortex) | 66 | | |
| DG (dentate gyrus, hippocampus) | 65 | | |
| PL (prelimbic cortex) | 56 | | |
| CA1 (hippocampus) | 50 | | |

So the "698 neurons" is thalamus + hippocampal formation + prefrontal/cingulate
cortex + visual cortex + a little motor cortex and hypothalamus, all recorded
simultaneously during the same behavior — real anatomical and functional diversity
that the SNN side has no equivalent of (a single homogeneous LIF population).

## SNN: recurrent LIF policy (as of the 2026-09-12 experiment)

**Task**: matched 2AFC contrast task — two input channels carry left/right contrast,
same four levels `{0, 0.25, 0.5, 1.0}`; equal-contrast trials excluded; higher-contrast
channel is the rewarded action (mirrors the bio task's structure, not a literal wheel
simulation).

**Input encoding**: each channel's instantaneous spike probability follows
`rate(t) = contrast * (0.3 + 0.7 * exp(-t/25))` over `T=150` steps — an instant onset
then decay to a 30%-of-peak sustained rate over a 25-step time constant (an
adapting-transient/sensory-adaptation-like profile), sampled via
`snntorch.spikegen.rate(..., time_var_input=True)`. Not a constant rate for the whole
trial (that was the prior prototype's design, since revised).

**Model** (`snntopo/models/snn_model.py`): `2 → Linear → RLeaky(698, all-to-all
recurrent) → Linear → Leaky → 2`. Both spiking layers are leaky integrate-and-fire
neurons (membrane decay β=0.9, threshold 1.0, snntorch defaults), with the standard
surrogate-gradient spike function for backprop through the non-differentiable spike
nonlinearity. Hidden layer is recurrent (full 698×698 learned recurrent weight
matrix); output layer is a plain feedforward readout. 698 hidden units chosen to
match the bio session's neuron count exactly.

**Training** (`snntopo/training/reinforce.py`): REINFORCE policy gradient — output
layer's spike counts summed over all 150 steps → softmax → sampled action; reward
±1 (correct/incorrect); EMA baseline (momentum 0.9) for variance reduction; entropy
bonus linearly annealed from 0.01 to 0 over training (added after an entropy-driven
late-training collapse was observed without annealing); Adam, lr=1e-3; gradient-norm
clipping at max_norm=10 (rescaled up from a too-tight default once the network's much
larger recurrent parameter count made that clear); batch size 64, 3000 updates; the
best-EMA-baseline checkpoint is what's saved and used for eval, not simply the final
one. Result: ~96% accuracy on 340 held-out eval trials.

**What has no counterpart on the bio side**: a designed reward signal and an
explicit training objective (bio neurons weren't "trained" by REINFORCE — the mouse
learned via its own biology over many prior sessions, not observed here), a single
homogeneous neuron population/type instead of the bio session's dozen anatomically
distinct regions, and full experimenter control over the input statistics (bio
sensory input arrives through real optics/retina/LGN before ever reaching any of the
recorded regions).
