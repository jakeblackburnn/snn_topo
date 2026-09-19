"""2AFC contrast discrimination matched to Steinmetz: two input channels carry
left/right contrast; the higher-contrast side is the rewarded action. Equal-contrast
trials are never presented (bio no-go trials are likewise excluded).

Input rate follows an adapting-transient profile (instant onset, exponential decay
to a sustained plateau) rather than a DC rate, so the network's drive keeps
evolving across the trial."""
import torch
from snntorch import spikegen

from ..contracts import Task

CONTRAST_LEVELS = (0.0, 0.25, 0.5, 1.0)
TAU_DECAY = 25  # steps
PLATEAU_FRAC = 0.3  # sustained rate as a fraction of the contrast-scaled peak


def transient_profile(num_steps: int) -> torch.Tensor:
    t = torch.arange(num_steps, dtype=torch.float32)
    return PLATEAU_FRAC + (1 - PLATEAU_FRAC) * torch.exp(-t / TAU_DECAY)


class Steinmetz2AFC(Task):
    name = "steinmetz_2afc"
    n_in = 2
    action_names = ("left", "right")
    num_steps = 150  # matches the bio window's 150 bins, for comparable point-cloud sizes
    response_steps = slice(0, 150)
    bio_match = "steinmetz"

    def sample_batch(self, batch_size, device, generator):
        levels = torch.tensor(CONTRAST_LEVELS)
        contrasts = torch.empty(batch_size, 2)
        n_filled = 0
        while n_filled < batch_size:
            c = levels[torch.randint(0, len(levels), (batch_size * 2, 2), generator=generator)]
            c = c[c[:, 0] != c[:, 1]]
            take = min(len(c), batch_size - n_filled)
            contrasts[n_filled:n_filled + take] = c[:take]
            n_filled += take
        target = (contrasts[:, 1] > contrasts[:, 0]).long()  # 0 = left wins, 1 = right wins
        rate = contrasts.unsqueeze(0) * transient_profile(self.num_steps).view(-1, 1, 1)
        spk_in = spikegen.rate(rate, time_var_input=True)
        return spk_in.to(device), target.to(device)
