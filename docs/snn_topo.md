# Topology of Brain Activity of Mice vs. Computational Models
Using Mathematical Tools to Compare Population Activity in Mice and Spiking Neural Networks
Jake Blackburn

**Research Question:** Can topological data analysis (TDA) extract meaningful measures from recorded brain activity? Can those measures discriminate real brain activity from that of comparable computational models?
**Answer**: Yes, topological features can differentiate models from real brains, and can have meaningful interpretations. 

## Introduction
Brains encode information in population activity: the joint firing of many neurons. 
The ability of scientists to observe this activity is limited, so the use of advanced data analytics 
and computational models are essential for making the most of what we can observe. 

The experiments outlined in this poster seek to scrutinize the comparability between brain activity recorded in living animals and in Spiking Neural Networks (SNNs), a class of biologically plausible neural networks, using Topological Data Analysis (TDA). 

Topology is a modern branch of mathematics which has shown remarkable richness in its applications to science. Curto (2017) [3] argued that the topology of brain activity can reveal how neural networks represent and process information. These experiments show that
brain activity recorded in mice exhibits different topology than SNNs in a comparable setting, 
highlighting the limitations of such models, and the utility of TDA for neuroscience.

## I - Topological Data Analysis

**Topology** describes a shape in terms of features that survive deformation without cutting or gluing, such as its pieces and its holes.  

**Picture: Topologists Breakfast:** A coffee mug is topologically equivalent to a donut: both have one ‘hole’. Therefore, one can be continuously deformed into the other, without cutting or gluing. Ceramic model by Keenan Crane and Henry Segerman, 2015, CC BY-SA 3.0, via Wikimedia Commons.

**Clique Topology** ... explain the method we use in broad strokes and its bio interpretation 
and present the figure

## II - Experiments

(a - dataset)
Neuropixels: Steinmetz et al. (2019) [1] recorded mice with Neuropixels probes, which pick up on spikes from hundreds of neurons across several brain regions at once. The mice were trained to perform a visual discrimination task, and their brain activity was recorded in both passive and task-engaged scenarios. We use the recorded activities of 13 sessions from their dataset, ranging from 584 to 1769 neurons each, with spikes counted in 10 ms bins over 1.5s, as a representative sample of population activities in mouse brains at rest and during task execution.

(b - model)
... note the paper and motivation for using large multitasking model with precedent

(c - pipeline) 

... what is done to data to yield curves / results, also summarize different scenarios for results figures

## III - Results
... summarize differences in structure / randomness, returning to the bio interpretation


## IV - Limitations
...


## Conclusion
... point about limitations of observing real brain activity, necessity of comparable models, utility of Topology
for establishing comparability between models and brains and as markers for activity stats, 
for instance for differentiating disease states vs healthy brains and other applications to medicine.

### References 

### Footnote - Credits and Code
