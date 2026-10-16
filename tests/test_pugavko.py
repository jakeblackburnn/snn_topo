import numpy as np
import torch

from snntopo import pugavko


def test_trials_answer_what_the_inputs_say():
    rng = np.random.default_rng(0)
    for task in pugavko.TASKS:
        for _ in range(20):
            x, y = pugavko.trial(task, rng)
            mod = int(task[-1]) - 1
            fix_off = np.flatnonzero(y[:, 0] == 0)[0]
            assert np.all(y[fix_off:, 0] == 0) and np.all(y[-1, 1:] == y[fix_off, 1:])
            if pugavko.is_go(task):
                assert y[-1, 1 + mod] in pugavko.GO_VALUES and y[-1, 2 - mod] == 0
                assert x[:, 1 + mod].max() == y[-1, 1 + mod]
            elif task.startswith("DM"):
                assert y[-1, 2] == (x[0, 1 + mod] > 0.5)
            elif task.startswith("CtxDM"):
                assert y[-1, 2] == (x[0, 1 + mod] > 0.5)
            else:  # Romo: first stimulus at step 0, second just before the answer
                v1, v2 = x[0, 1 + mod], x[fix_off - 1, 1 + mod]
                assert y[-1, 1] == (v1 < v2)


def test_batch_pads_with_fixation_and_holds_the_rule():
    x, y, idx, lengths = pugavko.batch([pugavko.TASKS, ("DMTask1", "DMTask2")], 16, np.random.default_rng(1))
    T = len(x)
    assert set(pugavko.TASKS[i] for i in idx[1]) <= {"DMTask1", "DMTask2"}
    for g in range(2):
        for b in range(16):
            pad = T - lengths[g, b]
            assert np.all(x[:pad, g, b, 0] == 1) and np.all(y[:pad, g, b, 0] == 1) and np.all(x[:pad, g, b, 1:3] == 0)
            assert np.all(x[:, g, b, 3 + idx[g, b]] == 1) and x[:, g, b, 3:].sum() == T


def test_adex_step_matches_hand_computation():
    v, i, a = torch.tensor([[0.2, 0.9]]), torch.tensor([[0.1, 0.0]]), torch.tensor([[0.05, 0.0]])
    z, w = torch.zeros(1, 2), torch.zeros(2, 2)
    z_new, v_new, i_new, a_new = pugavko.adex_step(torch.tensor([[0.0, 5.0]]), z, v, i, a, w, 0.45, 1.0)
    # neuron 0, sub-threshold: dv = 0.1 * (-0.2 + 0.5 exp(-0.5) + 0.1 - 0.05)
    assert np.isclose(v_new[0, 0].item(), 0.2 + 0.1 * (-0.2 + 0.5 * np.exp(-0.5) + 0.1 - 0.05))
    assert np.isclose(i_new[0, 0].item(), 0.1 * 0.8)
    assert np.isclose(a_new[0, 0].item(), 0.05 + 1e-3 * (4 * 0.2 - 0.05))
    # neuron 1 is driven over threshold: spikes, resets, adaptation jumps by A_SPIKE
    assert z_new[0, 1] == 1 and v_new[0, 1] == 0
    assert np.isclose(a_new[0, 1].item(), 1e-3 * 4 * 0.9 + 0.02)


def test_correct_scores_right_and_wrong_answers():
    x, y, idx, _ = pugavko.batch([("DMTask1", "GoTask1")], 32, np.random.default_rng(2))
    y, idx = torch.as_tensor(y[:, 0], dtype=torch.float32), idx[0]
    assert pugavko.correct(y, y, idx).all()
    flipped = y.clone()
    flipped[:, :, 1:] = y[:, :, 1:].flip(-1) + 0.3  # wrong channel for choices, off by 0.3 for Go
    assert not pugavko.correct(flipped, y, idx).any()
    never_releases = y.clone()
    never_releases[:, :, 0] = 1
    assert not pugavko.correct(never_releases, y, idx).any()


def test_side_by_side_nets_are_independent_and_checkpointing_is_exact():
    """Net 1's loss gradient never reaches net 0's weights; chunked recompute gives the
    same outputs and gradients as storing every step."""
    torch.manual_seed(0)
    net = pugavko.AdExNet(32, n_nets=2)
    x, y, _, _ = pugavko.batch([("DMTask1",), ("GoTask2",)], 4, np.random.default_rng(3))
    x, y = torch.as_tensor(x[:300], dtype=torch.float32), torch.as_tensor(y[:300], dtype=torch.float32)
    v0 = torch.rand(2, 4, 32)
    out, rate, spikes = net(x, v0, record=True)
    assert out.shape == (300, 2, 4, 3) and spikes.shape == (300, 2, 4, 32)
    assert torch.allclose(rate, spikes.mean((0, 2)))
    loss = pugavko.loss_fn(out, y, rate, 1e4)
    assert loss.shape == (2,)
    loss[1].backward()
    assert net.recurrent_weights.grad[0].abs().sum() == 0 and net.recurrent_weights.grad[1].abs().sum() > 0
    assert torch.all(net.recurrent_weights.grad[1].diagonal() == 0)
    full = net.recurrent_weights.grad.clone()
    net.zero_grad()
    out_c, rate_c, _ = net(x, v0, chunk=64)
    pugavko.loss_fn(out_c, y, rate_c, 1e4)[1].backward()
    assert torch.equal(out_c, out) and torch.allclose(net.recurrent_weights.grad, full, atol=1e-6)
