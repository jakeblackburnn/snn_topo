"""Port of the multitask spiking network of Pugavko, Maslennikov & Nekorkin 2023, "Multitask
computation through dynamics in recurrent spiking neural networks" (Sci Rep 13:3997): one
recurrent layer of adaptive exponential integrate-and-fire (AdEx) neurons trained by surrogate
gradients on 12 cognitive tasks (Yang et al. 2019's set, reduced to scalar stimuli).

A published architecture and recipe that is known to train, used here as the "brain that does
many things" whose neurons a random probe samples. Sources, ported line for line where they
matter: github.com/Pugavkom/cgtasknet (tasks, accuracy), norse's `lif_adex_step` and `ExpFilter`
(the network), and their regularized-training notebook
(multy_task/server/mean_fr_filter_bigger_tau_a_less), whose settings are the defaults here.

Time step 1 ms. Inputs: fixation, two noisy modalities, a one-hot task rule. Outputs: fixation
and two response channels. Choice tasks answer on the channel of their choice; Go tasks
reproduce a value on the channel of their modality.
"""
import math

import numpy as np
import torch
from torch import nn
from torch.utils.checkpoint import checkpoint

DT = 1e-3
TASKS = ("CtxDMTask1", "CtxDMTask2", "DMTask1", "DMTask2", "GoDlTask1", "GoDlTask2",
         "GoRtTask1", "GoRtTask2", "GoTask1", "GoTask2", "RomoTask1", "RomoTask2")  # sorted, their rule order
GO_VALUES = np.linspace(0, 1, 8)
N_OUT = 3
GO_TOLERANCE = 0.15
EVAL_SKIP = 50  # their test drops the first 50 steps

# Neuron constants: norse's LIFAdExParameters defaults, which the paper's Table 1 lists.
TAU_MEM_INV, TAU_SYN_INV = 100.0, 200.0
A_CURRENT, A_SPIKE, DELTA_T = 4.0, 0.02, 0.5
V_LEAK, V_RESET = 0.0, 0.0
SURROGATE_ALPHA = 100.0


def is_go(task: str) -> bool:
    return task.startswith("Go")


def _interval(rng, low, high) -> int:
    return round(rng.uniform(low, high) / DT)


def trial(task: str, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """One trial -> (inputs (T, 3): fixation, mod 1, mod 2; targets (T, 3)). Durations in
    seconds as in their notebook's task parameters; 'avg, +shift' ranges are uniform."""
    mod = int(task[-1]) - 1
    kind = task[:-1]
    answer = round(0.25 / DT)
    if kind in ("DMTask", "CtxDMTask"):
        stim = _interval(rng, 0.3, 1.8)
        x, y = np.zeros((stim + answer, 3)), np.zeros((stim + answer, 3))
        x[:stim, 0] = 1
        if kind == "DMTask":
            v = rng.uniform(0, 1)
            x[:stim, 1 + mod] = v
        else:
            v1, v2 = rng.uniform(0, 1, 2)
            x[:stim, 1], x[:stim, 2] = v1, v2
            v = (v1, v2)[mod]  # the rule names which modality counts
        y[:, 0] = x[:, 0]
        y[stim:, 1], y[stim:, 2] = v < 0.5, v > 0.5
    elif kind == "RomoTask":
        stim, delay = _interval(rng, 0.2, 0.6), _interval(rng, 0.2, 1.7)
        n = 2 * stim + delay + answer
        v1, v2 = rng.uniform(0, 1, 2)
        x, y = np.zeros((n, 3)), np.zeros((n, 3))
        x[:n - answer, 0] = 1
        x[:stim, 1 + mod] = v1
        x[stim + delay:n - answer, 1 + mod] = v2
        y[:, 0] = x[:, 0]
        y[n - answer:, 1], y[n - answer:, 2] = v1 < v2, v2 < v1
    elif kind == "GoTask":
        stim = _interval(rng, 0.3, 1.8)
        v = rng.choice(GO_VALUES)
        x, y = np.zeros((stim + answer, 3)), np.zeros((stim + answer, 3))
        x[:stim, 0] = 1
        x[:, 1 + mod] = v
        y[:, 0] = x[:, 0]
        y[stim:, 1 + mod] = v
    elif kind == "GoRtTask":
        stim, answer = _interval(rng, 0.3, 1.8), round(1.5 / DT)
        v = rng.choice(GO_VALUES)
        x, y = np.zeros((stim + answer, 3)), np.zeros((stim + answer, 3))
        x[:, 0] = 1  # fixation never goes off: the stimulus onset is the go signal
        x[stim:, 1 + mod] = v
        y[:stim, 0] = 1
        y[stim:, 1 + mod] = v
    elif kind == "GoDlTask":
        stim, delay = _interval(rng, 0.2, 0.6), _interval(rng, 0.2, 1.7)
        n = stim + delay + answer
        v = rng.choice(GO_VALUES)
        x, y = np.zeros((n, 3)), np.zeros((n, 3))
        x[:stim + delay, 0] = 1
        x[:stim, 1 + mod] = v
        y[:, 0] = x[:, 0]
        y[stim + delay:, 1 + mod] = v
    else:
        raise ValueError(f"unknown task {task}")
    return x, y


def batch(task_sets: list[tuple[str, ...]], batch_size: int, rng: np.random.Generator):
    """One trial per row for each of G networks, its task drawn uniformly from that network's
    set; front-padded to the longest trial with fixation on (their enable_fixation_delay).
    The rule input is one-hot over all of TASKS, so a net trained on a subset just never sees
    the other channels. -> (inputs (T, G, B, 3 + 12), targets (T, G, B, 3), task index into
    TASKS (G, B), trial length without padding (G, B))."""
    G = len(task_sets)
    idx = np.array([[TASKS.index(tasks[i]) for i in rng.integers(0, len(tasks), batch_size)] for tasks in task_sets])
    trials = [[trial(TASKS[i], rng) for i in row] for row in idx]
    lengths = np.array([[len(x) for x, _ in row] for row in trials])
    T = lengths.max()
    inputs = np.zeros((T, G, batch_size, 3 + len(TASKS)))
    targets = np.zeros((T, G, batch_size, N_OUT))
    for g in range(G):
        for b, (x, y) in enumerate(trials[g]):
            pad = T - lengths[g, b]
            inputs[:pad, g, b, 0] = targets[:pad, g, b, 0] = 1
            inputs[pad:, g, b, :3], targets[pad:, g, b] = x, y
            inputs[:, g, b, 3 + idx[g, b]] = 1
    return inputs, targets, idx, lengths


def add_noise(inputs: np.ndarray, sigma: float, rng: np.random.Generator) -> np.ndarray:
    """Gaussian noise on the two modalities, its sd drawn per trial row from U(0, sigma)."""
    sd = rng.uniform(0, sigma, inputs.shape[1:3])
    out = inputs.copy()
    out[..., 1:3] += rng.normal(0, 1, out[..., 1:3].shape) * sd[None, :, :, None]
    return out


class SuperSpike(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return (x > 0).to(x.dtype)

    @staticmethod
    def backward(ctx, grad):
        (x,) = ctx.saved_tensors
        return grad / (SURROGATE_ALPHA * x.abs() + 1.0) ** 2


def adex_step(in_cur, z, v, i, a, w_rec, v_th, tau_ada_inv):
    """norse's lif_adex_step: one Euler step of AdEx with a current synapse. w_rec (..., N, N)."""
    i_jump = i + in_cur + z @ w_rec.transpose(-1, -2)
    v_decayed = v + DT * TAU_MEM_INV * (V_LEAK - v + DELTA_T * torch.exp((v - v_th) / DELTA_T) + i_jump - a)
    i_new = i_jump - DT * TAU_SYN_INV * i_jump
    a_decayed = a + DT * tau_ada_inv * (A_CURRENT * (v - V_LEAK) - a)
    z_new = SuperSpike.apply(v_decayed - v_th)
    v_new = (1 - z_new) * v_decayed + z_new * V_RESET
    return z_new, v_new, i_new, a_decayed + z_new * A_SPIKE


def _run_chunk(x, z, v, i, a, w_in, w_rec, w_out, b_out, v_th, tau_ada_inv):
    """-> (readout drive (t, G, B, 3), spike count per neuron (G, N), spikes, state). The loss
    needs only the first two, so under checkpointing neither the (T, G, B, N) input currents
    nor the spikes are ever kept whole."""
    spikes = []
    # unbind, not in_cur[t]: each indexing op's backward writes a full-size zero tensor
    for cur in torch.einsum("tgbi,gni->tgbn", x, w_in).unbind(0):
        z, v, i, a = adex_step(cur, z, v, i, a, w_rec, v_th, tau_ada_inv)
        spikes.append(z)
    spikes = torch.stack(spikes)
    drive = torch.einsum("tgbn,gon->tgbo", spikes, w_out) + b_out[:, None]
    return drive, spikes.sum((0, 2)), spikes, z, v, i, a


class AdExNet(nn.Module):
    """G independent copies of norse's LIFAdExRecurrent (no autapses, weights randn *
    sqrt(2 / N)) into an ExpFilter readout, run side by side: the 1 ms step loop is bound by
    per-step overhead, not arithmetic, so G nets cost about as much as one. Nets share no
    parameter, and the training loss is a sum over nets, so each gets its own gradient."""

    def __init__(self, n_hidden: int, n_nets: int = 1, v_th: float = 0.45, tau_ada_inv: float = 1.0,
                 tau_filter_inv: float = 40.0, n_in: int = 3 + len(TASKS)):
        super().__init__()
        scale = math.sqrt(2.0 / n_hidden)
        self.input_weights = nn.Parameter(torch.randn(n_nets, n_hidden, n_in) * scale)
        self.recurrent_weights = nn.Parameter(torch.randn(n_nets, n_hidden, n_hidden) * scale)
        self.register_buffer("no_autapse", 1 - torch.eye(n_hidden))
        bound = 1 / math.sqrt(n_hidden)  # nn.Linear's default init, per net
        self.readout_weight = nn.Parameter(torch.empty(n_nets, N_OUT, n_hidden).uniform_(-bound, bound))
        self.readout_bias = nn.Parameter(torch.empty(n_nets, N_OUT).uniform_(-bound, bound))
        self.n_hidden, self.n_nets = n_hidden, n_nets
        self.v_th, self.tau_ada_inv = v_th, tau_ada_inv
        self.kappa = math.exp(-DT * tau_filter_inv)

    def forward(self, x: torch.Tensor, v0: torch.Tensor, chunk: int = 0, record: bool = False):
        """x (T, G, B, n_in), v0 (G, B, N) initial voltage -> (outputs (T, G, B, 3), firing
        rate per neuron (G, N) in spikes per step, spikes (T, G, B, N) if record else None).
        chunk > 0 recomputes the step loop in chunks of that many steps during backward
        instead of storing every step (activation checkpointing), to fit G nets."""
        w_rec = self.recurrent_weights * self.no_autapse
        state = (torch.zeros_like(v0), v0, torch.zeros_like(v0), torch.zeros_like(v0))
        drives, count, spikes = [], 0, []
        for part in x.split(chunk or len(x)):
            args = (part, *state, self.input_weights, w_rec, self.readout_weight, self.readout_bias, self.v_th,
                    self.tau_ada_inv)
            if chunk and torch.is_grad_enabled():
                drive, n, s, *state = checkpoint(_run_chunk, *args, use_reentrant=False)
            else:
                drive, n, s, *state = _run_chunk(*args)
            drives.append(drive)
            count = count + n
            if record:
                spikes.append(s)
        drive = torch.cat(drives).unbind(0)
        out = [drive[0]]
        for d in drive[1:]:
            out.append(self.kappa * out[-1] + d)
        rate = count / (len(x) * x.shape[2])
        return torch.stack(out), rate, torch.cat(spikes) if record else None


def loss_fn(out, targets, rate, reg: float, rate_limit: float = 0.03) -> torch.Tensor:
    """Per net (G,): masked MSE (0.1 while the target fixates, 1 in the response) plus their
    firing-rate penalty, reg * mean over neurons of rate * [rate > 30 Hz], rate (G, N) in
    spikes per 1 ms step."""
    mask = torch.where(targets[..., :1] == 1, 0.1, 1.0).expand_as(targets)
    mse = ((out - targets) ** 2 * mask).sum((0, 2, 3)) / mask.sum((0, 2, 3))
    return mse + reg * (rate * (rate > rate_limit).detach()).mean(-1)


def first_below(x: torch.Tensor, value: float) -> torch.Tensor:
    """Their _first_value: first step where x < value, per column; len(x) if none or if it is step 0."""
    below = x < value
    first = (below.cumsum(0) == 1) & below
    idx = first.int().argmax(0)
    return torch.where(idx == 0, torch.full_like(idx, len(x)), idx)


def correct(out: torch.Tensor, targets: torch.Tensor, task_idx) -> np.ndarray:
    """Their CorrectAnswerNetwork (mode 'mean') on single-trial batches of one net, out and
    targets (T, B, 3), task_idx into TASKS (B,); the first EVAL_SKIP steps are dropped. The
    response is the mean output from the later of (target fixation end, the net's own fixation
    drop) to the end. Choice: the unique argmax of the two channels is the target's. Go: the
    larger channel is within GO_TOLERANCE of the target value."""
    out, targets = out[EVAL_SKIP:].cpu(), targets[EVAL_SKIP:].cpu()
    T = len(out)
    stop = torch.maximum(targets[:, :, 0].argmin(0), first_below(out[:, :, 0], 0.5))
    result = np.zeros(out.shape[1], dtype=bool)
    for b in range(out.shape[1]):
        if stop[b] >= T - 1:
            continue
        response = out[stop[b]:, b, 1:].mean(0)
        if is_go(TASKS[task_idx[b]]):
            result[b] = abs(targets[-1, b, 1:].max() - response.max()) < GO_TOLERANCE
        else:
            top = response == response.max()
            result[b] = top.sum() == 1 and response.argmax() == targets[-1, b, 1:].argmax()
    return result


def sigma_at(epoch: int) -> float:
    """Their input-noise curriculum: none, then 0.2 from epoch 500, 0.5 from epoch 1000."""
    return 0.0 if epoch < 500 else 0.2 if epoch < 1000 else 0.5


def train(net: AdExNet, task_sets, device, seed: int, epochs: int = 3000, batch_size: int = 32,
          lr: float = 5e-3, reg: float = 1e4, chunk: int = 500, log_every: int = 100, on_log=print) -> list[dict]:
    """Their regularized loop, for G nets at once (task_sets[g] for net g): each sequence is
    two trials back to back (their dataset(2)), each half padded to its longest trial.
    on_log(row, epoch) runs every log_every epochs (the place to checkpoint or evaluate)."""
    rng = np.random.default_rng(seed)
    opt = torch.optim.Adam(net.parameters(), lr=lr)
    log = []
    for epoch in range(epochs):
        x1, y1, _, _ = batch(task_sets, batch_size, rng)
        x2, y2, _, _ = batch(task_sets, batch_size, rng)
        x = add_noise(np.concatenate([x1, x2]), sigma_at(epoch), rng)
        x = torch.as_tensor(x, dtype=torch.float32, device=device)
        y = torch.as_tensor(np.concatenate([y1, y2]), dtype=torch.float32, device=device)
        v0 = torch.rand(net.n_nets, batch_size, net.n_hidden, device=device)
        out, rate, _ = net(x, v0, chunk)
        loss = loss_fn(out, y, rate, reg)
        opt.zero_grad()
        loss.sum().backward()
        opt.step()
        if (epoch + 1) % log_every == 0:
            row = {"epoch": epoch + 1, "loss": loss.tolist(), "rate_hz": (rate.mean(-1) / DT).tolist()}
            log.append(row)
            on_log(row, epoch + 1)
    return log


@torch.no_grad()
def evaluate(net: AdExNet, task_sets, device, seed: int, n_trials: int, batch_size: int = 25,
             sigma: float = 0.01, record: bool = True):
    """Single-trial batches with their test noise, net g on task_sets[g]. -> per net, a tuple
    of (correct (n,), task index into TASKS (n,), per-trial uint8 spikes (N, steps) without
    the padding, empty unless record)."""
    rng = np.random.default_rng(seed)
    gen = torch.Generator(device=device).manual_seed(seed)
    hits, idxs, trials = ([[] for _ in range(net.n_nets)] for _ in range(3))
    for start in range(0, n_trials, batch_size):
        b = min(batch_size, n_trials - start)
        x, y, idx, lengths = batch(task_sets, b, rng)
        x = torch.as_tensor(add_noise(x, sigma, rng), dtype=torch.float32, device=device)
        v0 = torch.rand(net.n_nets, b, net.n_hidden, device=device, generator=gen)
        out, _, spikes = net(x, v0, record=record)
        if record:
            spikes = spikes.to(torch.uint8).cpu().numpy()
        for g in range(net.n_nets):
            hits[g].append(correct(out[:, g], torch.as_tensor(y[:, g]), idx[g]))
            idxs[g].append(idx[g])
            if record:
                trials[g].extend(spikes[len(x) - n:, g, j].T for j, n in enumerate(lengths[g]))
    return [(np.concatenate(hits[g]), np.concatenate(idxs[g]), trials[g]) for g in range(net.n_nets)]
