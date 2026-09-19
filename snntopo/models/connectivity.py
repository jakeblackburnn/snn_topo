"""Recurrent wiring masks, fixed at init. A mask is a (n, n) float tensor, 1 where a
trainable weight exists.

Density: every structure gets the same edge budget, mean degree
k = max(MIN_DEGREE, nearest even number to RECURRENT_DENSITY * (n - 1)), i.e. n*k/2
undirected edges, so structures differ in how edges are arranged, not how many there
are. 0.1 is in the range of local cortical connection probability; MIN_DEGREE = 4 is
the smallest degree at which Watts-Strogatz lattices have clustering at all (k=2 is a
bare ring), so at the smallest populations the density rises above 0.1 (n=32: 0.13).
Graphs are undirected (clustering, hubs and communities are defined on undirected
graphs), so each edge gives a reciprocal pair of independently trained weights. No
self-connections.

Modular architecture: modules are chained 0 -> 1 -> ... -> last with feedforward and
feedback projections between neighbours only, each directed neuron pair present with
probability INTER_MODULE_DENSITY, well below the within-module density."""
import networkx as nx
import numpy as np
import torch

RECURRENT_DENSITY = 0.1
MIN_DEGREE = 4
WS_REWIRE_P = 0.1  # Watts-Strogatz rewiring: high clustering with short paths
N_COMMUNITIES = 4  # modular_hub
HUB_WITHIN_FRAC = 0.9  # modular_hub: share of the non-hub edge budget kept inside communities
INTER_MODULE_DENSITY = 0.02


def mean_degree(n: int) -> int:
    return max(MIN_DEGREE, 2 * round(RECURRENT_DENSITY * (n - 1) / 2))


def split_sizes(n: int, k: int) -> list[int]:
    """n into k contiguous groups whose sizes differ by at most one."""
    return [n // k + (1 if i < n % k else 0) for i in range(k)]


def modular_hub_graph(n: int, n_edges: int, rng: np.random.Generator) -> nx.Graph:
    """N_COMMUNITIES contiguous communities, each with one hub (its first node) wired to
    its whole community and to every other hub, so hubs carry most cross-community
    traffic. The rest of the edge budget is spread uniformly over non-hub pairs, mostly
    inside communities."""
    sizes = split_sizes(n, N_COMMUNITIES)
    starts = np.cumsum([0] + sizes[:-1]).tolist()
    community = np.repeat(np.arange(N_COMMUNITIES), sizes)
    is_hub = np.zeros(n, dtype=bool)
    is_hub[starts] = True
    g = nx.empty_graph(n)
    for h, s in zip(starts, sizes):
        g.add_edges_from((h, j) for j in range(h + 1, h + s))
    g.add_edges_from((a, b) for a in starts for b in starts if a < b)

    i, j = np.triu_indices(n, 1)
    free = ~is_hub[i] & ~is_hub[j]
    same = community[i] == community[j]
    within = np.flatnonzero(free & same)
    between = np.flatnonzero(free & ~same)
    rest = n_edges - g.number_of_edges()
    n_within = min(round(rest * HUB_WITHIN_FRAC), len(within))
    n_between = min(rest - n_within, len(between))
    for pairs, count in ((within, n_within), (between, n_between)):
        chosen = rng.choice(pairs, size=count, replace=False)
        g.add_edges_from(zip(i[chosen].tolist(), j[chosen].tolist()))
    return g


def population_graph(connectivity: str, n: int, seed: int) -> nx.Graph:
    k = mean_degree(n)
    if connectivity == "random":
        return nx.gnm_random_graph(n, n * k // 2, seed=seed)
    if connectivity == "small_world":
        return nx.watts_strogatz_graph(n, k, WS_REWIRE_P, seed=seed)
    if connectivity == "scale_free":
        return nx.barabasi_albert_graph(n, k // 2, seed=seed)
    if connectivity == "modular_hub":
        return modular_hub_graph(n, n * k // 2, np.random.default_rng(seed))
    raise ValueError(f"unknown connectivity {connectivity!r}")


def population_mask(connectivity: str, n: int, seed: int) -> torch.Tensor:
    return torch.tensor(nx.to_numpy_array(population_graph(connectivity, n, seed), nodelist=range(n)) > 0,
                        dtype=torch.float32)


def modular_mask(connectivity: str, sizes: list[int], seed: int) -> torch.Tensor:
    rng = np.random.default_rng(seed)
    n = sum(sizes)
    starts = np.cumsum([0] + sizes[:-1]).tolist()
    mask = torch.zeros(n, n)
    for m, (s, size) in enumerate(zip(starts, sizes)):
        mask[s:s + size, s:s + size] = population_mask(connectivity, size, seed + m + 1)
    for m in range(len(sizes) - 1):
        a, b = slice(starts[m], starts[m] + sizes[m]), slice(starts[m + 1], starts[m + 1] + sizes[m + 1])
        mask[b, a] = torch.from_numpy(rng.random((sizes[m + 1], sizes[m])) < INTER_MODULE_DENSITY).float()
        mask[a, b] = torch.from_numpy(rng.random((sizes[m], sizes[m + 1])) < INTER_MODULE_DENSITY).float()
    return mask
