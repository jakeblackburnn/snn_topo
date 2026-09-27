"""Model registry: every valid axis combination builds and trains, the neuron models
and wiring masks have the dynamics/statistics they claim, and validate() rejects what
can't be built."""
import networkx as nx
import pytest
import snntorch as snn
import torch

from snntopo.contracts import ModelConfig
from snntopo.models import build_model, valid_triples, validate
from snntopo.models import connectivity as conn
from snntopo.models import neurons
from snntopo.models.networks import RecurrentSNN


def small_config(arch, neuron, connectivity):
    return ModelConfig(arch, neuron, connectivity, n_hidden=64,
                       n_layers=2 if arch == "feedforward" else 1, n_modules=2 if arch == "modular" else 1)


def test_valid_triples_cover_the_axis_product():
    triples = valid_triples()
    assert len(triples) == 3 * (1 + 4 + 4)  # neurons x (feedforward/none + 4 wirings x 2 recurrent archs)
    assert ("feedforward", "lif", "none") in triples and ("modular", "izhikevich", "modular_hub") in triples
    assert ("feedforward", "lif", "random") not in triples and ("recurrent", "lif", "none") not in triples


@pytest.mark.parametrize("triple", valid_triples(), ids="-".join)
def test_every_valid_triple_builds_runs_and_backprops(triple):
    torch.manual_seed(0)
    model = build_model(small_config(*triple), n_in=3, n_out=2)
    spk_in = (torch.rand(20, 4, 3) < 0.5).float()
    hidden, out = model(spk_in)
    assert hidden.shape == (20, 4, 64) and out.shape == (20, 4, 2)
    (hidden.sum() + out.sum()).backward()  # hidden too: the zero-init readout passes no gradient back yet
    for name, p in model.named_parameters():
        assert p.grad is not None and torch.isfinite(p.grad).all() and p.grad.abs().sum() > 0, name


def test_lif_step_matches_snntorch_leaky():
    torch.manual_seed(0)
    ref = snn.Leaky(beta=0.9)
    mem_ref = ref.init_leaky()
    state = neurons.init_state("lif", 8, 16, "cpu")
    for _ in range(50):
        cur = torch.randn(8, 16)
        spk_ref, mem_ref = ref(cur, mem_ref)
        spk, state = neurons.lif_step(cur, state, 0.9)
        assert torch.equal(spk, spk_ref) and torch.allclose(state[0], mem_ref)


def test_recurrent_lif_matches_prototype_rleaky():
    # the prototype's model (snn.RLeaky hidden + snn.Leaky readout) with the same weights,
    # dense wiring and no recurrent bias must produce identical spikes
    torch.manual_seed(0)
    n, n_in, n_out = 32, 2, 2
    model = RecurrentSNN(n_in, n_out, torch.ones(n, n), torch.ones(n, n_in), torch.ones(n_out, n), "lif", 0.9, 1.0)
    rlif = snn.RLeaky(beta=0.9, linear_features=n)
    lif = snn.Leaky(beta=0.9)
    with torch.no_grad():
        rlif.recurrent.weight.copy_(model.recurrent.weight)
        rlif.recurrent.bias.zero_()
        model.readout.weight.normal_(0, 0.5)  # the zero-init readout would never spike
    spk_in = (torch.rand(40, 4, n_in) < 0.5).float()
    spk1, mem1 = rlif.init_rleaky()
    mem2 = lif.init_leaky()
    hidden, out = model(spk_in)
    for t in range(40):
        spk1, mem1 = rlif(model.fc_in(spk_in[t]), spk1, mem1)
        spk2, mem2 = lif(model.readout(spk1), mem2)
        assert torch.equal(hidden[t], spk1) and torch.equal(out[t], spk2)
    assert hidden.sum() > 0 and out.sum() > 0


@pytest.mark.parametrize("neuron", ["alif", "izhikevich"])
def test_adapting_neurons_slow_down_under_constant_drive(neuron):
    def spike_counts(name):
        state = neurons.init_state(name, 1, 1, "cpu")
        spikes = []
        for _ in range(150):
            spk, state = neurons.STEPS[name](torch.full((1, 1), 0.3), state, 0.9)
            spikes.append(spk.item())
        return sum(spikes[:50]), sum(spikes[-50:])

    early, late = spike_counts(neuron)
    lif_early, lif_late = spike_counts("lif")
    assert early > 0 and late < early
    assert lif_late >= lif_early - 1  # LIF has no adaptation: rate stays put


def edge_count(mask):
    return int(mask.sum().item()) // 2


@pytest.mark.parametrize("connectivity", ["random", "small_world", "scale_free", "modular_hub"])
@pytest.mark.parametrize("n", [32, 256])
def test_masks_are_symmetric_loopless_and_share_an_edge_budget(connectivity, n):
    mask = conn.population_mask(connectivity, n, seed=0)
    assert mask.shape == (n, n) and torch.equal(mask, mask.T) and mask.diagonal().sum() == 0
    target = n * conn.mean_degree(n) // 2
    assert abs(edge_count(mask) - target) <= 0.1 * target
    assert nx.is_connected(nx.from_numpy_array(mask.numpy()))


def graph(connectivity, n=256, seed=0):
    return nx.from_numpy_array(conn.population_mask(connectivity, n, seed).numpy())


def test_small_world_is_more_clustered_than_random():
    assert nx.average_clustering(graph("small_world")) > 3 * nx.average_clustering(graph("random"))


def test_scale_free_has_heavy_tailed_degrees():
    max_degree = lambda g: max(d for _, d in g.degree())
    assert max_degree(graph("scale_free")) > 2 * max_degree(graph("random"))


def test_modular_hub_has_communities_and_hubs():
    n = 256
    mask = conn.population_mask("modular_hub", n, seed=0)
    community = torch.arange(n) // (n // conn.N_COMMUNITIES)
    same = community[:, None] == community[None, :]
    off_diag = ~torch.eye(n, dtype=torch.bool)
    assert mask[same & off_diag].mean() > 10 * mask[~same].mean()
    hubs = torch.arange(conn.N_COMMUNITIES) * (n // conn.N_COMMUNITIES)
    degree = mask.sum(1)
    assert degree[hubs].min() > 2 * degree.mean()


def test_modular_mask_is_block_chain():
    sizes = [64, 64, 64]
    mask = conn.modular_mask("random", sizes, seed=0)
    block = lambda i, j: mask[64 * i:64 * (i + 1), 64 * j:64 * (j + 1)]
    within = torch.stack([block(i, i).mean() for i in range(3)]).mean()
    between = torch.stack([block(0, 1).mean(), block(1, 0).mean(), block(1, 2).mean(), block(2, 1).mean()]).mean()
    assert within > 3 * between > 0
    assert block(0, 2).sum() == 0 and block(2, 0).sum() == 0  # only neighbouring modules connect


def test_modular_model_routes_input_to_first_module_and_reads_last():
    torch.manual_seed(0)
    model = build_model(ModelConfig("modular", "lif", "random", n_hidden=96, n_modules=3), n_in=2, n_out=2)
    assert model.in_mask[:32].all() and model.in_mask[32:].sum() == 0
    assert model.out_mask[:, 64:].all() and model.out_mask[:, :64].sum() == 0


@pytest.mark.parametrize("arch,n_modules", [("recurrent", 1), ("modular", 4)])
def test_masked_recurrent_matrix_has_target_radius_and_masked_weights_get_no_gradient(arch, n_modules):
    torch.manual_seed(0)
    model = build_model(ModelConfig(arch, "lif", "small_world", n_hidden=128, n_modules=n_modules,
                                    spectral_radius=0.8), n_in=2, n_out=2)
    w = model.recurrent.weight
    assert (w[model.rec_mask == 0] == 0).all()
    assert torch.linalg.eigvals(w).abs().max().item() == pytest.approx(0.8, rel=1e-4)
    _, out = model((torch.rand(30, 4, 2) < 0.5).float())
    out.sum().backward()
    assert (w.grad[model.rec_mask == 0] == 0).all()


def test_tau_spread_is_deterministic_per_neuron_and_changes_hidden_betas():
    model = build_model(ModelConfig("recurrent", "lif", "random", 64, beta=0.8, tau_spread=0.1), 2, 2)
    assert model.beta_by_neuron[0].item() == pytest.approx(0.7)
    assert model.beta_by_neuron[-1].item() == pytest.approx(0.9)
    assert torch.unique(model.beta_by_neuron).numel() == 64


@pytest.mark.parametrize("arch,n_modules", [("recurrent", 1), ("modular", 2)])
def test_dale_effective_recurrent_columns_keep_their_sign_after_optimizer_steps(arch, n_modules):
    torch.manual_seed(3)
    model = build_model(ModelConfig(arch, "lif", "random", 64, n_modules=n_modules,
                                    dale=True, frac_inhibitory=0.25), 2, 2)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    inputs = torch.rand(10, 4, 2)
    for _ in range(3):
        _, out = model(inputs)
        opt.zero_grad()
        out.sum().backward()
        opt.step()
    effective = model.effective_recurrent_weight().detach()
    excitatory = model.dale_sign > 0
    inhibitory = ~excitatory
    assert (effective[:, excitatory] >= 0).all()
    assert (effective[:, inhibitory] <= 0).all()


@pytest.mark.parametrize("cfg,reason", [
    (ModelConfig("feedforward", "lif", "random", 64), "connectivity must be 'none'"),
    (ModelConfig("recurrent", "lif", "none", 64), "needs a recurrent wiring"),
    (ModelConfig("recurrent", "hodgkin_huxley", "random", 64), "unknown neuron"),
    (ModelConfig("recurrent", "lif", "random", 64, n_layers=2), "n_layers"),
    (ModelConfig("modular", "lif", "random", 64, n_modules=1), "n_modules"),
    (ModelConfig("recurrent", "lif", "random", 64, n_modules=2), "n_modules"),
    (ModelConfig("modular", "lif", "random", 64, n_modules=3), "fewer than 32"),
    (ModelConfig("feedforward", "lif", "none", 64, n_layers=4), "fewer than 32"),
    (ModelConfig("recurrent", "lif", "random", 64, beta=0.0), "beta"),
    (ModelConfig("recurrent", "lif", "random", 64, tau_spread=-0.1), "tau_spread"),
    (ModelConfig("feedforward", "lif", "none", 64, dale=True), "dale applies"),
    (ModelConfig("recurrent", "lif", "random", 64, frac_inhibitory=0.3), "frac_inhibitory applies"),
    (ModelConfig("recurrent", "lif", "random", 64, spectral_radius=-1.0), "spectral_radius"),
])
def test_validate_rejects_with_reason(cfg, reason):
    with pytest.raises(ValueError, match=reason):
        validate(cfg)
    with pytest.raises(ValueError, match=reason):
        build_model(cfg, 2, 2)
