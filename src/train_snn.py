"""REINFORCE training of the LIF policy network on the 2AFC contrast task.
Output-layer spike counts -> softmax action probs; reward +1 correct / -1 incorrect;
EMA baseline + entropy bonus reduce variance. Differentiability comes entirely from
snntorch's surrogate-gradient spike function; REINFORCE supplies the reward-based
(non-differentiable-environment) objective on top.
"""
import sys
import time

import pandas as pd
import torch
import torch.nn.functional as F

from snn_model import SNNPolicy
from snn_task import sample_batch

ROOT_RESULTS = __import__("pathlib").Path(__file__).resolve().parent.parent / "results"


def train(n_updates=400, batch_size=32, num_steps=150, lr=1e-3, entropy_coef=0.01,
          baseline_momentum=0.9, seed=0, device=None, log_every=10):
    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    torch.manual_seed(seed)
    gen = torch.Generator().manual_seed(seed)

    model = SNNPolicy().to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    baseline = 0.0
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

        advantage = reward - baseline
        loss = -(dist.log_prob(action) * advantage.detach()).mean() - entropy_coef * dist.entropy().mean()

        opt.zero_grad()
        loss.backward()
        opt.step()

        baseline = baseline_momentum * baseline + (1 - baseline_momentum) * reward.mean().item()
        acc = correct.mean().item()
        rows.append({"update": update, "loss": loss.item(), "accuracy": acc, "baseline": baseline})

        if update % log_every == 0 or update == 1:
            elapsed = time.time() - t0
            print(f"update {update:4d}/{n_updates} loss={loss.item():+.3f} acc={acc:.2f} "
                  f"baseline={baseline:+.2f} elapsed={elapsed:.1f}s")

    total_time = time.time() - t0
    print(f"training done in {total_time:.1f}s ({total_time / n_updates:.3f}s/update)")

    df = pd.DataFrame(rows)
    ROOT_RESULTS.mkdir(exist_ok=True)
    df.to_csv(ROOT_RESULTS / "snn_training_curve.csv", index=False)
    torch.save(model.state_dict(), ROOT_RESULTS / "snn_policy_weights.pt")

    last_n = min(50, len(df))
    print(f"final {last_n}-update mean accuracy: {df['accuracy'].tail(last_n).mean():.3f}")
    return model, df


if __name__ == "__main__":
    n_updates = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    train(n_updates=n_updates)
