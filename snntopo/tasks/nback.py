"""2-back over a stream of rate-coded symbols: five items, each shown for ITEM_ON steps
then blank for the rest of its slot. The single decision is whether the final item
matches the one two positions back; it is read out over the final item's slot."""
import torch

from ..contracts import Task
from .symbols import CHANNELS_PER_SYMBOL, balanced_targets, other_symbol, symbol_spikes

N_SYMBOLS = 4
N_ITEMS = 5
SLOT = 30  # steps per item; N_ITEMS * SLOT = num_steps
ITEM_ON = 20


class NBack(Task):
    name = "nback"
    n_in = N_SYMBOLS * CHANNELS_PER_SYMBOL
    action_names = ("match", "non_match")
    num_steps = N_ITEMS * SLOT  # 150, same point-cloud size as the matched tasks
    response_steps = slice((N_ITEMS - 1) * SLOT, N_ITEMS * SLOT)
    bio_match = None

    def sample_batch(self, batch_size, device, generator):
        target = balanced_targets(batch_size, generator)
        items = torch.randint(0, N_SYMBOLS, (batch_size, N_ITEMS), generator=generator)
        two_back = items[:, -3]
        items[:, -1] = torch.where(target == 0, two_back, other_symbol(two_back, N_SYMBOLS, generator))
        slots = [(i * SLOT, i * SLOT + ITEM_ON) for i in range(N_ITEMS)]
        spk_in = symbol_spikes(items, slots, N_SYMBOLS, self.num_steps, generator)
        return spk_in.to(device), target.to(device)
