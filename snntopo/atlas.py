"""Atlas entries: how a bio session or an SNN config becomes one AtlasRecord, and how
records are stored.

Storage, per run directory:
  atlas.jsonl            one AtlasRecord per line, appended as entries finish (crash-safe)
  signatures/<id>.npz    persistence diagrams, keyed "{cond}_H{d}"
  curves/<id>.csv        SNN training curves
  entries.csv / distances.csv / *.parquet   flat tables written by write_tables()
"""
import json
import traceback
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from .contracts import AtlasRecord, BioSession, DistanceResult, ModelConfig, Signature, Task, TopoConfig, TrainConfig
from .evaluate import evaluate
from .logging_utils import get_logger
from .models import build_model
from .topology.pipeline import compute_signature
from .topology.stats import compare, split_half_null
from .training import train


def file_id(entry_id: str) -> str:
    return entry_id.replace(":", "__").replace("/", "_")


def save_signature(path, sig: Signature) -> None:
    arrays = {f"{cond}_H{d}": dgm for cond, dgms in sig.diagrams.items() for d, dgm in enumerate(dgms)}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, **arrays)


def load_signature_diagrams(path) -> dict[str, np.ndarray]:
    with np.load(path) as f:
        return {k: f[k] for k in f.files}


def signature_summary(sig: Signature) -> dict:
    out = {}
    for cond, dgms in sig.diagrams.items():
        out[f"{cond}_raw_diameter"] = sig.raw_diameter[cond]
        for d, dgm in enumerate(dgms):
            finite = dgm[np.isfinite(dgm[:, 1])]
            pers = finite[:, 1] - finite[:, 0]
            out[f"{cond}_H{d}_n"] = int(len(dgm))
            out[f"{cond}_H{d}_total_persistence"] = float(pers.sum()) if len(pers) else 0.0
            out[f"{cond}_H{d}_max_persistence"] = float(pers.max()) if len(pers) else 0.0
    return out


def append_record(run_dir, record: AtlasRecord) -> None:
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    with open(run_dir / "atlas.jsonl", "a") as f:
        f.write(json.dumps(asdict(record), default=float) + "\n")


def read_records(run_dir) -> list[AtlasRecord]:
    path = Path(run_dir) / "atlas.jsonl"
    if not path.exists():
        return []
    records = []
    for line in path.read_text().splitlines():
        raw = json.loads(line)
        raw["distances"] = [DistanceResult(**d) for d in raw["distances"]]
        records.append(AtlasRecord(**raw))
    return records


def read_tables(run_dir) -> tuple[pd.DataFrame, pd.DataFrame]:
    """-> (entries: one row per record, model/train/meta/summary flattened with
    prefixes; distances: one row per DistanceResult with its entry_id)."""
    entries, distances = [], []
    for r in read_records(run_dir):
        row = {k: v for k, v in asdict(r).items() if k not in ("model", "train", "summary", "distances", "meta")}
        for prefix, d in (("model", r.model), ("train", r.train), ("meta", r.meta), ("sum", r.summary)):
            for k, v in (d or {}).items():
                row[f"{prefix}.{k}"] = v if np.isscalar(v) or v is None else json.dumps(v)
        entries.append(row)
        distances += [{"entry_id": r.entry_id, **asdict(d)} for d in r.distances]
    return pd.DataFrame(entries), pd.DataFrame(distances)


def write_tables(run_dir) -> None:
    entries, distances = read_tables(run_dir)
    for name, df in (("entries", entries), ("distances", distances)):
        df.to_csv(Path(run_dir) / f"{name}.csv", index=False)
        df.to_parquet(Path(run_dir) / f"{name}.parquet", index=False)


def bio_entry(session: BioSession, topo: TopoConfig, run_dir) -> AtlasRecord:
    """A bio session's signature plus its split-half null, appended to the atlas."""
    entry_id = f"bio:{session.dataset}:{session.session_id}"
    sig = compute_signature(session.activity, topo)
    sig_path = Path(run_dir) / "signatures" / f"{file_id(entry_id)}.npz"
    save_signature(sig_path, sig)
    record = AtlasRecord(
        entry_id=entry_id, kind="bio", source=session.dataset, status="ok", session_id=session.session_id,
        signature_file=str(sig_path.relative_to(run_dir)), summary=signature_summary(sig),
        distances=split_half_null(session.activity, list(sig.diagrams), topo),
        meta={**session.meta, "skipped_conditions": sig.skipped},
    )
    append_record(run_dir, record)
    return record


def snn_entry(entry_id: str, task: Task, model_cfg: ModelConfig, train_cfg: TrainConfig, topo: TopoConfig,
              bio_refs: list[BioSession], run_dir, device: str, n_eval: int = 340) -> AtlasRecord:
    """Build, train, evaluate and measure one SNN config; always returns (and appends)
    a record, whatever happens. Matched tasks are compared per action condition against
    `bio_refs` (their dataset's reference sessions) and get objective_distance = mean
    Wasserstein over those conditions, dims and refs. Generic tasks are compared on the
    "all" condition against every ref (normally all datasets' references) and get
    nearest_bio instead of an objective."""
    log = get_logger()
    run_dir = Path(run_dir)
    record = AtlasRecord(entry_id=entry_id, kind="snn", source=task.name, status="failed",
                         model=model_cfg.to_dict(), train=asdict(train_cfg))
    try:
        model = build_model(model_cfg, task.n_in, task.n_actions).to(device)
        result = train(model, task, train_cfg, device)
        curve_path = run_dir / "curves" / f"{file_id(entry_id)}.csv"
        curve_path.parent.mkdir(parents=True, exist_ok=True)
        result["curve"].to_csv(curve_path, index=False)
        record.meta = {"train_elapsed_s": result["elapsed_s"], "n_updates_done": result["n_updates_done"],
                       "curve_file": str(curve_path.relative_to(run_dir))}
        if result["status"] == "failed":
            record.error = result["error"]
            append_record(run_dir, record)
            return record

        record.accuracy, activity = evaluate(model, task, n_eval, device)
        sig = compute_signature(activity, topo)
        sig_path = run_dir / "signatures" / f"{file_id(entry_id)}.npz"
        save_signature(sig_path, sig)
        record.signature_file = str(sig_path.relative_to(run_dir))
        record.summary = signature_summary(sig)
        record.meta["skipped_conditions"] = sig.skipped
        record.status = "degenerate" if any(c in sig.skipped for c in task.action_names) else result["status"]

        conditions = [c for c in task.action_names if c in sig.diagrams] if task.bio_match else ["all"]
        record.distances = split_half_null(activity, list(sig.diagrams), topo)
        for ref in bio_refs:
            target = f"bio:{ref.dataset}:{ref.session_id}"
            record.distances += compare(activity, ref.activity, target, conditions, topo)

        wass = [d for d in record.distances if d.target != "self" and d.metric == "wasserstein"]
        if task.bio_match and wass:
            record.objective_distance = float(np.mean([d.distance for d in wass]))
        elif not task.bio_match and wass:
            by_target = pd.DataFrame([asdict(d) for d in wass]).groupby("target")["distance"].mean()
            record.nearest_bio = str(by_target.idxmin())
    except Exception as e:
        record.status = "failed"
        record.error = f"{type(e).__name__}: {e}"
        log.warning(f"[{entry_id}] failed:\n{traceback.format_exc()}")
    append_record(run_dir, record)
    return record
