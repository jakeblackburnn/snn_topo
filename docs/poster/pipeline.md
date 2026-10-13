# The pipeline: from recordings to a point cloud

One code path for brains and models (`snntopo/topology/pipeline.py`). The input is always
the same array: **spike counts, neurons x trials x time bins**.

## Steps

| # | step | brain example (one Steinmetz session) |
|---|---|---|
| 1 | **Start with spike counts.** 10 ms bins for the brain; one simulation step per bin for a model. | 698 neurons x 340 trials x 250 bins |
| 2 | **Pick the trials and the window.** One trial group (e.g. active), and the 150 bins from stimulus onset. | 698 x 276 x 150 |
| 3 | **Average over trials.** Each neuron gets one mean response curve. Trial-to-trial noise averages out. | 698 x 150 |
| 4 | **Smooth in time.** 5-bin (50 ms) moving average. | 698 x 150 |
| 5 | **Turn time bins into points.** Each time bin is one point; its coordinates are every neuron's rate at that moment. | 150 points in 698 dimensions |
| 6 | **Reduce with PCA.** Centre, keep the 10 directions with the most variance. | 150 points in 10 dimensions |
| 7 | **Scale to diameter 1.** Divide by the largest distance between any two points, so shape is compared, not firing-rate scale. | the point cloud |

The result is the population's **trajectory**: 150 points tracing how the whole population's
activity moves through the 1.5 s of a trial.

## Then: the shape of the cloud

8. **Persistent homology** (Vietoris-Rips, via Ripser). Grow a ball around every point; as
   the radius increases, track when clusters merge (**H0**) and when loops appear and fill in
   (**H1**). Each feature is a bar from its birth radius to its death radius. Long bars are
   structure, short bars are noise. The set of bars is the **signature**.
9. **Noise level.** Split the trials into two random halves, run steps 3 to 8 on each, and
   measure the distance between the two signatures. Repeat 50 times. This says how much a
   signature moves from trial sampling alone.
10. **Robust count (R1).** Count the bars longer than twice the 95th percentile of that
    split-half noise. These are the features that survive resampling.

## What to keep in mind

- The cloud is a *trial-averaged path*, 150 points in time order. It is not a cloud of
  single-trial states. A loop means the average trajectory comes back near where it was.
- Signatures carry geometry as well as topology: two clouds with the same holes but
  different proportions give different signatures.
- Fewer trials or neurons means more noise. Comparisons are only fair at matched
  neuron and trial counts, which is why the brain-vs-model comparison subsamples both to
  the same size (50 neurons x 56 trials, and 128 x 100).

## One-line version for the poster

spikes (neurons x trials x time) → trial average → smooth → each time bin is a point →
PCA to 10-D → scale to unit size → persistent homology → bars for clusters (H0) and loops (H1).
