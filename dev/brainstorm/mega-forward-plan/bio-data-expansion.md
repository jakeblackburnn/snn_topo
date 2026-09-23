# Bio data expansion — options

> Brainstorm notes, 2026-09-23. **Nothing here is a decision.** Options with a recommendation.
> Every cost/availability claim marked ✅ was verified by running something this session; claims
> marked ⚠ are from literature/search and are unverified.

## Recommendation in one paragraph

Do **Tier 0 first, and do it before downloading anything**. Steinmetz's already-cached
`steinmetz_part0.npz` contains 13 sessions (only session 11 is used) and — the find of this
session — a `spks_passive` array: **the same neurons, same session, same bins, recorded during
passive viewing**. That is E4's Allen contrast with lab, animal, probe, unit count, region set and
firing-rate scale all controlled *by construction*, at zero download cost. E4 currently confounds
"task vs. passive" with "different lab / animal / probe / area set", so it cannot tell you which one
it failed on. `spks_passive` can. Then Tier 1: the Gardner grid-cell torus (320 MB, CC0) as the
pipeline's **known-answer positive control** — if `snntopo` cannot recover a published torus, D20 is
a pipeline bug and every negative result so far is uninterpretable. Then MC_Maze (690 MB,
✅ confirmed loadable today with the exact `allen.py` code pattern) as a genuinely different
paradigm/species/area. Scaling IBL 20→459 is the *worst* value-per-effort item on this list despite
looking like the obvious one — it adds ~240 GB and more of the same paradigm, which is not what the
yardstick problem is short of.

**Ranked by value-per-effort:**

| # | Item | New download | Effort | Why |
|---|---|---|---|---|
| 1 | Steinmetz `spks_passive` task-vs-passive | **0 B** ✅ | ~10 lines | Confound-free version of E4 |
| 2 | Steinmetz sessions 0–12 (all of part0) | **0 B** ✅ | 1 tuple | 13× the Steinmetz side, free |
| 3 | Gardner grid-cell torus positive control | 320 MB ✅ | new loader | Known answer: torus, β=(1,2,1) |
| 4 | Within-session condition/epoch splits | 0 B | small | Multiplies every dataset |
| 5 | MC_Maze / NLB macaque reaching | 690 MB ✅ | ~`allen.py` clone | New species/area/paradigm, 2295 trials |
| 6 | Steinmetz parts 1–2 (26 more sessions) | ~175 MB ⚠ | 1 line | 39 sessions total |
| 7 | Allen Visual Coding, 31 more sessions | ~9 GB ranges ✅ | small | Widens the held-out probe from n=1 |
| 8 | Per-region entries — **Steinmetz only** | 0 B ✅ | medium | See the trap in §8 |
| 9 | Peyrache HD ring attractor (DANDI 000056) | 208 GB ⚠ | new alignment | 2nd known-topology control, but no trials |
| 10 | Allen Visual Behavior Neuropixels (000713) | 4.8 TB ⚠ | medium | Allen task-vs-passive, same rig |
| 11 | Full IBL BWM 459 sessions | ~240 GB ✅ | small | Lowest value-per-byte here |

---

## 1. Tier 0 — data already on this disk (zero download)

### 1a. `spks_passive`: a within-session task-vs-passive contrast ✅

Verified on the cached `data/raw/steinmetz/steinmetz_part0.npz`, session 11:

```
spks          (698, 340, 250) int8   <- active 2AFC trials, currently the only thing loaded
spks_passive  (698, 110, 250) int8   <- SAME 698 neurons, passive replay, same 10 ms bins
active_trials (450,) bool            <- 340 active + 110 passive = one interleaved recording
contrast_left_passive / contrast_right_passive (110,)  <- passive stimulus labels
```

Why this matters more than anything else in this document: **E4's Allen contrast varies at least four
things at once** — task engagement, animal, lab/rig, and recorded area set. It failed. The project
then spent E5–E11 trying to control three of those four post hoc (region, unit count, trial count,
raw diameter) and failed every time. `spks_passive` controls all of them *by construction* and
leaves exactly one variable free: task engagement.

Two readings of the result, both informative:
- Passive **separates** from active within-session → the pipeline can detect the engagement axis,
  and E4's failure is about cross-lab/cross-animal nuisance, which is a fixable measurement problem.
- Passive **does not separate** even here → persistent homology of trial-averaged PCA trajectories
  does not resolve task engagement at this scale, full stop. That is a much stronger, cleaner
  negative claim than E4's, and it is exactly the claim the honest-negative reframe needs
  (see the `scientific-reframe.md` fork).

Caveats to preregister before running it, not after:
- 110 passive vs. 340 active trials — `compare()` already equalizes to `h = min//2 = 55`, so this is
  handled, but it is a trial-count difference and D25 showed trial count matters. Consider
  subsampling active to 110 as the preregistered primary and using the full 340 as a secondary.
- Passive trials have no choice, so the condition set is `all` (+ contrast-based splits), not
  `left`/`right`. The comparison is `all`-vs-`all`, the same condition E9/E10 analysed.
- Passive blocks are typically recorded *after* the task block, so drift/fatigue is confounded with
  engagement. Not fatal, but it belongs in the writeup as a stated limit.

Loader shape: `DatasetEntry` stretches without a contract change if passive becomes a separate
session id, e.g. `load("11")` and `load("11/passive")` — `steinmetz._session_data` already parses the
id, so it grows a `"/passive"` suffix check and swaps `spks`→`spks_passive`,
`contrast_*`→`contrast_*_passive`. ~10 lines. Alternative shape: add `"passive"` as a *condition*
mask on the existing Activity — **rejected**, because `Activity.spikes` is one `(neurons, trials,
bins)` array and active/passive have different trial counts; concatenating them along trials would
work but silently changes what `"all"` means in every existing result.

### 1b. Steinmetz is 13 sessions on disk, not 1 ✅

`steinmetz_part0.npz` (87 MB, already downloaded) decodes to **13 sessions**, 4 mice:

```
 0 Cori       units= 734 trials=214  L= 71 R= 69 nogo= 74  areas= 8
 1 Cori       units=1070 trials=251  L= 82 R= 75 nogo= 94  areas= 5
 2 Cori       units= 619 trials=228  L= 57 R= 94 nogo= 77  areas=11
 3 Forssmann  units=1769 trials=249  L= 51 R= 72 nogo=126  areas=11
 4 Forssmann  units=1077 trials=254  L= 53 R= 97 nogo=104  areas=10
 5 Forssmann  units=1169 trials=290  L= 85 R=113 nogo= 92  areas= 5
 6 Forssmann  units= 584 trials=252  L= 74 R=116 nogo= 62  areas= 8
 7 Hench      units=1156 trials=250  L= 99 R= 58 nogo= 93  areas=15
 8 Hench      units= 788 trials=372  L=146 R= 92 nogo=134  areas=12
 9 Hench      units=1172 trials=447  L=191 R=101 nogo=155  areas=13
10 Hench      units= 857 trials=342  L=126 R=119 nogo= 97  areas= 6
11 Lederberg  units= 698 trials=340  L=135 R=141 nogo= 64  areas=12  <- the only one used today
12 Lederberg  units= 983 trials=300  L=137 R=107 nogo= 56  areas=15
```

`DATASETS["steinmetz"].reference_sessions` is `("11",)`. Widening it to all 13 is a **one-tuple
change** and costs nothing. Note the unit counts (584–1769) are 3–20× IBL's probe00 counts
(32–302) — so Steinmetz is the dataset with population sizes large enough for the per-region
splitting in §8, and IBL is not.

It also gives a **second within-dataset bio-vs-bio range** from a different lab than IBL. Today the
"bio-vs-bio yardstick" is essentially an IBL-only construct (20 IBL sessions, 1 Steinmetz, 1 Allen).
A 13-session Steinmetz range that can be compared against the 20-session IBL range is an independent
replication of D20's core measurement — cheap, and it tests whether the range width is a property of
IBL's recordings or of the method.

### 1c. Steinmetz parts 1 and 2 — 26 more sessions, ~175 MB ⚠

Only `part0` is on disk; `list_sessions()` downloads all three when first called. The NMA release is
⚠ ~39 sessions total across the three parts. Two OSF fetches, no code change (`_download` already
handles parts). Cheap enough to just do alongside 1b.

### 1d. Behavioral covariates already in the cached file ✅

Session 11 carries, unused: `pupil (3,340,250)`, `wheel (1,340,250)`, `licks (1,340,250)`,
`reaction_time (340,2)`, `prev_reward (340,1)`, `feedback_type (340,)`, and `ccf (698,3)` CCF
coordinates per unit. These are the raw material for §7's within-dataset variation and for the
spatially-embedded model comparison the `model-zoo.md` fork raises (per-unit 3D coordinates let you
compare a spatially-embedded RNN's wiring geometry against real anatomy, not just its topology).

---

## 2. Known-topology positive controls — argued as the top external priority

**The argument.** D20 says the instrument does not discriminate Allen from 2AFC. There are two
explanations and the project currently cannot distinguish them: (a) the biology's topology really is
similar at this scale; (b) the measurement chain is broken/underpowered somewhere between
trial-averaging, PCA to 10 components, unit-diameter normalization, Rips at full diameter,
Wasserstein-2, and a 50-resample split-half null. Five failed fixes (E5–E11) have been searching
within explanation (a)'s framing. **A positive control settles it.** Until one passes, every negative
result in `dev/experiments.md` is ambiguous, and a poster claiming a negative finding is not
defensible. I would rank this above every other item except the free Tier 0 ones.

### 2a. Gardner et al. 2022 — grid cells, toroidal topology ✅ 320 MB, CC0

- Data: [figshare 16764508](https://figshare.com/articles/dataset/Toroidal_topology_of_population_activity_in_grid_cells/16764508),
  DOI [10.6084/m9.figshare.16764508.v6](https://doi.org/10.6084/m9.figshare.16764508) — ✅ verified
  via the figshare API: a **single 319.9 MB zip**, licence **CC0** (no attribution constraints at
  all). Code: [github.com/erikher/GridCellTorus](https://github.com/erikher/GridCellTorus).
  Paper: Gardner et al., *Toroidal topology of population activity in grid cells*, Nature 602 (2022),
  [doi:10.1038/s41586-021-04268-7](https://doi.org/10.1038/s41586-021-04268-7).
- Content ⚠: Neuropixels MEC recordings from 3 rats (Q, R, S; R × 2 sessions), open-field foraging,
  ~64 min/session. Exact in-zip variable names unverified — the figshare README/zip needs opening
  before committing to a loader.
- **The published answer is Betti numbers (1, 2, 1)** — a torus. That is a concrete, preregisterable
  acceptance criterion: does this pipeline's H1 on this data find 2 significant loops?
- Honest caveat, and it is a big one: Gardner's own pipeline is *not* this pipeline. They use
  spike-count vectors per time bin, dimensionality reduction tuned for it, and they analyse
  **single-trial-free continuous** activity, not trial-averaged trajectories. So a failure could
  legitimately mean "trial-averaged PCA trajectories destroy the torus", which is itself the most
  useful possible finding for this project — it would localize D20 to the `build_trajectories` step
  rather than to topology. Design the control to be informative *either way*: run the pipeline both
  in its native trial-averaged mode and in a continuous/untrial-averaged mode, and report both.
- Loader shape: this has **no trials**. The `Activity` contract needs `(neurons, trials, bins)` plus
  named boolean trial masks. Options: (i) chop the continuous recording into pseudo-trials by time
  and let `"all"` be every pseudo-trial — preserves the contract, probably destroys the torus by
  averaging across position; (ii) bin by the animal's *position/phase* rather than by time, so each
  "trial" is a pass through a region of the torus — preserves the topology but stretches what
  `window`/`bin_size_s` mean; (iii) accept it as an activity-only entry through
  `atlas.measure_activity` without going through `DatasetEntry` at all. Option (iii) is the smallest
  change and is what the `model-zoo.md` fork also lands on for synthetic generators — worth
  coordinating so there is one "activity-only entry" path, not two.

### 2b. Peyrache HD ring attractor — DANDI 000056 ⚠ 208 GB

[dandiset 000056](https://dandiarchive.org/dandiset/000056), "Internally organized mechanisms of the
head direction sense" (Peyrache et al., Nat Neurosci 2015,
[doi:10.1038/nn.3968](https://doi.org/10.1038/nn.3968)). Published answer: a **ring**, β=(1,1) —
see also Chaudhuri et al. 2019, [doi:10.1038/s41593-019-0460-x](https://doi.org/10.1038/s41593-019-0460-x).
Simpler expected topology than the torus, so a weaker but easier control. 208 GB total, though
remfile range reads mean the actual cost is per-session, not per-dandiset. Same no-trials alignment
problem as 2a, same options. **Lower priority than 2a** — CC0 + 320 MB + a richer expected answer
makes Gardner strictly better as the first control.

### 2c. Grid cells, DANDI 000582 ⚠ 1.9 GB

"Conjunctive Representation of Position, Direction, and Velocity in Entorhinal Cortex" —
[dandiset 000582](https://dandiarchive.org/dandiset/000582), CC-BY-4.0, ✅ verified 118 NWB files /
1.86 GB / 15 rats, tetrode recordings with LED position tracking. Cheap, but tetrode-scale unit
counts are small and the toroidal claim is Gardner's, not this dataset's. A supplement to 2a, not a
substitute.

### 2d. Synthetic positive controls — cheaper than all of the above

Not a bio dataset, so out of my scope, but it belongs in the same argument: a point cloud sampled
from a known circle/torus, pushed through `compute_signature` + `compare`, costs nothing and
validates the persistence + distance half of the chain. It does **not** validate the
trial-averaging/PCA half, which is where I'd bet the problem is. See `model-zoo.md` — the two forks
converged on this independently, which is itself a signal.

---

## 3. New paradigms — verified availability

All DANDI items below are ✅ **CC-BY-4.0** (verified via the DANDI API) and ✅ reachable from this
machine's Python 3.14 — `dandi 0.80.0`, `pynwb 4.2.0`, `h5py 3.16.0`, `remfile 0.1.14` are all
installed and I read a remote NWB with them this session. `allensdk`'s 3.14 incompatibility does
**not** generalize; the `h5py`+`remfile` pattern in `allen.py` is a working universal loader for
DANDI NWB.

### 3a. Neural Latents Benchmark — macaque reaching ✅ **verified loadable**

| dandiset | name | total size | units | trials |
|---|---|---|---|---|
| [000128](https://dandiarchive.org/dandiset/000128) | MC_Maze (M1/PMd, delayed reach w/ barriers) | 0.7 GB ✅ | **182** ✅ | **2295** ✅ |
| [000127](https://dandiarchive.org/dandiset/000127) | Area2_Bump (S1 area 2, reach + perturbation) | 1.8 GB ✅ | ⚠ ~65 | ⚠ |
| [000129](https://dandiarchive.org/dandiset/000129) | MC_RTT (M1, self-paced random-target) | 0.1 GB ✅ | ⚠ | ⚠ (continuous) |
| [000130](https://dandiarchive.org/dandiset/000130) | DMFC_RSG (DMFC, Ready-Set-Go timing) | <0.1 GB ✅ | ⚠ | ⚠ |

I opened `sub-Jenkins/sub-Jenkins_ses-full_desc-train_behavior+ecephys.nwb` (0.69 GB) over HTTP
range reads and read its structure directly:

```
units  cols: spike_times, spike_times_index, electrodes, heldout, obs_intervals   n_units=182
trials cols: start_time, stop_time, go_cue_time, move_onset_time, target_pos, active_target,
             maze_id, barrier_pos, num_barriers, num_targets, delay, rt, success, trial_type, split
n_trials = 2295
```

`spike_times` + `spike_times_index` is **exactly** the layout `allen.py` already unpacks, and
`intervals/trials` is exactly what `ibl.py` builds masks from. So the loader is a clone of
`allen.py` with three edits: the asset URL, the interval table name, and the condition construction.
No `nlb_tools` dependency needed.

What it adds that nothing currently in the atlas does:
- **Different species** (macaque), **different area** (M1/PMd motor, vs. all-visual today),
  **different modality** (movement production, not perception/choice).
- **2295 trials** — 5–10× any current session (IBL 420–1014, Steinmetz 214–447). Trial count is a
  known dominant nuisance (D25), so a dataset with trials to spare lets you *subsample to match* any
  other session rather than being stuck at its native count. That is a genuinely new degree of
  freedom for the matching work, and arguably worth the download on its own.
- Condition masks fall out of `active_target` (discrete reach directions) or `maze_id` — a
  many-condition structure like Allen's orientations, which the `Signature` dict already supports.
- Motor cortex reaching is the single most-studied population-geometry system (rotational dynamics,
  Churchland et al.), so there are published expectations to check against — a *soft* positive
  control, weaker than §2 but free with the data.

### 3b. Allen Visual Behavior Neuropixels — DANDI 000713 ⚠ 4.8 TB

[dandiset 000713](https://dandiarchive.org/dandiset/000713), CC-BY-4.0, ✅ 4293 assets / 4761 GB.
Scientifically this is the **best cross-check on Tier 0's finding**: same institute, same rig, same
probe type, same visual areas as Visual Coding (000021) — but the mice are performing a change-detection
*task*. So "Allen passive (000021) vs. Allen active (000713)" is the task-engagement contrast with
lab/rig/area controlled, at population sizes far larger than Steinmetz. It is the scaled-up
confirmation of §1a.
Cost is manageable *because of remfile*: you never download 4.8 TB, you range-read the units and
intervals tables of the ecephys session files you pick. ⚠ The asset listing mixes `_image.nwb`
(behavior/video) with ecephys files; identifying the ecephys subset is unverified work.

### 3c. Everything else, briefly ⚠

Searched DANDI; reporting honestly which are worth it:
- **Zebrafish whole-brain** — [000350](https://dandiarchive.org/dandiset/000350) (5.9 TB, Mu et al.
  glia/futility). Whole-brain, but calcium imaging, not spikes: `Activity` expects spike counts, and
  ΔF/F has a totally different noise model that would invalidate the split-half null's assumptions.
  **Skip** unless the project decides to handle calcium explicitly.
- **C. elegans** — [000692](https://dandiarchive.org/dandiset/000692) (80 GB, whole-brain
  spontaneous GCaMP + NeuroPAL), [000565](https://dandiarchive.org/dandiset/000565) (46 GB),
  [000541](https://dandiarchive.org/dandiset/000541). ~100–200 neurons with *identified cell
  identities* across animals — uniquely, the neurons are the same across recordings, so cross-animal
  comparison means something it never means in mouse. Genuinely interesting, but calcium again, and
  no trial structure. **Low priority, high novelty.**
- **Human/NHP Neuropixels** — [000397](https://dandiarchive.org/dandiset/000397) (24 GB),
  [001282](https://dandiarchive.org/dandiset/001282) (59 GB, NHP insertions). ⚠ unexamined trial
  structure. Interesting as a "does topology transfer across species" axis; not urgent.
- **Human intracranial naturalistic** — [000055](https://dandiarchive.org/dandiset/000055) AJILE12,
  846 GB, ECoG not single units. **Skip** — different signal type entirely.
- **MICrONS / connectomics** — structural, not population activity. Relevant to the *model* side
  (wiring priors for the connectivity axis) rather than to bio atlas entries. Belongs in
  `model-zoo.md`, not here.
- **Spontaneous/resting state** — no clean dandiset found in one pass, but note §1a's
  `spks_passive` and §7's pre-stimulus windows already give a spontaneous-ish contrast for free.

---

## 4. Scaling IBL 20 → 459 — the cost table, and why it ranks last

✅ Measured on this machine:

```
data/raw/ibl/one          12 GB   <- raw ONE downloads for ~23 sessions  (~520 MB/session)
data/raw/ibl/*.npz        50 MB   <- the compact binned caches            (~2.2 MB/session)
                                     range 0.42 MB .. 5.97 MB
```

**The npz is ~1/240th the size of the raw download it was built from.** That single ratio decides
this item:

| approach | 459 sessions | notes |
|---|---|---|
| naive (keep ONE cache, as today) | **~240 GB** | 801 GB free, so it *fits*, but it is 26% of the disk |
| prune ONE cache per session after the npz is written | **~1 GB** | 459 × ~2.2 MB |

So the storage objection is removable with a small change to `_download_processed` (delete the
downloaded `.npy`/`.pqt` files for a session once its npz exists). Download *time* remains: ~520 MB ×
459 ≈ 240 GB over the wire regardless, one-shot.

The real cost is **compute, and it is quadratic**: `snntopo baseline` is O(n²) in sessions and takes
~12 min at 22 sessions with raw data cached (journal Traps). Pairs go 231 → 105 111, a **455×**
increase, i.e. ~91 hours of CPU for one full baseline, and that is *per `TopoConfig`*. Every
reanalysis since E5 has re-derived from `results/baseline-wide/`; at 459 sessions each such
re-derivation becomes a multi-day job. This is squarely the `data-platform.md` fork's problem
(incremental, dedup'd, content-addressed pairwise storage) and IBL scaling should probably wait
behind it.

**Why it ranks last despite being the obvious move:** 459 IBL sessions are 459 samples of *the same
paradigm* (visual 2AFC, mouse, probe00). D20 is not a "too few samples of one condition" problem —
widening 3→20 sessions **widened** the range rather than tightening it (SPEC Validity). More of the
same paradigm plausibly widens it further. The yardstick is short of *contrast classes*, not sample
count. A cheaper, better-targeted version: take **60–80** IBL sessions (enough to stabilise the range
estimate, ~20 GB pruned to ~180 MB, ~2.5 h baseline) rather than all 459.

---

## 5. Allen Visual Coding — 1 → 32 sessions ✅ cheap

✅ Verified via the DANDI API: dandiset 000021 has **214 assets**, of which **32 are session-level**
`sub-*_ses-*.nwb` files (the rest are per-probe LFP), mean **2.51 GB**, 80.5 GB total, CC-BY-4.0.

The current loader never downloads a whole file — `remfile` + `DiskCache` pulled only **273 MB** of
byte ranges for session 719161530 (✅ `data/raw/allen` is 273 MB). Extrapolating, **all 32 sessions ≈
9 GB of cached ranges**, and 32 npz outputs at ~3 MB each.

Loader shape change: `allen.py` hardcodes `SESSION_ID = "719161530"` and a single `ASSET_URL`
constant. It needs a session→asset-URL map, which the DANDI assets API supplies
(`/api/dandisets/000021/versions/draft/assets/`). Either fetch-and-cache that listing (like
`ibl.list_sessions()` caches its session JSON — there is already a pattern to copy) or freeze the 32
`(session_id, asset_id)` pairs into a module constant. The frozen-tuple version matches
`ibl.REFERENCE_SESSIONS`'s existing style and avoids a network call in `list_sessions()`.

**Why it matters disproportionately:** Allen is the *held-out discriminative probe*. Right now that
probe is **n = 1 session**. Every E4/E11 verdict rests on one Allen session's position relative to a
20-session IBL range. With 32 Allen sessions the check becomes a distribution-vs-distribution
comparison (ROC/AUC between the Allen-vs-2AFC distances and the within-IBL distances) instead of
"does one point fall inside an interval". That is a strictly better-powered version of the *same*
preregistered check, and it connects directly to the `distance-construction.md` fork's point about
re-framing the criterion as an effect size rather than an interval-containment test.

---

## 6. Loader/contract shape — does `DatasetEntry` stretch?

`DatasetEntry(load, list_sessions, reference_sessions, description)` with
`load: Callable[[str], BioSession]`. Findings:

- **New trial-structured NWB dataset (MC_Maze, more Allen): stretches fine.** No contract change. A
  new module in `snntopo/data/`, one `DATASETS` entry. ✅ MC_Maze's NWB layout is confirmed
  compatible.
- **Sub-session entries (passive, per-region, per-epoch, per-behavioral-state): stretch via
  composite session ids** — `load("11/passive")`, `load("11/VISp")`, `load("11/engaged")`. `load`
  already takes an opaque string and `steinmetz._session_data` already parses it. This needs **zero**
  contract change and keeps `entry_id = f"bio:{dataset}:{session_id}"` unique and readable. The cost
  is that `list_sessions()` has to enumerate the composite ids (or not enumerate them, and let
  `reference_sessions` name them explicitly — note `ibl.load` currently *validates* against
  `list_sessions()`, so that check would need relaxing).
  The alternative — a new `sub_entries` field or a `SubSession` type — is more machinery for the same
  result. Composite ids look like the simplest thing that works.
- **Untrialed continuous data (Gardner torus, Peyrache HD): does NOT stretch cleanly.** `Activity`
  requires `(neurons, trials, bins)` + boolean trial masks + a `window`. Options in §2a. The
  activity-only path through `atlas.measure_activity` (which takes any `Activity` and never asks
  where it came from) is the least invasive, and is shared with the synthetic-generator need from
  `model-zoo.md`.
- **Calcium imaging (zebrafish, C. elegans): does NOT stretch.** `Activity.spikes` is documented as
  spike counts, and the split-half null's whole justification (`stats.py` docstring) reasons about
  Poisson counts vs. 0/1 spikes. ΔF/F would silently violate that. Would need an explicit decision,
  not a loader.

---

## 7. Within-dataset variation — free atlas entries from cached data

Every one of these is a new `BioSession`/`Activity` from bytes already on disk. Rough multipliers on
the bio side of the atlas:

| split | axis | available in | ×entries | note |
|---|---|---|---|---|
| active / passive | engagement | Steinmetz ✅ | ×2 | §1a — the important one |
| pre- vs. post-stimulus window | epoch | all ✅ | ×2 | `window` is already a slice; `WINDOW=slice(50,200)` leaves bins 0–50 unused |
| correct / error trials | outcome | Steinmetz (`feedback_type`) ✅, IBL (`feedbackType`) ✅ | ×2 | error trials are few — watch `min_trials=5` |
| high / low contrast | stimulus strength | Steinmetz ✅, IBL ✅ | ×2–4 | IBL contrasts {0, .0625, .125, .25, 1} |
| engaged / disengaged | behavioral state | IBL ⚠ (needs the trials table's reaction times or a performance criterion) | ×2 | the IBL loader currently keeps only `choice`; it would need to cache more columns |
| fast / slow RT | behavioral state | Steinmetz (`reaction_time`) ✅ | ×2 | |
| per animal | subject | Steinmetz ✅ (4 mice in part0) | — | grouping, not splitting |

Two warnings, both learned the hard way by E5–E10:
1. **These splits halve trial counts**, and trial count is a *confirmed* dominant nuisance (D25) —
   halving it shifts H0 systematically (`stats.py` docstring). Any within-session split must compare
   against a trial-count-matched control split of the *same* session (e.g. random-half vs.
   random-half), or the result is uninterpretable. That control split is itself free, so there is no
   excuse for skipping it.
2. These are **not independent samples** — many entries share neurons and sessions. A bio-vs-bio
   "range" built from them is pseudo-replicated and will look tighter than it is. Fine as atlas
   entries and as paired within-session contrasts; **not** fine as a widened yardstick population.

---

## 8. The region/area dimension — and a trap I'd flag loudly

Splitting a session's population by brain area gives more entries and a hypothesis with teeth: *does
topology vary more across areas than across sessions?* That is a variance-decomposition question the
atlas is well suited to and that does not depend on the yardstick being valid.

**It is a different experiment from E5.** E5 used region metadata to *select which session pairs to
compare* (matching), and failed. This uses region metadata to *define new entries*. Different
question, and E5's failure says nothing about it. Worth stating explicitly in any writeup so it does
not read as re-running a rejected candidate.

**The trap — verified ✅.** I counted regions with ≥50 units across the 23 cached IBL sessions:

```
IBL, probe00 only:  units per session 32–302, regions per session 3–19
  region-sessions with >=50 units:  15   (across ALL 23 sessions)
  region-sessions with >=30 units:  31
```

Only 15 IBL region-populations in the entire cache clear 50 units, and most sit at 10–40. Per-region
IBL entries would therefore differ from each other **mainly in unit count** — which is precisely the
nuisance that D23/D24 established dominates and that E6/E7 failed to control. It would manufacture
exactly the confound the project has spent a week fighting. I'd call per-region-on-IBL an
attractive-looking dead end unless all probes (not just probe00) are loaded.

**Steinmetz is the right dataset for this.** Session 11 alone has 8 areas at ≥50 units
(MD 126, SUB 105, root 100, VISam 79, VISp 66, DG 65, PL 56, CA1 50) ✅, and the 13 part0 sessions
carry 584–1769 units over 5–15 areas each. Rough estimate: **~50–100 region-entries at ≥50 units**
from part0 alone, at zero download, spanning visual (VISp/VISam), hippocampal (CA1/DG/SUB), thalamic
(MD/LGd/LH) and frontal (PL/ACA/MOs) areas. That is a far more interesting axis than 459 more IBL
sessions, and it is free.
(`root` = unassigned units; exclude it or keep it as an explicit negative control.)

---

## 9. Risks / what could go wrong

- **Pseudo-replication** (§7, §8): sub-session entries are not independent. If they leak into the
  bio-vs-bio yardstick population, the range narrows artificially and a future "Allen now falls
  outside the range!" result would be an artifact. Whatever the schema ends up being, it needs a
  field distinguishing independent sessions from derived sub-entries — worth raising with the
  `data-platform.md` fork.
- **O(n²) is already the binding constraint** (§4). Adding entries is cheap; *comparing* them is not.
  Any expansion plan that is not paired with incremental/dedup'd pairwise storage will stall.
- **Positive control could fail for a boring reason** (§2a): wrong preprocessing rather than a broken
  pipeline. Mitigate by running Gardner's data through *both* the native trial-averaged path and a
  continuous path, and by preregistering what each outcome would mean — before computing, per this
  project's standing discipline.
- **Licence hygiene**: everything recommended is ✅ CC-BY-4.0 or ✅ CC0, so redistribution of derived
  signatures is fine with attribution. `data/raw/` is already gitignored; keep it that way.
- **Loadability decays**: ONE's public client already has known breakage (`ibl.py`'s comments about
  HTTP_DATA_SERVER mismatches and `load_dataset` failures). Assume any new remote loader will rot;
  the cached-npz-per-session design already insulates against this and should be kept for every new
  dataset.

---

## 10. Cross-links to the other brainstorm threads

- `distance-construction.md` — §5's 32 Allen sessions turn the E4 check from
  interval-containment into an ROC/effect-size question, which is what a better-powered criterion
  wants. §1a gives a clean paired contrast that most two-sample tests would prefer.
- `model-zoo.md` — §2's known-topology controls and its synthetic generators are the same need
  approached from two sides; there should be **one** activity-only entry path serving both. §1d's
  per-unit CCF coordinates are the anatomical target for spatially-embedded RNNs.
- `data-platform.md` — §4's 455× pairwise blowup, §7/§8's entry multiplication, and §9's
  independent-vs-derived distinction are all schema requirements, not analysis choices.
- `scientific-reframe.md` — §2 is the precondition for the honest-negative framing: a negative
  result without a passing positive control is indistinguishable from a bug. §1a is the cleanest
  available test of the project's core claim.

---

## Sources

- Steinmetz et al. 2019, *Distributed coding of choice, action and engagement across the mouse brain*,
  Nature 576. NMA release: [OSF agvxh / uv3mw / ehmw2](https://osf.io/agvxh/) (part0/1/2).
- Gardner et al. 2022, *Toroidal topology of population activity in grid cells*, Nature 602 —
  [doi:10.1038/s41586-021-04268-7](https://doi.org/10.1038/s41586-021-04268-7);
  data [figshare 16764508](https://figshare.com/articles/dataset/Toroidal_topology_of_population_activity_in_grid_cells/16764508)
  ([doi:10.6084/m9.figshare.16764508](https://doi.org/10.6084/m9.figshare.16764508), CC0);
  code [erikher/GridCellTorus](https://github.com/erikher/GridCellTorus).
- Chaudhuri et al. 2019, *The intrinsic attractor manifold and population dynamics of a canonical
  cognitive circuit across waking and sleep*, Nat Neurosci 22 —
  [doi:10.1038/s41593-019-0460-x](https://doi.org/10.1038/s41593-019-0460-x).
- Peyrache et al. 2015, Nat Neurosci 18 — [doi:10.1038/nn.3968](https://doi.org/10.1038/nn.3968);
  data [DANDI 000056](https://dandiarchive.org/dandiset/000056).
- Pei et al. 2021, *Neural Latents Benchmark '21*, [arXiv:2109.04463](https://arxiv.org/abs/2109.04463);
  [nlb_tools](https://github.com/neurallatents/nlb_tools); DANDI
  [000128](https://dandiarchive.org/dandiset/000128) /
  [000127](https://dandiarchive.org/dandiset/000127) /
  [000129](https://dandiarchive.org/dandiset/000129) /
  [000130](https://dandiarchive.org/dandiset/000130).
- Allen Institute Visual Coding Neuropixels: [DANDI 000021](https://dandiarchive.org/dandiset/000021).
- Allen Institute Visual Behavior Neuropixels: [DANDI 000713](https://dandiarchive.org/dandiset/000713).
- Entorhinal conjunctive coding: [DANDI 000582](https://dandiarchive.org/dandiset/000582).
- IBL Brain-Wide Map: [openalyx.internationalbrainlab.org](https://openalyx.internationalbrainlab.org),
  [doi:10.1101/2023.07.04.547681](https://doi.org/10.1101/2023.07.04.547681).
