"""The prototype's recurrent LIF policy (snn.RLeaky hidden layer, LIF readout)."""
import snntorch as snn
import torch
import torch.nn as nn


def set_spectral_radius(weight: torch.Tensor, target: float) -> float:
    """Rescale a square weight in place to spectral radius `target`; returns the
    pre-rescale radius (the default init's radius is itself diagnostic)."""
    with torch.no_grad():
        current = torch.linalg.eigvals(weight).abs().max().item()
        if current > 0:
            weight.mul_(target / current)
    return current


class PrototypeRLIF(nn.Module):
    def __init__(self, n_in, n_hidden, n_out, beta, spectral_radius):
        super().__init__()
        self.fc1 = nn.Linear(n_in, n_hidden)
        self.rlif1 = snn.RLeaky(beta=beta, linear_features=n_hidden)
        self.fc2 = nn.Linear(n_hidden, n_out)
        self.lif2 = snn.Leaky(beta=beta)
        if spectral_radius is not None:
            set_spectral_radius(self.rlif1.recurrent.weight, spectral_radius)

    def forward(self, spk_in):
        spk1, mem1 = self.rlif1.init_rleaky()
        mem2 = self.lif2.init_leaky()
        hidden, out = [], []
        for t in range(spk_in.shape[0]):
            spk1, mem1 = self.rlif1(self.fc1(spk_in[t]), spk1, mem1)
            spk2, mem2 = self.lif2(self.fc2(spk1), mem2)
            hidden.append(spk1)
            out.append(spk2)
        return torch.stack(hidden), torch.stack(out)
