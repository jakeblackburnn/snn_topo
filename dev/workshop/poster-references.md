# Workshop: poster references
2026-10-13 · status: open
**Material:** `docs/poster/references.md` (agent-written list, 9 entries marked † as written from memory); `docs/snn_topo.md` (Jake's poster doc, never edited by the agent; it has two `**cite**` markers at `:9` and `:57` and five figure placeholders).

## Problems
| # | problem | status | outcome |
|---|---|---|---|
| 1 | Which references go on the poster: `references.md:84-86` names 8, chosen before the results; none backs the finding that carries the poster (dimension and noise), and Gardner 2022 was only ever read from a summary | settled | 9 references, one per claim, table in thread 1; Gao 2017 still has to be read |
| 2 | Software credits: the code calls the `ripser` Python package (`snntopo/topology/pipeline.py:47`), not Bauer's C++ Ripser directly, and GUDHI computes every diagram distance (`snntopo/topology/stats.py:132-134`) but is not in the list | settled | one tools line on the poster; full entries in `references.md` |
| 3 | The entries not marked † were copied from `docs/learn/06-literature.md` and `dev/agents/project/learning/reading.md`, never checked against the sources | settled | split `references.md` into checked and unchecked; check on promotion |
| 4 | Figure credits: `docs/snn_topo.md:27` credits Crane and Segerman "via wikipedia", unchecked, licence unknown; `:36`, `:52`, `:53` have no source yet | settled | mug credit confirmed (CC BY-SA 3.0); the rest drawn by us, Möbius dropped |
| 5 | The 9 † entries lack year, venue and DOI | change list | all 9 confirmed on title and authors; details below |
| 6 | `docs/snn_topo.md:57` needs a Neuropixels citation and the list has none | change list | Jun et al. 2017 confirmed, add it |
| 7 | IBL and Allen entries sit under "Datasets" although no poster number uses them (`core-summary.md:101`) | change list | move under a "not on the poster" heading |

## Threads
### 1. Which references go on the poster (settled, one check outstanding)
**Settled (Jake, 2026-10-13):** about 8 references, each backing a specific sentence or box, numbered short form; the full list stays in `references.md`. Set aside: a 5-plus-QR-code list, and printing everything.
**Settled:** Gardner 2022 stays, on condition it was read. It now has been, from the Europe PMC full text (PMC8810387, the XML itself, not a summary). Nature 602, 123-128 (2022).
- What `docs/learn/06-literature.md:71-83` says holds: 66 to 189 grid cells per module, six principal components, four long bars (one H0, two H1, one H2), 1,000 spike-time-rotation shuffles (P < 0.001), torus in 5 of 6 modules in REM and 4 of 6 in slow-wave sleep.
- What that file could not confirm, now read: the cloud is 1,200 points, each a single 10 ms time point (not a trial average), picked from the 15,000 most active by a density-based rule. Spikes are smoothed (Gaussian, 50 ms) and z-scored first. Distances come from UMAP's neighbourhood graph, not straight-line distance. Ripser, coefficients mod 47. Three rats, medial entorhinal cortex.
- Safe poster wording: "persistent homology recovered a predicted torus in rat grid-cell activity". Not safe: any suggestion that their method and ours are the same; theirs measures single time points up to H2, ours a trial-averaged path up to H1.

**Settled:** the dimension finding is backed by Gao et al. 2017 (Jake). Cunningham & Yu 2014 set aside: general, says nothing about task complexity.
**Settled:** trimming was left to the agent ("whatever makes sense"). Out: Maheswaranathan 2019 (no poster sentence rests on it) and Neftci 2019 (surrogate gradients become a phrase in the models box). Both stay in `references.md`. Izhikevich stays: dropping it leaves one of the two loop-producing neuron models uncredited.

**The set (9), one per claim:**
| # | claim on the poster | reference | checked against |
|---|---|---|---|
| 1 | the brain data | Steinmetz, Zatka-Haas, Carandini & Harris, Nature 576, 266-273 (2019). doi:10.1038/s41586-019-1787-x | PMC6913580 |
| 2 | the probe | Jun et al., Nature 551, 232-236 (2017). doi:10.1038/nature24636 | pubmed 29120427 |
| 3 | why topology for neural activity | Curto, Bull. AMS 54(1), 63-78 (2017). arXiv:1605.01905 | arxiv.org/abs/1605.01905 |
| 4 | topology has found real structure in a brain | Gardner et al., Nature 602, 123-128 (2022). doi:10.1038/s41586-021-04268-7 | PMC8810387 full text |
| 5 | the method | Bauer, J. Appl. Comput. Topol. 5, 391-423 (2021). doi:10.1007/s41468-021-00071-5 | thread 5 |
| 6 | robust count | Fasy, Lecci, Rinaldo, Wasserman, Balakrishnan & Singh, Ann. Stat. 42(6), 2301-2339 (2014). doi:10.1214/14-AOS1252 | arxiv.org/abs/1303.7117 |
| 7 | adaptive neuron | Bellec et al., NeurIPS 2018. arXiv:1803.09574 | thread 5 |
| 8 | Izhikevich neuron | Izhikevich, IEEE Trans. Neural Netw. 14(6), 1569-1572 (2003). doi:10.1109/TNN.2003.820440 | thread 5 |
| 9 | dimension separates brain from model | Gao, Trautmann, Yu, Santhanam, Ryu, Shenoy & Ganguli, bioRxiv 2017. doi:10.1101/214262 | title, authors and DOI only (search result) |

**Not done:** Gao's text was not read. bioRxiv returned HTTP 429 twice, so whether it defines participation ratio, and its claim that task complexity bounds dimension, are unconfirmed. It must be read before the poster leans on it.

**Side result, from the Steinmetz paper (PMC6913580):** "39 sessions in 10 mice" is right, which clears the unchecked figure at `docs/poster/datasets.md:43-44`. The task description there also holds: stimuli on the left, right, both or neither; hold still for 1.5 s when nothing is shown; passive replay after the task.

### 5. † entries (no alternative: checked, goes to the change list)
Each checked by web search on 2026-10-13; the source is the page that confirmed it.

| entry | confirmed as | checked against |
|---|---|---|
| IBL | International Brain Laboratory, *A brain-wide map of neural activity during complex behaviour*, Nature 645, 177-191 (2025). doi:10.1038/s41586-025-09235-0 | repository.cshl.edu/id/eprint/41978 |
| Siegle | Siegle, Jia, Durand et al., *Survey of spiking in the mouse visual system reveals functional hierarchy*, Nature 592, 86-92 (2021). doi:10.1038/s41586-020-03171-x | ideas.repec.org (Nature v592 i7852) |
| Ripser | Bauer, *Ripser: efficient computation of Vietoris-Rips persistence barcodes*, J. Appl. Comput. Topol. 5, 391-423 (2021). doi:10.1007/s41468-021-00071-5. arXiv:1908.02518 | arxiv.org/abs/1908.02518, mediatum.ub.tum.de |
| Bellec | Bellec, Salaj, Subramoney, Legenstein & Maass, *Long short-term memory and learning-to-learn in networks of spiking neurons*, NeurIPS 2018. arXiv:1803.09574 | arxiv.org/abs/1803.09574, igi-web.tugraz.at |
| Izhikevich | Izhikevich, *Simple model of spiking neurons*, IEEE Trans. Neural Netw. 14(6), 1569-1572 (2003). doi:10.1109/TNN.2003.820440 | brian2.readthedocs.io (Izhikevich_2003) |
| Williams | Williams, *Simple statistical gradient-following algorithms for connectionist reinforcement learning*, Mach. Learn. 8, 229-256 (1992). doi:10.1007/BF00992696 | cs.utexas.edu/~shivaram/readings |
| Watts & Strogatz | *Collective dynamics of 'small-world' networks*, Nature 393, 440-442 (1998). doi:10.1038/30918 | ideas.repec.org (Nature v393 i6684) |
| Barabási & Albert | *Emergence of scaling in random networks*, Science 286, 509-512 (1999). doi:10.1126/science.286.5439.509 | citedrive.com, arxiv.org/abs/cond-mat/9910332 |
| Eshraghian | Eshraghian, Ward, Neftci et al., *Training spiking neural networks using lessons from deep learning*, Proc. IEEE 111(9), 1016-1054 (2023). arXiv:2109.12894. DOI not confirmed. | proceedingsoftheieee.ieee.org, ieeexplore.ieee.org/document/10242251 |

None was wrong. What was missing: the IBL entry had no venue or year; the rest had no volume, pages or DOI.

### 6. Neuropixels (no alternative)
Jun, Steinmetz, Siegle et al., *Fully integrated silicon probes for high-density recording of neural activity*, Nature 551, 232-236 (2017). doi:10.1038/nature24636. Checked against pubmed.ncbi.nlm.nih.gov/29120427.

### 2. Software credits (settled)
Chosen (Jake): Bauer's Ripser paper is the numbered reference; a small tools line reads "Computed with ripser.py and GUDHI". Set aside: numbering all three (11 references), and citing Ripser alone (leaves the distance library unmentioned).
Full entries for `references.md`:
- `ripser` 0.6.15: Tralie, Saul & Bar-On, *Ripser.py: A Lean Persistent Homology Library for Python*, J. Open Source Softw. 2018. doi:10.21105/joss.00925 (joss.theoj.org).
- GUDHI 3.13.0: The GUDHI Project, *GUDHI User and Reference Manual*, GUDHI Editorial Board, 3.13.0 edition, 2026. https://gudhi.inria.fr/doc/3.13.0/ . Modules used: Bottleneck distance (Godi), Wasserstein distance (Lacombe & Glisse). Checked against gudhi.inria.fr/doc/latest/_citation.html.
- `networkx` builds the wiring graphs (`snntopo/models/connectivity.py:72-74`); snnTorch only generates input spikes (`snntopo/tasks/steinmetz_2afc.py:9`). Neither is on the poster.

### 3. Unchecked entries (settled)
Chosen (Jake): `references.md` gets a checked section (the nine, the software, the other † entries) and an "unchecked, not on the poster" section; an entry is checked when it is promoted to the poster. Set aside: checking all ~20 now (none reaches the poster), and deleting them (loses the reading list).

### 4. Figure credits (settled)
- Mug and donut (`docs/snn_topo.md:27`): Wikimedia Commons `File:Topology_joke.jpg`, by Keenan Crane and Henry Segerman, 8 May 2015, CC BY-SA 3.0. The poster must print the credit and the licence name. Checked against the Commons file page.
- Chosen (Jake): the other background figures are drawn by us: the Rips thickening from one of our own point clouds, the torus with its two loops as a simple drawing. The Möbius strip is dropped (same Betti numbers as a circle; the pipeline cannot tell them apart). Set aside: borrowing and crediting existing figures.
- Drawing them is not part of this workshop (follow-up).

## Changes applied
None. Every thread is settled, but Jake closed the session before confirming the change list, so the status stays open. Proposed, to apply on his confirmation:
- `docs/poster/references.md` (rewrite): a checked section with the nine in numbered short form and the page each was checked against (thread 1); the tools line and full ripser.py and GUDHI entries (thread 2); year, venue and DOI on the old † entries, † marks dropped, Eshraghian marked "DOI not confirmed" (thread 5); IBL and Allen under "not on the poster" (thread 7); the remaining ~20 entries under "unchecked" (thread 3); the old minimum set at `:84-86` replaced by the nine; the mug-and-donut credit (thread 4); Gao flagged "text not read".
- `docs/poster/datasets.md:43-44`: replace "not checked this session" with the confirmed "39 sessions in 10 mice" (PMC6913580).
- `docs/learn/06-literature.md:9-13`, `:71-75`: Gardner was read from the full text; drop the automated-summary caveat and fill in the point count (1,200 single time points).
- `docs/snn_topo.md` is Jake's and is not edited. Suggested to him: `:9` cite Curto 2017; `:57` cite Jun et al. 2017; `:27` credit "Keenan Crane and Henry Segerman, CC BY-SA 3.0".

## Follow-ups (not applied)
- Read Gao et al. 2017 (bioRxiv 10.1101/214262; HTTP 429 twice on 2026-10-13) and confirm it defines participation ratio and makes the task-complexity claim, before the poster leans on it.
- Draw the Rips thickening figure from one of our own point clouds, and the torus with its two loops.
- Confirm the Eshraghian 2023 DOI.
