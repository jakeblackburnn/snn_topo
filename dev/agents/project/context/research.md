# snntopo v3: research

Findings the build depends on. Full notes: `dev/brainstorm/snn-tda-dataset/` (the read-only
checks and their outputs are in its `checks/`). The stale claims in the 09-23 brainstorm are
listed in its `seed-errata.md`.

## 2026-09-27 · Code facts that shape the design
- `compare` computes `h = min(n_a, n_b)//2` per condition (`stats.py:222`) and never records it.
  Nulls pool both sides' within-distances (`stats.py:237`). Cross distances run serially in the
  caller (`stats.py:228-233`); only ripser uses the pool (`stats.py:171`, `os.cpu_count()` workers).
- The in-memory halves cache holds 32 entries and is keyed without code identity
  (`stats.py:108-111, 148`). That's unsafe to persist without adding `topo_id`/`cmp_id`.
- `snn_entry` builds the model before `train` seeds torch (`atlas.py:237`, `training.py:32`), so
  initial weights depend on earlier RNG state. `controls.untrained` seeds first (`controls.py:18`).
- `train` keeps the best checkpoint (`training.py:58-59, 67-68`) and has no hook for snapshots
  at fixed updates (`training.py:25-73`).
- The readout never feeds back into the hidden layer (`models/networks.py`), so "task stimuli,
  readout ignored" is byte-identical to the task regime. Spontaneous means zero input.
- Steinmetz: active `all` = responded trials only (`data/steinmetz.py:103-117`); passive
  left/right = stimulus side; the download isn't atomic (`steinmetz.py:37-50`).
- `contracts.py:4`: dataclass fields may only be added with defaults.
- The forkserver pool falls back to serial in a sandbox (`stats.py:170-181`) at about 1/16 the
  throughput. Real runs need the sandbox off.

## 2026-09-27 · Data facts
- Steinmetz part0 is 13 sessions from 4 mice (Cori, Forssmann, Hench, Lederberg), with 77 region
  populations ≥50 units (40 ≥100), excluding `root` (`checks/bio_inventory.out` §1).
- Passive blocks have **0** zero-contrast trials. No-go splits into zero-contrast withholds
  (31-71/session) and nonzero-contrast misses (9-84). Sessions 6/11/12 have 14/14/9 misses
  (`checks/e16_and_determinism.out` §1). This constrains E16's population.
- Legacy self-null H1 `null_mean` spans 4.9e-5 to 0.116 across 22 sessions, and 6/22 have H1_n = 0
  at `n_pca=10` (`checks/bio_inventory.out` §2). A null is meaningful only with its `h`.
- Blob sizes (`checks/inventory.out` §4): bio activity ~2.4 MB; SNN spikes packbits 0.6-2.5 MB;
  halves 0.1-0.2 MB; weights 0.26-4.2 MB.

## 2026-09-27 · Costs (from file timestamps and experiments.md)
- E12: 160 synthetic pairs in 8.6 min (~3.2 s/pair). E14: 120 pairs in 5.7 min. E15: 195 compares
  in 6.4 min.
- Topology per SNN activity ~10-15 s (signature + nulls, 3 conditions). Training: ~51 s at 1500
  updates (E1), ~15 s at 200.
- Zoo v0 estimate: ~970 activities, GPU ~2.3 h + CPU ~2.7 h serialized, ~3-4 h total. GPU
  concurrency is unmeasured (M7 measures it). The card is shared with local models.

## 2026-09-27 · Instrument facts carried forward (dev/agents/experiments.md)
- E12: split-half null valid at 300×340 (A 1/40 H0, 0/40 H1); C 40/40.
- E14: at 698×110, noise 16, A 0/40, B H1 q95 = 1.09, C H1 q50 2.84 with q5 > B q95.
- Journal traps: never compare a ratio against a bar measured at a different `null_mean`. H0
  matches at higher noise than H1. A null pair shares `mixing_seed`. Significant ≠ different
  topology (signatures include geometry).
