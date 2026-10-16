"""Clique topology of neuron-to-neuron correlations (Giusti, Pastalkova, Curto & Itskov 2015).

Neurons are the vertices. Edges enter in order of decreasing correlation, so the filtration
parameter is edge density: the fraction of neuron pairs already joined. Only the ranks of
the correlations matter, which makes the Betti curves blind to any monotone change of the
correlations, firing rate and noise scale included. A random symmetric matrix gives a Betti
curve that depends only on the number of neurons; correlations that come from distances in
a low-dimensional space give curves well below it. That gap is the measure.
"""
import numpy as np

MAX_DENSITY = 0.5  # Giusti stop at about half the edges; past that the random curves are dominated by high cliques
DENSITY = np.linspace(0.0, MAX_DENSITY, 101)


def correlations(x: np.ndarray, remove_population: bool = False) -> np.ndarray:
    """x: (neurons, samples) activity. Pearson correlation matrix. remove_population first
    regresses every neuron on the probe's mean z-scored activity: a shared up/down signal
    (arousal, drift, a common drive) gives a rank-one ordering whose Betti curves sit below
    random for a reason that has nothing to do with geometry."""
    x = np.asarray(x, dtype=np.float64)
    z = (x - x.mean(1, keepdims=True)) / x.std(1, keepdims=True)
    if remove_population:
        pop = z.mean(0)
        pop = pop - pop.mean()
        z = z - np.outer(z @ pop / (pop @ pop), pop)
    return np.corrcoef(z)


def demean_trials(x: np.ndarray, bounds: np.ndarray) -> np.ndarray:
    """x: (neurons, samples) of concatenated trials, bounds: trial edges in samples. Each
    neuron's mean is subtracted within every trial, so co-fluctuations between trials (drift,
    arousal, anything slower than a trial) no longer count; within-trial structure stays.
    Unlike projecting out principal components, which imposes its own order on the residual
    correlations and lifts even place cells far above random (tested 2026-10-16), this leaves
    independent neurons at random and geometric ones well below."""
    x = np.array(x, dtype=np.float64)
    for a, b in zip(bounds[:-1], bounds[1:]):
        x[:, a:b] -= x[:, a:b].mean(1, keepdims=True)
    return x


def order_distance(c: np.ndarray) -> np.ndarray:
    """Off-diagonal entries replaced by the edge density at which that edge enters (highest
    correlation first); ties broken by position, deterministically."""
    n = len(c)
    i, j = np.triu_indices(n, 1)
    order = np.argsort(-c[i, j], kind="stable")
    density = np.empty(len(order))
    density[order] = np.arange(1, len(order) + 1) / len(order)
    d = np.zeros((n, n))
    d[i, j] = d[j, i] = density
    return d


def betti_curves(c: np.ndarray, maxdim: int = 2) -> np.ndarray:
    """-> (maxdim, len(DENSITY)): Betti 1..maxdim of the order complex at each edge density."""
    import ripser
    dgms = ripser.ripser(order_distance(c), distance_matrix=True, maxdim=maxdim, thresh=MAX_DENSITY)["dgms"]
    curves = np.zeros((maxdim, len(DENSITY)))
    for dim in range(1, maxdim + 1):
        births, deaths = dgms[dim][:, 0], dgms[dim][:, 1]
        curves[dim - 1] = ((births[:, None] <= DENSITY) & (DENSITY < deaths[:, None])).sum(0)
    return curves


def integrated(curves: np.ndarray) -> np.ndarray:
    """Area under each Betti curve over DENSITY."""
    return np.trapezoid(curves, DENSITY, axis=-1)


def random_matrix(n: int, rng: np.random.Generator) -> np.ndarray:
    """A symmetric matrix with i.i.d. off-diagonal entries: a uniformly random edge order."""
    a = rng.standard_normal((n, n))
    c = (a + a.T) / 2
    np.fill_diagonal(c, 1.0)
    return c
