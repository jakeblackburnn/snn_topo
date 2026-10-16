# Topology of Brain Activity of Mice vs. Computational Models

**Research Question:** Can topological data analysis (TDA) extract meaningful as;dflaksjdf
**Answer:** Yes, the topodfgaksdf 

## Introduction

Topology is a branch of modern mathematics which has shown remarkable richness in its applications to data analysis. 
Methods such as persistent homology can be leveraged to characterize and differentiate datasets based on their topological features.
This poster shows how TDA reveals meaningful differences between recorded neuron population activity in mice and that of simulated spiking neural networks.

## I - Topological Data Analysis


**Topology**

**Picture: Topologist's Breakfast**

**Persistent Homology**

**Figure: Vietoris-Rips Complex**

## II - TDA Applied to Brain Activity

**Neuropixels**
Stienmetz et al 2019 recorded population activity in mice performing a visual discrimination task using Neuropixels probes, which can register spikes
from hundreds of neurons across several brain regions. These mice were trained on a visual 

**Figure: Visual Discrimination Task**

**Spiking Neural Networks** (SNNs) are a form of artificial neural network intended to mirror real neurons with their all-or-none spikes.
We collected comparable population activity data from a variety of SNNs trained on a simplified version of the Stienmetz task. The following table
summarizes the varieties and session counts:

**Table: the different model types**

**Population Trajectories**

The raw data collected from the mouse brains and SNNs track when individual neurons fire, binned into 10ms intervals, over a set of trials.
To make this raw data amenable for TDA, each recorded session was first equalized to a set of 128 neurons, over 150 time steps, and 100 random trials. Then, the following pipeline was applied to each session:

1. average over trials
2. smooth spikes over a 50ms window
3. reduce the neuron axes via PCA to a 10-dim 'activity space'
4. scale the activity space to unit width

This converts a (128x150x100) grid of individual spikes to a smoothed and normalized (10x150) point cloud: 10 dimensions in activity space over 150 time steps.

**Figure: Trajectories**
Left: raw spikes from a population of 128 neurons over time. Right: three population 'trajectories' shown in the reduced activity space (using 3 of the 10 dimensions). The leftmost population is a passive mouse brain, middle, a mouse engaged in the visual discrimination task, and finailly a recurrent
SNN. Each example is selected as the median 'path length' in its group of sessions.

## III - Results

**Cluster Persistence corresponds to trajectory length**
and is explained by participation rate PCA stuff

**Task engagement changes the topological signature:** in 11 of 12 held-out tests, engagement changed persistence - making trajectories
more smooth and detectable.

**SNNs are Differentiable** from brains, though task engagement makes brains more model-like.

**loops are insignificant**
These experients did not detect persistent topological features other than connected components, or 'clusters' in the activity space. In mouse
populations, task engagement reliably reduced the total persistence of clusters.

## IV - Limitations

**Smoothed Average trajectories w/ PCA** are used but not justified, avoids granular detail within an individual trial.

**Neural Recordings are Imperfect** compared to noiseless models.

**Descriptive only**, but with no significance test, unclear whether models truly differentiate with added noise
Unclear whether differences are truly topological or geometric.

**Doesnt account for the directed, time series nature of the trajectory**, and instead treats it only as a cloud of points.

**Limited amount and comparability of data**
with 13 sessions and only 4 mice, sessions are not completely independent. Additionally, the SNN discrimination task 




