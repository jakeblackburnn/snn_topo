# References

Everything the repo's docs and code cite, grouped by what the poster would use it for.
Links are the ones recorded in `docs/learn/06-literature.md` and
`dev/agents/project/learning/reading.md`. Entries marked † are not cited anywhere in the repo:
I added them from memory because the code uses the dataset or tool. Check † entries (authors,
year, DOI) before printing.

## Datasets
- **Steinmetz** (the poster's brain data). Steinmetz, Zatka-Haas, Carandini & Harris,
  *Distributed coding of choice, action and engagement across the mouse brain*, Nature 2019.
  <https://www.nature.com/articles/s41586-019-1787-x>
  - Used in the Neuromatch Academy preprocessed form, part 0 (`steinmetz_part0.npz`, OSF
    `agvxh`). Loader notebook:
    <https://nbviewer.org/github/NeuromatchAcademy/course-content/blob/main/projects/neurons/load_steinmetz_decisions.ipynb>
- **IBL brain-wide map** (earlier experiments only, not in the poster results). Public release
  read through ONE, <https://openalyx.internationalbrainlab.org>.
  † International Brain Laboratory, *A brain-wide map of neural activity during complex behaviour*.
- **Allen Visual Coding Neuropixels** (earlier experiments only). DANDI dandiset 000021,
  session 719161530.
  † Siegle et al., *Survey of spiking in the mouse visual system reveals functional hierarchy*, Nature 2021.

## Topology of neural activity
- Curto, *What can topology tell us about the neural code?* (2017). <https://arxiv.org/abs/1605.01905>
- Gardner et al., *Toroidal topology of population activity in grid cells*, Nature 2022.
  <https://www.nature.com/articles/s41586-021-04268-7>
- Chaudhuri et al., *The intrinsic attractor manifold and population dynamics of a canonical
  cognitive circuit across waking and sleep*, Nat. Neurosci. 2019. <https://www.nature.com/articles/s41593-019-0460-x>
- Giusti et al., *Clique topology reveals intrinsic geometric structure in neural correlations* (2015).
  <https://arxiv.org/abs/1502.06172>
- Kang, Xu & Morozov, *Evaluating state space discovery by persistent cohomology in the spatial
  representation system*, Front. Comput. Neurosci. 2021.
  <https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2021.616748/full>
- Ayhan et al., *A persistent homology pipeline for the analysis of neural spike train data* (2025).
  <https://arxiv.org/abs/2512.08637>

## Persistent homology (the method)
- Ghrist, *Barcodes: the persistent topology of data*, Bull. AMS 2008.
  <https://www.ams.org/bull/2008-45-01/S0273-0979-07-01191-3/>
- Chazal & Michel, *An introduction to Topological Data Analysis* (2017). <https://arxiv.org/abs/1710.04019>
- Otter et al., *A roadmap for the computation of persistent homology* (2015). <https://arxiv.org/abs/1506.08903>
- Fasy et al., *Confidence sets for persistence diagrams*, Ann. Stat. 2014 (the idea behind
  the robust count R1). <https://arxiv.org/abs/1303.7117>
- † Bauer, *Ripser: efficient computation of Vietoris-Rips persistence barcodes* (the software
  that computes every diagram here).

## Neural trajectories
- Vyas et al., *Computation through neural population dynamics*, Annu. Rev. Neurosci. 2020.
  <https://doi.org/10.1146/annurev-neuro-092619-094115>
- Cunningham & Yu, *Dimensionality reduction for large-scale neural recordings*, Nat. Neurosci. 2014.
  <https://doi.org/10.1038/nn.3776>
- Churchland et al., *Neural population dynamics during reaching*, Nature 2012.
  <https://doi.org/10.1038/nature11129>

## Comparing models with brains
- Maheswaranathan et al., *Universality and individuality in neural dynamics across large
  populations of recurrent networks* (2019). <https://arxiv.org/abs/1907.08549>
- Kriegeskorte, Mur & Bandettini, *Representational similarity analysis*, Front. Syst. Neurosci. 2008.
  <https://www.frontiersin.org/articles/10.3389/neuro.06.004.2008/full>
- Kornblith et al., *Similarity of neural network representations revisited* (2019). <https://arxiv.org/abs/1905.00414>
- Williams et al., *Generalized shape metrics on neural representations* (2021). <https://arxiv.org/abs/2110.14739>
- Ostrow et al., *Beyond geometry: ... dynamical similarity analysis* (2023). <https://arxiv.org/abs/2306.10168>
- Nejatbakhsh et al., *Comparing noisy neural population dynamics using optimal transport distances* (2024).
  <https://arxiv.org/abs/2412.14421>
- Lin & Kriegeskorte, *The topology and geometry of neural representations*, PNAS 2024. <https://arxiv.org/abs/2309.11028>
- Barannikov et al., *Representation topology divergence* (2022). <https://arxiv.org/abs/2201.00058>
- Sucholutsky et al., *Getting aligned on representational alignment* (2023). <https://arxiv.org/abs/2310.13018>

## Spiking networks
- Neftci, Mostafa & Zenke, *Surrogate gradient learning in spiking neural networks* (2019).
  <https://arxiv.org/abs/1901.09948>
- Bellec et al. 2018 (the adaptive neuron `alif` and the gradient dampening factor;
  `snntopo/models/neurons.py:12,35`). † Title: *Long short-term memory and learning-to-learn
  in networks of spiking neurons*, NeurIPS 2018.
- † Izhikevich, *Simple model of spiking neurons*, IEEE Trans. Neural Netw. 2003 (the
  `izhikevich` neuron follows its regular-spiking cell).
- † Williams, *Simple statistical gradient-following algorithms for connectionist reinforcement
  learning*, Mach. Learn. 1992 (REINFORCE, the training rule).
- † Watts & Strogatz, Nature 1998 (small-world wiring); Barabási & Albert, Science 1999
  (scale-free wiring).
- † Eshraghian et al., *Training spiking neural networks using lessons from deep learning*
  (snnTorch, used for input spike generation).

## Minimum set for a poster
Steinmetz 2019, Gardner 2022, Curto 2017, Maheswaranathan 2019, Fasy 2014, Neftci 2019,
Bellec 2018, and Ripser.
