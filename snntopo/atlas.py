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

from . import objective
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


def rescore(run_dir, weight: float = objective.STRUCTURE_WEIGHT) -> pd.DataFrame:
    """Re-score every snn record in a finished run under a different objective weight,
    with no retraining or re-measuring -- lets an objective change (or weight) be
    checked offline against a completed search before spending any GPU time."""
    records = read_records(run_dir)
    target_counts = {r.entry_id: objective.feature_counts(r.summary) for r in records if r.kind == "bio"}
    rows = []
    for r in records:
        if r.kind != "snn":
            continue
        result = objective.score(r.distances, r.summary, target_counts, weight)
        row = {
            "entry_id": r.entry_id, "accuracy": r.accuracy, "status": r.status,
            "objective_distance": r.objective_distance,
            "rescored_distance_ratio": result["distance_ratio"] if result else None,
            "rescored_structure_penalty": result["structure_penalty"] if result else None,
            "rescored_objective_distance": result["objective_distance"] if result else None,
        }
        for k, v in (r.model or {}).items():
            row[f"model.{k}"] = v
        rows.append(row)
    return pd.DataFrame(rows)


def bio_entry(session: BioSession, topo: TopoConfig, run_dir, siblings: list[BioSession] | None = None) -> AtlasRecord:
    """A bio session's signature plus its split-half null, appended to the atlas. If
    `siblings` (other reference sessions of the same dataset) are given, also compares
    against each of them -- D18: bio-vs-bio distances land in distances.csv alongside
    SNN-vs-bio ones, as the "how far is far" baseline. `compare` is symmetric, so pass
    only already-processed siblings (e.g. earlier ones in a loop) to avoid computing
    each pair twice."""
    entry_id = f"bio:{session.dataset}:{session.session_id}"
    sig = compute_signature(session.activity, topo)
    sig_path = Path(run_dir) / "signatures" / f"{file_id(entry_id)}.npz"
    save_signature(sig_path, sig)
    distances = split_half_null(session.activity, list(sig.diagrams), topo)
    conditions = list(sig.diagrams)
    for sib in (siblings or []):
        target = f"bio:{sib.dataset}:{sib.session_id}"
        distances += compare(session.activity, sib.activity, target, conditions, topo)
    record = AtlasRecord(
        entry_id=entry_id, kind="bio", source=session.dataset, status="ok", session_id=session.session_id,
        signature_file=str(sig_path.relative_to(run_dir)), summary=signature_summary(sig),
        distances=distances,
        meta={**session.meta, "skipped_conditions": sig.skipped, "topo": asdict(topo)},
    )
    append_record(run_dir, record)
    return record


def snn_entry(entry_id: str, task: Task, model_cfg: ModelConfig, train_cfg: TrainConfig, topo: TopoConfig,
              bio_refs: list[BioSession], run_dir, device: str, n_eval: int = 340,
              target_counts: dict[str, dict] | None = None,
              weight: float = objective.STRUCTURE_WEIGHT) -> AtlasRecord:
    """Build, train, evaluate and measure one SNN config; always returns (and appends)
    a record, whatever happens. Matched tasks are compared per action condition against
    `bio_refs` (their dataset's reference sessions) and get objective_distance from
    objective.score (null-normalized distance + a structural penalty; see objective.py).
    `target_counts` is bio-reference feature counts keyed by "bio:{dataset}:{session_id}"
    (objective.feature_counts of each ref's summary); pass a precomputed map to avoid
    recomputing ref signatures on every trial (run_search does this). None recomputes it
    here as a fallback for direct/manual calls (e.g. cli.cmd_snn). Generic tasks are
    compared on the "all" condition against every ref (normally all datasets'
    references) and get nearest_bio instead of an objective."""
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
                       "curve_file": str(curve_path.relative_to(run_dir)), "topo": asdict(topo)}
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

        if task.bio_match:
            counts = target_counts
            if counts is None:
                counts = {}
                for ref in bio_refs:
                    ref_sig = compute_signature(ref.activity, topo)
                    counts[f"bio:{ref.dataset}:{ref.session_id}"] = objective.feature_counts(signature_summary(ref_sig))
            result_score = objective.score(record.distances, record.summary, counts, weight)
            if result_score is not None:
                record.objective_distance = result_score["objective_distance"]
                record.distance_ratio = result_score["distance_ratio"]
                record.structure_penalty = result_score["structure_penalty"]
                record.objective_terms = result_score["objective_terms"]
                record.objective_version = result_score["objective_version"]
        else:
            # D4: generic tasks stay accuracy-only; no structural penalty applies here,
            # just the closest bio target by raw mean distance.
            wass = [d for d in record.distances if d.target != "self" and d.metric == "wasserstein"]
            if wass:
                by_target = pd.DataFrame([asdict(d) for d in wass]).groupby("target")["distance"].mean()
                record.nearest_bio = str(by_target.idxmin())
    except Exception as e:
        record.status = "failed"
        record.error = f"{type(e).__name__}: {e}"
        log.warning(f"[{entry_id}] failed:\n{traceback.format_exc()}")
    append_record(run_dir, record)
    return record
