"""The poster's figures, built from tables the overview scripts already wrote. No new runs.

Reads results/analysis/{snn_vs_bio,zoo_overview,topo_or_noise}/, the E18 run and the two grid
runs; writes each figure as PDF and 300 dpi PNG into docs/poster/figures/. The draft plots in
snn_vs_bio.py, bio_overview.py and zoo_overview.py are left as they are.

The trajectory and pipeline figures need point clouds, which no run stores. They are rebuilt
from the activity's recipe and kept in results/analysis/poster_figures/clouds/. A brain cloud
takes seconds; a model cloud retrains that one network (about a minute, no weights were kept).
A rebuilt cloud is used only if its diagram equals the stored one.

Sizes assume a 48 x 36 in landscape poster in three columns: COLUMN_IN is one column's width,
and fonts are 24 pt at that size. Change COLUMN_IN if the layout changes. The poster uses
results, table, trajectories, engagement, pipeline and rips; main, noise, nogo, zoo and torus
are kept for results.md and handouts.

The clique figures (clique_method, clique_model, clique_results, clique_table) are the
restarted poster's: they read results/analysis/clique_probe/ (`scripts/clique_probe.py`) and
draw clique_method from made-up place cells.

    python scripts/poster_figures.py                                   # every figure
    python scripts/poster_figures.py results table                     # only these
    python scripts/poster_figures.py trajectory <run_dir> <activity_id>  # rotatable 3D view
"""
import sys
import zlib
from itertools import combinations
from pathlib import Path

import matplotlib

if sys.argv[1:2] != ["trajectory"]:  # the trajectory view needs a window
    matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.ndimage import uniform_filter1d
from scipy.spatial.distance import pdist, squareform

from scripts import clique_probe
from snntopo import clique, dataset, floor, grid, producers
from snntopo.runner import load_spec
from snntopo.topology.pipeline import build_trajectories, persistence, unit_diameter

ROOT = Path(__file__).parents[1]
ANALYSIS = ROOT / "results" / "analysis"
E18_RUN = ROOT / "results" / "runs" / "20260928-1100-e15_engagement"
GRID_RUNS = {"bio": ROOT / "results" / "runs" / "20261013-1300-bio_grid", "snn": ROOT / "results" / "runs" / "20261013-1300-zoo_grid"}
CLOUDS = ANALYSIS / "poster_figures" / "clouds"
OUT = ROOT / "docs" / "poster" / "figures"

COLUMN_IN = 14.5
CELL = (128, 100)  # the matched size every brain-vs-model panel is drawn at; cells are never pooled
PASSIVE, ENGAGED, SNN, NOGO = "#4477AA", "#228833", "#EE7733", "#AA3377"
NEURON = {"lif": "#777777", "alif": "#4477AA", "izhikevich": "#EE7733"}
WIRING = {"none": "o", "random": "o", "small_world": "s", "scale_free": "^", "modular_hub": "D"}
LOOP = "#CC3311"
CLIQUE = ANALYSIS / "clique_probe"
UNTRAINED, RANDOM, RANDOM_EDGE = "#AA3377", "#BBBBBB", "#777777"

plt.rcParams.update({"font.size": 24, "axes.titlesize": 26, "axes.labelsize": 24, "xtick.labelsize": 22,
                     "ytick.labelsize": 22, "legend.fontsize": 20, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.linewidth": 1.5, "pdf.fonttype": 42})


def save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=300)
    plt.close(fig)


def matched_groups() -> dict[str, pd.DataFrame]:
    """Passive brain, engaged brain, two-choice and no-go SNNs at CELL, as snn_vs_bio.plot_main picks them."""
    acts = pd.read_csv(ANALYSIS / "snn_vs_bio" / "activities.csv")
    acts = acts[acts["skipped"].isna() & (acts["cell_units"] == CELL[0]) & (acts["cell_trials"] == CELL[1])]
    bio = acts[acts["side"] == "bio"]
    snn = acts[(acts["side"] == "snn") & (acts["checkpoint"] == acts["checkpoint"].max()) & (acts["status"] == "ok")]
    return {"passive": bio[bio["select"] == "all"], "engaged": bio[bio["select"] == "responded"],
            "snn": snn[snn["task"] == "steinmetz_2afc"], "nogo": snn[snn["task"] == "steinmetz_nogo"]}


def values(g: dict[str, pd.DataFrame], key: str, measure: str, dim: int = 0) -> np.ndarray:
    return g[key][g[key]["dim"] == dim][measure].dropna().to_numpy(float)


def strip(ax, columns: list[tuple[str, np.ndarray, str]], fmt: str) -> None:
    """One jittered column of dots per group, a bar and the number at its median."""
    rng = np.random.default_rng(0)  # jitter only
    for x, (_, v, color) in enumerate(columns):
        ax.scatter(x + rng.uniform(-0.28, 0.28, len(v)), v, s=70, alpha=0.55, color=color, linewidths=0)
        ax.hlines(np.median(v), x - 0.4, x + 0.4, color="k", lw=4)
        ax.text(x + 0.44, np.median(v), format(np.median(v), fmt), va="center", fontsize=22, fontweight="bold",
                bbox={"facecolor": "white", "alpha": 0.8, "lw": 0, "pad": 2})
    ax.set_xticks(range(len(columns)), [f"{name}\nn={len(v)}" for name, v, _ in columns])
    ax.set_xlim(-0.6, len(columns) - 0.1)


def fig_main() -> None:
    g = matched_groups()
    names = [("passive\nbrain", "passive", PASSIVE), ("engaged\nbrain", "engaged", ENGAGED), ("spiking\nmodels", "snn", SNN)]
    fig, axes = plt.subplots(1, 4, figsize=(2 * COLUMN_IN, 10.5))
    for ax, (measure, title, fmt) in zip(axes, [("total_persistence", "How spread out\nis the path?", ".1f"),
                                                ("participation_ratio", "How many dimensions\ndoes it use?", ".1f"),
                                                ("null_mean", "How much does it change\nbetween halves of the trials?", ".2f")]):
        strip(ax, [(name, values(g, key, measure), color) for name, key, color in names], fmt)
        ax.set_title(title, fontsize=24)
        ax.set_ylim(bottom=0)
    axes[0].set_ylabel("total cluster persistence")
    axes[1].set_ylabel("participation ratio")
    axes[2].set_ylabel("split-half distance")
    ax = axes[3]
    for x, (name, key, color) in enumerate(names):
        r1 = g[key][g[key]["dim"] == 1]["r1"].dropna()
        share = 100 * (r1 >= 1).mean()
        ax.bar(x, share, color=color, width=0.7)
        ax.text(x, share + 1.5, f"{int((r1 >= 1).sum())} of {len(r1)}", ha="center", fontsize=22, fontweight="bold")
    ax.set_xticks(range(len(names)), [name for name, _, _ in names])
    ax.set_title("How many have a loop that\nsurvives resampling?", fontsize=24)
    ax.set(ylabel="% of populations", ylim=(0, 100))
    fig.suptitle("Brains and models differ in spread, dimension and noise, not in robust loops", fontsize=30)
    fig.text(0.5, 0.01, f"Each dot: one brain population (13 sessions) or one trained network, cut to {CELL[0]} neurons x "
             f"{CELL[1]} trials. Bars: medians. Descriptive, no test.", ha="center", fontsize=20)
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    save(fig, "main")


def fig_nogo() -> None:
    g = matched_groups()
    columns = [(name, g[key][g[key]["dim"] == 0]["total_persistence"].dropna().to_numpy(float), color)
               for name, key, color in [("engaged\nbrain", "engaged", ENGAGED), ("models:\n2 choices", "snn", SNN),
                                        ("models:\n+ no-go", "nogo", NOGO)]]
    fig, ax = plt.subplots(figsize=(COLUMN_IN, 10))
    strip(ax, columns, ".1f")
    ax.set(ylabel="total cluster persistence", ylim=(0, None),
           title=f"Models trained with a third action sit\nwith the engaged brain ({len(columns[2][1])} trainings)")
    fig.text(0.5, 0.01, "A lead, not a finding: few trainings, and their average\n"
             "includes a trial type the 2-choice models never see.", ha="center", fontsize=20)
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    save(fig, "nogo")


def fig_engagement() -> None:
    e15 = load_spec(ROOT / "experiments" / "e15_engagement.py")
    t = dataset.load(E18_RUN, dataset.topo_id(e15.TOPO), dataset.cmp_id(e15.CMP["metrics"], e15.CMP["n_resamples"]))
    table, _ = e15.verdict(t)
    pre = e15.PREREG["floor"]
    fl = floor.floor(t, e15.PREREG["criteria"]["dim"], (pre["n_neurons"], pre["n_trials"], pre["noise"]))
    table = table.sort_values("primary").reset_index(drop=True)
    held = ~table["excluded"]
    missed = held & ~table["detected"]
    fig, ax = plt.subplots(figsize=(1.5 * COLUMN_IN, 10))
    ax.axhspan(fl["C_q5"], fl["C_q50"], color="#CC3311", alpha=0.18, lw=0)
    ax.axhspan(fl["B_q50"], fl["B_q95"], color="#4477AA", alpha=0.25, lw=0)
    right = len(table) - 0.4
    ax.text(right, fl["C_q50"], "synthetic: circle vs figure-8 ", ha="right", va="top", fontsize=20, color="#881100")
    ax.text(right, fl["B_q95"] + 0.05, "synthetic: same shape, stretched ", ha="right", va="bottom", fontsize=20, color="#224466")
    ax.scatter(table.index[held], table["primary"][held], s=320, color=ENGAGED, zorder=3, label="engaged vs passive")
    ax.scatter(table.index[missed], table["primary"][missed], s=320, color="#BBBBBB", edgecolors=ENGAGED, linewidths=3,
               zorder=4, label="not significant")
    ax.scatter(table.index[~held], table["primary"][~held], s=320, facecolors="none", edgecolors=ENGAGED, linewidths=3,
               zorder=3, label="session used to design the test")
    ax.scatter(table.index, table["drift_max"], marker="_", s=900, linewidths=4, color="k", zorder=3,
               label="same condition, later in the session")
    ax.axhline(1, color="k", lw=1, ls=":")
    ax.set_xticks(table.index, table["session"])
    ax.set(xlabel="recording session (sorted)", ylabel="difference in loops\n(1 = trial-to-trial noise)", ylim=(0.5, None),
           title=f"Engagement changes the signature in\n{int(table['detected'][held].sum())} of {int(held.sum())} held-out sessions")
    ax.legend(loc="center right", bbox_to_anchor=(1, 0.42), frameon=False)
    fig.tight_layout()
    save(fig, "engagement")


def fig_zoo() -> None:
    acts = pd.read_csv(ANALYSIS / "zoo_overview" / "activities.csv")
    # the 27 plain configurations: variants (Dale, mixed tau, no-go) carry a suffix after a space, rate nets have their own family
    d = acts[(acts["checkpoint"] == acts["checkpoint"].max()) & (acts["status"] == "ok") & acts["skipped"].isna()
             & (acts["dim"] == 1) & (acts["n_hidden"] == 128) & (acts["family"] == "snn")
             & ~acts["config"].str.contains(" ")]
    fig, ax = plt.subplots(figsize=(1.5 * COLUMN_IN, 10))
    rng = np.random.default_rng(0)  # jitter only
    ticks = []
    for i, arch in enumerate(["feedforward", "recurrent", "modular"]):
        for j, neuron in enumerate(["lif", "alif", "izhikevich"]):
            x = 4 * i + j
            group = d[(d["arch"] == arch) & (d["neuron"] == neuron)]
            for wiring, marker in WIRING.items():
                v = group[group["connectivity"] == wiring]["max_persistence"].to_numpy(float)
                ax.scatter(x + rng.uniform(-0.25, 0.25, len(v)), v, s=170, alpha=0.75, color=NEURON[neuron], marker=marker, linewidths=0)
            ax.hlines(group["max_persistence"].median(), x - 0.4, x + 0.4, color="k", lw=4)
        ticks.append((4 * i + 1, arch))
    ax.set_xticks([x for x, _ in ticks], [name for _, name in ticks])
    ax.set(ylabel="longest loop", ylim=(0, None),
           title="Loops appear with adaptive and Izhikevich neurons,\nmostly in modular networks")
    handles = [plt.Line2D([], [], marker="o", ls="", ms=15, color=NEURON[n], label=name)
               for n, name in [("lif", "leaky (LIF)"), ("alif", "adaptive"), ("izhikevich", "Izhikevich")]]
    handles += [plt.Line2D([], [], marker=WIRING[w], ls="", ms=15, color="k", label=name)
                for w, name in [("random", "random"), ("small_world", "small-world"), ("scale_free", "scale-free"),
                                ("modular_hub", "hub-modular")]]
    ax.legend(handles=handles, title="neuron (colour), wiring (shape)", frameon=False, loc="upper left", ncols=2)
    fig.text(0.5, 0.01, "Each dot: one trained network, 128 neurons, 3 seeds per wiring. Bars: medians. "
             "Grouping chosen after looking.", ha="center", fontsize=20)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save(fig, "zoo")


def trial_sweep(ax, a: pd.DataFrame, sweep: pd.DataFrame) -> None:
    """Each brain population's persistence as more trials are averaged, the models at CELL's trials
    and the no-signal ceiling. `a` and `sweep` are topo_or_noise.py's tables at CELL's units."""
    per_pop = sweep.groupby(["group", "activity_id", "trials"])["total_persistence"].mean().reset_index()
    for key, color in [("passive", PASSIVE), ("engaged", ENGAGED)]:
        for _, p in per_pop[per_pop["group"] == key].groupby("activity_id"):
            ax.plot(p["trials"], p["total_persistence"], color=color, alpha=0.25, lw=1.5)
        # medians only where every population of the group reaches the trial count, so the set is fixed
        g = per_pop[per_pop["group"] == key]
        common = g.groupby("trials")["activity_id"].nunique() == g["activity_id"].nunique()
        med = g[g["trials"].isin(common.index[common])].groupby("trials")["total_persistence"].median()
        ax.plot(med.index, med.to_numpy(), color=color, lw=6, marker="o", ms=12)
    snn = a[a["group"] == "snn_2c"]["total_persistence"]
    ax.errorbar(CELL[1], snn.median(), yerr=[[snn.median() - snn.quantile(0.25)], [snn.quantile(0.75) - snn.median()]],
                color=SNN, marker="s", ms=18, lw=4, capsize=10, zorder=5)
    ax.text(CELL[1] + 8, snn.median(), "models", color=SNN, va="center", fontsize=22, fontweight="bold")
    ceiling = sweep["ceiling"].median()
    ax.axhline(ceiling, color="#777777", lw=3, ls=":")
    ax.text(200, ceiling + 0.6, "trials shuffled in time (no signal)", ha="right", va="bottom", fontsize=20, color="#555555")
    ax.set_xticks(sorted(sweep["trials"].unique()))
    ax.set(xlabel="trials averaged", ylim=(0, ceiling + 4))


def fig_noise() -> None:
    """From topo_or_noise.py's tables: cluster persistence against path length, the brain trial
    sweep against the models and a no-signal ceiling, and each loop against its own noise."""
    a = pd.read_csv(ANALYSIS / "topo_or_noise" / "activities.csv")
    a = a[a["cell_units"] == CELL[0]]
    sweep = pd.read_csv(ANALYSIS / "topo_or_noise" / "sweep.csv")
    names = [("passive\nbrain", "passive", PASSIVE), ("engaged\nbrain", "engaged", ENGAGED), ("spiking\nmodels", "snn_2c", SNN)]
    fig, axes = plt.subplots(1, 3, figsize=(2 * COLUMN_IN, 10.5), gridspec_kw={"width_ratios": [1.1, 1.1, 0.9]})

    ax = axes[0]
    for name, key, color in names[::-1]:
        g = a[a["group"] == key]
        ax.scatter(g["L"], g["total_persistence"], s=90, alpha=0.6, color=color, linewidths=0, label=name.replace("\n", " "))
    top = a["L"].max() * 1.05
    ax.plot([0, top], [0, top], color="k", lw=2, ls="--", label="equal")
    ax.set(xlim=(0, top), ylim=(0, top), xlabel="path length (in path widths)", ylabel="total cluster persistence",
           title="Cluster persistence is\nthe length of the path")
    ax.legend(frameon=False, loc="upper left", markerscale=1.5)

    trial_sweep(axes[1], a, sweep)
    axes[1].set(ylabel="total cluster persistence", title="Averaging more trials\nshortens the brain's path")

    ax = axes[2]
    strip(ax, [(name, a[a["group"] == key]["h1_max_over_null"].dropna().to_numpy(float), color) for name, key, color in names], ".2f")
    ax.axhline(1, color="k", lw=2, ls=":")
    ax.set(ylabel="longest loop / split-half noise", ylim=(0, None), title="Against its own noise, the longest\nloop is alike in brain and model")

    fig.suptitle("What separates brains from models is how smooth the average path is, not its loops", fontsize=30)
    fig.text(0.5, 0.01, f"{CELL[0]} neurons. Left and right: each dot one brain population or trained network at {CELL[1]} trials. "
             "Middle: each thin line one brain population (mean of 5 trial draws), thick lines medians where\nevery population has the trials; "
             f"models: median and quartiles at {CELL[1]} trials (no model was rerun). Descriptive, no test.",
             ha="center", fontsize=20)
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    save(fig, "noise")


def fig_results() -> None:
    """The poster's results figure: path length by group, and the brain's path shortening as more
    trials are averaged. Dimension, noise and loops are in the table."""
    g = matched_groups()
    a = pd.read_csv(ANALYSIS / "topo_or_noise" / "activities.csv")
    a = a[a["cell_units"] == CELL[0]]
    sweep = pd.read_csv(ANALYSIS / "topo_or_noise" / "sweep.csv")
    fig, axes = plt.subplots(1, 2, figsize=(2 * COLUMN_IN, 10.5), gridspec_kw={"width_ratios": [0.8, 1.2]})
    ax = axes[0]
    strip(ax, [(name, values(g, key, "total_persistence"), color) for name, key, color in
               [("passive\nbrain", "passive", PASSIVE), ("engaged\nbrain", "engaged", ENGAGED), ("spiking\nmodels", "snn", SNN)]], ".1f")
    ax.set(ylabel="path length (total cluster persistence)", ylim=(0, 30),
           title=f"Brains' paths are longer\n({CELL[0]} neurons x {CELL[1]} trials)")
    trial_sweep(axes[1], a, sweep)
    axes[1].set(ylabel="path length (total cluster persistence)", ylim=(0, 30),
                title="More trials, less noise,\na shorter brain path")
    fig.suptitle("Brains' average paths are longer than models', and noise makes them longer", fontsize=30)
    fig.text(0.5, 0.01, "Left: each dot one brain population (13 sessions) or one trained network; bars, medians. Right: each thin line one "
             "brain population (mean of 5 trial draws),\nthick lines medians where every population has the trials; models at "
             f"{CELL[1]} trials only, median and quartiles (no model was rerun). Descriptive, no test.", ha="center", fontsize=20)
    fig.tight_layout(rect=(0, 0.07, 1, 0.96))
    save(fig, "results")


def fig_table() -> None:
    """The poster's summary table at CELL, printed and drawn. Top half: what separates brain from
    model, with how often a random engaged-brain population exceeds a random model (ties count
    half). Bottom half: topology measured against each population's own noise."""
    g = matched_groups()
    a = pd.read_csv(ANALYSIS / "topo_or_noise" / "activities.csv")
    a = a[a["cell_units"] == CELL[0]]
    keys = ["passive", "engaged", "snn"]

    def exceeds(measure: str) -> str:
        e, m = values(g, "engaged", measure)[:, None], values(g, "snn", measure)[None, :]
        return f"{100 * ((e > m).mean() + 0.5 * (e == m).mean()):.0f}%"

    def loops(key: str) -> str:
        r1 = values(g, key, "r1", dim=1)
        return f"{int((r1 >= 1).sum())} of {len(r1)}"

    loop_noise = {k: a[a["group"] == t]["h1_max_over_null"].median() for k, t in zip(keys, ["passive", "engaged", "snn_2c"])}
    rows = [("What separates them", None, None),
            ("path length", [f"{np.median(values(g, k, 'total_persistence')):.1f}" for k in keys], exceeds("total_persistence")),
            ("dimensions used", [f"{np.median(values(g, k, 'participation_ratio')):.1f}" for k in keys], exceeds("participation_ratio")),
            ("trial-to-trial noise", [f"{np.median(values(g, k, 'null_mean')):.2f}" for k in keys], exceeds("null_mean")),
            ("Topology, against its own noise", None, None),
            ("clusters that survive resampling", [f"{np.median(values(g, k, 'r1')):.0f}" for k in keys], ""),
            ("populations with a loop that survives", [loops(k) for k in keys], ""),
            ("longest loop / its own noise", [f"{loop_noise[k]:.2f}" for k in keys], "")]
    header = ["", "passive\nbrain", "engaged\nbrain", "spiking\nmodels", "engaged\n> model"]
    n = [len(values(g, k, "total_persistence")) for k in keys]
    for label, cells, rank in rows:
        print(f"{label:40s}" + ("" if cells is None else "".join(f"{c:>12s}" for c in cells) + f"{rank:>8s}"))

    fig, ax = plt.subplots(figsize=(COLUMN_IN, 8.5))
    ax.axis("off")
    xs = [0.0, 0.53, 0.67, 0.81, 0.95]
    y, step = 0.95, 0.083
    for x, text, color in zip(xs, header, ["k", PASSIVE, ENGAGED, SNN, "k"]):
        ax.text(x, y, text, ha="left" if x == 0 else "center", va="center", fontsize=22, fontweight="bold", color=color)
    y -= 1.2 * step
    ax.axhline(y + 0.5 * step, color="k", lw=2)
    for label, cells, rank in rows:
        if cells is None:
            ax.text(0, y, label, va="center", fontsize=22, fontweight="bold", fontstyle="italic")
        else:
            ax.text(0.02, y, label, va="center", fontsize=22)
            for x, c in zip(xs[1:], cells + [rank]):
                ax.text(x, y, c, ha="center", va="center", fontsize=22)
        y -= step
    ax.axhline(y + 0.5 * step, color="k", lw=2)
    ax.set(xlim=(0, 1), ylim=(y + 0.4 * step, 1))
    fig.text(0.02, 0.01, f"Medians at {CELL[0]} neurons x {CELL[1]} trials; n = {n[0]}, {n[1]}, {n[2]}. Path length: total cluster (H0) "
             "persistence,\n95-99% of the path's length in its own widths. Dimensions: participation ratio. Noise: distance\n"
             "between signatures of two random halves of the trials. Survives resampling: longer than twice the\n"
             "95th percentile of that noise. Descriptive, no test; models measured at 100 trials only; 50 x 56 agrees.",
             ha="left", va="bottom", fontsize=17)
    fig.subplots_adjust(left=0.03, right=0.97, top=0.98, bottom=0.22)
    save(fig, "table")


def cloud(run: Path, activity_id: str) -> dict[str, np.ndarray]:
    """The activity's point cloud as the pipeline builds it for condition `all`, with one trial's
    raster and the trial-averaged rates for the pipeline strip. Cached; see the module docstring."""
    path = CLOUDS / f"{activity_id}.npz"
    if path.exists():
        return dict(np.load(path))
    recipe = next(r["recipe"] for f in sorted(run.glob("activities*.jsonl")) for r in dataset.read_jsonl(f)
                  if r["activity_id"] == activity_id)
    key = next(r["diagram"] for f in sorted(run.glob("signatures*.jsonl")) for r in dataset.read_jsonl(f)
               if r["activity_id"] == activity_id and r["condition"] == "all")
    activity, _, _ = producers._produce_one(recipe)
    activity = producers.subsample(activity, recipe["subsample"])
    trials = np.flatnonzero(activity.conditions["all"])
    points, _ = unit_diameter(build_trajectories(activity.spikes, [trials], activity.window, grid.TOPO)[0])
    h0, h1 = persistence(points, 1, threshold=1.0)
    stored = dataset.store_get_npz("diagrams", key)
    if h1.shape != stored["all:H1"].shape or not (np.allclose(h0, stored["all:H0"], atol=1e-9, equal_nan=True)
                                                    and np.allclose(h1, stored["all:H1"], atol=1e-9)):
        raise RuntimeError(f"rebuilt cloud for {activity_id} does not reproduce its stored diagram")
    window = activity.spikes[:, :, activity.window]
    rates = uniform_filter1d(window[:, trials].mean(axis=1), size=grid.TOPO.smooth_win, axis=1, mode="nearest")
    out = {"points": points, "h0": h0, "h1": h1, "raster": window[:, trials[0]], "rates": rates}
    CLOUDS.mkdir(parents=True, exist_ok=True)
    np.savez(path, **out)
    return out


def draw_path(ax, points: np.ndarray, color: str) -> None:
    """The first three PCA axes of a cloud on a 3D axis, pale at stimulus onset and dark at the end."""
    shade = np.linspace(0.25, 1.0, len(points))
    for i in range(len(points) - 1):
        ax.plot(*points[i:i + 2, :3].T, color=color, alpha=shade[i], lw=3)
    ax.scatter(*points[:, :3].T, color=color, s=25, alpha=0.6, linewidths=0)
    ax.scatter(*points[0, :3], color="k", s=160, marker="o", zorder=5)
    ax.set_xticklabels([]), ax.set_yticklabels([]), ax.set_zticklabels([])
    ax.set_xlabel("axis 1", labelpad=-8), ax.set_ylabel("axis 2", labelpad=-8), ax.set_zlabel("axis 3", labelpad=-8)
    ax.set_box_aspect(np.ptp(points[:, :3], axis=0))


def share_in_3(points: np.ndarray) -> float:
    variance = points.var(axis=0)
    return 100 * variance[:3].sum() / variance.sum()


def examples() -> list[tuple[str, str, str, str]]:
    """(name, side, activity_id, colour): the whole-session brain population and the trainings
    nearest their group's median total cluster persistence at CELL. One session gives both brain examples."""
    g = matched_groups()
    out = []
    engaged = g["engaged"][(g["engaged"]["dim"] == 0) & g["engaged"]["area"].isna()]
    session = engaged.loc[(engaged["total_persistence"] - g["engaged"][g["engaged"]["dim"] == 0]["total_persistence"].median()).abs().idxmin(), "session"]
    for name, key, color in [("passive brain", "passive", PASSIVE), ("engaged brain", "engaged", ENGAGED)]:
        d = g[key][(g[key]["dim"] == 0) & g[key]["area"].isna() & (g[key]["session"] == session)]
        out.append((f"{name}\n(session {int(session)})", "bio", d["activity_id"].iloc[0], color))
    d = g["snn"][(g["snn"]["dim"] == 0) & (g["snn"]["family"] == "snn")]  # a spiking example, not a rate network
    row = d.loc[(d["total_persistence"] - d["total_persistence"].median()).abs().idxmin()]
    neuron = {"lif": "leaky", "alif": "adaptive", "izhikevich": "Izhikevich"}[row["neuron"]]
    out.append((f"spiking model\n({row['arch']}, {neuron})", "snn", row["activity_id"], SNN))
    return out


def fig_trajectories() -> None:
    fig = plt.figure(figsize=(2 * COLUMN_IN, 9.5))
    for i, (name, side, activity_id, color) in enumerate(examples()):
        c = cloud(GRID_RUNS[side], activity_id)
        ax = fig.add_subplot(1, 3, i + 1, projection="3d")
        draw_path(ax, c["points"], color)
        ax.set_title(f"{name}\n3 axes hold {share_in_3(c['points']):.0f}%", fontsize=24)
    fig.suptitle("One population's average path through a trial", fontsize=30)
    fig.text(0.5, 0.01, f"One example per group, the one nearest its group's median; {CELL[0]} neurons x {CELL[1]} trials. "
             "150 points, 10 ms apart, from stimulus onset (black dot). Three of the ten axes measured.", ha="center", fontsize=20)
    fig.tight_layout(rect=(0, 0.05, 1, 0.97))
    save(fig, "trajectories")


def barcode(ax, h0: np.ndarray, h1: np.ndarray, lw: float) -> None:
    """Cluster bars (grey, all born at 0) above loop bars (red), longest first. The cluster that never dies is left out."""
    h0 = h0[np.isfinite(h0[:, 1])]
    h0 = h0[np.argsort(h0[:, 0] - h0[:, 1])]
    h1 = h1[np.argsort(h1[:, 0] - h1[:, 1])]
    for y, (birth, death) in enumerate(np.vstack([h0, h1])):
        ax.hlines(-y, birth, death, color="#777777" if y < len(h0) else LOOP, lw=lw)
    ax.set_yticks([-len(h0) / 2, -len(h0) - len(h1) / 2], ["clusters", "loops"], rotation=90, va="center")
    ax.tick_params(axis="y", length=0)
    ax.set_xlabel("ball radius")


def fig_pipeline() -> None:
    name, side, activity_id, color = examples()[1]
    c = cloud(GRID_RUNS[side], activity_id)
    fig = plt.figure(figsize=(2 * COLUMN_IN, 8.5))
    grid_spec = fig.add_gridspec(1, 4, wspace=0.35)
    ax = fig.add_subplot(grid_spec[0])
    ax.imshow(c["raster"] > 0, aspect="auto", cmap="Greys", interpolation="nearest", extent=(0, 1.5, len(c["raster"]), 0))
    ax.set(title="1. Spikes, one trial", xlabel="time after stimulus (s)", ylabel="neuron")
    ax = fig.add_subplot(grid_spec[1])
    ax.imshow(c["rates"], aspect="auto", cmap="viridis", interpolation="nearest", extent=(0, 1.5, len(c["rates"]), 0))
    ax.set(title=f"2. Average of {CELL[1]} trials", xlabel="time after stimulus (s)", ylabel="neuron")
    ax = fig.add_subplot(grid_spec[2], projection="3d")
    draw_path(ax, c["points"], color)
    ax.set_title("3. Each moment is a point", fontsize=26)
    ax = fig.add_subplot(grid_spec[3])
    barcode(ax, c["h0"], c["h1"], 1.5)
    ax.set_title("4. Its shape, as bars")
    fig.text(0.5, 0.03, f"Real data at every step: {name.replace(chr(10), ' ')}, {CELL[0]} neurons. Step 3 shows 3 of the 10 axes kept.",
             ha="center", fontsize=20)
    fig.subplots_adjust(left=0.05, right=0.98, top=0.9, bottom=0.2)
    save(fig, "pipeline")


def fig_rips() -> None:
    """An illustration on made-up points: a noisy circle, where the picture and the bars agree exactly."""
    rng = np.random.default_rng(3)
    angle = np.sort(rng.uniform(0, 2 * np.pi, 28))
    points = np.c_[np.cos(angle), np.sin(angle)] * (1 + rng.normal(0, 0.08, 28))[:, None]
    h0, h1 = persistence(points, 1)
    loop = h1[np.argmax(h1[:, 1] - h1[:, 0])]
    radii = [0.45 * loop[0], 0.5 * (loop[0] + loop[1]), 1.03 * loop[1]]
    dist = squareform(pdist(points))
    fig, axes = plt.subplots(1, 4, figsize=(2 * COLUMN_IN, 8), gridspec_kw={"width_ratios": [1, 1, 1, 1.3]})
    for ax, r, title in zip(axes, radii, ["small balls:\nmany clusters", "bigger: one cluster,\na loop", "bigger still:\nthe loop fills in"]):
        n = len(points)
        for i in range(n):
            ax.add_patch(plt.Circle(points[i], r / 2, color="#4477AA", alpha=0.18, lw=0))
            for j in range(i + 1, n):
                if dist[i, j] <= r:
                    ax.plot(*points[[i, j]].T, color="#4477AA", lw=1.5, zorder=2)
                    for k in range(j + 1, n):
                        if dist[i, k] <= r and dist[j, k] <= r:
                            ax.fill(*points[[i, j, k]].T, color="#4477AA", alpha=0.25, lw=0, zorder=1)
        ax.scatter(*points.T, color="k", s=60, zorder=3)
        ax.set_title(title, fontsize=24)
        ax.set_aspect("equal")
        ax.set(xlim=(-2.3, 2.3), ylim=(-2.3, 2.3))
        ax.axis("off")
    barcode(axes[3], h0, h1, 4)
    for r in radii:
        axes[3].axvline(r, color="k", lw=1.5, ls=":")
    axes[3].set_title("every feature is a bar:\nits length is how long it lasts", fontsize=24)
    fig.tight_layout()
    save(fig, "rips")


def fig_torus() -> None:
    u, v = np.meshgrid(np.linspace(0, 2 * np.pi, 80), np.linspace(0, 2 * np.pi, 40))
    big, small = 2.0, 0.8
    fig = plt.figure(figsize=(COLUMN_IN, 7))
    ax = fig.add_subplot(projection="3d")
    ax.plot_surface((big + small * np.cos(v)) * np.cos(u), (big + small * np.cos(v)) * np.sin(u), small * np.sin(v),
                    color="#BBCCEE", alpha=0.45, lw=0, rstride=1, cstride=1)
    t = np.linspace(0, 2 * np.pi, 200)
    lift = 1.02  # the loops sit just off the surface so it does not hide them
    ax.plot((big + lift * small) * np.cos(t), (big + lift * small) * np.sin(t), 0 * t, color=LOOP, lw=6, zorder=5)
    ax.plot(big + lift * small * np.cos(t), 0 * t, lift * small * np.sin(t), color="#EE7733", lw=6, zorder=5)
    ax.set_box_aspect((1, 1, small / (big + small)), zoom=1.35)
    ax.view_init(elev=32, azim=-65)
    ax.axis("off")
    ax.set_title("A torus: one piece, two different loops")
    fig.subplots_adjust(left=0, right=1, bottom=0, top=0.92)
    save(fig, "torus")


def place_cells(preferred: np.ndarray, rng: np.random.Generator, samples: int = 15000) -> np.ndarray:
    """Spikes of neurons with von Mises tuning on a circle, driven by a random-walk angle: Giusti's
    geometric case, as in tests/test_clique.py."""
    angle = np.cumsum(rng.normal(0, 0.1, samples))
    rate = 0.2 * np.exp(2 * (np.cos(angle[None] - preferred[:, None]) - 1))
    return (rng.random((len(preferred), samples)) < rate).astype(float)


def draw_complex(ax, pos: np.ndarray, c: np.ndarray, density: float, color: str, size: float) -> None:
    """The order complex at one edge density: the strongest correlations as edges, every triangle filled."""
    edge = (clique.order_distance(c) <= density) & ~np.eye(len(c), dtype=bool)
    for i, j, k in combinations(range(len(c)), 3):
        if edge[i, j] and edge[i, k] and edge[j, k]:
            ax.fill(*pos[[i, j, k]].T, color=color, alpha=0.2, lw=0, zorder=1)
    for i, j in zip(*np.nonzero(np.triu(edge))):
        ax.plot(*pos[[i, j]].T, color=color, lw=1.5, zorder=2)
    ax.scatter(*pos.T, color="k", s=size, zorder=3)
    ax.set_aspect("equal")
    ax.axis("off")


def betti1_at(curves: np.ndarray, density: float) -> int:
    return int(curves[0, np.argmin(np.abs(clique.DENSITY - density))])


def fig_clique_method() -> None:
    """Made-up neurons, one column: 16 place cells on a circle joined at three densities, then the
    Betti 1 curve at the probe's size, 50, against the random band, with the three densities marked.
    The caption is the poster's (docs/poster/draft.md, Fig. 2)."""
    rng = np.random.default_rng(1)
    n = 16
    preferred = np.linspace(0, 2 * np.pi, n, endpoint=False) + rng.uniform(-0.1, 0.1, n)
    pos = np.c_[np.cos(preferred), np.sin(preferred)]
    c = clique.correlations(place_cells(preferred, rng))
    curves = clique.betti_curves(c, 1)
    ring = clique.DENSITY[np.argmax(curves[0] > 0)]
    densities = [0.05, ring, 0.4]
    fig = plt.figure(figsize=(COLUMN_IN, 12))
    grid_spec = fig.add_gridspec(2, 3, height_ratios=[1, 1.7], wspace=0.15, hspace=0.2)
    for col, density in enumerate(densities):
        ax = fig.add_subplot(grid_spec[0, col])
        draw_complex(ax, pos, c, density, ENGAGED, 60)
        loops = betti1_at(curves, density)
        ax.set_title(f"top {density:.0%}\n{loops} loop{'s' * (loops != 1)}", fontsize=24)
    ax = fig.add_subplot(grid_spec[1, :])
    rng = np.random.default_rng(2)
    band = np.array([clique.betti_curves(clique.random_matrix(50, rng), 1)[0] for _ in range(20)])
    ax.fill_between(clique.DENSITY, band.min(0), band.max(0), color=RANDOM, alpha=0.6, lw=0)
    ax.plot(clique.DENSITY, np.median(band, 0), color=RANDOM_EDGE, lw=3)
    geometric = clique.betti_curves(clique.correlations(place_cells(rng.uniform(0, 2 * np.pi, 50), rng)), 1)[0]
    ax.plot(clique.DENSITY, geometric, color=ENGAGED, lw=3)
    for density in densities:
        ax.axvline(density, color="k", ls="--", lw=1.5, zorder=0)
    ax.set_xticks(densities, [f"{d:.0%}" for d in densities])
    peak = np.argmax(np.median(band, 0))
    ax.text(clique.DENSITY[peak] + 0.09, band.max(0)[peak] - 20, "random order\n(20 draws)", ha="left", fontsize=22)
    ax.text(clique.DENSITY[np.argmax(geometric)] + 0.03, geometric.max() + 2, "place cells", fontsize=22, color="k")
    ax.set(xlabel="pairs joined", ylabel="number of loops (Betti 1)", xlim=(0, 0.5), ylim=(0, None))
    ax.set_title("loops at every density, 50 neurons", fontsize=24)
    fig.subplots_adjust(left=0.12, right=0.97, top=0.93, bottom=0.08)
    save(fig, "clique_method")


def spring_positions(c: np.ndarray) -> np.ndarray:
    """2D positions from a force layout over every pair, pulled harder the higher the pair ranks, so
    strongly correlated neurons sit close and none drifts off; for display only."""
    import networkx as nx
    g = nx.from_numpy_array((1 - clique.order_distance(c)) ** 8 * ~np.eye(len(c), dtype=bool))
    pos = nx.spring_layout(g, seed=0, weight="weight")
    return np.array([pos[i] for i in range(len(c))])


def fig_clique_model() -> None:
    """The first k = 50 probe of the 12-task net, seed 0, redrawn exactly as clique_probe drew it, netted
    by its top 5% of correlations; one column. The caption is the poster's (docs/poster/draft.md, Fig. 4)."""
    f = np.load(CLIQUE / "spikes" / "multitask-0.npz")
    counts, bounds = f["counts"], f["bounds"]
    eligible = np.flatnonzero(counts.mean(1) >= clique_probe.RATE_FLOOR)
    rng = np.random.default_rng(zlib.crc32(b"12-task SNN/multitask-0"))
    units = rng.choice(eligible, 50, replace=False)
    x, _ = clique_probe.probe_samples(counts, bounds, units, rng)
    c = clique.correlations(x)
    curves = clique.betti_curves(c, 1)
    df = pd.read_csv(CLIQUE / "probes.csv")
    stored = df[(df.source == "multitask-0") & (df.k == 50) & (df.draw == 0) & ~df.residual & ~df.trial_demeaned].iloc[0]
    assert np.isclose(clique.integrated(curves)[0], stored.betti1), "the redrawn probe is not the one in probes.csv"
    density = 0.05

    fig, ax = plt.subplots(figsize=(COLUMN_IN, COLUMN_IN))
    draw_complex(ax, spring_positions(c), c, density, SNN, 160)
    loops = betti1_at(curves, density)
    ax.set_title(f"50 neurons of a 12-task net, joined by\ntheir top {density:.0%} of correlations: {loops} loop{'s' * (loops != 1)}", fontsize=26)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.88, bottom=0.02)
    print(f"clique_model caption facts: {len(counts)} neurons, {len(eligible)} firing >= {clique_probe.RATE_FLOOR} spikes/bin (1 Hz), "
          f"{clique_probe.N_SAMPLES} bins, Betti 1 area {stored.betti1_vs_random:.2f} of random's")
    save(fig, "clique_model")


CLIQUE_GROUPS = [("untrained\nnet", "untrained SNN", UNTRAINED), ("12-task\nnet", "12-task SNN", SNN),
                 ("engaged\nbrain", "brain engaged", ENGAGED), ("passive\nbrain", "brain passive", PASSIVE)]


def per_source(df: pd.DataFrame, group: str, removed: bool, k: int = 50) -> pd.Series:
    """Each session's or seed's median probe, as clique_probe.summary takes it. removed: trial means and population signal both removed."""
    sel = df[(df.group == group) & (df.k == k) & (df.residual == removed) & (df.trial_demeaned == removed)]
    return sel.groupby("source")["betti1_vs_random"].median()


def fig_clique_results() -> None:
    df = pd.read_csv(CLIQUE / "probes.csv")
    curves = np.load(CLIQUE / "curves.npz")["curves"][:, 0]
    fig, axes = plt.subplots(1, 3, figsize=(2 * COLUMN_IN, 11), gridspec_kw={"width_ratios": [1.5, 1, 1]})
    ax = axes[0]
    rand = curves[((df.group == "random") & (df.k == 50)).to_numpy()]
    ax.fill_between(clique.DENSITY, *np.percentile(rand, [10, 90], 0), color=RANDOM, alpha=0.6, lw=0)
    ax.plot(clique.DENSITY, np.median(rand, 0), color=RANDOM_EDGE, lw=3)
    ax.plot([], [], color=RANDOM_EDGE, lw=3, label="random order")
    for name, group, color in CLIQUE_GROUPS:
        sel = (df.group == group) & (df.k == 50) & ~df.residual & ~df.trial_demeaned
        sources = df[sel].source.to_numpy()
        c = curves[sel.to_numpy()]
        c = np.array([np.median(c[sources == s], 0) for s in np.unique(sources)])  # one curve per session or seed
        ax.fill_between(clique.DENSITY, *np.percentile(c, [10, 90], 0), color=color, alpha=0.2, lw=0)
        ax.plot(clique.DENSITY, np.median(c, 0), color=color, lw=3, label=name.replace("\n", " "))
    ax.legend(loc="upper right", frameon=False)
    ax.set(xlabel="edge density", ylabel="number of loops (Betti 1)", xlim=(0, 0.5), ylim=(0, None))
    ax.set_title("1. Loops as pairs are joined,\n50-neuron probes", fontsize=24)
    for ax, removed, title in ((axes[1], False, "2. Raw"), (axes[2], True, "3. Trial means and\npopulation signal removed")):
        strip(ax, [(name, per_source(df, group, removed).to_numpy(), color) for name, group, color in CLIQUE_GROUPS], ".2f")
        ax.axhline(1, color=RANDOM_EDGE, lw=2, ls="--")
        ax.set(ylim=(0, 1.05), ylabel="Betti 1 area / random")
        ax.set_title(title, fontsize=24)
        ax.tick_params(axis="x", labelsize=20)
    axes[2].text(axes[2].get_xlim()[1], 1.0, "random", ha="right", va="bottom", fontsize=20)
    fig.text(0.02, 0.02, "Curves: median of the sessions' or seeds' median curves, band 10th-90th percentile. Dots: one session (13 per brain group) "
             "or training seed (5 per net),\neach the median of 10 random 50-neuron probes; bars and numbers are medians. 1 = no order "
             "beyond chance, 0 = a perfect geometric order.\nTraining moves a net toward chance and toward the brain; "
             "with both removals the ranges separate.", ha="left", va="bottom", fontsize=19)
    fig.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.25, wspace=0.35)
    save(fig, "clique_results")


def fig_clique_table() -> None:
    """Betti 1 area / random at k = 50, median [range] over sessions or seeds; printed as markdown and drawn."""
    df = pd.read_csv(CLIQUE / "probes.csv")
    rows = [("untrained net, 12-task inputs", "untrained SNN", UNTRAINED), ("DM-only net, DM inputs", "DM-only SNN", RANDOM_EDGE),
            ("DM-only net, 12-task inputs", "DM-only SNN, 12-task inputs", RANDOM_EDGE), ("12-task net", "12-task SNN", SNN),
            ("brain, engaged", "brain engaged", ENGAGED), ("brain, passive", "brain passive", PASSIVE)]

    def cell(v: pd.Series) -> str:
        return f"{v.median():.2f} [{v.min():.2f}-{v.max():.2f}]"

    table = [(name, color, str(len(per_source(df, group, False))), cell(per_source(df, group, False)), cell(per_source(df, group, True)))
             for name, group, color in rows]
    header = ["source", "n", "raw", "drift + population removed"]
    print("| " + " | ".join(header) + " |\n|" + "---|" * len(header))
    for name, _, *cells in table:
        print("| " + " | ".join([name, *cells]) + " |")

    fig, ax = plt.subplots(figsize=(COLUMN_IN, 7.5))
    ax.axis("off")
    xs = [0.04, 0.5, 0.67, 0.88]
    y, step = 0.93, 0.11
    for x, text in zip(xs, ["", "n", "raw", "drift +\npopulation\nremoved"]):
        ax.text(x, y, text, ha="left" if x == xs[0] else "center", va="center", fontsize=22, fontweight="bold")
    y -= 1.3 * step
    ax.axhline(y + 0.55 * step, color="k", lw=2)
    for name, color, *cells in table:
        ax.scatter(0.012, y, s=200, color=color, linewidths=0, clip_on=False)
        ax.text(xs[0], y, name, va="center", fontsize=22)
        for x, c in zip(xs[1:], cells):
            ax.text(x, y, c, ha="center", va="center", fontsize=22)
        y -= step
    ax.axhline(y + 0.5 * step, color="k", lw=2)
    ax.set(xlim=(0, 1), ylim=(y + 0.4 * step, 1))
    fig.text(0.02, 0.01, "Betti 1 area of 50-neuron probes as a fraction of random's: 1 = chance, 0 = perfect order. Median [range] over\n"
             "sessions or training seeds, each the median of 10 probes. Drift removed: each neuron's mean within every trial.\n"
             "Population removed: each neuron regressed on the probe's mean activity.", ha="left", va="bottom", fontsize=17)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.2)
    save(fig, "clique_table")


def show_trajectory(run: Path, activity_id: str) -> None:
    c = cloud(run, activity_id)
    fig = plt.figure(figsize=(9, 8))
    ax = fig.add_subplot(projection="3d")
    plt.rcParams.update({"font.size": 11})
    draw_path(ax, c["points"], "#4477AA")
    ax.set_title(f"{run.name} {activity_id}: 3 of 10 axes hold {share_in_3(c['points']):.0f}% of the variance; "
                 f"{len(c['h1'])} loop bars, longest {np.max(c['h1'][:, 1] - c['h1'][:, 0], initial=0):.3f}", fontsize=11)
    plt.show()


def main():
    if sys.argv[1:2] == ["trajectory"]:
        show_trajectory(Path(sys.argv[2]), sys.argv[3])
        return
    figures = {"results": fig_results, "table": fig_table, "main": fig_main, "nogo": fig_nogo, "engagement": fig_engagement,
               "zoo": fig_zoo, "noise": fig_noise, "trajectories": fig_trajectories, "pipeline": fig_pipeline, "rips": fig_rips, "torus": fig_torus,
               "clique_method": fig_clique_method, "clique_model": fig_clique_model, "clique_results": fig_clique_results,
               "clique_table": fig_clique_table}
    for name in sys.argv[1:] or figures:
        figures[name]()
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
