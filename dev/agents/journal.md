# Journal · 2026-10-13 18:12 · poster-results · 1c6713e
## Start
**State:** `dev/journal.md` ("Oct 13 Part 2"): results and draft figures are done; this session collates poster materials. Jake has a poster doc on his laptop: merge `poster-results` to `main` so he can move it to GitHub, add the doc, and pull it back here.
**Next (carried forward):**
1. Check the † citations in `docs/poster/references.md` and the 39 sessions / 10 mice figure in `datasets.md`.
2. Polish the three poster figures: `results/analysis/snn_vs_bio/main.png`, `bio_overview/e18_engagement.png`, a one-row cut of `zoo_overview/families_ckpt1500.png`.
3. Still open from before: `zoo-blocks` and `stash@{0}` cleanup, E16 population, `grid-measure` branch deletion.
**Traps:**
- Total persistence rises with noise alone, so the persistence, dimension and noise gaps between brain and SNN may be one fact. Nothing run separates them.
- The no-go result is 2 configs, 8 trainings, and their `all` condition averages over a third trial type. A lead, not a finding.
- Brain n in the grid tables counts populations that share 13 sessions; the session is the replicate.
- Zoo grouping by neuron/architecture was chosen after looking; 3 seeds per config.
- SNN-vs-bio is descriptive only (no matched floor, `dev/agents/spec.md:43`): no significance claims.
- `dev/agents/spec.md` is stale (zoo_v1 "dry-run only", no grid specs); `snntopo/data/steinmetz.py:32` comment is wrong.
- Merges here are `--no-ff` with a "Merge <branch>: summary" subject.
**Pointers:**
- `docs/poster/core-summary.md` (the answer and the poster layout), `docs/poster/results.md` (numbers, paths, caveats, rebuild commands).
- `results/runs/20261013-1300-bio_grid`, `results/runs/20261013-1300-zoo_grid`; `scripts/snn_vs_bio.py` `plot_main`.
- `dev/agents/project/notes.md` "Zoo vs bio comparability" and "Poster analysis (2026-10-13)".

## Task: Merge results, respond to Jake's poster doc · 18:12
**Goal:** `main` carries the poster results so Jake can add his laptop doc and pull it here; he then gets a written response to the doc (errors, structure, content), and we start workshopping content resources, references first.
**Now:**
- `poster-results` is 4 commits ahead of `main` (`43c0393`): analysis scripts, `docs/poster/` (6 files), notes, journals. `main` has nothing `poster-results` lacks.
- Uncommitted and Jake's: `.gitignore` (`.nodeterm`), `dev/journal.md` (Part 2 notes).
- Jake's doc is not in the repo yet; its path and format are unknown until he pulls it.
- `docs/poster/references.md` has † entries written from memory, unchecked.
**Scope:**
- In: `--no-ff` merge of `poster-results` into `main`; pause; read the doc once it is here; a response in chat covering factual errors against `results.md`/the CSVs, structure, and content; then `/workshop` on content resources (references first).
- Out: editing Jake's doc in any way (his rule, `dev/journal.md:20`; suggested rewrites go in chat or agent files); pushing; deleting `poster-results`; figure polish; new runs or analysis; poster layout and design.
**Constraints:**
- Never push; Jake moves things to GitHub himself.
- Jake's uncommitted `.gitignore` and `dev/journal.md` stay uncommitted and intact through the merge.
- Every number in the response is checked against `docs/poster/results.md` or `results/analysis/` CSVs, not memory; anything unverifiable is said to be so.
- Assumption: the checkout moves to `main` after the merge, so Jake's pull lands on the branch he pushed.
- Assumption: the workshop record goes in `dev/workshop/<topic>.md`; reference corrections go to `docs/poster/references.md` (agent-written), not into Jake's doc.
**Approach:**
1. Merge in a throwaway worktree (the dirty `dev/journal.md` blocks a plain checkout of `main`), then switch the checkout to `main`; the trees are identical so Jake's edits carry over.
2. Stop. Jake pushes, adds the doc, pulls, and names the file.
3. Read the doc whole; check each claim and number against `results.md`, `core-summary.md` and the CSVs; respond in chat: errors first, then structure, then content, with suggested wording where it helps.
4. Start `/workshop` on content resources: verify the † citations against the sources, then whatever else the doc turns out to need.
**Risks:**
- Jake's pull conflicts with his own uncommitted `dev/journal.md`. Seen as a failed pull; fix is his call (commit or stash).
- A citation gets "verified" from memory again. Each checked entry records the source it was checked against.
- The doc contradicts a recorded caveat (noise confound, no-go n). Flagged as an error, not smoothed over.
**Done when:**
- `git log --oneline -1 main` is a "Merge poster-results: ..." commit, `git diff main poster-results` is empty, and `git status --short` still shows only Jake's two files plus this journal.
- `pytest -q` and `pytest -q -m data` pass on that tree.
- Jake has a chat response to the doc listing each factual error with the source that contradicts it, a proposed structure, and content notes; the doc's `git diff` is empty.
- A workshop file exists with the first settled items on references.
**Open:**
1. Path of the doc once pulled (Jake names it).
