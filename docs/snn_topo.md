# SNN TOPO

## Research Question
Does the topological signature of activity in computational models mirror that of real biological brains?
Does topological data analysis offer any new insight into neural codes?

### Topology and Topological Data Analysis

*Curta* **cite** explains how topological data analysis can be applied to interpret neural codes, in other words how brains represent
experiences with spike patterns across populations of neurons.

#### Topological Invariants
Topology and its applications to data analysis are burgeoning fields of mathematics. Its applications to science are especially
relevant to understanding the brain where data is more and more abundant. 

Topology is a field of mathematics concerned with characterizing objects by their topological properties, rather than geometric properties.
The classic example is *the homeomorphism between a donut and a coffee cup*. The geometry differs, but both contain one topological 
hole / loop, and are therefore *homeomorphic*, a form of topological equivalence.
The key invariant between topologically equivalent objects is their Homology groups, or *Betti Numbers:*

- $\beta_0$ - number of connected components, meaning contiguous 'pieces' of an object

- $\beta_1$ - the number of topological holes / loops

- $\beta_2$ - the number of 'voids', or enclosed spaces. 

**Figure a Homeomorphism from coffee cup to donut: ceramic model by Keenan Crane and Henry Segerman, via wikipedia**


##### Example: Torus 
A donut, as discussed has one hole, and clearly has only one contiguous connected component, 
therefore betti0 = 1 and betti1=1. A *Torus* is the geometric equivalent of the *surface* of a donut, without the 
interior filled in. A torus therefore still has one connected component, but has *two* holes, the usual one in the center, but
also the ring around the interior of the donut. Furthermore, it encloses an empty space - a void. thus betti0 = 1 betti1 = 2 and betti2=1.

**Figure: homology groups of a donut**

*Note: the homology groups of a torus are relevant to the poincare conjecture, proved in 2003 by grigori perelman*

#### Topology Applied to Data Analysis
Topological data analysis seeks to apply topology to characterize datasets, for instance, a high dimentional point cloud, by its 
topological features. The classic application of TDA is persistent homology.

Cech or Vitoris-Rips methods take a point cloud, and progressively 'Thicken' the points. During this process, points connect 
and overlap to form *simplicial complexes* which can be readily analyzed in terms of their topological features, and measure how 
topology *persists* across the varying "thickenings". The key idea being that real topological features will persist
significantly longer than features resulting from noise, allowing for a distinct topological 'signature' of a dataset.
This signature gives us power to identify characteristics of the underlying distribution data is sampled from, and reveal 
differences invisible to typical statistical techniques. This is also especially useful for analyzing and discriminating 
high dimentional, hard to visualize datasets. 

**Figure: rips / cech complex thickenings**
**Figure: Mobius Strip**

### Topology of Brain Activity

Applying TDA to brain activity requires a means for turning raw recordings (Neuropixels **cite**) into a meaningful and interpetable 
point cloud, at a scale / dimension which is tractable for persistent homology. 

Neuropixels recordings are taken by an electrode array, deep enough to cross multiple layers of cortex. from the raw recordings,
secondary analysis is able to (with some accuracy) pinpoint activations of individual 'units' (neurons). 



#### The dataset
The Steinmetz dataset 


##### The task: visual discrimination
Rats are presented with a screen, the left or right side lights up with a striped black and white pattern, 
the mouse is trained to turn a wheel to the left or right depending on which side the pattern appears. 

populations of neurons recorded range from **Numbers-Numbers**, and are taken in one of two scenarios: the active scenario, where the 
rat is made to turn the wheel, and the passive scenario, where the rat simply observes the stimulus. Spikes are separated into 
discrete time 'bins' about 10ms each. the number of spikes coming from individual neurons on this time scale tend to be 0 or 1. 
These experiments were repeated for a number of trials for each rat / scenario. 


### Turning neuropixels into point clouds
Due to the high variance in recordings across trials, and the need for computational tractability two things were done 
to reduce the dimensionality of the recordings: 

1. Average over 150 trials 
Turns (neurons, time bins, trials) to (averaged neurons, time bins)

2. 10-component PCA
Turns the hundreds of neurons into a simple 10 dimentional neuron activity components characterizing the 
activity of all neurons in a given time bin

3. Also, we smooth activations over neighboring time bins, to avoid arbitrary divisions and make trajectory smoother 

Then finailly we have a cloud of 150 points in a 10 dimentional, 'reduced neuron space' that is ready for TDA.


### Computational models 

### Comparing Models vs Brains
beyond just observing and doing statistics on the most persistent betti numbers
bottleneck and wasserstein distance used to quantify the difference between persistence diagrams

### Making differences statistically significant
some distance between datasets is expected due to random noise even with the same population of neurons in the same scenario. 
Thus, two methods were employed to put a lower bound on the distance between brains and models due to noise. 
distances above this threshold therefore are likely to represent real topological differences, and are usable signals for discrimination.

1. split half null

2. noise floor


### Results 




