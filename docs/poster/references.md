# References

Two parts. **Checked** entries were compared with a source page on 2026-10-13 (the page is
named beside each); **unchecked** entries were copied from `docs/learn/06-literature.md` and
`dev/agents/project/learning/reading.md` and are not on the poster. An entry is checked when
it is promoted to the poster. The record of the checking is `dev/workshop/poster-references.md`.

## On the poster (9, one per claim)

| # | claim it backs | reference | checked against |
|---|---|---|---|
| 1 | the brain data | Steinmetz, Zatka-Haas, Carandini & Harris, *Distributed coding of choice, action and engagement across the mouse brain*, Nature 576, 266-273 (2019). doi:10.1038/s41586-019-1787-x | PMC6913580 |
| 2 | the probe | Jun, Steinmetz, Siegle et al., *Fully integrated silicon probes for high-density recording of neural activity*, Nature 551, 232-236 (2017). doi:10.1038/nature24636 | pubmed 29120427 |
| 3 | why topology for neural activity | Curto, *What can topology tell us about the neural code?*, Bull. AMS 54(1), 63-78 (2017). arXiv:1605.01905 | arxiv.org/abs/1605.01905 |
| 4 | topology has found real structure in a brain | Gardner et al., *Toroidal topology of population activity in grid cells*, Nature 602, 123-128 (2022). doi:10.1038/s41586-021-04268-7 | PMC8810387, full text |
| 5 | the method | Bauer, *Ripser: efficient computation of Vietoris-Rips persistence barcodes*, J. Appl. Comput. Topol. 5, 391-423 (2021). doi:10.1007/s41468-021-00071-5. arXiv:1908.02518 | arxiv.org/abs/1908.02518, mediatum.ub.tum.de |
| 6 | the robust count | Fasy, Lecci, Rinaldo, Wasserman, Balakrishnan & Singh, *Confidence sets for persistence diagrams*, Ann. Stat. 42(6), 2301-2339 (2014). doi:10.1214/14-AOS1252 | arxiv.org/abs/1303.7117 |
| 7 | the adaptive neuron | Bellec, Salaj, Subramoney, Legenstein & Maass, *Long short-term memory and learning-to-learn in networks of spiking neurons*, NeurIPS 2018. arXiv:1803.09574 | arxiv.org/abs/1803.09574, igi-web.tugraz.at |
| 8 | the Izhikevich neuron | Izhikevich, *Simple model of spiking neurons*, IEEE Trans. Neural Netw. 14(6), 1569-1572 (2003). doi:10.1109/TNN.2003.820440 | brian2.readthedocs.io (Izhikevich_2003) |
| 9 | dimension separates brain from model | Gao, Trautmann, Yu, Santhanam, Ryu, Shenoy & Ganguli, *A theory of multineuronal dimensionality, dynamics and measurement*, bioRxiv 2017. doi:10.1101/214262 | authors and DOI only; **text not read** |

- Gao (9) must be read before the poster leans on it: whether it defines participation ratio
  and claims that task complexity bounds dimension is unconfirmed (bioRxiv returned HTTP 429).
  Its title here is from memory, not from the source page.
- Gardner (4): safe wording is "persistent homology recovered a predicted torus in rat
  grid-cell activity". Their method is not ours: 1,200 single time points up to H2, against
  our 150-point trial-averaged path up to H1.

**Tools line for the poster:** "Computed with ripser.py and GUDHI."

**Figure credit:** the mug-and-donut image is Wikimedia Commons `File:Topology_joke.jpg`, by
Keenan Crane and Henry Segerman, 2015, CC BY-SA 3.0. The poster must print the credit and the
licence name. Checked against the Commons file page. Every other figure is drawn by us.

## Checked, not numbered on the poster

Software:
- `ripser` 0.6.15 (computes every diagram): Tralie, Saul & Bar-On, *Ripser.py: A Lean
  Persistent Homology Library for Python*, J. Open Source Softw. 2018.
  doi:10.21105/joss.00925. Checked against joss.theoj.org.
- GUDHI 3.13.0 (computes every diagram distance): The GUDHI Project, *GUDHI User and
  Reference Manual*, GUDHI Editorial Board, 3.13.0 edition, 2026.
  <https://gudhi.inria.fr/doc/3.13.0/>. Modules: Bottleneck distance (Godi), Wasserstein
  distance (Lacombe & Glisse). Checked against gudhi.inria.fr/doc/latest/_citation.html.
- `networkx` builds the wiring graphs; snnTorch only generates input spikes. Neither is on
  the poster.

Models and training:
- Williams, *Simple statistical gradient-following algorithms for connectionist reinforcement
  learning*, Mach. Learn. 8, 229-256 (1992). doi:10.1007/BF00992696 (REINFORCE, the training
  rule). Checked against cs.utexas.edu/~shivaram/readings.
- Watts & Strogatz, *Collective dynamics of 'small-world' networks*, Nature 393, 440-442
  (1998). doi:10.1038/30918. Checked against ideas.repec.org (Nature v393 i6684).
- Barabási & Albert, *Emergence of scaling in random networks*, Science 286, 509-512 (1999).
  doi:10.1126/science.286.5439.509. Checked against arxiv.org/abs/cond-mat/9910332.
- Eshraghian, Ward, Neftci et al., *Training spiking neural networks using lessons from deep
  learning*, Proc. IEEE 111(9), 1016-1054 (2023). arXiv:2109.12894. **DOI not confirmed.**
  Checked against ieeexplore.ieee.org/document/10242251.

Datasets used earlier, in no poster number:
- IBL brain-wide map (read through ONE, <https://openalyx.internationalbrainlab.org>):
  International Brain Laboratory, *A brain-wide map of neural activity during complex
  behaviour*, Nature 645, 177-191 (2025). doi:10.1038/s41586-025-09235-0. Checked against
  repository.cshl.edu/id/eprint/41978.
- Allen Visual Coding Neuropixels (DANDI dandiset 000021, session 719161530): Siegle, Jia,
  Durand et al., *Survey of spiking in the mouse visual system reveals functional hierarchy*,
  Nature 592, 86-92 (2021). doi:10.1038/s41586-020-03171-x. Checked against ideas.repec.org
  (Nature v592 i7852).

The Steinmetz data is used in the Neuromatch Academy preprocessed form, part 0
(`steinmetz_part0.npz`, OSF `agvxh`). Loader notebook:
<https://nbviewer.org/github/NeuromatchAcademy/course-content/blob/main/projects/neurons/load_steinmetz_decisions.ipynb>

## Unchecked, not on the poster

### Topology of neural activity
- Chaudhuri et al., *The intrinsic attractor manifold and population dynamics of a canonical
  cognitive circuit across waking and sleep*, Nat. Neurosci. 2019. <https://www.nature.com/articles/s41593-019-0460-x>
- Giusti et al., *Clique topology reveals intrinsic geometric structure in neural correlations* (2015).
  <https://arxiv.org/abs/1502.06172>
- Kang, Xu & Morozov, *Evaluating state space discovery by persistent cohomology in the spatial
  representation system*, Front. Comput. Neurosci. 2021.
  <https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2021.616748/full>
- Ayhan et al., *A persistent homology pipeline for the analysis of neural spike train data* (2025).
  <https://arxiv.org/abs/2512.08637>

### Persistent homology (the method)
- Ghrist, *Barcodes: the persistent topology of data*, Bull. AMS 2008.
  <https://www.ams.org/bull/2008-45-01/S0273-0979-07-01191-3/>
- Chazal & Michel, *An introduction to Topological Data Analysis* (2017). <https://arxiv.org/abs/1710.04019>
- Otter et al., *A roadmap for the computation of persistent homology* (2015). <https://arxiv.org/abs/1506.08903>

### Neural trajectories
- Vyas et al., *Computation through neural population dynamics*, Annu. Rev. Neurosci. 2020.
  <https://doi.org/10.1146/annurev-neuro-092619-094115>
- Cunningham & Yu, *Dimensionality reduction for large-scale neural recordings*, Nat. Neurosci. 2014.
  <https://doi.org/10.1038/nn.3776>
- Churchland et al., *Neural population dynamics during reaching*, Nature 2012.
  <https://doi.org/10.1038/nature11129>

### Comparing models with brains
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

### Spiking networks
- Neftci, Mostafa & Zenke, *Surrogate gradient learning in spiking neural networks* (2019).
  <https://arxiv.org/abs/1901.09948>
