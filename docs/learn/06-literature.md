# 06 · Reading guide: three papers

*Day 2. Ten minutes for this guide, then 40 + 60 + 40 minutes for the papers.*

A guide, not a survey. For each paper: why it is here, what to read and skip, three
questions to hold while reading, and where it touches this repo. Answer the questions in a
sentence each; document 07 uses them.

How these were prepared: Curto and Maheswaranathan were read in full from their arXiv PDFs.
Gardner was read from the full text of the open-access copy on Europe PMC (PMC8810387).

## 1. Curto, *What can topology tell us about the neural code?* (2017)

<https://arxiv.org/abs/1605.01905> · 16 pages · 40 minutes

**Why.** The clearest account of why anyone thought topology and neurons belong together,
written as a talk for mathematicians who know no neuroscience. You are the mirror image of
her audience, and it still works.

**Read** sections 1 to 3 (pages 1 to 8). Section 2, "Neurons: nodes in a network or
autonomous sensors?", is the best two pages of neuroscience background you'll get today.
Section 3, "Topology of hippocampal place cell codes", is the core: place cells, the Nerve
Lemma, Figures 3 to 5, and then grid cells and why their code lives on a torus (Figure 6).

**Read** section 4.1, "'Traditional' TDA applied to neuroscience data sets" (pages 8 to 9).
It is one page and it describes this project's method exactly: a point cloud, balls of
growing radius, a Vietoris-Rips complex, persistent homology.

**Skim** section 4.2, "An upgrade to network science". **Skip** sections 5 and 6 (codes of
open covers, convexity, local obstructions): real mathematics, no bearing on this project.
Section 7, "Codes from networks", is one page and worth it if you have time.

**Questions.**
1. In section 3, what is the thing whose topology is being recovered, and what has to be
   true of the place fields for the Nerve Lemma to apply?
2. Section 4 sorts topology-in-neuroscience into three themes. Which one is snntopo?
3. Page 7 describes an experiment with a bendable track, where place fields "respected
   topological aspects of the environment more than metric features". Compare with document
   01, section 10. Does snntopo's measure ignore metric features?

**Where it touches the repo.** Section 4.1 is `snntopo/topology/pipeline.py:42-47`. But
notice that her main thread builds its shape differently: from *which neurons fire
together*, so that the recovered shape is the space the animal is in. snntopo's shape is
built from time bins of one averaged path (document 02, section 4). The tools are shared;
the object is not.

## 2. Gardner et al., *Toroidal topology of population activity in grid cells* (2022)

<https://www.nature.com/articles/s41586-021-04268-7> · open access · 60 minutes
(full text also at Europe PMC:
<https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8810387/fullTextXML>)

**Why.** The field's reference result: persistent homology applied to a real recording,
finding the shape theory predicted. It is also the dataset this project's notes name as a
possible known-answer test on brain data
(`dev/brainstorm/mega-forward-plan/bio-data-expansion.md` §2a).

**Read** the opening ("Main"), "Visualization of toroidal manifold", "Quantification of
toroidal topology" and "Toroidal topology persists during sleep", with Fig. 1 ("Signatures
of toroidal structure in the activity of a module of grid cells") and Fig. 3 ("Preservation
of toroidal structure during sleep"), then the Discussion.

**Skim** "Tori persist despite grid distortions". **Skip** "Classes of grid cells" and the
Methods on surgery, recording and spike sorting. Do read the Methods passage on
preprocessing and dimensionality reduction, slowly, with document 02 open beside it.

**Questions.**
1. What is one point in their cloud? The population state at one 10 ms time point, from 66
   to 189 grid cells per module, smoothed, z-scored and reduced to six principal components.
   The cloud is 1,200 such points, picked from the 15,000 most active. Go through document
   02's steps one at a time: which do they share, and which one is missing?
2. What does a torus look like as a barcode? They require "four bars of substantial length":
   one in dimension 0, two in dimension 1, one in dimension 2. Which of those four could
   snntopo see with its current settings (`snntopo/contracts.py:118`)?
3. What is their null, and what else makes the claim convincing? The bars were "longer than
   the lifetime of any bar obtained in 1,000 shuffles of the data in which spike times were
   randomly rotated", and the torus was found again in a second environment and in sleep
   (reported in five of six modules in REM sleep and four of six in slow-wave sleep). How is
   that null different in purpose from the split-half null of document 03?

**Where it touches the repo.** Their recordings have no trials: the animal wanders freely.
snntopo's `Activity` requires trials and averages over them (`snntopo/contracts.py:15-30`).
The brainstorm note flags this as the main obstacle and as the interesting part: would the
torus survive this project's pipeline at all?

## 3. Maheswaranathan et al., *Universality and individuality in neural dynamics across large populations of recurrent networks* (2019)

<https://arxiv.org/abs/1907.08549> · 9 pages of text · 40 minutes

**Why.** It is the model-side version of this project's question, done at scale: train
thousands of recurrent networks on the same task and ask what they have in common. Its
answer is the sentence the whole packet has been circling: geometry varies, something
topological doesn't.

**A warning about one word.** Their "topology" is not persistent homology. It is the
arrangement of a network's *fixed points* (states where the dynamics stand still) and the
routes between them, written as a graph. Same intuition (structure that survives
deformation), different object and different maths.

**Read** the abstract and section 1; section 2.3, "Assessing model similarity"; section
3.1, "3-bit discrete memory", with Figure 1; Figure 4 and its caption; and section 5,
"Discussion". **Skim** sections 3.2 and 3.3. **Skip** the appendices.

**Questions.**
1. Compare panels d and f of Figure 1. Which measure sorts the networks by architecture,
   and which doesn't?
2. Figure 4 shows an *untrained* network scoring as more similar to a trained one than two
   trained networks with different nonlinearities are to each other. Which experiment in
   document 04 found the same embarrassment?
3. They trained 96 configurations with 30 random seeds each, 2,880 networks per task. The
   zoo in document 05 has the same design at smaller size. What would their Figure 1d be,
   made from `zoo_v1`'s signatures? What would you expect to see?

**Where it touches the repo.** E12's arm B is this paper in miniature: same topology,
different geometry, and the similarity measure reacts. Note their closing caveat as well:
the fixed-point comparison only works when every network has the same number of fixed
points, and networks that didn't were discarded.

## Optional reading

All links were checked for the packet (`dev/agents/project/learning/reading.md`, which also
says how each was checked). One line each; none is needed for documents 07 and 08.

**Persistent homology**
- Ghrist, *Barcodes* (2008): the classic short introduction. <https://www.ams.org/bull/2008-45-01/S0273-0979-07-01191-3/>
- Chazal & Michel, *An introduction to TDA* (2017): the best fit for an ML reader. <https://arxiv.org/abs/1710.04019>
- Otter et al., *A roadmap for the computation of persistent homology* (2015): algorithms and software. <https://arxiv.org/abs/1506.08903>
- Fasy et al., *Confidence sets for persistence diagrams* (2014): the idea behind the robust count. <https://arxiv.org/abs/1303.7117>

**Topology of neural population activity**
- Chaudhuri et al. (2019): a ring in head-direction cells, awake and asleep. <https://www.nature.com/articles/s41593-019-0460-x>
- Giusti et al., *Clique topology* (2015): topology of correlation matrices, a different construction. <https://arxiv.org/abs/1502.06172>
- Kang, Xu & Morozov (2021): how many neurons and how much data the method needs. <https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2021.616748/full>
- Ayhan et al. (2025): a recent persistent-homology pipeline for spike trains. <https://arxiv.org/abs/2512.08637>

**Population dynamics and trajectories**
- Vyas et al., *Computation through neural population dynamics* (2020): what a neural trajectory is and why people study it. <https://doi.org/10.1146/annurev-neuro-092619-094115>
- Cunningham & Yu (2014): PCA on trial-averaged population activity. <https://doi.org/10.1038/nn.3776>
- Churchland et al. (2012): rotations, which are loops in a trial-averaged path. <https://doi.org/10.1038/nature11129>

**Comparing models with brains**
- Kriegeskorte, Mur & Bandettini, *Representational similarity analysis* (2008): where it started. <https://www.frontiersin.org/articles/10.3389/neuro.06.004.2008/full>
- Kornblith et al. (2019): CKA. <https://arxiv.org/abs/1905.00414>
- Williams et al., *Generalized shape metrics* (2021): comparison as a proper metric. <https://arxiv.org/abs/2110.14739>
- Ostrow et al., *Dynamical similarity analysis* (2023): comparing dynamics instead of geometry. <https://arxiv.org/abs/2306.10168>
- Nejatbakhsh et al. (2024): a distance that models trial noise. <https://arxiv.org/abs/2412.14421>
- Lin & Kriegeskorte, *The topology and geometry of neural representations* (2024): a family between geometry and topology. <https://arxiv.org/abs/2309.11028>
- Barannikov et al., *Representation topology divergence* (2022): TDA for comparing networks. <https://arxiv.org/abs/2201.00058>
- Sucholutsky et al., *Getting aligned on representational alignment* (2023): a map of the area. <https://arxiv.org/abs/2310.13018>

**Spiking networks and the data**
- Neftci, Mostafa & Zenke, *Surrogate gradient learning* (2019): how these networks are trained. <https://arxiv.org/abs/1901.09948>
- Steinmetz et al. (2019): the dataset's own paper. <https://www.nature.com/articles/s41586-019-1787-x>
- Neuromatch loader notebook for the Steinmetz archive (field names). <https://nbviewer.org/github/NeuromatchAcademy/course-content/blob/main/projects/neurons/load_steinmetz_decisions.ipynb>
