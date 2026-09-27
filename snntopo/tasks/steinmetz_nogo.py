"""Three-action Steinmetz contrast task with a rewarded zero-contrast withhold."""
import torch

from ..contracts import Task
from .steinmetz_2afc import CONTRAST_LEVELS, transient_profile


class SteinmetzNoGo(Task):
    """Left/right choices for unequal contrasts, ``nogo`` for (0, 0).

    ``left``, ``right``, and ``nogo`` deliberately match the conditions used for
    Steinmetz bio activity, so task-produced and biological rows can be joined by
    condition name without a translation layer.
    """

    name = "steinmetz_nogo"
    n_in = 2
    action_names = ("left", "right", "nogo")
    num_steps = 150
    response_steps = slice(0, 150)
    bio_match = "steinmetz"

    def sample_batch(self, batch_size, device, generator):
        levels = torch.tensor(CONTRAST_LEVELS)
        pairs = torch.cartesian_prod(levels, levels)
        left = pairs[pairs[:, 0] > pairs[:, 1]]
        right = pairs[pairs[:, 1] > pairs[:, 0]]
        target = torch.randint(0, 3, (batch_size,), generator=generator)
        contrasts = torch.zeros(batch_size, 2)
        for action, choices in ((0, left), (1, right)):
            mask = target == action
            contrasts[mask] = choices[torch.randint(len(choices), (int(mask.sum()),), generator=generator)]
        # target == 2 retains (0, 0): a rewarded, balanced withhold class.
        rate = contrasts.unsqueeze(0) * transient_profile(self.num_steps).view(-1, 1, 1)
        spikes = (torch.rand(rate.shape, generator=generator) < rate).float()
        return spikes.to(device), target.to(device)
