"""Neuron dynamics as explicit per-step functions, all trained through the same
dampened surrogate gradient (see SurrogateSpike).

Every model keeps its state after the update (un-reset) and applies the reset at the
start of the next step from a detached "did it cross threshold" test, which is exactly
snntorch's Leaky/RLeaky convention (reset_delay=True, detached reset). Time is in
simulation steps; the tasks' steps correspond to the bio data's bins."""
import torch

THRESHOLD = 1.0
# Surrogate gradient: snntorch's default ATan shape, 1 / (1 + (pi x)^2), scaled down by
# Bellec et al. 2018's dampening factor. Undamped, gradients through 150 steps of
# recurrence at spectral radius 1 reach norms ~1e12 against ~1e3 at the readout, so a
# global-norm clip leaves the readout with no effective step (200-update mini-runs:
# 14/18 recurrent/modular runs at chance undamped, 7/18 damped). 0.3 brings every
# layer's gradient norm into the same 1-100 range. The ATan shape (not Bellec's triangle) keeps a gradient far from
# threshold, which a silent output layer needs to start spiking.
SURROGATE_DAMPENING = 0.3


class SurrogateSpike(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x):
        ctx.save_for_backward(x)
        return (x > 0).float()

    @staticmethod
    def backward(ctx, grad):
        (x,) = ctx.saved_tensors
        return grad * SURROGATE_DAMPENING / (1 + (torch.pi * x) ** 2)


spike = SurrogateSpike.apply

# ALIF (Bellec et al. 2018 LSNN formulation): a is an exponential running estimate of
# the neuron's own firing rate, and the threshold rises by ADAPT_STRENGTH * a. The
# ~100-step time constant spans most of a 150-step trial, so adaptation acts on the
# trial timescale rather than just after each spike.
ADAPT_DECAY = 0.99
ADAPT_STRENGTH = 1.8

# Izhikevich-style: v has a quadratic leak (1 - beta) * v * (v - 1), so rest is 0, the
# unstable fixed point sits at threshold 1, and the leak weakens as v nears threshold
# (type-1 excitability instead of LIF's linear leak). u is a recovery variable coupled
# to v below threshold (IZH_B) and kicked by each spike (IZH_D), subtracted from v. The
# reset goes to a fixed value, not by subtraction. Constants follow the regular-spiking
# cell mapped onto a rest=0 / threshold=1 scale (c=-65mV on -70..-50 -> 0.25, b=0.2),
# with recovery slower than the membrane (20 steps vs 1/(1-beta)=10 at beta 0.9).
IZH_A = 0.05
IZH_B = 0.2
IZH_D = 0.05
IZH_RESET = 0.25
IZH_V_MIN = -1.0  # hyperpolarization floor: keeps the Euler step of the quadratic stable

N_STATE = {"lif": 1, "alif": 2, "izhikevich": 2}


def init_state(neuron: str, batch: int, n: int, device) -> tuple:
    return tuple(torch.zeros(batch, n, device=device) for _ in range(N_STATE[neuron]))


def lif_step(cur, state, beta):
    (mem,) = state
    reset = (mem > THRESHOLD).float()
    mem = beta * mem + cur - reset * THRESHOLD
    return spike(mem - THRESHOLD), (mem,)


def alif_step(cur, state, beta):
    mem, a = state
    thr = THRESHOLD + ADAPT_STRENGTH * a
    reset = (mem > thr).float()
    a = ADAPT_DECAY * a + (1 - ADAPT_DECAY) * reset
    mem = beta * mem + cur - reset * thr
    return spike(mem - (THRESHOLD + ADAPT_STRENGTH * a)), (mem, a)


def izhikevich_step(cur, state, beta):
    v, u = state
    reset = (v > THRESHOLD).float()
    v = v * (1 - reset) + IZH_RESET * reset
    u = u + IZH_D * reset
    v_next = (v + (1 - beta) * v * (v - THRESHOLD) - u + cur).clamp(min=IZH_V_MIN)
    u = u + IZH_A * (IZH_B * v - u)
    return spike(v_next - THRESHOLD), (v_next, u)


STEPS = {"lif": lif_step, "alif": alif_step, "izhikevich": izhikevich_step}
