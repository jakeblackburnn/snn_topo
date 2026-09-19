"""SNN model registry: ModelConfig (4 axes) -> nn.Module.

Interface-phase placeholder: only the prototype's recurrent LIF with random all-to-all
wiring builds; the model-registry workstream implements the full axis product."""
from ..contracts import ModelConfig
from .prototype_rlif import PrototypeRLIF

ARCHS = ("feedforward", "recurrent", "modular")
NEURONS = ("lif", "alif", "izhikevich")
CONNECTIVITIES = ("none", "random", "small_world", "scale_free", "modular_hub")


def build_model(cfg: ModelConfig, n_in: int, n_out: int):
    if (cfg.arch, cfg.neuron, cfg.connectivity) == ("recurrent", "lif", "random"):
        return PrototypeRLIF(n_in, cfg.n_hidden, n_out, cfg.beta, cfg.spectral_radius)
    raise NotImplementedError(f"model not built yet: {cfg}")
