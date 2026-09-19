"""Delayed match-to-sample: a sample symbol, a silent delay, then a test symbol. The
single decision (match / non-match) is read out over the test period only, so the
sample has to be held across the delay."""
import torch

from ..contracts import Task
from .symbols import CHANNELS_PER_SYMBOL, balanced_targets, other_symbol, symbol_spikes

N_SYMBOLS = 4
SAMPLE = (0, 30)
TEST = (100, 150)  # steps 30-99 are the delay


class DMS(Task):
    name = "dms"
    n_in = N_SYMBOLS * CHANNELS_PER_SYMBOL
    action_names = ("match", "non_match")
    num_steps = 150  # same point-cloud size as the matched tasks
    response_steps = slice(*TEST)
    bio_match = None

    def sample_batch(self, batch_size, device, generator):
        target = balanced_targets(batch_size, generator)
        sample = torch.randint(0, N_SYMBOLS, (batch_size,), generator=generator)
        test = torch.where(target == 0, sample, other_symbol(sample, N_SYMBOLS, generator))
        spk_in = symbol_spikes(torch.stack([sample, test], 1), [SAMPLE, TEST], N_SYMBOLS, self.num_steps, generator)
        return spk_in.to(device), target.to(device)
