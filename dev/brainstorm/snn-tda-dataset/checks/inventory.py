"""Read-only facts for the snn-tda-dataset brainstorm (2026-09-27). Writes nothing.

1. Legacy results inventory: records per run dir by kind, and which provenance fields
   each carries (meta.topo, DistanceResult.construction, anything naming h or seed).
2. Steinmetz part0 trial counts per session: active responded, no-go (response == 0),
   passive -- the E16 population.
3. Masked vs sliced trial selection: does build_trajectories give bit-identical points
   when a trial subset is expressed as a mask over the full array (what E13/E15 did) vs
   as a sliced array? Decides whether a recipe that slices can reproduce E15 exactly.
4. Payload sizes that bear on storage: one bio activity, one SNN-shaped 0/1 activity
   stored packed, one split-half diagram set.

    ~/Code/python_venv_01_main/bin/python dev/brainstorm/snn-tda-dataset/checks/inventory.py
"""
import io
import json
from collections import Counter
from pathlib import Path

import numpy as np

from snntopo.config import RESULTS_DIR
from snntopo.contracts import TopoConfig
from snntopo.data import load_session
from snntopo.data import steinmetz
from snntopo.topology.pipeline import build_trajectories, persistence, unit_diameter


def inventory() -> None:
    print("== 1. legacy results inventory ==")
    for path in sorted(RESULTS_DIR.glob("*/atlas.jsonl")):
        kinds, with_topo, constructions, dist_keys = Counter(), 0, Counter(), set()
        for line in path.read_text().splitlines():
            r = json.loads(line)
            kinds[r["kind"]] += 1
            with_topo += "topo" in (r.get("meta") or {})
            for d in r["distances"]:
                constructions[d.get("construction", "<absent>")] += 1
                dist_keys |= set(d)
        print(f"{path.parent.name:40s} {dict(kinds)} meta.topo={with_topo} "
              f"construction={dict(constructions)} h_or_seed_field={sorted(k for k in dist_keys if k in ('h', 'seed'))}")
    for csv in sorted(RESULTS_DIR.glob("*/*.csv")):
        if csv.name in ("entries.csv", "distances.csv"):
            continue
        print(f"script output (no atlas record): {csv.relative_to(RESULTS_DIR)} "
              f"header={csv.open().readline().strip()}")


def steinmetz_counts() -> None:
    print("\n== 2. Steinmetz part0 trial counts ==")
    print("session n_units active responded nogo passive subject")
    for s in steinmetz.list_sessions():
        dat = steinmetz._session_data(s)
        response = np.asarray(dat["response"])
        print(f"{s:>7s} {dat['spks'].shape[0]:7d} {len(response):6d} {int((response != 0).sum()):9d} "
              f"{int((response == 0).sum()):4d} {dat['spks_passive'].shape[1]:7d} {dat['mouse_name']}")


def masked_vs_sliced() -> None:
    print("\n== 3. masked vs sliced trial selection (Steinmetz 11, E13 block 110) ==")
    act = load_session("steinmetz", "11").activity
    topo = TopoConfig()
    responded = np.flatnonzero(act.conditions["all"])
    early = responded[:110]
    rng = np.random.default_rng(0)
    perm = rng.permutation(early)
    half = np.sort(perm[:55])
    masked = build_trajectories(act.spikes, [half], act.window, topo)[0]
    # The same trials as a sliced array: positions of `half` inside `early`.
    sliced_spikes = act.spikes[:, early]
    pos = np.searchsorted(early, half)
    sliced = build_trajectories(sliced_spikes, [pos], act.window, topo)[0]
    diff = np.abs(masked - sliced).max()
    print(f"bit-identical: {np.array_equal(masked, sliced)}  max abs diff: {diff:.3e}")
    # Unsorted order, as _split_halves passes perm[:h] directly.
    masked_u = build_trajectories(act.spikes, [perm[:55]], act.window, topo)[0]
    print(f"sorted vs unsorted half, masked path, bit-identical: {np.array_equal(masked, masked_u)}")
    d_masked = persistence(unit_diameter(masked)[0], 1)
    d_sliced = persistence(unit_diameter(sliced)[0], 1)
    print("diagrams identical:", all(np.array_equal(a, b) for a, b in zip(d_masked, d_sliced)))


def sizes() -> None:
    print("\n== 4. payload sizes ==")

    def npz_bytes(**arrays) -> int:
        buf = io.BytesIO()
        np.savez_compressed(buf, **arrays)
        return buf.tell()

    act = load_session("steinmetz", "11").activity
    print(f"steinmetz 11 activity {act.spikes.shape} as compressed int8 npz: "
          f"{npz_bytes(s=act.spikes.astype(np.int8)) / 1e6:.2f} MB")
    rng = np.random.default_rng(0)
    for n in (256, 1024):
        snn = (rng.random((n, 340, 150)) < 0.05).astype(np.uint8)  # 5% spike prob per step
        print(f"SNN-shaped 0/1 activity ({n}, 340, 150) at 5% rate: packbits+npz "
              f"{npz_bytes(s=np.packbits(snn, axis=-1)) / 1e6:.2f} MB, uint8 npz {npz_bytes(s=snn) / 1e6:.2f} MB")
        print(f"  recurrent weights {n}x{n} float32: {n * n * 4 / 1e6:.2f} MB")
    # one split-half diagram set: 2 halves x 50 resamples x (150 H0 + ~3 H1) bars
    dgms = rng.random((100, 153, 2)).astype(np.float64)
    print(f"split-half diagram set (100 diagrams x ~153 bars, float64): {npz_bytes(d=dgms) / 1e6:.2f} MB, "
          f"float32 {npz_bytes(d=dgms.astype(np.float32)) / 1e6:.2f} MB")


if __name__ == "__main__":
    inventory()
    steinmetz_counts()
    masked_vs_sliced()
    sizes()
