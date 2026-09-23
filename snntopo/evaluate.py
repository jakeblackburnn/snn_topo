"""Run a trained policy greedily on fresh trials and return its hidden-layer activity
in the bio layout, split into conditions by chosen action."""
import numpy as np
import torch

from .contracts import Activity, Task
from .training import policy_logits

N_EVAL = 340


def evaluate(model, task: Task, n_eval: int, device: str, seed: int = 1) -> tuple[float, Activity]:
    """-> (greedy accuracy, Activity). Conditions are "all" plus one mask per action
    name; an action the policy never picks gets an empty mask, which the topology
    step records as skipped (degenerate policy) rather than failing."""
    model.eval()
    torch.manual_seed(seed)
    spk_in, target = task.sample_batch(n_eval, device, torch.Generator().manual_seed(seed))
    with torch.no_grad():
        hidden_spk, out_spk = model(spk_in)
        action = policy_logits(out_spk, task).argmax(dim=-1)
    model.train()
    accuracy = (action == target).float().mean().item()
    action = action.cpu().numpy()
    conditions = {"all": np.ones(n_eval, dtype=bool)}
    for i, name in enumerate(task.action_names):
        conditions[name] = action == i
    spikes = hidden_spk.permute(2, 1, 0).cpu().numpy().astype(np.float32)  # (neurons, trials, steps)
    return accuracy, Activity(spikes, conditions, slice(0, task.num_steps), bin_size_s=1.0)
