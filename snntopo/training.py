"""REINFORCE training of any registered model on any registered task.

Output spike counts over task.response_steps are the policy logits; reward is +1
correct / -1 incorrect; an EMA baseline and an annealed entropy bonus reduce variance.
Lessons carried from the prototype: the entropy coefficient anneals linearly to 0
(a fixed bonus pushes a saturated policy back to uniform), gradients are clipped at a
norm sized for large recurrent layers, and the best-EMA-baseline checkpoint is what
gets returned so late instability can't clobber a usable policy."""
import copy
import math
import time

import pandas as pd
import torch
import torch.nn.functional as F

from .contracts import Task, TrainConfig
from .logging_utils import get_logger


def policy_logits(out_spk: torch.Tensor, task: Task) -> torch.Tensor:
    return out_spk[task.response_steps].sum(dim=0)


def train(model, task: Task, cfg: TrainConfig, device: str, log_every: int = 100) -> dict:
    """Trains in place and loads the best checkpoint. Returns {"curve": DataFrame,
    "status": "ok" | "timeout" | "failed", "elapsed_s", "n_updates_done",
    "best_baseline", "error"}. Timeout keeps the best checkpoint so far; a non-finite
    loss stops training and reports "failed" instead of raising, since the search
    treats bad configs as routine outcomes."""
    log = get_logger()
    torch.manual_seed(cfg.seed)
    gen = torch.Generator().manual_seed(cfg.seed)
    opt = torch.optim.Adam(model.parameters(), lr=cfg.lr)
    baseline, best_baseline, best_state = 0.0, -math.inf, None
    rows, status, error = [], "ok", None

    t0 = time.time()
    for update in range(1, cfg.n_updates + 1):
        spk_in, target = task.sample_batch(cfg.batch_size, device, gen)
        _, out_spk = model(spk_in)
        dist = torch.distributions.Categorical(probs=F.softmax(policy_logits(out_spk, task), dim=-1))
        action = dist.sample()
        correct = (action == target).float()
        reward = correct * 2 - 1
        entropy_coef = cfg.entropy_coef * (1 - (update - 1) / cfg.n_updates)
        loss = -(dist.log_prob(action) * (reward - baseline)).mean() - entropy_coef * dist.entropy().mean()
        if not torch.isfinite(loss):
            status, error = "failed", f"non-finite loss at update {update}"
            break

        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=cfg.grad_clip)
        opt.step()

        baseline = cfg.baseline_momentum * baseline + (1 - cfg.baseline_momentum) * reward.mean().item()
        if baseline > best_baseline:
            best_baseline, best_state = baseline, copy.deepcopy(model.state_dict())
        rows.append({"update": update, "loss": loss.item(), "accuracy": correct.mean().item(), "baseline": baseline})
        if update % log_every == 0:
            log.info(f"update {update}/{cfg.n_updates} loss={loss.item():+.3f} "
                     f"acc={rows[-1]['accuracy']:.2f} baseline={baseline:+.2f} elapsed={time.time() - t0:.0f}s")
        if time.time() - t0 > cfg.max_seconds:
            status = "timeout"
            break

    if best_state is not None:
        model.load_state_dict(best_state)
    if error:
        log.warning(error)
    return {"curve": pd.DataFrame(rows), "status": status, "elapsed_s": time.time() - t0,
            "n_updates_done": len(rows), "best_baseline": best_baseline, "error": error}
