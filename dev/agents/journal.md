# Journal · 2026-09-28 10:17 · v3-build · e007cc9
## Start
**State:** v3 build on `v3-build`: M1-M3, M6, M7+M8 and the runner `derive()` hook merged; `pytest -q`
at 8ad1b48 → 179 passed (not rerun this session). bio_core full run done (732/732 activities, 0 failed),
no R1 derived rows yet. Track A (M4 floor + validate_instrument, M5 PREREG binding + `snntopo verdict`,
E15 spec, E16 skeleton) sits unmerged on `v3-a` (5 commits, 29d3869), stopped at CHECKPOINT 3.
E17 validation: PASS 8/8.
**Since:** Nothing since e007cc9. `dev/journal.md` still ends with the 15:08 `## Results`; its task 4
reads "not started", but the build ran after it (M1-M8 minus M9; the 18:19 Close didn't append results there).
**Next:** (user's journal tasks 1-3 done; 4, the implementation sub-session, is mid-flight)
1. CHECKPOINT 3: add noise level 14 to the E15 scan (`python experiments/e15_engagement.py scan` in
   the v3-a worktree), show the table + intended PREREG; current pick is noise 12 (H1 0.0581 vs target
   0.06644; 16 → 0.0756).
2. On approval: commit PREREG on v3-a, run E15 (~30+ min), `snntopo verdict experiments/e15_engagement.py`,
   E-entry; real `snntopo run experiments/e16_nogo.py --mini`.
3. Gate v3-a: `pytest -q`, reviewer on `git diff v3-build...v3-a` (`runner.load_spec` compile-from-source,
   binding tests), merge `--no-ff` (journal conflict: keep both).
4. `sweeps/bio_core.py`: `derive()` → `floor.robust_count_rows(aid, activity, TOPO, CMP)`, drop dead
   `TOPO.metrics=`; rerun into a new dir (~16 min).
5. M9 docs (README, docs/architecture.md, v3 dev/agents/spec.md, D29-D38 into dev/agents/decisions.md,
   root CLAUDE.md), Done-when checks by command, CHECKPOINT 4: merge v3-build → main.
6. Paused science: E16 population (user's call), D28 floor stress tests, SNN-vs-bio vs matched floor,
   D19 controls rerun.
**Traps:**
- `snntopo run --out` relative path resolves against cwd; from a worktree pass `$SNNTOPO_RESULTS_DIR/runs/<id>`.
- nodeterm `send`/`settings` refused; follow-ups = new node in the group. Codex nodes show
  "AGENT STATUS UNCONFIRMED"; read panes via `tmux -L node-terminal capture-pane -p -t nt-<node-id>`.
- Parallel tracks sharing 16 cores slow topology ~3×.
- Agent briefs must say APPEND to `dev/agents/journal.md`.
- E16 contrast-matched no-go = misses only (14/14/9 trials in sessions 6/11/12).
- v3-a's journal still lists gap 2 (derived rows) as open; it was resolved on v3-build (`85dee0e`).
**Pointers:**
- Track A report: `git show v3-a:dev/agents/journal.md` from line 223.
- Build packet: `dev/agents/project/context/{requirements,design,decisions,agent-team}.md`.
- Worktrees `../snn_topo.worktrees/v3-{a,b,c,m2,m3}`; only v3-a unmerged (b/c/m2/m3 removable). Track A group `group-mukacave-5de15e30`.
- Runs: `results/runs/20260927-1703-bio_core`, `results/runs/20260927-1703-validate_instrument`.
- Derive hook `snntopo/runner.py:447-495`; R1 `floor.robust_count_rows` (v3-a `snntopo/floor.py:258`).

## Task: Finish the v3 build up to (not including) the zoo sweeps · 10:51
**Goal:** Every requirements.md Done-when met by a real command, v3-build merged to main; the zoo v0/v1 overnight runs are the next step, left for you to launch.
**Now:**
- On `v3-build` (e007cc9): M1-M3, M6, M7+M8 and the derive hook are merged. bio_core ran 732/732, with no R1 derived rows.
- `v3-a` (29d3869) is unmerged: M4 floor + validation (E17 PASS 8/8), M5 binding/verdict, E15 spec (`PREREG = None`), E16 skeleton. It stopped at CHECKPOINT 3.
- M9 docs are not started. Merged worktrees b/c/m2/m3 are still checked out.
**Scope:** in: Next 1-5 (E15 scan+PREREG+run+verdict+E-entry, E16 `--mini` real run, v3-a gate+merge, bio_core `derive()` rerun, M9 docs, Done-when checks), merge to main, worktree cleanup. out: zoo_v0/zoo_v1 full runs, E16 population/PREREG, D28 stress tests, SNN-vs-bio floor, D19 controls.
**Constraints:**
- The user's answers at 10:50: CHECKPOINT 3: add noise 14 to the scan and commit the nearest level. Criteria: H1, α 0.05; detected iff primary > B_q95, > drift max and p ≤ α; ≥7/12 → REPLICATES, ≤3 → DOES NOT, else MIXED; judged only if arm A H1 ≤ 4/40 and the floor is sane; session 11 excluded; 40 arms. CHECKPOINT 4 is pre-approved: if all checks pass, merge `--no-ff` to main and remove the merged worktrees and branches.
- Experiments run only from a clean tree. Never edit PREREG after its first run. Never push.
- Assumption: the work runs inline in this session (not nodeterm fan-out, since what's left is mostly sequential). The `reviewer` agent handles the v3-a merge gate, per agent-team.md.
**Approach:**
1. In v3-a: add 14 to `SCAN_LEVELS`, rescan, fill PREREG, commit, run E15 (clean tree, absolute `--out`), then `snntopo verdict`, then the E-entry. Real E16 `--mini` run.
2. Gate v3-a: `pytest -q` + `-m data`, reviewer on `git diff v3-build...v3-a`, fix findings on v3-a, merge `--no-ff` (journal: keep both).
3. bio_core `derive()` → `floor.robust_count_rows`, drop dead `TOPO.metrics=`, rerun into a new dir, `status` 0 missing.
4. M9: README, `docs/architecture.md`, `dev/agents/spec.md` v3, D29-D38 → `dev/agents/decisions.md`, root `CLAUDE.md` sandbox. Then walk Done-when by command, merge to main, clean worktrees.
**Risks:**
- Adding 14 after seeing 12/16 looks like tuning. It isn't: only nulls were read, and the nearest-level rule was fixed earlier. The journal says so.
- E15 runs 30+ min under load. Nothing else heavy runs alongside it.
- The reviewer may flag `load_spec` compile-from-source. If so, fix on v3-a, not around it.
- A bio_core rerun on the merged floor code could fail on regions with few units. We'd see it in `status` failed ids.
**Done when:**
- `snntopo verdict experiments/e15_engagement.py` prints a judged line from a counted clean run, and the E-entry is in experiments.md.
- `snntopo run experiments/e16_nogo.py --mini` completes and its verdict executes.
- The new bio_core run dir's derived.jsonl has R1 rows for every ok activity, and `status` shows 0 missing.
- `pytest -q` is green on main after the merge. `snntopo --help` lists 11 subcommands. The README quickstart commands run.
- `zoo_v0`/`zoo_v1` `--dry-run` still work on main. No zoo full run was launched.
**Open:** none.

## Progress · 11:45
Done. Main is at `cd897a2` (`--no-ff` merge of v3-build). Every requirements.md Done-when has a command, test or run behind it.
- E15: scan + PREREG `840b7f6` (noise 14; 12 → 0.0581, 14 → 0.0740, target 0.0664). Clean run `results/runs/20260928-1100-e15_engagement` (29 min, 252 activities, 0 failed). **E18: REPLICATES 11/12**; session 6 misses on p = 0.059. Floor H1: B_q95 1.196, C_q5 3.465; arm A 0/40.
- E16 `--mini`: `results/runs/20260928-1130-e16_nogo-mini` (13 s), descriptive verdict executes.
- v3-a gate: the reviewer found one real issue. floor.py is not bound by verdict_hash; that was already an accepted gap, so only the docstring was fixed, plus a None guard (`0e9c280`). Merged as `eb0e2b9`.
- bio_core: `derive()` → R1 (`3c80bc9`). Rerun `results/runs/20260928-1128-bio_core`: 732/732 ok, 924 comparisons, 3416 R1 rows, 0 ok activities without R1, status 0 to do. code_rev reads `eb0e2b9-dirty`: the derive edit was committed after launch, identical.
- zoo_v1 imported `sweeps.zoo_v0`, which the console script can't resolve. It now loads zoo_v0 by path. Dry-runs: v0 972, v1 1260.
- M9 docs `2709805` (README, architecture, spec.md, D29-D38, CLAUDE.md, notes "Zoo launch").
- `-m data` failed: `steinmetz_nogo.bio_match = "steinmetz"` but the v1 loader has no `nogo` condition (`tests/test_data.py:25`). Set to None; v3 never reads bio_match (`4e80022`). No test edited.
- Checks on main: `pytest -q` 190 passed, `-m data` 13 passed; the README quickstart ran verbatim into a scratch results dir (mini validate 88 s, status, verdict, `dataset.load` snippet).
- Removed worktrees and branches v3-{a,b,c,m2,m3} and v3-build.
**Left for the user:** stash `stash@{0}` ("v3 finish: docs + bio_core derive + journal") is superseded; dropping it was blocked, so drop it by hand. The zoo launch command is in `dev/agents/project/notes.md` "Zoo launch".

## Close · 2026-09-28 12:14 · eb0e2b9..cd897a2
- **changed:** sweeps/bio_core.py: `derive()` writes R1 robust-count rows; bio_core rerun with them
- **changed:** sweeps/zoo_v1.py: loads zoo_v0 by path (console script lacked the repo root)
- **changed:** snntopo/tasks/steinmetz_nogo.py: `bio_match = None` (v1 loader has no `nogo`; `-m data` failed)
- **changed:** M9 docs: README, docs/architecture.md, dev/agents/spec.md, D29-D38, CLAUDE.md sandbox, notes "Zoo launch"
- **why:** finish the v3 build up to the zoo sweeps: every Done-when met, v3 on main
- **verified:** `pytest -q` on main → 190 passed; `pytest -q -m data` → 13 passed; README quickstart verbatim → ran; `snntopo run sweeps/zoo_v1.py --dry-run` → 1260; E15 verdict → REPLICATES 11/12 (E18, earlier in session)
- **by:** claude
- `3c80bc9` sweeps: bio_core derive() writes R1 rows, drop dead TOPO metrics; zoo_v1 loads zoo_v0 by path
- `2709805` M9 docs: README, docs/architecture.md, v3 dev/agents/spec.md, D29-D38 into decisions.md, CLAUDE.md sandbox, zoo launch notes
- `4e80022` steinmetz_nogo: bio_match None; spec.md: E18 line
- `cd897a2` Merge v3-build: snntopo v3
- 9 files, +320 −235
- ⚠ uncommitted: `.nodeterm/` (nodeterm board state, not project code)

### Next
1. **Model zoo is next.** With the user's OK, launch zoo_v1 (a superset of v0, so it covers both). From main: `SNNTOPO_WORKERS=8 snntopo run sweeps/zoo_v1.py --out results/runs/<YYYYMMDD-HHMM>-zoo_v1 --shard i/2`, for i = 0 and 1 in two shells. Estimate ~9 h serial. Check with `snntopo status <dir>` and rerun a killed shard as-is.
2. After the zoo: look at the degenerate fraction and accuracy per family, then the descriptive SNN-vs-bio comparison. It stays descriptive until a matched floor for SNN vs bio exists (spec.md Validity).
3. E16: the user picks the no-go population, then PREREG it (`experiments/e16_nogo.py` has `PREREG = None`).
4. Drop the superseded `stash@{0}` ("v3 finish: docs + bio_core derive + journal") by hand.
### Traps
- bio_core run `20260928-1128-bio_core` records code_rev `eb0e2b9-dirty`: the `derive()` edit was committed (`3c80bc9`) after launch, and the code is identical.
- The ripser pool needs AF_UNIX (forkserver). A sandboxed shell falls back to serial.
### Pointers
- Zoo launch facts: `dev/agents/project/notes.md` "Zoo launch". GPU N = 2 comes from M7.
- Runs: `results/runs/20260928-1100-e15_engagement` (E18), `results/runs/20260928-1128-bio_core` (R1 rows), `results/runs/20260927-1703-validate_instrument` (E17).
- E18 entry: `dev/agents/experiments.md`. Specs table: `dev/agents/spec.md`. Build packet: `dev/agents/project/context/requirements.md`.
