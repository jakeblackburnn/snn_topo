"""Static markdown reports over one or more append-only atlas run directories."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .atlas import load_signature_diagrams, read_tables
from .figures import (plot_accuracy_distance, plot_accuracy_distribution,
                      plot_comparison_bars, plot_signature_diagrams)


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


def _pareto_front(entries: pd.DataFrame) -> pd.DataFrame:
    """Nondominated rows for maximize-accuracy, minimize-distance objectives."""
    usable = entries.dropna(subset=["accuracy", "objective_distance"]).copy()
    keep = []
    for index, row in usable.iterrows():
        dominates = ((usable["accuracy"] >= row.accuracy)
                     & (usable["objective_distance"] <= row.objective_distance)
                     & ((usable["accuracy"] > row.accuracy)
                        | (usable["objective_distance"] < row.objective_distance))).any()
        if not dominates:
            keep.append(index)
    return usable.loc[keep].sort_values(["objective_distance", "accuracy"], ascending=[True, False])


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

    bio = entries[entries["kind"] == "bio"]
    for dataset, rows in bio.groupby("source"):
        lines.extend([f"## Bio signature: {dataset}", ""])
        summary_columns = ["entry_id", "session_id"] + [
            f"sum.{condition}_H{dim}_{stat}"
            for condition in sorted({column.split("_H", 1)[0][4:] for column in rows.columns
                                     if column.startswith("sum.") and "_H" in column})
            for dim in range(3) for stat in ("n", "total_persistence", "max_persistence")
            if f"sum.{condition}_H{dim}_{stat}" in rows
        ]
        lines.append(_markdown_table(rows, summary_columns))
        diagrams = {row.entry_id: load_signature_diagrams(signatures[row.entry_id])
                    for row in rows.itertuples() if row.entry_id in signatures and signatures[row.entry_id].exists()}
        if diagrams:
            name = f"{dataset}_reference_diagrams.png"
            plot_signature_diagrams(diagrams, figures / name, f"{dataset} reference sessions")
            lines.extend([f"![{dataset} diagrams](figures/{name})", ""])
        bio_distances = distances[distances["entry_id"].isin(rows["entry_id"])] if not distances.empty else distances
        if not bio_distances.empty:
            lines.extend(["### Split-half distance results", "", _markdown_table(
                bio_distances, ["entry_id", "target", "condition", "dim", "metric", "distance", "null_mean", "null_q95", "p_value", "n_resamples"]
            )])

    matched_tasks = set(snn.loc[snn.get("objective_distance", pd.Series(dtype=float)).notna(), "source"])
    matched = snn[snn["source"].isin(matched_tasks)]
    for task, rows in matched.groupby("source"):
        front = _pareto_front(rows)
        name = f"{task}_accuracy_distance.png"
        plot_accuracy_distance(rows.dropna(subset=["accuracy", "objective_distance"]), figures / name,
                               f"{task}: accuracy versus topology", set(front.entry_id))
        lines.extend([f"## Matched task: {task}", "", f"![{task} Pareto plot](figures/{name})", "",
                      "### Pareto front", "", _markdown_table(front, ["entry_id", "accuracy", "objective_distance", "status"])])

    generic = snn[~snn["source"].isin(matched_tasks)]
    for task, rows in generic.groupby("source"):
        lines.extend([f"## Generic task: {task}", ""])
        usable = rows.dropna(subset=["accuracy"])
        if not usable.empty:
            name = f"{task}_accuracy_distribution.png"
            plot_accuracy_distribution(usable, figures / name, f"{task}: accuracy distribution")
            lines.extend([f"![{task} accuracy](figures/{name})", ""])
        counts = rows["nearest_bio"].dropna().value_counts().rename_axis("nearest_bio").reset_index(name="count")
        lines.extend(["### Nearest bio signatures", "", _markdown_table(counts, ["nearest_bio", "count"])])

    if not distances.empty:
        lines.extend(["## Distance results", "", "Every distance includes its resampling null mean and p-value (D7).", ""])
        for source, row_ids in snn.groupby("source").groups.items():
            task_distances = distances[distances["entry_id"].isin(entries.loc[row_ids, "entry_id"])]
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
