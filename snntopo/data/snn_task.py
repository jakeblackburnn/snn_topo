"""Poisson-encoded 2AFC contrast-discrimination task, mirroring the Steinmetz task
structure: two channels carry left/right stimulus contrast; the higher-contrast side
is the rewarded action. Equal-contrast trials are excluded (no clear correct side),
matching how bio no-go trials are excluded in scripts/run_bio_analysis.py."""
import torch
from snntorch import spikegen

from ..config import CONTRAST_LEVELS

_LEVELS = torch.tensor(CONTRAST_LEVELS)


def sample_batch(batch_size: int, num_steps: int, device: str, generator: torch.Generator = None):
    """Returns (spk_in: (T,batch,2), correct_action: (batch,) long [0=left,1=right], contrasts)."""
    contrasts = torch.empty(batch_size, 2)
    n_filled = 0
    while n_filled < batch_size:
        idx = torch.randint(0, len(_LEVELS), (batch_size * 2, 2), generator=generator)
        c = _LEVELS[idx]
        keep = c[:, 0] != c[:, 1]
        c = c[keep]
        take = min(len(c), batch_size - n_filled)
        contrasts[n_filled : n_filled + take] = c[:take]
        n_filled += take

    correct_action = (contrasts[:, 1] > contrasts[:, 0]).long()  # 0=left wins, 1=right wins
    spk_in = spikegen.rate(contrasts, num_steps=num_steps).to(device)  # (T, batch, 2)
    return spk_in, correct_action.to(device), contrasts
