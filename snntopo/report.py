"""Static markdown reports over one or more append-only atlas run directories."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .atlas import load_signature_diagrams, read_tables
from .figures import (plot_accuracy_distance, plot_accuracy_distribution,
                      plot_comparison_bars, plot_signature_diagrams)
from .search import ACCURACY_FLOOR
from .tasks import TASKS

N_REPRESENTATIVES = 5


def _markdown_table(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No rows._\n"
    table = frame.reindex(columns=columns).copy()
    for column in ("accuracy", "objective_distance", "distance", "null_mean", "null_q95", "p_value"):
        if column in table:
            table[column] = table[column].map(lambda x: f"{x:.4g}" if pd.notna(x) else "")
    headers = [str(column) for column in table.columns]
    rows = []
    for values in table.fillna("").itertuples(index=False, name=None):
        rows.append("| " + " | ".join(str(value).replace("|", "\\|") for value in values) + " |")
    return "\n".join([
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *rows,
        "",
    ])


def _signature_table(rows: pd.DataFrame) -> pd.DataFrame:
    """One row per (entry, condition, dim). The flat "sum.{cond}_H{d}_{stat}" columns are
    unioned across every dataset in the atlas, so pivoting them into headers gives a
    hundred-column table that is mostly another dataset's empty conditions."""
    records = []
    for _, row in rows.iterrows():  # itertuples mangles the "sum.{cond}_H{d}" column names
        stats = {column[4:]: row[column] for column in rows.columns
                 if column.startswith("sum.") and pd.notna(row[column])}
        for key in sorted(k for k in stats if k.endswith("_n")):
            condition, dim = key[:-len("_n")].rsplit("_H", 1)
            records.append({"entry_id": row["entry_id"], "session_id": row["session_id"],
                            "condition": condition, "dim": f"H{dim}", "n": int(stats[key]),
                            "total_persistence": stats.get(f"{condition}_H{dim}_total_persistence"),
                            "max_persistence": stats.get(f"{condition}_H{dim}_max_persistence"),
                            "raw_diameter": stats.get(f"{condition}_raw_diameter")})
    if not records:  # every condition was too thin to compute (see TopoConfig.min_trials)
        return pd.DataFrame(columns=["entry_id", "session_id", "condition", "dim", "n"])
    table = pd.DataFrame(records)
    for column in ("total_persistence", "max_persistence", "raw_diameter"):
        table[column] = table[column].map(lambda x: f"{x:.4g}" if pd.notna(x) else "")
    return table.sort_values(["entry_id", "condition", "dim"])


def _best_objective_entries(entries: pd.DataFrame) -> pd.DataFrame:
    """Lowest-distance matched entries that meet the search accuracy floor."""
    feasible = entries.dropna(subset=["accuracy", "objective_distance"])
    return feasible[feasible["accuracy"] >= ACCURACY_FLOOR].sort_values("objective_distance").head(N_REPRESENTATIVES)


def _is_matched_task(source: str) -> bool:
    task = TASKS.get(source)
    return task is not None and task.bio_match is not None


def _read_runs(run_dirs: list[Path]) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Path]]:
    entry_frames, distance_frames, signature_roots = [], [], {}
    for run_dir in run_dirs:
        entries, distances = read_tables(run_dir)
        if not entries.empty:
            entries = entries.copy()
            entries["run_dir"] = str(run_dir)
            entry_frames.append(entries)
            for row in entries.dropna(subset=["signature_file"]).itertuples():
                signature_roots[row.entry_id] = run_dir / row.signature_file
        if not distances.empty:
            distances = distances.copy()
            distances["run_dir"] = str(run_dir)
            distance_frames.append(distances)
    return (pd.concat(entry_frames, ignore_index=True) if entry_frames else pd.DataFrame(),
            pd.concat(distance_frames, ignore_index=True) if distance_frames else pd.DataFrame(),
            signature_roots)


def write_report(run_dirs: list[Path], out_dir: Path) -> Path:
    """Write a combined atlas report and tables. Missing artifact types are omitted."""
    run_dirs = [Path(path) for path in run_dirs]
    out_dir = Path(out_dir)
    figures = out_dir / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    entries, distances, signatures = _read_runs(run_dirs)
    entries.to_csv(out_dir / "entries.csv", index=False)
    distances.to_csv(out_dir / "distances.csv", index=False)
    entries.to_parquet(out_dir / "entries.parquet", index=False)
    distances.to_parquet(out_dir / "distances.parquet", index=False)

    lines = ["# snntopo atlas report", "", "## Inputs", ""]
    lines.extend(f"- `{run_dir}`" for run_dir in run_dirs)
    lines.append("")
    if entries.empty:
        lines.extend(["## Atlas status", "", "_No atlas records found._", ""])
        report = out_dir / "report.md"
        report.write_text("\n".join(lines))
        return report

    snn = entries[entries["kind"] == "snn"].copy()
    lines.extend(["## Status by task", ""])
    if snn.empty:
        lines.append("_No SNN task rows._\n")
    else:
        status = (snn.groupby(["source", "status"]).size().unstack(fill_value=0)
                  .reindex(columns=["ok", "degenerate", "failed", "timeout"], fill_value=0).reset_index())
        lines.append(_markdown_table(status, list(status.columns)))

    # A reference session is recomputed in every run that needs it (a generic task pulls
    # all three datasets'), and its entry_id is dataset+session, so duplicates are the
    # same signature. SNN entry_ids are per-run trial numbers and must not be deduped.
    bio = entries[entries["kind"] == "bio"].drop_duplicates(subset="entry_id")
    for dataset, rows in bio.groupby("source"):
        lines.extend([f"## Bio signature: {dataset}", ""])
        summary = _signature_table(rows)
        lines.append(_markdown_table(summary, list(summary.columns)))
        diagrams = {row.entry_id: load_signature_diagrams(signatures[row.entry_id])
                    for row in rows.itertuples() if row.entry_id in signatures and signatures[row.entry_id].exists()}
        if diagrams:
            name = f"{dataset}_reference_diagrams.png"
            plot_signature_diagrams(diagrams, figures / name, f"{dataset} reference sessions")
            lines.extend([f"![{dataset} diagrams](figures/{name})", ""])
    # astype(bool): on an empty frame map() yields an object-dtype Series, which pandas
    # reads as a column selector instead of a mask (bio-only runs then lose every column).
    is_matched = snn["source"].map(_is_matched_task).astype(bool)
    matched = snn[is_matched]
    representatives: dict[str, pd.DataFrame] = {}
    for task, rows in matched.groupby("source"):
        best = _best_objective_entries(rows)
        representatives[task] = best
        lines.extend([f"## Matched task: {task}", ""])
        scored = rows.dropna(subset=["accuracy", "objective_distance"])
        if not scored.empty:
            name = f"{task}_accuracy_distance.png"
            plot_accuracy_distance(scored, figures / name, f"{task}: accuracy versus topology", set(best.entry_id))
            lines.extend([f"![{task} objective ranking](figures/{name})", ""])
        lines.extend(["### Best feasible entries", "", _markdown_table(best, ["entry_id", "accuracy", "objective_distance", "status"])])

    generic = snn[~is_matched]
    for task, rows in generic.groupby("source"):
        lines.extend([f"## Generic task: {task}", ""])
        usable = rows.dropna(subset=["accuracy"])
        representatives[task] = usable.nlargest(N_REPRESENTATIVES, "accuracy")
        if not usable.empty:
            name = f"{task}_accuracy_distribution.png"
            plot_accuracy_distribution(usable, figures / name, f"{task}: accuracy distribution")
            lines.extend([f"![{task} accuracy](figures/{name})", ""])
        counts = rows["nearest_bio"].dropna().value_counts().rename_axis("nearest_bio").reset_index(name="count")
        lines.extend(["### Nearest bio signatures", "", _markdown_table(counts, ["nearest_bio", "count"])])

    if not distances.empty:
        lines.extend([
            "## Distance results", "", "Every distance includes its resampling null mean and p-value (D7). "
            "This report shows the best feasible matched entries by topology objective, the top five generic entries by accuracy, "
            "and bio split-half rows; the complete table is [`distances.csv`](distances.csv).", "",
        ])
        bio_ids = set(bio["entry_id"])
        bio_distances = distances[(distances["entry_id"].isin(bio_ids)) & (distances["target"] == "self")] \
            .drop_duplicates(subset=["entry_id", "condition", "dim", "metric"])
        if not bio_distances.empty:
            lines.extend(["### Bio split-half nulls", "", _markdown_table(
                bio_distances, ["entry_id", "target", "condition", "dim", "metric", "distance", "null_mean", "null_q95", "p_value", "n_resamples"]
            )])
        for source, representative_rows in representatives.items():
            task_distances = distances[distances["entry_id"].isin(representative_rows["entry_id"])]
            if task_distances.empty:
                continue
            lines.extend([f"### {source}", "", _markdown_table(
                task_distances, ["entry_id", "target", "condition", "dim", "metric", "distance", "null_mean", "null_q95", "p_value", "n_resamples"]
            )])
            name = f"{source}_distance_bars.png"
            plot_comparison_bars(task_distances, figures / name)
            lines.extend([f"![{source} distances](figures/{name})", ""])

    report = out_dir / "report.md"
    report.write_text("\n".join(lines))
    return report
