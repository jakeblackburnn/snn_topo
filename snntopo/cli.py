"""Command-line entry point: `snntopo <command> ...`."""
import argparse
import random
from pathlib import Path

import torch

from . import controls, objective
from .atlas import bio_entry, control_entry, rescore, snn_entry, write_tables
from .config import RESULTS_DIR
from .contracts import ModelConfig, TopoConfig, TrainConfig
from .data import DATASETS, load_session
from .logging_utils import setup_logging
from .models import ARCHS, valid_triples
from .report import write_report
from .search import ACCURACY_FLOOR, run_search
from .tasks import TASKS
from .topology.stats import METRICS

CONTROL_N_HIDDEN = 128  # simplest fixed width for controls -- not a search axis here


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
    p.add_argument("--residualize-raw-diameter", action="store_true", default=d.residualize_raw_diameter,
                   help="also record D27's raw-diameter-residualized cross distance")


def topo_from_args(args) -> TopoConfig:
    return TopoConfig(n_pca=args.n_pca, smooth_win=args.smooth_win, maxdim=args.maxdim,
                      min_trials=args.min_trials, n_resamples=args.n_resamples,
                      metrics=tuple(args.metrics), residualize_raw_diameter=args.residualize_raw_diameter)


def cmd_bio(args):
    run_dir = Path(args.out)
    setup_logging("bio", run_dir / "logs")
    sessions = args.session or list(DATASETS[args.dataset].reference_sessions)
    # Cross-dataset siblings (e.g. Allen vs Steinmetz/IBL): loaded once, compared
    # against every --dataset session below.
    compare_refs = [load_session(d, s) for d in (args.compare_dataset or [])
                     for s in DATASETS[d].reference_sessions]
    for s in sessions:
        bio_entry(load_session(args.dataset, s), topo_from_args(args), run_dir, compare_refs)
    write_tables(run_dir)


def cmd_baseline(args):
    """Every bio dataset's reference-session signatures in one run, fully cross-compared
    -- the single-command version of the E4-style validity check (is Allen's topology
    distance from Steinmetz/IBL inside or outside the IBL-vs-IBL bio-vs-bio range)."""
    run_dir = Path(args.out)
    setup_logging("baseline", run_dir / "logs")
    topo = topo_from_args(args)
    processed = []  # compare() is symmetric, so only already-processed sessions (across
                    # all datasets) are passed as siblings, per bio_entry's docstring (D18)
    for name, entry in DATASETS.items():
        for s in entry.reference_sessions:
            session = load_session(name, s)
            bio_entry(session, topo, run_dir, list(processed))
            processed.append(session)
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


def cmd_control(args):
    """Surrogate-activity controls (untrained SNN / shuffled bio), measured the same
    way as an SNN trial but never trained or searched -- a floor for the search's
    bio-distance objective, not a search itself."""
    run_dir = Path(args.out)
    setup_logging("control", run_dir / "logs")
    task = TASKS[args.task]
    datasets = [task.bio_match] if task.bio_match else list(DATASETS)
    refs = [load_session(d, s) for d in datasets for s in DATASETS[d].reference_sessions]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    topo = topo_from_args(args)
    if args.kind == "untrained":
        rng = random.Random(args.seed)
        families = valid_triples()
        for i in range(args.n):
            arch, neuron, connectivity = rng.choice(families)
            cfg = ModelConfig(arch=arch, neuron=neuron, connectivity=connectivity, n_hidden=args.n_hidden,
                              n_modules=2 if arch == "modular" else 1)
            activity = controls.untrained(cfg, task, args.seed + i, device)
            control_entry(f"control:{task.name}:untrained:{i:04d}", "untrained", task, activity, topo, refs,
                          run_dir, model_cfg=cfg)
    else:  # shuffled: destroy population structure in a bio reference's own activity
        for i in range(args.n):
            ref = refs[i % len(refs)]
            activity = controls.shuffled(ref.activity, args.seed + i)
            control_entry(f"control:{task.name}:shuffled:{i:04d}", "shuffled", task, activity, topo, refs, run_dir)
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
    b.add_argument("--compare-dataset", action="append", choices=list(DATASETS),
                   help="also compare --dataset sessions against this dataset's reference sessions (repeatable)")
    b.add_argument("--out", default=str(RESULTS_DIR / "bio"))
    add_topo_args(b)
    b.set_defaults(fn=cmd_bio)

    bl = sub.add_parser("baseline", help="every bio dataset's reference sessions, fully cross-compared")
    bl.add_argument("--out", default=str(RESULTS_DIR / "baseline"))
    add_topo_args(bl)
    bl.set_defaults(fn=cmd_baseline)

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

    c = sub.add_parser("control", help="measure a surrogate control (untrained SNN / shuffled bio) for one task")
    c.add_argument("--task", required=True, choices=list(TASKS))
    c.add_argument("--kind", required=True, choices=["untrained", "shuffled"])
    c.add_argument("--n", type=int, required=True, help="number of control entries to produce")
    c.add_argument("--n-hidden", type=int, default=CONTROL_N_HIDDEN, help="untrained only: hidden width")
    c.add_argument("--seed", type=int, default=0)
    c.add_argument("--out", default=str(RESULTS_DIR / "control"))
    add_topo_args(c)
    c.set_defaults(fn=cmd_control)

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
