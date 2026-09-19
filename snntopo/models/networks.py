"""The two network shapes every ModelConfig builds into: a stack of feedforward
hidden layers, or one recurrent population whose masks encode the rest (plain
recurrent: full input and readout; modular: block-structured recurrence, input into
the first module only, readout from the last only). Both end in a LIF readout whose
spike counts are the policy logits."""
import torch
import torch.nn as nn
import torch.nn.functional as F

from . import neurons


def set_spectral_radius(weight: torch.Tensor, target: float) -> float:
    """Rescale a square weight in place to spectral radius `target`; returns the
    pre-rescale radius (the default init's radius is itself diagnostic)."""
    with torch.no_grad():
        current = torch.linalg.eigvals(weight).abs().max().item()
        if current > 0:
            weight.mul_(target / current)
    return current


def zero_readout(readout: nn.Linear) -> None:
    """Start the output layer silent so the initial policy is uniform. With a random
    init, output spike counts differ by tens of spikes per trial, the softmax over
    counts is already near-deterministic, and REINFORCE's log-prob gradient vanishes
    before it can explore (6/9 recurrent runs stuck at chance in 200-update mini-runs
    vs 0/9 with this). The surrogate still passes gradient to a silent layer."""
    with torch.no_grad():
        readout.weight.zero_()
        readout.bias.zero_()


class FeedforwardSNN(nn.Module):
    def __init__(self, n_in, sizes, n_out, neuron, beta):
        super().__init__()
        self.neuron, self.beta = neuron, beta
        widths = [n_in] + sizes
        self.layers = nn.ModuleList(nn.Linear(a, b) for a, b in zip(widths[:-1], widths[1:]))
        self.readout = nn.Linear(sizes[-1], n_out)
        zero_readout(self.readout)

    def forward(self, spk_in):
        T, B, _ = spk_in.shape
        step = neurons.STEPS[self.neuron]
        states = [neurons.init_state(self.neuron, B, fc.out_features, spk_in.device) for fc in self.layers]
        out_state = neurons.init_state("lif", B, self.readout.out_features, spk_in.device)
        first_cur = self.layers[0](spk_in)  # the input layer has no dependence on state, so batch it over time
        hidden, out = [], []
        for t in range(T):
            cur, spikes = first_cur[t], []
            for i, fc in enumerate(self.layers):
                spk, states[i] = step(cur if i == 0 else fc(spk), states[i], self.beta)
                spikes.append(spk)
            spk_out, out_state = neurons.lif_step(self.readout(spk), out_state, self.beta)
            hidden.append(torch.cat(spikes, dim=1))
            out.append(spk_out)
        return torch.stack(hidden), torch.stack(out)


class RecurrentSNN(nn.Module):
    """Masks are fixed buffers; masked-out weights are zeroed in every forward, so they
    stay out of the dynamics whatever the optimizer does to them."""

    def __init__(self, n_in, n_out, rec_mask, in_mask, out_mask, neuron, beta, spectral_radius):
        super().__init__()
        n_hidden = rec_mask.shape[0]
        self.neuron, self.beta = neuron, beta
        self.fc_in = nn.Linear(n_in, n_hidden)
        self.recurrent = nn.Linear(n_hidden, n_hidden, bias=False)
        self.readout = nn.Linear(n_hidden, n_out)
        self.register_buffer("rec_mask", rec_mask)
        self.register_buffer("in_mask", in_mask)
        self.register_buffer("out_mask", out_mask)
        zero_readout(self.readout)
        with torch.no_grad():
            self.recurrent.weight.mul_(rec_mask)
        self.init_spectral_radius = None
        if spectral_radius is not None:
            self.init_spectral_radius = set_spectral_radius(self.recurrent.weight, spectral_radius)

    def forward(self, spk_in):
        T, B, _ = spk_in.shape
        n_hidden = self.rec_mask.shape[0]
        step = neurons.STEPS[self.neuron]
        w_rec = self.recurrent.weight * self.rec_mask
        w_out = self.readout.weight * self.out_mask
        in_cur = F.linear(spk_in, self.fc_in.weight * self.in_mask, self.fc_in.bias)
        state = neurons.init_state(self.neuron, B, n_hidden, spk_in.device)
        out_state = neurons.init_state("lif", B, self.readout.out_features, spk_in.device)
        spk = torch.zeros(B, n_hidden, device=spk_in.device)
        hidden, out = [], []
        for t in range(T):
            spk, state = step(in_cur[t] + spk @ w_rec.T, state, self.beta)
            spk_out, out_state = neurons.lif_step(F.linear(spk, w_out, self.readout.bias), out_state, self.beta)
            hidden.append(spk)
            out.append(spk_out)
        return torch.stack(hidden), torch.stack(out)
