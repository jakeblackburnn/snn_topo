# SNN topo Sept 28 2026

last session we set up and ran stuff up to the model zoo sweeps. before running these, I'd like to segregate
them into more bite-sized experiments, and/or ones that can be budgeted with time.
todays goal is to set up a way to run the zoo in blocks of roughly 1-2 hour runs each.

## Results · 2026-09-28 18:48 (agent)
1. Run the zoo in 1-2 h blocks: done. `snntopo run --budget MIN` plus a seed-major zoo order (`fe4e8cc`). zoo_v1 finished in 4 blocks (20/65/36/19 min, ~3 h wall): `results/runs/20260928-1502-zoo_v1`, 1260/1260, 0 failed. Launch recipe in `dev/agents/project/notes.md` "Zoo launch".
