# SNN topo Sept 27 2026

session goal: reframe the project like main.md: reorganize snn experimental workspace
as a general snn topo data gathering setup. refactor everything to accomodate broader scale
experiments for a variety of snns, with organization for results. Overall, just accumulate an
organized dataset of snn tda results

process: do exploratory work via /brainstorm to develop ideas for the project expansion,
then /consolidate results. define a workflow for implementation, using /context-builder, to make
a packet for the implementation sub-session. implementation should use a nodeterm workflow with claude
orchestrator with subagents and heavily utilizing codex in permissive mode.

## Results · 2026-09-27 15:08 (agent)
1. /brainstorm project expansion: done — `dev/brainstorm/snn-tda-dataset/index.md` (`479b25d`)
2. /consolidate: done — `3fa110a`, `f0006e1`
3. /context-builder implementation packet: done — `dev/agents/project/context/` (v3, M1-M9)
4. nodeterm implementation sub-session: not started — Next 1 (`/project-builder`)

## Results · 2026-09-28 12:14 (agent)
1. Implementation (v3 build, M1-M9): done. `cd897a2` merged to main. `pytest -q` 190 passed, `-m data` 13 passed.
2. Validation: E17 PASS 8/8. E15 re-derived on the new pipeline (E18): REPLICATES 11/12. See `dev/agents/experiments.md`.
3. bio_core atlas: done. 732 activities with R1 counts, in `results/runs/20260928-1128-bio_core`.
4. Model zoo sweeps: not started, **next**. Needs your OK (~9 h). The command is in `dev/agents/project/notes.md` "Zoo launch".
