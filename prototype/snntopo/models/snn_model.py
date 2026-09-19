"""LIF spiking network: 2 time-varying-coded inputs -> recurrent LIF hidden layer
-> 2 LIF outputs. Output spike counts over time form the policy logits (REINFORCE
trains this). The hidden layer is all-to-all recurrent (snn.RLeaky) so trajectories
can evolve beyond a purely feedforward transient-to-fixed-point response."""
import torch
import torch.nn as nn
import snntorch as snn

from ..config import LIF_BETA, N_HIDDEN


def set_spectral_radius(weight: torch.Tensor, target: float) -> float:
    """Rescale a square recurrent weight matrix in-place so its spectral radius
    (largest |eigenvalue|) equals `target`. Returns the pre-rescale radius, since the
    default init's radius is itself diagnostic (a sub-critical/damped network never
    sustains a trajectory, regardless of what the input does)."""
    with torch.no_grad():
        current = torch.linalg.eigvals(weight).abs().max().item()
        if current > 0:
            weight.mul_(target / current)
    return current


class SNNPolicy(nn.Module):
    def __init__(self, n_in: int = 2, n_hidden: int = N_HIDDEN, n_out: int = 2, beta: float = LIF_BETA,
                 spectral_radius: float | None = None):
        super().__init__()
        self.fc1 = nn.Linear(n_in, n_hidden)
        self.rlif1 = snn.RLeaky(beta=beta, linear_features=n_hidden)
        self.fc2 = nn.Linear(n_hidden, n_out)
        self.lif2 = snn.Leaky(beta=beta)
        self.init_spectral_radius = None
        if spectral_radius is not None:
            self.init_spectral_radius = set_spectral_radius(self.rlif1.recurrent.weight, spectral_radius)

    def forward(self, spk_in: torch.Tensor):
        """spk_in: (T, batch, n_in) -> hidden_spk: (T, batch, n_hidden), out_spk: (T, batch, n_out)."""
        T = spk_in.shape[0]
        spk1, mem1 = self.rlif1.init_rleaky()
        mem2 = self.lif2.init_leaky()
        hidden_rec, out_rec = [], []
        for t in range(T):
            cur1 = self.fc1(spk_in[t])
            spk1, mem1 = self.rlif1(cur1, spk1, mem1)
            cur2 = self.fc2(spk1)
            spk2, mem2 = self.lif2(cur2, mem2)
            hidden_rec.append(spk1)
            out_rec.append(spk2)
        return torch.stack(hidden_rec), torch.stack(out_rec)
