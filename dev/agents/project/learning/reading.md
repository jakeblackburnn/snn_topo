# Reading list and findings

All links checked 2026-10-09. "fetched" means the page was opened and its title and authors
matched. "Crossref" means the DOI's metadata matched but the publisher page redirected the
fetcher to a login, so the builder should open it again and fall back to the abstract if it
can't. Nothing here is listed from memory alone.

## Core (read on day 2)

| paper | link | check | min | why |
|---|---|---|---|---|
| Curto, *What can topology tell us about the neural code?* (2017, 16 pp) | https://arxiv.org/abs/1605.01905 | fetched | 40 | survey of why and how topology is used on neural data, written for non-specialists |
| Gardner et al., *Toroidal topology of population activity in grid cells*, Nature 2022 | https://www.nature.com/articles/s41586-021-04268-7 | Crossref; licence CC BY 4.0 | 60 | the reference TDA result on population recordings, and the Gardner torus named in the brainstorms as a known-answer dataset |
| Maheswaranathan et al., *Universality and individuality in neural dynamics across large populations of recurrent networks* (2019) | https://arxiv.org/abs/1907.08549 | fetched | 40 | thousands of trained RNNs: geometry depends on architecture, the topological structure of the dynamics doesn't |

## Optional, by block

**Persistent homology**
| paper | link | check | note |
|---|---|---|---|
| Ghrist, *Barcodes: the persistent topology of data*, Bull. AMS 2008 | https://www.ams.org/bull/2008-45-01/S0273-0979-07-01191-3/ | Crossref (DOI 10.1090/S0273-0979-07-01191-3); the author's PDF returned 403 | the classic short introduction |
| Chazal & Michel, *An introduction to Topological Data Analysis: fundamental and practical aspects for data scientists* | https://arxiv.org/abs/1710.04019 | fetched | the best fit for an ML reader |
| Otter et al., *A roadmap for the computation of persistent homology* | https://arxiv.org/abs/1506.08903 | fetched | how it's computed; software comparison |
| Fasy et al., *Confidence sets for persistence diagrams*, Ann. Stat. 2014 | https://arxiv.org/abs/1303.7117 | fetched | the idea behind robust count R1 (`snntopo/floor.py:229`) |

**Topology of neural population activity**
| paper | link | check | note |
|---|---|---|---|
| Chaudhuri et al., *The intrinsic attractor manifold and population dynamics of a canonical cognitive circuit across waking and sleep*, Nat. Neurosci. 2019 | https://www.nature.com/articles/s41593-019-0460-x | Crossref | a ring in head-direction cells |
| Giusti et al., *Clique topology reveals intrinsic geometric structure in neural correlations* (2015) | https://arxiv.org/abs/1502.06172 | fetched | topology of correlation matrices, a different construction |
| Kang, Xu & Morozov, *Evaluating state space discovery by persistent cohomology in the spatial representation system*, Front. Comput. Neurosci. 2021 | https://www.frontiersin.org/journals/computational-neuroscience/articles/10.3389/fncom.2021.616748/full | fetched | how many neurons and how much data the method needs, on simulations |
| Ayhan et al., *A persistent homology pipeline for the analysis of neural spike train data* (2025) | https://arxiv.org/abs/2512.08637 | fetched | a recent pipeline with spike-train distances; already cited in `distance-construction.md` |

**Population dynamics and trajectories**
| paper | link | check | note |
|---|---|---|---|
| Vyas et al., *Computation through neural population dynamics*, Annu. Rev. Neurosci. 2020 | https://doi.org/10.1146/annurev-neuro-092619-094115 | Crossref; a PMC copy (PMC7402639) was found by search and sat behind a captcha | what a neural trajectory is and why people study it |
| Cunningham & Yu, *Dimensionality reduction for large-scale neural recordings*, Nat. Neurosci. 2014 | https://doi.org/10.1038/nn.3776 | Crossref | PCA on trial-averaged population activity |
| Churchland et al., *Neural population dynamics during reaching*, Nature 2012 | https://doi.org/10.1038/nature11129 | Crossref | rotational trajectories: loops in a trial-averaged path |

**Comparing models with brains**
| paper | link | check | note |
|---|---|---|---|
| Kriegeskorte, Mur & Bandettini, *Representational similarity analysis*, Front. Syst. Neurosci. 2008 | https://www.frontiersin.org/articles/10.3389/neuro.06.004.2008/full | fetched | where model-brain comparison started |
| Kornblith et al., *Similarity of neural network representations revisited* (2019) | https://arxiv.org/abs/1905.00414 | fetched | CKA |
| Williams et al., *Generalized shape metrics on neural representations* (2021) | https://arxiv.org/abs/2110.14739 | fetched | comparison as a proper metric |
| Ostrow et al., *Beyond geometry: … dynamical similarity analysis* (2023) | https://arxiv.org/abs/2306.10168 | fetched | comparing dynamics instead of geometry |
| Nejatbakhsh et al., *Comparing noisy neural population dynamics using optimal transport distances* (2024) | https://arxiv.org/abs/2412.14421 | fetched | takes trial noise into the metric |
| Lin & Kriegeskorte, *The topology and geometry of neural representations* (PNAS 2024) | https://arxiv.org/abs/2309.11028 | fetched | a family between geometry and topology |
| Barannikov et al., *Representation topology divergence* (2022) | https://arxiv.org/abs/2201.00058 | fetched | TDA for comparing network representations |
| Sucholutsky et al., *Getting aligned on representational alignment* (2023) | https://arxiv.org/abs/2310.13018 | fetched | a map of the whole area |

**Spiking networks and the data**
| paper | link | check | note |
|---|---|---|---|
| Neftci, Mostafa & Zenke, *Surrogate gradient learning in spiking neural networks* (2019) | https://arxiv.org/abs/1901.09948 | fetched | how these networks are trained |
| Steinmetz et al., *Distributed coding of choice, action and engagement across the mouse brain*, Nature 2019 | https://www.nature.com/articles/s41586-019-1787-x | Crossref | the dataset; "engagement" in the title is what E13-E18 measure |
| Neuromatch loader notebook for the Steinmetz data | https://nbviewer.org/github/NeuromatchAcademy/course-content/blob/main/projects/neurons/load_steinmetz_decisions.ipynb | found by search; fetch returned 429 | field names of the archive this repo downloads (`snntopo/data/steinmetz.py:31, 44-45`) |

## Findings the documents depend on (2026-10-09)

1. **A point is a time bin.** The cloud is a single trial-averaged, smoothed PCA trajectory:
   150 points in at most 10 dimensions, scaled to diameter 1, H0 and H1 only
   (`snntopo/topology/pipeline.py:15-32, 50-65`; `snntopo/contracts.py:115-118`). Essential
   bars are dropped from distances; Wasserstein is order 2 (`snntopo/topology/stats.py:3-4`).
2. **`compare` is a test of "same signature", not "same topology".** Its docstring records the
   false-positive and power measurements (`stats.py:38-52`); the builder quotes them with that
   citation.
3. **Possible wrong comment.** `snntopo/data/steinmetz.py:32` says `WINDOW = slice(50, 200)` is
   "0.5--2.0 s after the stimulus". The Neuromatch description of this archive (search result,
   not opened) says bins are 10 ms and start 500 ms before stimulus onset, which would make the
   window 0 to 1.5 s after onset. Unverified; flag it, don't resolve it.
4. **Training is REINFORCE with a surrogate gradient** (`snntopo/training.py:1`,
   `snntopo/models/neurons.py:2`), not supervised backprop on labels.
5. **No link list existed before this file.** The brainstorms cite about 25 URLs
   (`grep -n 'arxiv\|doi' dev/brainstorm/*/*.md`); they were not rechecked here and are not
   part of this list unless they appear above.
6. **How Gardner et al. build their cloud was not read** (full text unreachable from this
   session). The contrast drawn in `documents.md` (many time points on a manifold vs one
   averaged trajectory) is the packet author's recollection. The builder confirms it from the
   paper before writing it into 06 or 07, or leaves it out.

## Stale sources

- `dev/agents/project/2026-09-22-poster-report.md` predates D28-D38: its yardstick discussion
  and "what's next" are superseded.
- `dev/brainstorm/mega-forward-plan/` (09-23): corrected by
  `dev/brainstorm/snn-tda-dataset/seed-errata.md`. Its "anticonservative null" claim was
  retracted in E12.
- `dev/agents/project/notes.md`, "Science": "prose-reasoned numbers have been wrong". Hence
  the rule that every number is copied from `experiments.md` with its E-number.
- `dev/agents/spec.md` lists zoo_v1 as "dry-run only"; it completed on
  2026-09-28 (`results/runs/20260928-1502-zoo_v1`, `dev/agents/journal.md:3`).
