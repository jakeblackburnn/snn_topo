"""IBL-style one-sided visual 2AFC.

Each trial presents contrast on one side at one of IBL's levels.  Zero-contrast
trials receive a random rewarded side; this deliberately omits IBL's block prior,
so the task remains a direct sensory discrimination rather than a prior-learning
task.  Input timing reuses the adapting transient used by Steinmetz2AFC.
"""
import torch
from snntorch import spikegen

from ..contracts import Task
from .steinmetz_2afc import transient_profile

CONTRAST_LEVELS = (0.0, 0.0625, 0.125, 0.25, 1.0)


class Ibl2AFC(Task):
    name = "ibl_2afc"
    n_in = 2
    action_names = ("left", "right")
    num_steps = 150
    response_steps = slice(0, 150)
    bio_match = "ibl"

    def sample_batch(self, batch_size, device, generator):
        side = torch.randint(0, 2, (batch_size,), generator=generator)
        level = torch.tensor(CONTRAST_LEVELS)[torch.randint(0, len(CONTRAST_LEVELS), (batch_size,), generator=generator)]
        target = side.clone()
        zero = level == 0
        target[zero] = torch.randint(0, 2, (int(zero.sum()),), generator=generator)
        contrasts = torch.zeros(batch_size, 2)
        contrasts[torch.arange(batch_size), side] = level
        rate = contrasts.unsqueeze(0) * transient_profile(self.num_steps).view(-1, 1, 1)
        return spikegen.rate(rate, time_var_input=True).to(device), target.to(device)
