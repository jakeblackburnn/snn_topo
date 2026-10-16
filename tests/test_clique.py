import numpy as np

from snntopo import clique

N = 50
SAMPLES = 15000  # 100 trials x 150 bins, the probe's size


def random_band(n_draws=20):
    rng = np.random.default_rng(0)
    return np.array([clique.integrated(clique.betti_curves(clique.random_matrix(N, rng))) for _ in range(n_draws)])


def place_cells(rng):
    """Neurons with von Mises tuning on a circle, driven by a random-walk angle: correlations
    fall with the distance between preferred angles, Giusti's geometric case."""
    preferred = rng.uniform(0, 2 * np.pi, N)
    angle = np.cumsum(rng.normal(0, 0.1, SAMPLES))
    rate = 0.2 * np.exp(2 * (np.cos(angle[None] - preferred[:, None]) - 1))
    return (rng.random((N, SAMPLES)) < rate).astype(float)


def test_order_distance_is_edge_density():
    c = np.array([[1, 0.9, 0.1], [0.9, 1, 0.5], [0.1, 0.5, 1]])
    d = clique.order_distance(c)
    assert np.allclose(d, [[0, 1 / 3, 1], [1 / 3, 0, 2 / 3], [1, 2 / 3, 0]])


def test_monotone_transform_does_not_change_curves():
    c = clique.random_matrix(20, np.random.default_rng(1))
    assert np.array_equal(clique.betti_curves(c), clique.betti_curves(np.tanh(3 * c)))


def test_independent_neurons_look_random_and_place_cells_do_not():
    band = random_band()
    rng = np.random.default_rng(2)
    noise = clique.integrated(clique.betti_curves(clique.correlations((rng.random((N, SAMPLES)) < 0.05).astype(float))))
    geometric = clique.integrated(clique.betti_curves(clique.correlations(place_cells(rng))))
    lo, hi = band.min(0), band.max(0)
    mean, sd = band.mean(0), band.std(0)
    assert np.all(np.abs(noise - mean) < 4 * sd), (noise, mean, sd)
    assert np.all(geometric < lo), (geometric, lo)
    assert np.all(geometric < 0.5 * mean), (geometric, mean)


def test_shared_drive_is_removed_by_population_regression():
    """Independent neurons plus a common gain: the raw ordering is rank-one-like (curves
    collapse below random); regressing out the population signal restores a random order."""
    band = random_band()
    rng = np.random.default_rng(3)
    gain = rng.uniform(0.2, 1.0, N)
    drive = np.repeat(rng.random(SAMPLES // 50), 50)
    x = (rng.random((N, SAMPLES)) < 0.02 + 0.3 * gain[:, None] * drive).astype(float)
    raw = clique.integrated(clique.betti_curves(clique.correlations(x)))
    residual = clique.integrated(clique.betti_curves(clique.correlations(x, remove_population=True)))
    assert np.all(raw < band.min(0)), (raw, band.min(0))
    assert np.all(np.abs(residual - band.mean(0)) < 4 * band.std(0)), (residual, band.mean(0))


def test_trial_demeaning_removes_slow_modes_and_keeps_geometry():
    """Three shared modes that change only between 150-bin trials push the curves below
    random; demeaning each trial restores random. Place cells stay far below it."""
    band = random_band()
    rng = np.random.default_rng(4)
    bounds = np.arange(0, SAMPLES + 1, 150)
    gain = rng.uniform(0.2, 1.0, (N, 3))
    drive = np.repeat(rng.random((3, SAMPLES // 150)), 150, axis=1)
    x = (rng.random((N, SAMPLES)) < 0.02 + 0.3 * gain @ drive).astype(float)
    raw = clique.integrated(clique.betti_curves(clique.correlations(x)))
    demeaned = clique.integrated(clique.betti_curves(clique.correlations(clique.demean_trials(x, bounds))))
    geometric = clique.integrated(clique.betti_curves(clique.correlations(clique.demean_trials(place_cells(rng), bounds))))
    assert np.all(raw < band.min(0)), (raw, band.min(0))
    assert np.all(np.abs(demeaned - band.mean(0)) < 4 * band.std(0)), (demeaned, band.mean(0))
    assert np.all(geometric < 0.5 * band.mean(0)), (geometric, band.mean(0))
