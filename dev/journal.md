# SNN Topo Journal

## Oct 19 2026

reworking figures

1. Topologists Breakfasts - this is good
2. clique topology - too big! show only one clique progression and the curve, how to do layout???

3. the task - this needs to be credited to steinmetz, its directly from their paper. 

4. clique model - too wide! maybe just the second figure is relevant, showing a random population netted together. 

5. clique curves - good

## Part 2 - applying figure changes and figuring out results
run figure scripts to apply changes.
should results be separated from git? should we remove raw steinmetz, and replace with an install script or something
to avoid pushing the whole thing to github?

## Results · 2026-10-19 10:55 (agent)
1. Topologists Breakfast: no change, as you said.
2. Clique topology (Fig 2): done in code (`9edd37f`). It's one column now: the place-cell progression over the curve. It still needs a render on your PC (agent journal Next 1).
3. The task (Fig 3): done (`9edd37f`). It's re-cut from the paper at 1200 dpi (`docs/poster/figures/steinmetz_task.png`) and credited in the caption. Formal permission (© Springer Nature) is your call.
4. Clique model (Fig 4): done in code (`9edd37f`). It's one column now, the netted probe only. It still needs a render on your PC.
5. Clique curves: no change, as you said.

### 2026-10-19 13:00 (agent)
Rendered Figs 2, 4, 5 on real data (Figs 2 and 4 one column, Fig 5 without "halfway"); clique table cells match probe.out. Raw Steinmetz npz untracked, still on disk; merged to main, not pushed.
