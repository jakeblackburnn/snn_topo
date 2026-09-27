"""One-off M7 GPU concurrency measurement; runs only 200-update recurrent LIF trainers."""
from __future__ import annotations

import argparse
import multiprocessing as mp
import subprocess
import threading
import time


def worker(n_hidden: int, queue) -> None:
    import torch
    from snntopo.contracts import ModelConfig, TrainConfig
    from snntopo.models import build_model
    from snntopo.tasks import TASKS
    from snntopo.training import train

    torch.manual_seed(10_000 + n_hidden)
    torch.cuda.reset_peak_memory_stats()
    task = TASKS["steinmetz_2afc"]
    model = build_model(ModelConfig("recurrent", "lif", "random", n_hidden=n_hidden),
                        task.n_in, task.n_actions).to("cuda")
    result = train(model, task, TrainConfig(n_updates=200, batch_size=64, max_seconds=1800,
                                             seed=10_000 + n_hidden), "cuda", log_every=1000)
    queue.put({"elapsed_s": result["elapsed_s"], "updates": result["n_updates_done"],
               "peak_mib": torch.cuda.max_memory_allocated() / 2**20, "status": result["status"]})


def sample_gpu(stop, samples):
    while not stop.is_set():
        try:
            line = subprocess.check_output([
                "nvidia-smi", "--query-gpu=utilization.gpu,memory.used", "--format=csv,noheader,nounits",
            ], text=True).strip().splitlines()[0]
            util, memory = (float(x.strip()) for x in line.split(","))
            samples.append((util, memory))
        except (OSError, subprocess.CalledProcessError, ValueError):
            pass
        stop.wait(0.25)


def measure(n_hidden: int, trainers: int) -> dict:
    ctx = mp.get_context("spawn")
    queue = ctx.Queue()
    stop, samples = threading.Event(), []
    monitor = threading.Thread(target=sample_gpu, args=(stop, samples), daemon=True)
    monitor.start()
    processes = [ctx.Process(target=worker, args=(n_hidden, queue)) for _ in range(trainers)]
    t0 = time.perf_counter()
    for process in processes:
        process.start()
    results = [queue.get() for _ in processes]
    for process in processes:
        process.join()
        if process.exitcode:
            raise RuntimeError(f"trainer exited {process.exitcode}")
    elapsed = time.perf_counter() - t0
    stop.set()
    monitor.join(timeout=1)
    return {
        "n_hidden": n_hidden, "trainers": trainers, "wall_s": elapsed,
        "per_trainer_updates_s": sum(r["updates"] / r["elapsed_s"] for r in results) / trainers,
        "total_updates_s": sum(r["updates"] for r in results) / elapsed,
        "peak_mib_per_trainer": max(r["peak_mib"] for r in results),
        "gpu_util_mean_pct": sum(s[0] for s in samples) / len(samples) if samples else 0.0,
        "gpu_util_max_pct": max((s[0] for s in samples), default=0.0),
        "gpu_mem_max_mib": max((s[1] for s in samples), default=0.0),
        "statuses": ",".join(r["status"] for r in results),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sizes", nargs="*", type=int, default=(64, 256, 1024))
    parser.add_argument("--trainers", nargs="*", type=int, default=(1, 2, 4))
    args = parser.parse_args()
    print("n_hidden trainers wall_s per_trainer_updates_s total_updates_s peak_mib gpu_util_mean gpu_util_max gpu_mem_max statuses")
    for n_hidden in args.sizes:
        for trainers in args.trainers:
            row = measure(n_hidden, trainers)
            print("{n_hidden} {trainers} {wall_s:.2f} {per_trainer_updates_s:.2f} {total_updates_s:.2f} "
                  "{peak_mib_per_trainer:.1f} {gpu_util_mean_pct:.1f} {gpu_util_max_pct:.1f} "
                  "{gpu_mem_max_mib:.1f} {statuses}".format(**row), flush=True)


if __name__ == "__main__":
    main()
