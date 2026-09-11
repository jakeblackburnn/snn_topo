"""LIF spiking network: 2 Poisson-coded inputs -> LIF hidden layer -> 2 LIF outputs.
Output spike counts over time form the policy logits (REINFORCE trains this)."""
import torch
import torch.nn as nn
import snntorch as snn

from ..config import LIF_BETA, N_HIDDEN


class SNNPolicy(nn.Module):
    def __init__(self, n_in: int = 2, n_hidden: int = N_HIDDEN, n_out: int = 2, beta: float = LIF_BETA):
        super().__init__()
        self.fc1 = nn.Linear(n_in, n_hidden)
        self.lif1 = snn.Leaky(beta=beta)
        self.fc2 = nn.Linear(n_hidden, n_out)
        self.lif2 = snn.Leaky(beta=beta)

    def forward(self, spk_in: torch.Tensor):
        """spk_in: (T, batch, n_in) -> hidden_spk: (T, batch, n_hidden), out_spk: (T, batch, n_out)."""
        T = spk_in.shape[0]
        mem1 = self.lif1.init_leaky()
        mem2 = self.lif2.init_leaky()
        hidden_rec, out_rec = [], []
        for t in range(T):
            cur1 = self.fc1(spk_in[t])
            spk1, mem1 = self.lif1(cur1, mem1)
            cur2 = self.fc2(spk1)
            spk2, mem2 = self.lif2(cur2, mem2)
            hidden_rec.append(spk1)
            out_rec.append(spk2)
        return torch.stack(hidden_rec), torch.stack(out_rec)
