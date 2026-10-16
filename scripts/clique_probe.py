"""Clique topology of random neuron probes, brains against a published multitask spiking net.

A probe is k neurons drawn at random from one source, and 15000 10-ms bins of their spike
counts from trials taken in random order (a brain probe: 100 trials x 150 bins). Its
correlation matrix goes through `snntopo.clique`, raw and after regressing out the probe's
population signal.

Sources: the 13 Steinmetz part-0 sessions, engaged (active block, responded trials) and
passive; Pugavko et al. 2023's AdEx network (`snntopo.pugavko`, their regularized recipe) at
N_HIDDEN units, trained on all 12 tasks, or on DMTask1+2 only, five seeds each; and the
12-task nets before training, on 12-task inputs. Units under RATE_FLOOR spikes per bin are
never probed, on either side.

    PYTHONPATH=. python scripts/clique_probe.py train   # all 10 nets side by side, ~3 h on the GPU
    PYTHONPATH=. python scripts/clique_probe.py gate    # the paper's own config (256 units), 2 seeds
    PYTHONPATH=. python scripts/clique_probe.py probe   # ~10 min on 16 cores
    PYTHONPATH=. python scripts/clique_probe.py figure

Outputs in results/analysis/clique_probe/: train_log.csv (loss, rate, accuracy per task through
training), models.csv (final accuracy per net and task), spikes/*.npz, probes.csv (one row per
probe: integrated Betti 1 and 2, and as a multiple of the random mean), curves.npz, clique.png.
"""
import multiprocessing
import os
import sys
import time
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from snntopo import clique, producers, pugavko
from snntopo.config import RESULTS_DIR
from snntopo.data import steinmetz

OUT = Path(RESULTS_DIR) / "analysis" / "clique_probe"
KS = (50, 128)
N_SAMPLES = 15000  # bins per probe, the brain's 100 trials x 150 bins
BIN = 10  # model steps (ms) per bin, the brain's bin
DRAWS = 10  # probes per (source, k)
RANDOM_DRAWS = 50
RATE_FLOOR = 0.01  # spikes per bin: 1 Hz in 10 ms bins
SEEDS = range(5)
N_HIDDEN = 512
EPOCHS = 3000
LOG_EVERY = 50
CHECK_EVERY = 250  # a multiple of LOG_EVERY
N_EVAL = 600  # final evaluation trials per net: 50 per task for the 12-task nets
NETS = [("multitask", seed, pugavko.TASKS) for seed in SEEDS] + [("dm_only", seed, ("DMTask1", "DMTask2")) for seed in SEEDS]
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def accuracy_rows(results, nets, **extra) -> list[dict]:
    rows = []
    for (name, seed, _), (hits, idx, _) in zip(nets, results):
        for i in np.unique(idx):
            rows.append({"model": name, "seed": seed, "task": pugavko.TASKS[i], "accuracy": hits[idx == i].mean(),
                         "n": int((idx == i).sum()), **extra})
    return rows


def binned(trials: list[np.ndarray]) -> tuple[np.ndarray, np.ndarray]:
    """Per-trial (N, steps) spikes -> (N, total bins) counts in BIN-step bins, and the trial
    boundaries in bins. A trial's last partial bin is dropped."""
    counts = [t[:, :t.shape[1] // BIN * BIN].reshape(len(t), -1, BIN).sum(-1, dtype=np.uint8) for t in trials]
    bounds = np.concatenate([[0], np.cumsum([c.shape[1] for c in counts])])
    return np.concatenate(counts, axis=1), bounds


def run_training(nets, n_hidden: int, tag: str) -> None:
    """Trains nets side by side, logging accuracy every CHECK_EVERY epochs; saves the
    untrained and final weights and the final evaluation with spikes."""
    (OUT / "spikes").mkdir(parents=True, exist_ok=True)
    torch.manual_seed(0)
    net = pugavko.AdExNet(n_hidden, n_nets=len(nets)).to(DEVICE)
    task_sets = [tasks for _, _, tasks in nets]
    torch.save(net.state_dict(), OUT / f"{tag}_untrained.pt")
    log, t0 = [], time.time()

    def on_log(row, epoch):
        rows = [{"epoch": epoch, "model": name, "seed": seed, "loss": row["loss"][g], "rate_hz": row["rate_hz"][g]}
                for g, (name, seed, _) in enumerate(nets)]
        if epoch % CHECK_EVERY == 0:
            results = pugavko.evaluate(net, task_sets, DEVICE, seed=10_000 + epoch, n_trials=120, record=False)
            acc = pd.DataFrame(accuracy_rows(results, nets)).groupby(["model", "seed"]).accuracy.mean()
            for r in rows:
                r["accuracy"] = acc[(r["model"], r["seed"])]
        log.extend(rows)
        pd.DataFrame(log).to_csv(OUT / f"{tag}_train_log.csv", index=False)
        summary = pd.DataFrame(rows).groupby("model")[[c for c in ("loss", "rate_hz", "accuracy") if c in rows[0]]].median()
        print(f"epoch {epoch} {time.time() - t0:.0f}s", summary.round(3).to_dict("index"), flush=True)

    pugavko.train(net, task_sets, DEVICE, seed=0, epochs=EPOCHS, log_every=LOG_EVERY, on_log=on_log)
    torch.save(net.state_dict(), OUT / f"{tag}_trained.pt")
    print(f"trained in {time.time() - t0:.0f}s", flush=True)


def final_evaluation(nets, n_hidden: int, tag: str, record: bool) -> pd.DataFrame:
    net = pugavko.AdExNet(n_hidden, n_nets=len(nets)).to(DEVICE)
    task_sets = [tasks for _, _, tasks in nets]
    rows = []
    for version in ("trained", "untrained"):
        net.load_state_dict(torch.load(OUT / f"{tag}_{version}.pt"))
        sets = task_sets if version == "trained" else [pugavko.TASKS] * len(nets)
        results = pugavko.evaluate(net, sets, DEVICE, seed=20_000, n_trials=N_EVAL, record=record)
        names = [(name if version == "trained" else f"untrained_{name}", seed, s) for (name, seed, _), s in zip(nets, sets)]
        rows += accuracy_rows(results, names, version=version, n_hidden=n_hidden)
        for (name, seed, _), (_, idx, trials) in zip(names, results):
            if record:
                counts, bounds = binned(trials)
                np.savez_compressed(OUT / "spikes" / f"{name}-{seed}.npz", counts=counts, bounds=bounds, task=idx)
                rate = counts.mean() / (BIN * pugavko.DT)
                print(f"{name}-{seed}: {counts.shape[0]} units, {counts.shape[1]} bins, mean rate {rate:.1f} Hz, "
                      f"{(counts.mean(1) >= RATE_FLOOR).sum()} above the floor", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / f"{tag}_models.csv", index=False)
    print(df.pivot_table(index=["model", "seed"], columns="task", values="accuracy").round(2).to_string())
    return df


def train() -> None:
    run_training(NETS, N_HIDDEN, "main")
    final_evaluation(NETS, N_HIDDEN, "main", record=True)


def gate() -> None:
    nets = [("multitask", seed, pugavko.TASKS) for seed in range(2)]
    run_training(nets, 256, "gate")
    final_evaluation(nets, 256, "gate", record=False)


def sources():
    """-> iterator of (group, source id, counts (neurons, bins), trial bounds in bins)."""
    for session in steinmetz.list_sessions():
        for group, block, select in (("brain engaged", "active", "responded"), ("brain passive", "passive", "all")):
            activity, _ = producers.bio_activity({"kind": "bio", "dataset": "steinmetz", "session": session,
                                                  "block": block, "trials": {"select": select}})
            spikes = activity.spikes[:, activity.conditions["all"], activity.window]
            n, trials, bins = spikes.shape
            yield group, session, spikes.reshape(n, trials * bins), np.arange(trials + 1) * bins
    groups = {"multitask": "12-task SNN", "dm_only": "DM-only SNN", "untrained_multitask": "untrained SNN"}
    for name, group in groups.items():
        for seed in SEEDS:
            f = np.load(OUT / "spikes" / f"{name}-{seed}.npz")
            yield group, f"{name}-{seed}", f["counts"], f["bounds"]


def probe_samples(counts, bounds, units, rng) -> np.ndarray:
    """Trials in random order, concatenated and cut at N_SAMPLES bins."""
    order = rng.permutation(len(bounds) - 1)
    lengths = np.diff(bounds)[order]
    take = order[:np.searchsorted(np.cumsum(lengths), N_SAMPLES) + 1]
    x = np.concatenate([counts[units, bounds[t]:bounds[t + 1]] for t in take], axis=1)
    return x[:, :N_SAMPLES].astype(np.float64)


def probe_matrices():
    """-> (rows without curves, correlation matrices), DRAWS probes per (source, k)."""
    rows, mats = [], []
    for group, source, counts, bounds in sources():
        eligible = np.flatnonzero(counts.mean(1) >= RATE_FLOOR)
        rng = np.random.default_rng(zlib.crc32(f"{group}/{source}".encode()))
        for k in KS:
            if len(eligible) < k or counts.shape[1] < N_SAMPLES:
                print(f"skip {group} {source} k={k}: {len(eligible)} units, {counts.shape[1]} bins", flush=True)
                continue
            for draw in range(DRAWS):
                x = probe_samples(counts, bounds, rng.choice(eligible, k, replace=False), rng)
                for residual in (False, True):
                    rows.append({"group": group, "source": source, "k": k, "draw": draw, "residual": residual,
                                 "n_eligible": len(eligible)})
                    mats.append(clique.correlations(x, remove_population=residual))
    return rows, mats


def probe() -> None:
    rows, mats = probe_matrices()
    rng = np.random.default_rng(0)
    for k in KS:
        for draw in range(RANDOM_DRAWS):
            rows.append({"group": "random", "source": "random", "k": k, "draw": draw, "residual": False, "n_eligible": k})
            mats.append(clique.random_matrix(k, rng))
    workers = int(os.environ.get("SNNTOPO_WORKERS", os.cpu_count()))
    order = np.argsort([-len(m) for m in mats])  # the slow k = 128 probes first
    with ProcessPoolExecutor(workers, mp_context=multiprocessing.get_context("forkserver")) as pool:
        done = list(pool.map(clique.betti_curves, [mats[i] for i in order], chunksize=4))
    curves = np.empty((len(mats), 2, len(clique.DENSITY)))
    curves[order] = done
    df = pd.DataFrame(rows)
    df[["betti1", "betti2"]] = clique.integrated(curves)
    for k in KS:
        rand = df[(df.group == "random") & (df.k == k)]
        for d in ("betti1", "betti2"):
            df.loc[df.k == k, f"{d}_vs_random"] = df.loc[df.k == k, d] / rand[d].mean()
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "probes.csv", index=False)
    np.savez_compressed(OUT / "curves.npz", curves=curves, density=clique.DENSITY)
    summary(df)


def summary(df: pd.DataFrame) -> None:
    """Medians over sources of each source's median probe: sessions and training seeds are the units."""
    per_source = df.groupby(["group", "source", "k", "residual"])[["betti1_vs_random", "betti2_vs_random"]].median()
    out = per_source.groupby(["group", "k", "residual"]).agg(["median", "min", "max", "count"]).round(2)
    print(out.to_string())


def figure() -> None:
    import matplotlib.pyplot as plt
    df = pd.read_csv(OUT / "probes.csv")
    curves = np.load(OUT / "curves.npz")["curves"]
    groups = ["random", "brain passive", "brain engaged", "12-task SNN", "DM-only SNN", "untrained SNN"]
    colors = dict(zip(groups, ["#999999", "#1f77b4", "#08306b", "#d62728", "#ff7f0e", "#2ca02c"]))
    fig, axes = plt.subplots(2, 4, figsize=(16, 7), sharex=True)
    for row, k in enumerate(KS):
        for col, (dim, residual) in enumerate(((0, False), (1, False), (0, True), (1, True))):
            ax = axes[row, col]
            for g in groups:
                sel = (df.group == g) & (df.k == k) & ((df.residual == residual) | (g == "random"))
                c = curves[sel.to_numpy(), dim]
                if not len(c):
                    continue
                ax.plot(clique.DENSITY, np.median(c, 0), color=colors[g], label=g)
                ax.fill_between(clique.DENSITY, *np.percentile(c, [10, 90], 0), color=colors[g], alpha=0.15, lw=0)
            ax.set_title(f"Betti {dim + 1}, k = {k}{', population removed' if residual else ''}", fontsize=10)
            if row == 1:
                ax.set_xlabel("edge density")
    axes[0, 0].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "clique.png", dpi=150)
    print(OUT / "clique.png")


if __name__ == "__main__":
    {"train": train, "gate": gate, "probe": probe, "figure": figure}[sys.argv[1]]()
