# Glossary

Reference, not scheduled reading. One or two plain sentences per term, and the document that
introduces it (where the full explanation and an example are). Alphabetical.

| term | meaning | introduced in |
|---|---|---|
| active vs passive block | The two parts of a Steinmetz session. In the active block the mouse does the task; in the passive block that follows, the same stimuli are shown and nothing is asked of it. | 03 |
| activity | An array of spike counts with shape (neurons, trials, time bins), plus named subsets of trials. The one input the pipeline accepts, from a brain or a model. | 02 |
| activity id | A hash of the recipe that produced an activity. The same recipe always gives the same id. | 02 |
| arm | One set of synthetic comparisons with a known answer, used for calibration. A: same shape, same placement. B: same shape, different placement. C: circle vs figure-8. | 03 |
| barcode | A picture of a persistence diagram: one horizontal bar per feature, from its birth to its death. | 01 |
| Betti number | The count of features of one kind in a shape: pieces (dimension 0), loops (dimension 1). A ring has Betti numbers (1, 1). | 01 |
| birth | The scale at which a feature first appears as the scale grows. | 01 |
| bottleneck distance | A distance between two persistence diagrams: match their points as cheaply as possible, and report the single worst pair. | 01 |
| brain region | A named anatomical area of the brain (for example VISp, primary visual cortex). A probe passes through several, and each unit is labelled with one. | 04 |
| checkpoint | A saved copy of a network's weights at a fixed point in training (here after 0, 300 or 1500 updates). | 05 |
| condition | A named subset of an activity's trials, such as `left` or `all`, stored as a yes/no mask. | 02 |
| connected component | One piece of a shape. Two separate blobs are two components. | 01 |
| Dale's law | The rule that a biological neuron is either excitatory or inhibitory: all its outgoing connections have the same sign. | 05 |
| death | The scale at which a feature disappears: a piece merges into another, or a loop gets filled in. | 01 |
| descriptor | A plain number about a trajectory that involves no topology (participation ratio, mean rate, trajectory length), stored next to the signature. | 02 |
| embedding | How a shape is placed into the space of neurons: which neurons respond to which part of it, and how strongly. Two embeddings of one circle have the same topology and different geometry. | 03 |
| engagement | Whether the animal is doing the task (engaged, active block) or just being shown stimuli (passive block). | 03 |
| essential bar | A bar that never dies. In dimension 0 there is always exactly one (in the end everything is one piece). Dropped before any distance is measured. | 01 |
| false-positive rate | How often a test says "different" when the two things are in fact the same. | 03 |
| filtration | A sequence of nested shapes, each containing the last, obtained by growing the scale. | 01 |
| floor | The largest ratio that a change of geometry alone produces at a given noise level (arm B's 95th percentile). A real result has to clear it. | 03 |
| geometry vs topology | Topology: how many pieces and holes, unchanged by stretching. Geometry: sizes, distances and proportions, which stretching changes. A persistence diagram contains both. | 01 |
| go / no-go | A task trial where the right answer is to act (go) or to hold still (no-go). In Steinmetz, no-go is correct when no stimulus is shown. | 05 |
| `h` | The number of trials in each half of a split-half. Both sides of a comparison always use the same `h`. | 03 |
| homology (`H0`, `H1`) | The machinery that counts holes by dimension. `H0` counts pieces, `H1` counts loops, `H2` counts enclosed cavities. | 01 |
| leaky integrate-and-fire (LIF) neuron | The simplest spiking neuron model: a voltage that sums its input, leaks toward zero, and emits a spike and resets when it crosses a threshold. | 05 |
| loop | A closed path around a hole, which can't be shrunk to a point without leaving the shape. | 01 |
| matched noise | Running the synthetic arms at the noise level that makes their null mean equal to the data's, so their ratios are on the same scale. | 03 |
| membrane time constant | How quickly a model neuron's voltage leaks away, and so how long it remembers its input. In the code it appears as the decay factor `beta`. | 05 |
| neuron (unit) | A brain cell. In a recording, a "unit" is one neuron's spikes as isolated by spike sorting. In a model, one artificial spiking element. | 02 |
| Neuropixels probe | A thin silicon recording needle with hundreds of electrodes along it, which records hundreds of neurons across several brain regions at once. | 05 |
| null distribution | The spread of values a statistic takes when nothing but noise is at work. Here: the distances between random halves of the same activity. | 03 |
| null mean | The average of the null distribution: the typical distance between two random halves of one activity. The project's unit of noise. | 03 |
| p-value | The fraction of null values at least as large as the observed one. Small means "noise alone rarely does this". | 03 |
| PCA trajectory | The trajectory after PCA has reduced it to its 10 largest directions of variation. | 02 |
| persistence | Death minus birth: how long a feature lasts as the scale grows. | 01 |
| persistence diagram | The record of a filtration: one point (birth, death) per feature. | 01 |
| point cloud | A finite set of points in space. Here: 150 points, one per time bin. | 01 |
| power | How often a test says "different" when the two things really are different. | 03 |
| rate network | A recurrent network whose units output a continuous firing rate instead of spikes. Its rates are turned into spike counts by random sampling so it fits the same pipeline. | 05 |
| ratio | Observed distance divided by null mean: "how many noise-units apart". It has no fixed scale across noise levels. | 03 |
| recipe | A small dictionary that names one activity completely, with every number filled in. | 02 |
| recurrent vs feedforward | Feedforward: signals pass through the layers once, input to output. Recurrent: neurons in a layer also feed each other, so activity can persist and evolve on its own. | 04 |
| regime | The input a trained network is given when its activity is recorded: `task` (the task's stimuli) or `spontaneous` (no input at all). | 05 |
| REINFORCE | A training rule that needs only a reward signal: try an action, and make it more likely if it was rewarded and less likely if not. | 05 |
| resample | One random redraw. Here: one random split of a condition's trials into two halves. | 03 |
| robust count (R1) | The number of bars in a diagram that are longer than twice the noise band measured from split halves. | 03 |
| sampling noise | The variation in a result that comes only from which trials happened to be recorded. | 03 |
| seed | The number that starts a random number generator. Same seed, same random choices. Used for resampling, for subsampling and for network training. | 03 |
| session | One sitting of one animal on one day: a fixed set of neurons and a few hundred trials. | 02 |
| signature | The persistence diagrams (`H0` and `H1`) of one condition of one activity, with their summary numbers. | 02 |
| simplicial complex | A shape built from points, edges, filled triangles and their higher-dimensional versions. | 01 |
| smoothing | Replacing each value by the average of its neighbours in time (here, 5 bins) to remove jitter. | 02 |
| spike | The brief electrical pulse a neuron fires. The basic event in all the data here. | 02 |
| spike count | The number of spikes a neuron fired in one time bin. | 02 |
| split-half | Shuffle a condition's trials and cut them into two halves that share no trial. Comparing the halves shows how much a result moves from sampling noise alone. | 03 |
| stability | The guarantee that moving the points of a cloud a little moves its persistence diagram only a little. | 01 |
| stimulus contrast | How visible the visual stimulus is, from 0 (not shown) to 1 (full strength). | 05 |
| surrogate gradient | A smooth stand-in for the spike's derivative (which is zero almost everywhere), used so a spiking network can be trained by backpropagation. | 05 |
| time bin | A short window of time (10 ms here) over which spikes are counted. | 02 |
| trajectory | The path the population's state traces through neuron-space over the course of a trial: one point per time bin, in order. | 02 |
| trial | One repetition of the experiment, cut out of the recording and aligned to the stimulus. | 02 |
| trial average | The mean over a condition's trials, giving one typical curve per neuron. | 02 |
| two-alternative choice | A task where the subject must pick one of two options, here left or right. | 05 |
| unit diameter | A cloud rescaled so its two farthest points are exactly 1 apart. | 02 |
| Vietoris-Rips complex | The simplicial complex built at scale `t` by joining points closer than `t` and filling any triangle whose three edges exist. | 01 |
| Wasserstein distance | A distance between two persistence diagrams: match their points as cheaply as possible, and combine the costs of all pairs. The project's main measure. | 01 |
