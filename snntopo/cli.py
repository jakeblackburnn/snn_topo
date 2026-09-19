"""Command-line entry point: `snntopo <command> ...`."""
import argparse
from pathlib import Path

import torch

from .atlas import bio_entry, snn_entry, write_tables
from .config import RESULTS_DIR
from .contracts import ModelConfig, TopoConfig, TrainConfig
from .data import DATASETS, load_session
from .logging_utils import setup_logging
from .report import write_report
from .tasks import TASKS


def cmd_bio(args):
    run_dir = Path(args.out)
    setup_logging("bio", run_dir / "logs")
    sessions = args.session or list(DATASETS[args.dataset].reference_sessions)
    for s in sessions:
        bio_entry(load_session(args.dataset, s), TopoConfig(), run_dir)
    write_tables(run_dir)


def cmd_snn(args):
    """Train and measure one model config: a smoke/mini-run, not a search."""
    run_dir = Path(args.out)
    setup_logging("snn", run_dir / "logs")
    task = TASKS[args.task]
    datasets = [task.bio_match] if task.bio_match else list(DATASETS)
    refs = [load_session(d, s) for d in datasets for s in DATASETS[d].reference_sessions]
    cfg = ModelConfig(arch=args.arch, neuron=args.neuron, connectivity=args.connectivity, n_hidden=args.n_hidden)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    snn_entry(f"snn:{task.name}:single", task, cfg, TrainConfig(n_updates=args.n_updates), TopoConfig(), refs,
              run_dir, device)
    write_tables(run_dir)


def cmd_report(args):
    write_report([Path(run) for run in args.run], Path(args.out))


def main(argv=None):
    p = argparse.ArgumentParser(prog="snntopo")
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("bio", help="compute bio atlas entries")
    b.add_argument("--dataset", required=True, choices=list(DATASETS))
    b.add_argument("--session", action="append", help="session id (repeatable); default: reference sessions")
    b.add_argument("--out", default=str(RESULTS_DIR / "bio"))
    b.set_defaults(fn=cmd_bio)

    s = sub.add_parser("snn", help="train and measure one SNN config")
    s.add_argument("--task", required=True, choices=list(TASKS))
    s.add_argument("--arch", default="recurrent")
    s.add_argument("--neuron", default="lif")
    s.add_argument("--connectivity", default="random")
    s.add_argument("--n-hidden", type=int, default=256)
    s.add_argument("--n-updates", type=int, default=200)
    s.add_argument("--out", default=str(RESULTS_DIR / "snn_single"))
    s.set_defaults(fn=cmd_snn)

    r = sub.add_parser("report", help="build a static report from atlas run directories")
    r.add_argument("--run", action="append", required=True, help="atlas run directory (repeatable)")
    r.add_argument("--out", required=True, help="report output directory")
    r.set_defaults(fn=cmd_report)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
