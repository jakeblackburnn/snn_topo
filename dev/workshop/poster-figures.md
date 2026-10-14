# Workshop: poster figures
2026-10-13 · status: closed
**Material:** `scripts/poster_figures.py` and the figures it writes to `docs/poster/figures/`, built from `results/analysis/*/activities.csv`, the E18 run and the two grid runs. What each must carry: `docs/poster/core-summary.md:87-103`; numbers and caveats: `docs/poster/results.md`. Sizes assume A0 landscape, three columns (`COLUMN_IN`), 24 pt.

## Problems
| # | problem | status | outcome |
|---|---|---|---|
| 1 | The main figure did not show the headline: "noise and dimension, not holes" (`core-summary.md:88-89`) but no noise panel | settled | four panels: spread, dimension, noise, robust loops |
| 2 | 3D trajectory view: tool, poster figure, or both; model weights were never stored | settled | both; a model is retrained once (about a minute) and its cloud cached |
| 3 | Zoo figure: measure, and a title claiming wiring does not matter over a picture that pooled wirings | settled | longest loop at native size, wiring as marker shape |
| 4 | Rips thickening: balls on a 2D view of a real cloud would not match its 10-D bars | settled | small synthetic cloud; reverses `poster-references.md` thread 4 |
| 5 | Titles claimed more than the panels show | settled | one-sentence claim titles, cut to what is shown |
| 6 | `engagement` draft dropped the mark on session 6 | applied | grey-filled marker, "not significant" in the legend |
| 7 | `nogo` computed `n_configs` and never used it | applied | line deleted |
| 8 | Torus: nothing to decide | applied | plain surface with its two loops; no claim about the enclosed space |
| 9 | Pipeline strip needed an example and a stage count | settled | one engaged-brain population, four stages |

## Threads
### 1. Main figure
Chosen (Jake): four panels, adding trial-to-trial noise, because the first three fall passive > engaged > models and the fourth does not, which is the poster's answer in one row. Set aside: three panels with noise only in the text (the headline word has no picture), and swapping persistence for noise (drops the measure that separates the groups 99% of the time). No-go moves out to its own figure. One matched size only (128 x 100); the 50 x 56 row stays in the draft `results/analysis/snn_vs_bio/main.png`.

### 2. 3D trajectory view
Chosen (Jake): a command for looking at any activity, and one poster figure with passive brain, engaged brain, a 2-choice model and a no-go model. Examples are picked by rule, not by eye: the whole-session population or spiking training nearest its group's median total cluster persistence; both brain examples come from that one session (session 0). Each rebuilt cloud must reproduce its stored diagram to 1e-9 or the script stops; all five rebuilt so far did, including three retrained networks. Set aside: tool only, figure only.

### 3. Zoo figure
Chosen (Jake): the longest loop, one dot per network, marker shape for wiring, so "wiring changes little" is visible. Set aside: the robust-loop share at matched size (most groups are 0 to 2, a nearly empty picture) and the pooled draft. Shown: 128 neurons, the 27 plain configurations; 512 is not pooled in and not drawn.

### 4. Rips thickening
Chosen (Jake): 28 made-up points on a noisy circle, three radii and a barcode that match exactly, labelled an illustration. Set aside: a real cloud projected to 2D (picture and bars disagree), and both. The barcode title says a bar's length is how long the feature lasts, not "long = real": robust features are not what separates brains from models (`results.md:95`).

### 5. Titles
Chosen (Jake): claim titles, softened. "Engagement changes the signature in 11 of 12 held-out sessions"; "Models trained with a third action sit with the engaged brain (8 trainings)"; "Loops appear with adaptive and Izhikevich neurons, mostly in modular networks"; main: "Brains and models differ in spread, dimension and noise, not in robust loops". Set aside: no titles (the PNGs would not stand alone) and the punchier drafts.

### 9. Pipeline strip
Chosen (Jake): the engaged-brain example from thread 2 at four stages: one trial's spikes, the trial average, the path in 3 axes, its bars. Set aside: a second row for a model (doubles the space) and a schematic with no data.

## Changes applied
Confirmed by Jake ("apply all"), 2026-10-13:
- `scripts/poster_figures.py` (new): `fig_main`, `fig_nogo`, `fig_engagement`, `fig_zoo`, `fig_trajectories`, `fig_pipeline`, `fig_rips`, `fig_torus`, and the `trajectory <run_dir> <activity_id>` command.
- `docs/poster/figures/`: the eight figures as PDF and PNG.
- `docs/poster/plan.md` (new) lists each with its panel and caveat.

## Follow-ups (not applied)
- Poster size and layout tool are undecided; every size hangs off `COLUMN_IN` in `scripts/poster_figures.py`.
- The venv's editable install of `snntopo` points at `/home/jake/Code/main/experiments/snn_topo`, which no longer exists; scripts need `PYTHONPATH=<repo>` until Jake reinstalls it.
- The `trajectory` command was run headless only (it builds the cloud and the plot); nobody has looked at the window yet.
- The trajectory and pipeline figures show 3 of 10 axes; if a reader asks, the share of variance is printed on each trajectory panel but not on the pipeline strip.
- 512-neuron zoo networks have no poster figure.
