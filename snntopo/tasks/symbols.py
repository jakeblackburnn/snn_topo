"""Rate-coded symbol presentations shared by the generic working-memory tasks: a group
of CHANNELS_PER_SYMBOL input channels per symbol, spiking at SYMBOL_RATE while that
symbol is shown and silent otherwise. A group rather than one channel per symbol,
because a single channel drove the hidden layer too weakly for the readout to spike."""
import torch

SYMBOL_RATE = 0.5  # spike probability per step on the shown symbol's channels
CHANNELS_PER_SYMBOL = 8


def symbol_spikes(symbols: torch.Tensor, slots: list[tuple[int, int]], n_symbols: int, num_steps: int,
                  generator: torch.Generator) -> torch.Tensor:
    """symbols: (batch, len(slots)) long, symbols[:, i] shown during steps slots[i].
    -> (num_steps, batch, n_symbols * CHANNELS_PER_SYMBOL) float spikes."""
    rate = torch.zeros(num_steps, symbols.shape[0], n_symbols)
    for i, (start, stop) in enumerate(slots):
        rate[start:stop] += SYMBOL_RATE * torch.nn.functional.one_hot(symbols[:, i], n_symbols).float()
    rate = rate.repeat_interleave(CHANNELS_PER_SYMBOL, dim=2)
    return torch.bernoulli(rate, generator=generator)


def balanced_targets(batch_size: int, generator: torch.Generator) -> torch.Tensor:
    """Exactly half 0 (match), half 1 (non-match), shuffled; odd batches get one extra 1."""
    return (torch.randperm(batch_size, generator=generator) >= batch_size // 2).long()


def other_symbol(symbols: torch.Tensor, n_symbols: int, generator: torch.Generator) -> torch.Tensor:
    """A uniformly random symbol different from each of `symbols`."""
    return (symbols + torch.randint(1, n_symbols, symbols.shape, generator=generator)) % n_symbols
