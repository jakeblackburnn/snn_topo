"""Command-line entry point: `snntopo <command> ...`."""
import argparse
from pathlib import Path

import torch

from . import objective
from .atlas import bio_entry, rescore, snn_entry, write_tables
from .config import RESULTS_DIR
from .contracts import ModelConfig, TopoConfig, TrainConfig
from .data import DATASETS, load_session
from .logging_utils import setup_logging
from .models import ARCHS
from .report import write_report
from .search import ACCURACY_FLOOR, run_search
from .tasks import TASKS
from .topology.stats import METRICS


def add_topo_args(p):
    d = TopoConfig()
    p.add_argument("--n-pca", type=int, default=d.n_pca)
    p.add_argument("--maxdim", type=int, default=d.maxdim)
    p.add_argument("--n-resamples", type=int, default=d.n_resamples)
    p.add_argument("--smooth-win", type=int, default=d.smooth_win)
    p.add_argument("--min-trials", type=int, default=d.min_trials)
    p.add_argument("--metrics", nargs="+", choices=list(METRICS), default=list(d.metrics),
                   help="diagram distance metrics to compute (default: wasserstein only -- "
                        "objective.py never reads bottleneck)")


def topo_from_args(args) -> TopoConfig:
    return TopoConfig(n_pca=args.n_pca, smooth_win=args.smooth_win, maxdim=args.maxdim,
                      min_trials=args.min_trials, n_resamples=args.n_resamples,
                      metrics=tuple(args.metrics))


def cmd_bio(args):
    run_dir = Path(args.out)
    setup_logging("bio", run_dir / "logs")
    sessions = args.session or list(DATASETS[args.dataset].reference_sessions)
    for s in sessions:
        bio_entry(load_session(args.dataset, s), topo_from_args(args), run_dir)
    write_tables(run_dir)


def cmd_snn(args):
    """Train and measure one model config: a smoke/mini-run, not a search."""
    run_dir = Path(args.out)
    setup_logging("snn", run_dir / "logs")
    task = TASKS[args.task]
    datasets = [task.bio_match] if task.bio_match else list(DATASETS)
    refs = [load_session(d, s) for d in datasets for s in DATASETS[d].reference_sessions]
    cfg = ModelConfig(arch=args.arch, neuron=args.neuron, connectivity=args.connectivity, n_hidden=args.n_hidden,
                      n_layers=args.n_layers, n_modules=args.n_modules)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    snn_entry(f"snn:{task.name}:single", task, cfg, TrainConfig(n_updates=args.n_updates), topo_from_args(args),
              refs, run_dir, device)
    write_tables(run_dir)


def cmd_search(args):
    """Wall-clock-capped model search for one task; rerun the same command to resume."""
    setup_logging("search", Path(args.out) / "logs")
    run_search(args.task, args.out, args.budget_hours * 3600, seed=args.seed, n_trials=args.n_trials,
               train_cfg=TrainConfig(n_updates=args.n_updates), topo=topo_from_args(args),
               accuracy_floor=args.accuracy_floor, weight=args.structure_weight, arch=args.arch)


def cmd_report(args):
    write_report([Path(run) for run in args.run], Path(args.out))


def cmd_rescore(args):
    df = rescore(args.run, weight=args.structure_weight)
    if args.out is None:
        print(df.to_string(index=False))
    else:
        df.to_csv(args.out, index=False)


def main(argv=None):
    p = argparse.ArgumentParser(prog="snntopo")
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("bio", help="compute bio atlas entries")
    b.add_argument("--dataset", required=True, choices=list(DATASETS))
    b.add_argument("--session", action="append", help="session id (repeatable); default: reference sessions")
    b.add_argument("--out", default=str(RESULTS_DIR / "bio"))
    add_topo_args(b)
    b.set_defaults(fn=cmd_bio)

    s = sub.add_parser("snn", help="train and measure one SNN config")
    s.add_argument("--task", required=True, choices=list(TASKS))
    s.add_argument("--arch", default="recurrent")
    s.add_argument("--neuron", default="lif")
    s.add_argument("--connectivity", default="random")
    s.add_argument("--n-hidden", type=int, default=256)
    s.add_argument("--n-layers", type=int, default=1, help="feedforward depth")
    s.add_argument("--n-modules", type=int, default=1, help="modular: number of modules (>= 2)")
    s.add_argument("--n-updates", type=int, default=200)
    s.add_argument("--out", default=str(RESULTS_DIR / "snn_single"))
    add_topo_args(s)
    s.set_defaults(fn=cmd_snn)

    r = sub.add_parser("search", help="search model configs for one task under a wall-clock budget")
    r.add_argument("--task", required=True, choices=list(TASKS))
    r.add_argument("--budget-hours", type=float, required=True)
    r.add_argument("--out", required=True, help="run directory; an existing one is resumed")
    r.add_argument("--n-trials", type=int, help="stop once the study holds this many trials")
    r.add_argument("--n-updates", type=int, default=TrainConfig().n_updates,
                   help="per-trial update cap; lower it (with --n-trials) for a mini-run")
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--accuracy-floor", type=float, default=ACCURACY_FLOOR,
                   help="matched trials below this accuracy are constrained-infeasible (D17)")
    r.add_argument("--structure-weight", type=float, default=objective.STRUCTURE_WEIGHT,
                   help="weight on the structure penalty term in the objective")
    r.add_argument("--arch", choices=list(ARCHS), default=None,
                   help="restrict sampling to one architecture family (default: all)")
    add_topo_args(r)
    r.set_defaults(fn=cmd_search)

    rp = sub.add_parser("report", help="build a static report from atlas run directories")
    rp.add_argument("--run", action="append", required=True, help="atlas run directory (repeatable)")
    rp.add_argument("--out", required=True, help="report output directory")
    rp.set_defaults(fn=cmd_report)

    rs = sub.add_parser("rescore", help="recompute the objective for every SNN record in a finished run")
    rs.add_argument("--run", required=True, help="atlas run directory")
    rs.add_argument("--structure-weight", type=float, default=objective.STRUCTURE_WEIGHT,
                    help="weight on the structure penalty term in the objective")
    rs.add_argument("--out", help="CSV output path; omit to print to stdout")
    rs.set_defaults(fn=cmd_rescore)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
