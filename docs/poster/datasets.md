# The brain data

## Steinmetz et al. 2019: the poster's brain data

**What it is.** Recordings from mice doing a visual choice task, made with Neuropixels
probes: thin silicon shanks with hundreds of recording sites, long enough to pass through
several brain regions at once. Spike-sorting software turns the electrical signal into
*units*, each presumed to be one neuron, labelled with the region it sits in.

**The task.** A striped pattern appears on the left screen, the right screen, both, or
neither, each at a contrast of 0, 0.25, 0.5 or 1. The mouse turns a wheel to pick the side
with the higher contrast. If nothing is shown, the right answer is to hold still (*no-go*).
So every trial ends as left, right, or no response.

**The passive block.** After the task, the same kind of stimuli are replayed with nothing
asked of the mouse. Same neurons, same probes, same day. This is what makes
"engaged vs passive" a clean comparison.

**What we use.** The Neuromatch Academy preprocessed archive, part 0 of 3:

| | |
|---|---|
| sessions | 13, from 4 mice (Cori, Forssmann, Hench, Lederberg) |
| units per session | 584 to 1769 |
| regions | 50 named regions in total; 77 session-region populations with at least 50 units |
| trials per session | 123 to 292 responded task trials, 110 to 150 passive trials |
| format | spike counts in 10 ms bins, 250 bins (2.5 s) per trial, stimulus at 0.5 s |
| analysis window | bins 50 to 200: the 1.5 s from stimulus onset |

**Trial groups we analyse.**

| group | trials |
|---|---|
| active | task trials where the mouse chose left or right |
| passive | every passive-block trial |
| no-go | task trials with no response |

**Things to say honestly.**
- "No-go" mixes two things: nothing was shown and the mouse correctly held still (31 to 71
  per session), and something was shown but the mouse did not respond (9 to 84).
- Regions within a session share trials and neurons with the whole session: they are not
  independent samples. The session is the replicate (n = 13).
- The full dataset is 39 sessions from 10 mice; we use the first 13. (Full-dataset figure is
  from the paper, not checked this session.)

Source: `snntopo/data/steinmetz.py`, `docs/learn/05-brains-and-snns.md`. The window timing
was checked against the archive's `stim_onset` field (0.5 s, session 11); the code comment at
`steinmetz.py:32` says "0.5--2.0 s after the stimulus", which is wrong.

## Used earlier, not in the poster results

**IBL brain-wide map.** Many labs running the same left/right visual choice task in mice,
with Neuropixels. We used 20 sessions spread across a release of about 459, one probe each,
32 to 288 units per session. Served as the "many brains" set in early experiments.

**Allen Visual Coding Neuropixels.** Mice passively viewing images: no choice, no reward.
One session (719161530), good units in visual cortex. Brought in as a deliberately different
recording.

Neither is in the rebuilt pipeline's runs, so no number on the poster comes from them.
