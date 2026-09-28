"""The v3 dataset: recipe-identified activities and the rows measured on them.

Five append-only record types live as jsonl in a run directory, one file per type (per
shard): activities, signatures, nulls, comparisons, derived. Every row carries `run_id`.
A measured number is never rewritten; a correction is a `derived` row next to it.
Blobs (diagrams, split-half halves, spikes, weights) live in a write-once store shared
by all runs, keyed by content or by a caller-given key.

    results/runs/<YYYYMMDD-HHMM>-<spec-stem>/run.json
    results/runs/<id>/<type>[.s<i>of<N>].jsonl
    results/store/<kind>/<key>.<ext>

Construction ids: `topo_id` names how a signature was computed and `cmp_id` how a
distance/null was computed. Rows with different ids are never pooled, so `load` takes
both as required arguments and returns only matching rows.
"""
from __future__ import annotations

import glob
import hashlib
import io
import json
import os
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from . import config
from .contracts import TopoConfig
from .topology.pipeline import PIPELINE_VERSION
from .topology.stats import STATS_VERSION

RECORD_TYPES = ("activities", "signatures", "nulls", "comparisons", "derived")

KEYS = {
    "activities": ("activity_id",),
    "signatures": ("activity_id", "condition", "topo_id", "dim"),
    "nulls": ("activity_id", "condition", "topo_id", "cmp_id", "h", "seed", "metric", "dim"),
    "comparisons": ("pair_key", "condition", "topo_id", "cmp_id", "h", "seed", "metric", "dim"),
    "derived": ("source_key", "derivation_id"),
}

STORE_KINDS = ("diagrams", "halves", "spikes", "weights")


# --- ids -----------------------------------------------------------------------------

def _json_default(x):
    # numpy scalars become the Python value they hold, so a recipe built with np.int64(14)
    # hashes like one built with 14; anything else (arrays, objects) is a bug in the caller
    if isinstance(x, np.generic):
        return x.item()
    raise TypeError(f"not JSON-serializable: {type(x).__name__}")


def canonical_json(obj) -> str:
    """Sorted keys, no whitespace. Floats stay floats (16.0 is not 16), so a recipe's
    types are part of its identity."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=_json_default, allow_nan=False)


def short_hash(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode()).hexdigest()[:16]


def recipe_id(recipe: dict) -> str:
    """activity_id: the hash of a fully resolved recipe."""
    return short_hash(recipe)


def topo_id(topo: TopoConfig) -> str:
    """Everything that changes a signature. residualize_raw_diameter is a correction
    (a derived row), not part of the construction."""
    return short_hash({"n_pca": topo.n_pca, "smooth_win": topo.smooth_win, "maxdim": topo.maxdim,
                       "min_trials": topo.min_trials, "normalization": "unit_diameter",
                       "filtration": "rips", "pipeline_version": PIPELINE_VERSION})


def cmp_id(metrics, n_resamples: int) -> str:
    """Everything that changes a distance or null at fixed h and seed."""
    return short_hash({"metrics": sorted(metrics), "n_resamples": n_resamples,
                       "null": "split_half_pooled", "stats_version": STATS_VERSION})


def derivation_id(name: str, constants: dict | None = None) -> str:
    return short_hash({"name": name, "constants": constants or {}})


def pair_key(a_id: str, b_id: str) -> str:
    """Order-free: compare is symmetric at a fixed seed; rows keep a, b in spec order."""
    return "__".join(sorted((a_id, b_id)))


def row_key(record_type: str, row: dict) -> str:
    """A row's key as one string, e.g. for a derived row's `source_key`."""
    return canonical_json({"type": record_type, **{k: row[k] for k in KEYS[record_type]}})


# --- rows ----------------------------------------------------------------------------

def shard_suffix(shard: tuple[int, int] | None) -> str:
    return "" if shard is None else f".s{shard[0]}of{shard[1]}"


class RunWriter:
    """Appends rows to one run directory's jsonl files, one writer per file. Each row is
    one write() of one line, flushed, so a crash can tear at most the last line.
    Reopening a file whose last line is torn truncates it back to the last newline
    first; otherwise the next row would be glued onto the fragment."""

    def __init__(self, run_dir, shard: tuple[int, int] | None = None):
        self.run_dir = Path(run_dir)
        self.run_id = self.run_dir.name
        self.shard = shard
        self._files = {}
        self.run_dir.mkdir(parents=True, exist_ok=True)

    def path(self, record_type: str) -> Path:
        return self.run_dir / f"{record_type}{shard_suffix(self.shard)}.jsonl"

    def write(self, record_type: str, row: dict) -> None:
        missing = [k for k in KEYS[record_type] if k not in row]
        if missing:
            raise KeyError(f"{record_type} row missing key fields {missing}")
        f = self._files.get(record_type)
        if f is None:
            f = self._files[record_type] = self._open(self.path(record_type))
        f.write(json.dumps({**row, "run_id": self.run_id}, default=_json_default) + "\n")
        f.flush()

    @staticmethod
    def _open(path: Path):
        if path.exists() and path.stat().st_size > 0:
            with open(path, "rb+") as f:
                data = f.read()
                if not data.endswith(b"\n"):
                    f.truncate(data.rfind(b"\n") + 1)
                    warnings.warn(f"{path}: dropped torn last line before appending")
        return open(path, "a")

    def close(self) -> None:
        for f in self._files.values():
            f.close()
        self._files.clear()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def read_jsonl(path) -> list[dict]:
    """A torn (unparsable) last line is dropped with a warning; any other bad line raises."""
    lines = Path(path).read_text().splitlines()
    rows = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as e:
            if i == len(lines) - 1:
                warnings.warn(f"{path}: dropped torn last line {i + 1}")
            else:
                raise ValueError(f"{path}:{i + 1}: corrupt row: {e}") from e
    return rows


def run_dirs(pattern: str = "*") -> list[Path]:
    """Run directories under results/runs matching `pattern`, oldest first (ids start
    with a timestamp)."""
    return sorted(p for p in (Path(config.RESULTS_DIR) / "runs").glob(pattern) if p.is_dir())


def _as_run_dirs(runs) -> list[Path]:
    if isinstance(runs, (str, Path)):
        runs = [runs]
    out = []
    for r in runs:
        matches = sorted(glob.glob(str(r))) if any(c in str(r) for c in "*?[") else [r]
        out.extend(Path(m) for m in matches)
    return out


def load(runs, topo_id: str, cmp_id: str) -> dict[str, pd.DataFrame]:
    """-> {record_type: DataFrame} over every jsonl (all shards) of `runs` (a run dir,
    a glob, or a list of either). Rows are deduped on their keys, first seen wins, in
    run order then file order, except that an activity's ok/degenerate row beats a
    `failed` one (a --retry-failed rerun appends the success after the failure). signatures are filtered to `topo_id`; nulls and
    comparisons to both ids. activities and derived rows are returned whole."""
    tables = {}
    dirs = _as_run_dirs(runs)
    for t in RECORD_TYPES:
        rows = []
        for d in dirs:
            for path in sorted(d.glob(f"{t}.jsonl")) + sorted(d.glob(f"{t}.s*of*.jsonl")):
                rows.extend(read_jsonl(path))
        df = pd.DataFrame(rows, columns=None if rows else list(KEYS[t]) + ["run_id"])
        if t in ("signatures", "nulls", "comparisons"):
            df = df[df["topo_id"] == topo_id]
        if t in ("nulls", "comparisons"):
            df = df[df["cmp_id"] == cmp_id]
        if t == "activities" and not df.empty:
            df = df.sort_values("status", key=lambda s: s == "failed", kind="stable")
        tables[t] = df.drop_duplicates(subset=list(KEYS[t]), keep="first").reset_index(drop=True)
    return tables


# --- store ---------------------------------------------------------------------------

def _store_root(root) -> Path:
    return Path(root) if root is not None else Path(config.RESULTS_DIR) / "store"


def store_path(kind: str, key: str, ext: str, root=None) -> Path:
    if kind not in STORE_KINDS:
        raise ValueError(f"unknown store kind {kind!r}; one of {STORE_KINDS}")
    return _store_root(root) / kind / f"{key}.{ext}"


def store_put_bytes(kind: str, key: str, ext: str, data: bytes, root=None) -> Path:
    """Write-once: an existing blob is left alone. The blob lands via tmp + os.replace,
    so a reader never sees a partial file; write it before the row that points at it."""
    path = store_path(kind, key, ext, root)
    if path.exists():
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    return path


def store_get_bytes(kind: str, key: str, ext: str, root=None) -> bytes:
    return store_path(kind, key, ext, root).read_bytes()


def store_has(kind: str, key: str, ext: str, root=None) -> bool:
    return store_path(kind, key, ext, root).exists()


def array_hash(arrays: dict[str, np.ndarray]) -> str:
    """Content hash over names, dtypes, shapes and bytes. npz files themselves aren't
    byte-stable (zip timestamps), so blobs are keyed by this instead."""
    h = hashlib.sha256()
    for name in sorted(arrays):
        a = np.ascontiguousarray(arrays[name])
        h.update(f"{name}|{a.dtype.str}|{a.shape}|".encode())
        h.update(a.tobytes())
    return h.hexdigest()[:16]


def store_put_npz(kind: str, arrays: dict[str, np.ndarray], key: str | None = None, root=None) -> str:
    """-> key (array_hash(arrays) unless given)."""
    key = key or array_hash(arrays)
    buf = io.BytesIO()
    np.savez_compressed(buf, **arrays)
    store_put_bytes(kind, key, "npz", buf.getvalue(), root)
    return key


def store_get_npz(kind: str, key: str, root=None) -> dict[str, np.ndarray]:
    with np.load(store_path(kind, key, "npz", root)) as z:
        return {name: z[name] for name in z.files}
