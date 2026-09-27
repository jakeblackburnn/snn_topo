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
    """Rescale a square weight in place to spectral radius `target`."""
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


def membrane_betas(beta: float, tau_spread: float, n: int, device=None) -> torch.Tensor:
    """Deterministic per-neuron beta values spanning ``beta ± tau_spread``.

    The endpoint clamp keeps all discrete decays in the valid (0, 1] interval.  A
    one-neuron population receives beta itself, so the axis is neutral there too.
    """
    offsets = torch.linspace(-1.0, 1.0, n, device=device) if n > 1 else torch.zeros(1, device=device)
    return (beta + tau_spread * offsets).clamp(min=torch.finfo(torch.float32).eps, max=1.0)


class FeedforwardSNN(nn.Module):
    def __init__(self, n_in, sizes, n_out, neuron, beta, tau_spread=0.0):
        super().__init__()
        self.neuron, self.beta = neuron, beta
        widths = [n_in] + sizes
        self.layers = nn.ModuleList(nn.Linear(a, b) for a, b in zip(widths[:-1], widths[1:]))
        for i, size in enumerate(sizes):
            self.register_buffer(f"beta_{i}", membrane_betas(beta, tau_spread, size))
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
                spk, states[i] = step(cur if i == 0 else fc(spk), states[i], getattr(self, f"beta_{i}"))
                spikes.append(spk)
            spk_out, out_state = neurons.lif_step(self.readout(spk), out_state, self.beta)
            hidden.append(torch.cat(spikes, dim=1))
            out.append(spk_out)
        return torch.stack(hidden), torch.stack(out)


class RecurrentSNN(nn.Module):
    """Masks are fixed buffers; masked-out weights are zeroed in every forward, so they
    stay out of the dynamics whatever the optimizer does to them."""

    def __init__(self, n_in, n_out, rec_mask, in_mask, out_mask, neuron, beta, spectral_radius,
                 tau_spread=0.0, dale=False, frac_inhibitory=0.2):
        super().__init__()
        n_hidden = rec_mask.shape[0]
        self.neuron, self.beta, self.dale = neuron, beta, dale
        self.fc_in = nn.Linear(n_in, n_hidden)
        self.recurrent = nn.Linear(n_hidden, n_hidden, bias=False)
        self.readout = nn.Linear(n_hidden, n_out)
        self.register_buffer("rec_mask", rec_mask)
        self.register_buffer("in_mask", in_mask)
        self.register_buffer("out_mask", out_mask)
        self.register_buffer("beta_by_neuron", membrane_betas(beta, tau_spread, n_hidden))
        n_inhibitory = int(round(frac_inhibitory * n_hidden)) if dale else 0
        dale_sign = torch.ones(n_hidden)
        if n_inhibitory:
            dale_sign[-n_inhibitory:] = -1
        self.register_buffer("dale_sign", dale_sign)
        zero_readout(self.readout)
        with torch.no_grad():
            self.recurrent.weight.mul_(rec_mask)
        if spectral_radius is not None:
            with torch.no_grad():
                current = torch.linalg.eigvals(self.effective_recurrent_weight()).abs().max().item()
                if current > 0:
                    self.recurrent.weight.mul_(spectral_radius / current)

    def effective_recurrent_weight(self) -> torch.Tensor:
        """Masked recurrent matrix, sign-constrained by presynaptic column when Dale is on."""
        if self.dale:
            return torch.abs(self.recurrent.weight) * self.dale_sign.unsqueeze(0) * self.rec_mask
        return self.recurrent.weight * self.rec_mask

    def forward(self, spk_in):
        T, B, _ = spk_in.shape
        n_hidden = self.rec_mask.shape[0]
        step = neurons.STEPS[self.neuron]
        w_rec = self.effective_recurrent_weight()
        w_out = self.readout.weight * self.out_mask
        in_cur = F.linear(spk_in, self.fc_in.weight * self.in_mask, self.fc_in.bias)
        state = neurons.init_state(self.neuron, B, n_hidden, spk_in.device)
        out_state = neurons.init_state("lif", B, self.readout.out_features, spk_in.device)
        spk = torch.zeros(B, n_hidden, device=spk_in.device)
        hidden, out = [], []
        for t in range(T):
            spk, state = step(in_cur[t] + spk @ w_rec.T, state, self.beta_by_neuron)
            spk_out, out_state = neurons.lif_step(F.linear(spk, w_out, self.readout.bias), out_state, self.beta)
            hidden.append(spk)
            out.append(spk_out)
        return torch.stack(hidden), torch.stack(out)


class RateCTRNN(nn.Module):
    """A compact rate CTRNN.  Its hidden output is a non-negative rate per time bin."""

    def __init__(self, n_in: int, n_hidden: int, n_out: int, tau: float = 10.0, dt: float = 1.0,
                 spectral_radius: float | None = 0.9):
        super().__init__()
        if n_hidden < 1 or tau <= 0 or dt <= 0 or dt > tau:
            raise ValueError("rate CTRNN needs n_hidden >= 1 and 0 < dt <= tau")
        self.alpha = dt / tau
        self.fc_in = nn.Linear(n_in, n_hidden)
        self.recurrent = nn.Linear(n_hidden, n_hidden, bias=False)
        self.readout = nn.Linear(n_hidden, n_out)
        # A direct sensory readout is a standard leaky-integrator/CTRNN skip path:
        # it makes the current input observable while recurrence carries history.
        self.input_readout = nn.Linear(n_in, n_out, bias=False)
        # As in the spiking families, begin with equal policy logits so REINFORCE
        # explores both actions instead of inheriting a random-output bias.
        zero_readout(self.readout)
        with torch.no_grad():
            self.input_readout.weight.zero_()
        if spectral_radius is not None:
            set_spectral_radius(self.recurrent.weight, spectral_radius)

    def forward(self, inputs):
        T, B, _ = inputs.shape
        state = torch.zeros(B, self.recurrent.in_features, device=inputs.device)
        hidden, out = [], []
        for t in range(T):
            drive = self.fc_in(inputs[t]) + self.recurrent(torch.tanh(state))
            state = (1 - self.alpha) * state + self.alpha * drive
            rate = F.softplus(state)
            hidden.append(rate)
            # Policy logits are signed readout scores; only the hidden state is the
            # rate-valued population that becomes an Activity.  Rectifying this
            # output adds a large common baseline over 150 bins and suppresses the
            # REINFORCE signal at the 200-update smoke budget.
            out.append(self.readout(rate) + self.input_readout(inputs[t]))
        return torch.stack(hidden), torch.stack(out)
