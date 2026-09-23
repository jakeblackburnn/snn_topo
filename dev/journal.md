# Journal · 2026-09-23 12:02 · main · e4935cb

## Start
**State:** D20's discriminative-validity gap is still open and still blocks the full-budget
`steinmetz_2afc` search. Four session-matching candidates are now exhausted, all FAIL by the same
preregistered Allen-vs-bio criterion: region (E5/D22), unit-count (E6/E7/D23/D24), trial-count
(E8/D25), raw-diameter (E10/D26). E9's diagnostic is the standing result: `|Δraw_diameter|` is the
only covariate clearing `|r|>0.5` on both dims (+0.639 H0, +0.569 H1). D26's conclusion is that
matching alone cannot close the gap — the fix belongs in the distance construction itself.
**Since:** nothing since the last journal commit (`e4935cb`); tree clean apart from the
pre-existing untracked `.nodeterm/`.
**Next:**
1. Design + implement raw-diameter residualization as a first-class option in the package —
   decide the mechanism first (new `TopoConfig` field threaded through `stats.compare` vs. a
   post-hoc correction in `objective.py`), then implement. Design-bearing package change, not
   another scratchpad script.
2. Once implemented, re-run E4's Allen discriminative-validity check against the new
   normalization under the same preregistration discipline (hypothesis + criterion before
   computing) — E11.
3. If it passes: re-derive `structure_weight` (2.0), still only calibrated at `n_pca=10`.
4. Full-budget `steinmetz_2afc` search stays blocked (D20) until some fix passes the Allen check
   on both H0 and H1.
**Traps:** `results/baseline-*/` are gitignored, local-only. E8/E9/E10's analysis scripts lived in
a rotated-out scratchpad (`/tmp/snntopo_e8/`) — methodology is written out in `dev/experiments.md`
E8-E10 if it needs reconstructing. Backgrounding a script with a leading `cd` changes that
command's own execution directory — pass an absolute output path instead. python needs
`source ~/Code/python_venv_01_main/bin/activate`. `snntopo` console script resolves to whichever
checkout was last `pip install -e`'d — use `python -m snntopo.cli` from the target dir.
`snntopo baseline` is O(n²) in session count (~12 min at 22 sessions with raw data cached).
`--n-updates` defaults to 3000, not 1500.
**Pointers:** `dev/experiments.md` E8/E9/E10; `dev/DECISIONS.md` D25/D26; `dev/SPEC.md` Validity
section (current through D26). `results/baseline-wide/{entries,distances}.csv` is the source table
every candidate since E5 has reanalyzed from. Refactor targets, verified present this session:
`snntopo/contracts.py:105` (`TopoConfig`, no residualization field today),
`snntopo/contracts.py:126` / `snntopo/topology/pipeline.py:61` (`raw_diameter` computed and stored),
`snntopo/topology/stats.py:171` (`compare`) / `:197` (`split_half_null`) — the distance path, which
currently never reads `raw_diameter`; `snntopo/objective.py:41` (`score`).

## Close · 2026-09-23 15:48 · e4935cb..abf8007
- **changed:** `snntopo/contracts.py`/`snntopo/topology/stats.py` (+`TopoConfig.
  residualize_raw_diameter`: `compare()` fits `distance/null_mean` on `|Δraw_diameter|` from the
  within-IBL reference population, subtracts it per H0/H1, leaves null/p-value untouched);
  `tests/test_topology.py` (+regression test: flag-off bit-for-bit unchanged, flag-on transforms
  only `.distance`); `dev/experiments.md` (+E11, preregistered, result FAIL); `dev/DECISIONS.md`
  (+D27: mechanism implemented, does not resolve D20); `dev/SPEC.md` (Validity section updated
  through D27).
- **why:** implemented D26's required next step — the Next item's refactor (raw-diameter
  residualization as a first-class `TopoConfig` option) — then re-ran E4's Allen discriminative-
  validity check against it as E11, per the project's preregistration discipline.
- **verified:** `python -m pytest tests/test_topology.py -q -k "raw_diameter or residualization"`
  → 1 passed. Full suite run by the implementer (codex) before and after: 9 passed then the same
  pre-existing forkserver Unix-socket sandbox error both times (not a regression, not fixed
  either — sandbox artifact, see Traps).
- **by:** claude, implementation delegated to a codex node driven by claude (nodeterm canvas);
  claude reviewed the diff and caught one real error before it was hardcoded (see Traps).
- `abf8007` topo: raw-diameter ratio residualization option (D26/D27)
- 3 files, +42 −1 (code commit); `dev/` commit follows this one (journal + D27 + E11 + SPEC)
- ⚠ uncommitted: none outside this journal commit (`.nodeterm/` untracked, pre-existing, unrelated)

### Next
1. **D20 is still open.** All five candidates tried so far — four session-matching (region/unit/
   trial/raw-diameter, E5-E10) plus one distance-construction fix (raw-diameter ratio
   residualization, E11) — FAIL the Allen discriminative-validity check. No lever is currently
   flagged as untested; the next candidate needs to be designed, not just re-run. Consider
   whether the linear-fit form itself (OLS on `|Δraw_diameter|`) is the wrong shape before trying
   a different covariate — E11's residual range is *wider* than E10's raw matched range on H1
   ([-3.824, 11.138] vs E10's matched max 2.568), so a global linear correction may be adding
   variance for pairs poorly described by the fit, worth checking before ruling out
   raw_diameter-based correction entirely.
2. Full-budget `steinmetz_2afc` search stays blocked (D20) until some fix passes the Allen check
   on both H0 and H1 — do not start it in the meantime.
3. `structure_weight` (2.0) re-derivation stays deferred until D20 resolves (unchanged from prior
   sessions).

### Traps
Codex's first draft residualized on raw `distance` (r=0.406 H0) instead of the `distance/
null_mean` ratio E9 actually diagnosed (r=0.639 H0) and that the Allen check evaluates — caught
by comparing against E9's numbers before the fit was hardcoded; if re-deriving this again, fit
the ratio, not raw distance. The full pytest suite hits a pre-existing sandbox-only failure
(`test_bio_entry_siblings_cross_compare`, forkserver Unix-socket permission error) unrelated to
this session's change — present before and after, run `-k` to scope around it rather than reading
`-x` failure as a regression. Driving an agent via nodeterm's plain `open-terminal` (not
`open-agent`) gives raw CLI flag control (`--sandbox workspace-write --ask-for-approval never`
used here) but the node isn't auto-linked — needs an explicit `link --to <id>` before
get-linked-context can read it.
### Pointers
`dev/experiments.md` E11; `dev/DECISIONS.md` D27; `dev/SPEC.md` Validity section (current through
D27). `snntopo/topology/stats.py:_RAW_DIAMETER_FIT`/`_raw_diameter`/`compare` — the implemented
mechanism. D27's decision (residualization implemented but rejected as a D20 fix) is already in
`dev/DECISIONS.md`, no `/decide` needed.
