"""REINFORCE training of the LIF policy network on the 2AFC contrast task.
Output-layer spike counts -> softmax action probs; reward +1 correct / -1 incorrect;
EMA baseline + entropy bonus reduce variance. Differentiability comes entirely from
snntorch's surrogate-gradient spike function; REINFORCE supplies the reward-based
(non-differentiable-environment) objective on top.

BPTT through the recurrent hidden layer over NUM_STEPS destabilizes under the
original (128-hidden, feedforward) settings' fixed entropy_coef once the policy is
near-perfect: advantage (reward - baseline) vanishes at high accuracy, so the
constant entropy bonus term dominates the loss and actively pushes the policy back
toward uniform (observed: accuracy collapses from ~100% to chance and stays there).
Linearly annealing entropy_coef to 0 over training removes that late-training failure
mode. Gradient-norm clipping is also scaled for the much larger recurrent parameter
count (~490k vs ~500 in the original feedforward network) rather than reusing a
small-network default. The best-EMA-baseline checkpoint is what actually gets
saved/returned, so any residual instability doesn't clobber the usable trained policy.
"""
import copy
import time

import pandas as pd
import torch
import torch.nn.functional as F

from ..config import (
    BASELINE_MOMENTUM, BATCH_SIZE, ENTROPY_COEF, LEARNING_RATE, N_UPDATES,
    NUM_STEPS, RESULTS_DIR, TRAIN_SEED,
)
from ..data.snn_task import sample_batch
from ..io_utils import save_dataframe
from ..logging_utils import get_logger
from ..models.snn_model import SNNPolicy


def train(n_updates: int = N_UPDATES, batch_size: int = BATCH_SIZE, num_steps: int = NUM_STEPS,
          lr: float = LEARNING_RATE, entropy_coef: float = ENTROPY_COEF,
          baseline_momentum: float = BASELINE_MOMENTUM, seed: int = TRAIN_SEED,
          spectral_radius: float | None = None, tag: str = "",
          device: str = None, log_every: int = 10):
    log = get_logger()
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    log.info(f"training on device={device}, n_updates={n_updates}, batch_size={batch_size}, "
             f"spectral_radius={spectral_radius}")
    torch.manual_seed(seed)
    gen = torch.Generator().manual_seed(seed)

    model = SNNPolicy(spectral_radius=spectral_radius).to(device)
    if model.init_spectral_radius is not None:
        log.info(f"recurrent weight rescaled: default-init radius={model.init_spectral_radius:.3f} "
                 f"-> target={spectral_radius}")
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    baseline = 0.0
    best_baseline = -1.0
    best_state = None
    rows = []

    t0 = time.time()
    for update in range(1, n_updates + 1):
        spk_in, correct_action, _ = sample_batch(batch_size, num_steps, device, generator=gen)
        _, out_spk = model(spk_in)  # (T, batch, 2)
        logits = out_spk.sum(dim=0)  # (batch, 2) spike counts as action logits
        probs = F.softmax(logits, dim=-1)
        dist = torch.distributions.Categorical(probs=probs)
        action = dist.sample()
        correct = (action == correct_action).float()
        reward = correct * 2 - 1  # +1 / -1

        entropy_coef_t = entropy_coef * (1 - (update - 1) / n_updates)  # linear anneal to 0

        advantage = reward - baseline
        loss = -(dist.log_prob(action) * advantage.detach()).mean() - entropy_coef_t * dist.entropy().mean()

        opt.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=10.0)
        opt.step()

        baseline = baseline_momentum * baseline + (1 - baseline_momentum) * reward.mean().item()
        if baseline > best_baseline:
            best_baseline = baseline
            best_state = copy.deepcopy(model.state_dict())
        acc = correct.mean().item()
        rows.append({"update": update, "loss": loss.item(), "accuracy": acc, "baseline": baseline})

        if update % log_every == 0 or update == 1:
            elapsed = time.time() - t0
            log.info(f"update {update:4d}/{n_updates} loss={loss.item():+.3f} acc={acc:.2f} "
                      f"baseline={baseline:+.2f} elapsed={elapsed:.1f}s")

    total_time = time.time() - t0
    log.info(f"training done in {total_time:.1f}s ({total_time / n_updates:.3f}s/update)")

    df = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(exist_ok=True)
    save_dataframe(df, RESULTS_DIR / f"snn_training_curve{tag}.csv")

    if best_state is not None:
        model.load_state_dict(best_state)
    log.info(f"restoring best checkpoint (best EMA baseline={best_baseline:+.2f}) for saving/return")
    torch.save(model.state_dict(), RESULTS_DIR / f"snn_policy_weights{tag}.pt")

    last_n = min(50, len(df))
    log.info(f"final {last_n}-update mean accuracy: {df['accuracy'].tail(last_n).mean():.3f}")
    return model, df
