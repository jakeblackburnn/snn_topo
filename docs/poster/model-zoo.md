# The model zoo

A *zoo* is a sweep: train every combination, record its activity, measure it the same way as
the brain data. Run `zoo_v1`: 35 configurations, 210 trainings, 1260 recorded activities.

## The neurons

| name | what it is |
|---|---|
| `lif` | Leaky integrate-and-fire. Voltage decays by 0.9 each step, input is added, a spike fires above threshold 1 and the threshold is subtracted. |
| `alif` | LIF whose threshold rises with its own recent firing, so it tires over the trial (Bellec et al. 2018). |
| `izhikevich` | Quadratic voltage curve plus a slow recovery variable: closer to a real cell's spike dynamics. |

## The architectures

| name | what it is |
|---|---|
| feedforward | Input drives one hidden layer; no connections within the layer. |
| recurrent | One population whose neurons also drive each other. |
| modular | Two recurrent groups in a chain. Input enters the first, the answer is read from the second, so the signal must cross the boundary, like a signal crossing brain regions. |

## The wiring (recurrent and modular only)

All four use the same number of connections (10% density), arranged differently:
random, small-world (clustered with shortcuts), scale-free (a few hubs), hub-modular
(four communities joined by hubs).

3 neurons x (1 feedforward + 4 recurrent + 4 modular) = **27 configurations**.

## Eight more (all recurrent or modular LIF unless noted)

| count | variant |
|---|---|
| 2 | Mixed time constants across neurons (two spread sizes) |
| 2 | Dale's law: each neuron is excitatory or inhibitory, 20% inhibitory |
| 2 | Rate networks: continuous outputs instead of spikes, converted to spike counts by Poisson sampling |
| 2 | Trained on a three-action version of the task with a no-go option |

27 + 8 = **35 configurations**.

## The task

A stripped-down copy of the mouse's task. Two input channels carry left and right contrast
(0, 0.25, 0.5, 1) as spike trains for 150 time steps, with a sharp onset decaying to a
plateau. The right action is the side with higher contrast. 150 steps matches the 150 bins
of the brain window.

## Training

- Learning from reward, not labels (REINFORCE): the network picks an action, gets +1 or -1.
- Spikes have no usable derivative, so gradients use a smooth stand-in (surrogate gradient).
- 1500 updates, batch 64, Adam. Trained networks reach about 99.7% median accuracy.

## What is recorded

Each configuration x {128, 512 hidden neurons} x 3 training seeds x 3 checkpoints
(0 = untrained, 300, 1500 updates) x 2 regimes (task input, no input).

For each: the hidden neurons' spikes on 340 test trials, 150 steps each. That array
(neurons x trials x time) goes through exactly the pipeline the brain data does.
The output neurons are never measured.

## What turned out unusable

- **Untrained networks** pick one side on every trial, so there is no left/right split.
- **No-input regime**: without input the networks are deterministic, every trial is
  identical, and there is no trial-to-trial noise to measure against.
- 13 of 210 trainings never learned the task and are left out.

That leaves 197 trained networks, task regime, as the zoo the poster describes.

Source: `snntopo/models/`, `snntopo/tasks/steinmetz_2afc.py`, `snntopo/training.py`,
`sweeps/zoo_v0.py`, `sweeps/zoo_v1.py`.
