# Journal · 2026-10-13 20:53 · poster-figures · abfab4b
## Start
**State:** `dev/journal.md` ("Oct 13 Session 3"): Jake is unsure how to proceed, wants that settled and the figures workshopped, and wants to speedrun the poster (content Wed, design Thu, finish Fri). Results are final. `poster-results` is merged; Jake's doc `docs/snn_topo.md` is here, vetted, not revised.
**Next (carried forward):**
1. Read Gao et al. 2017 and confirm it defines participation ratio (out of scope this session).
2. Workshop the Models and Results sections of Jake's doc; `docs/poster/model-zoo.md` and `core-summary.md` hold the material.
3. Still open from before: `poster-results`, `grid-measure`, `zoo-blocks` branch cleanup, `stash@{0}`, E16 population.
**Traps:**
- Total persistence rises with noise alone, so the persistence, dimension and noise gaps between brain and SNN may be one fact. Nothing run separates them.
- The no-go result is 2 configs, 8 trainings, and their `all` condition averages over a third trial type. A lead, not a finding.
- Brain n in the grid tables counts populations that share 13 sessions; the session is the replicate.
- Zoo grouping by neuron/architecture was chosen after looking; 3 seeds per config.
- SNN-vs-bio is descriptive only (no matched floor, `dev/agents/spec.md:43`): no significance claims.
- The poster's brain-vs-model comparison is not a diagram distance; Jake's doc currently says otherwise (`docs/snn_topo.md:97-108`).
- Gardner's method is not ours: 1,200 single time points up to H2, against a 150-point trial-averaged path up to H1.
- `dev/agents/spec.md` is stale (zoo_v1 "dry-run only", no grid specs); `snntopo/data/steinmetz.py:32` comment is wrong.
- `main` is ahead of `origin/main` and never pushed by the agent; Jake pushes. Merges here are `--no-ff` with a "Merge <branch>: summary" subject.
**Pointers:**
- `docs/poster/core-summary.md:87-103` (what goes on the poster), `docs/poster/results.md` (numbers and caveats).
- `dev/agents/project/2026-10-13-doc-response.md` (errors in Jake's doc by line), `dev/workshop/poster-references.md` (the nine references, sources, change list).
- `results/runs/20261013-1300-bio_grid`, `results/runs/20261013-1300-zoo_grid`; draft plots in `scripts/snn_vs_bio.py` `plot_main`, `scripts/bio_overview.py` `plot_e18`, `scripts/zoo_overview.py` `plot_families`.

## Task: Poster plan and figure set · 20:53
**Goal:** Jake ends the session with a one-page poster plan (every panel: source, status, day) and poster-ready figure files, so Wednesday is only writing.
**Now:**
- Drafts only: `results/analysis/snn_vs_bio/main.png` (2x3 grid, both matched sizes, 8 pt labels), `bio_overview/e18_engagement.png` (titled "E18", floor/arm jargon in the legend), `zoo_overview/families_ckpt1500.png` (5x2 panels, 35 rotated config labels: unreadable on a poster).
- No background figures exist (Rips thickening, torus, pipeline strip); no trajectory view.
- `results/store/` holds diagrams and split halves, not activities or point clouds: a trajectory must be rebuilt from its recipe (`snntopo/producers.py:123` `bio_activity`, `:215` `snn_activity`, then `snntopo/topology/pipeline.py:15` `build_trajectories`).
- Poster layout is `docs/poster/core-summary.md:87-103`; the reference change list is in `dev/workshop/poster-references.md` "Changes applied".
**Scope:**
- In, in this order (cut from the bottom if time runs out):
  1. Poster plan: `docs/poster/plan.md`, a table of panels (text source, figure file, status, which day), plus the Wed/Thu/Fri split.
  2. Apply the reference change list (`docs/poster/references.md`, `datasets.md:43-44`, `docs/learn/06-literature.md`); close that workshop.
  3. `/workshop` the figures one at a time (record: `dev/workshop/poster-figures.md`), then build: main comparison; engagement; zoo (cut to one row); 3D trajectory view; no-go panel; pipeline strip; Rips thickening; torus.
- Out: new runs, sweeps or statistics; editing `docs/snn_topo.md` (suggestions go in chat); poster layout and design; writing the poster text; branch and stash cleanup; Gao 2017.
**Constraints:**
- Figures show only numbers already in `results/analysis/*.csv` and the two grid runs (`results/runs/20261013-1300-{bio,zoo}_grid`); no pooling across `topo_id`/`cmp_id`.
- Draft PNGs in `results/analysis/` stay as they are; poster files go to a new `docs/poster/figures/`.
- Caveats travel with the figures: "descriptive" on the brain-vs-model panels, n shown, the no-go panel says 8 trainings, significance language only on the engagement figure.
- Assumption: A0 landscape, three columns. Each figure's size is one constant, exported as PDF (vector) and 300 dpi PNG, fonts sized to read at 1.5 m (>= 24 pt at print size).
- Assumption: the 3D view is the first 3 PCA components of the trial-averaged trajectory (150 points, coloured by time), chosen by run dir + activity label; static PNG for the poster and an interactive matplotlib window for looking around.
- Commits on a feature branch `poster-figures`; no merge, no push.
**Approach:**
- One new script, `scripts/poster_figures.py`: one function per figure, a shared style block (font sizes, four group colours), reading the CSVs the overview scripts already write. The existing `plot_main` / `plot_e18` / `plot_families` are left alone as drafts.
- Trajectory code first after the three results figures: the same rebuilt point cloud feeds the 3D view, the pipeline strip (real picture at each stage) and the Rips thickening (balls at 3 radii on a 2D projection, bars underneath).
- Workshop each figure with a rendered draft in hand: what claim it carries, what is cut, then build the final. Starting positions: main = one row at 128x100 with the 50x56 row dropped; engagement = plain-word legend, no "E18"; zoo = longest loop only, grouped by neuron model x architecture; no-go = its own small panel, removed from main.
- Torus is a plain parametric surface with the two loops drawn on it.
**Risks:**
- Eight figures is a lot for one evening. The order above is the cut line; the plan doc records what was not reached.
- Rebuilding an SNN activity may mean retraining (weights may not be persisted). Checked before the 3D view is built; if it is over ~30 min the 3D view ships for brain sessions and one freshly trained example model, and that is said on the figure.
- A rebuilt trajectory might not match the stored signature. Checked: its diagram equals the stored one (`results/store/diagrams/`) to 1e-9, else the figure is not used.
- A polished figure drops a caveat. Each one is checked against `core-summary.md:74-85`.
**Done when:**
- `docs/poster/plan.md` lists every poster panel with a text source, a figure path (or "none"), a status, and a day; nothing on it is "TBD" without a named owner.
- `docs/poster/references.md` has the checked/unchecked sections and no † marks; the references workshop status is closed.
- `python scripts/poster_figures.py` regenerates every built figure into `docs/poster/figures/` as PDF and PNG from a clean checkout, with no new run.
- Each built figure: one message, axis labels in plain words, no internal ids ("E18", "R1", `total_persistence`), n visible, readable when the PNG is viewed at 25% zoom.
- Medians printed on the main figure match `docs/poster/results.md` (9.7 / 16.5 / 4.4 / 10.2 at 128x100).
- `python scripts/poster_figures.py trajectory <run> <label>` opens a rotatable 3D view of that activity and its diagram matches the stored one.
- `pytest -q` passes; `git status --short docs/snn_topo.md dev/journal.md dev/main.md` shows no agent edits.
- Figures not reached are listed as such in `plan.md`.
**Open:**
1. Poster size and layout tool (assumed A0 landscape; changes one constant per figure).

## Close · 2026-10-13 21:12 · abfab4b..a8ac066
- **changed:** `scripts/poster_figures.py` (new): eight figures (`main`, `engagement`, `zoo`, `nogo`, `trajectories`, `pipeline`, `rips`, `torus`) and a `trajectory <run_dir> <activity_id>` 3D view; output in `docs/poster/figures/` as PDF and PNG.
- **changed:** `docs/poster/plan.md` (new): every poster panel with its text source, figure, status and day.
- **changed:** `docs/poster/references.md` rewritten into checked and unchecked sections; `docs/poster/datasets.md:43-44` and `docs/learn/06-literature.md` updated; `dev/workshop/poster-references.md` closed.
- **changed:** `dev/workshop/poster-figures.md` (new, closed): the figure decisions. `dev/agents/project/notes.md`: "Poster figures" section.
- **why:** Jake wanted the way forward settled and the figures workshopped so Wednesday is only writing.
- **verified:** `PYTHONPATH=. python scripts/poster_figures.py` → all eight written, each PNG looked at; medians on `main` are 16.5 / 9.7 / 4.4 and on `nogo` 10.2, matching `docs/poster/results.md:81`. Five rebuilt clouds (two brain, three retrained networks) reproduced their stored diagrams. `pytest -q` → 196 passed, 13 deselected.
- **not verified:** the `trajectory` window (run with `MPLBACKEND=Agg` only, exit 0); `pytest -q -m data` not run; the figures at print size; Gao 2017 (unread, its title in `references.md` is from memory).
- `c836cdb` Poster figures, plan and checked references (also carries the two `dev/workshop/` records, which should have gone in the journal commit)
- `a8ac066` notes: Oct 13 session 3, figure out next steps, workshop figures (Jake)

### Next
1. Jake writes panels 1 to 6 and 12 of `docs/poster/plan.md`; the agent vets each against `docs/poster/results.md`.
2. Read Gao et al. 2017 (bioRxiv 10.1101/214262): confirm the title, that it defines participation ratio, and the task-complexity claim.
3. Jake opens the `trajectory` view once and looks at the eight PNGs; changes go through `scripts/poster_figures.py`.
4. Thursday: pick poster size and tool, set `COLUMN_IN`, rebuild; decide whether the `trajectories` panel stays.
5. Merge `poster-figures` to `main` on Jake's OK. Older cleanup still open: `poster-results`, `grid-measure`, `zoo-blocks`, `stash@{0}`, E16 population.
### Traps
- `import snntopo` fails from scripts: the venv's editable install points at a path that no longer exists. Use `PYTHONPATH=.`.
- `results/analysis/` is gitignored: the figures rebuild only where those tables exist, and an empty cloud cache costs about three minutes of retraining.
- Jake's `dev/journal.md` for this session replaced the earlier Oct 13 entries, including the agent's two Results notes; they are in git history (`abfab4b`).
- The science traps in the Start section above all still hold.
### Pointers
- `docs/poster/plan.md` (start here), `docs/poster/figures/`, `scripts/poster_figures.py` (`examples()` picks the example populations, `cloud()` rebuilds and checks them).
- `dev/workshop/poster-figures.md` (why each figure looks the way it does), `dev/agents/project/notes.md` "Poster figures".
