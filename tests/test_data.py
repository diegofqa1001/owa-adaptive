import numpy as np

from owa_adaptive.data import generate_market


def test_reproducible_same_seed():
    m1 = generate_market(n_assets=12, n_days=300, seed=123)
    m2 = generate_market(n_assets=12, n_days=300, seed=123)
    assert np.allclose(m1.prices.to_numpy(), m2.prices.to_numpy())
    assert np.allclose(m1.vix.to_numpy(), m2.vix.to_numpy())


def test_different_seed_differs():
    m1 = generate_market(n_assets=12, n_days=300, seed=1)
    m2 = generate_market(n_assets=12, n_days=300, seed=2)
    assert not np.allclose(m1.prices.to_numpy(), m2.prices.to_numpy())


def test_shapes_and_positivity():
    m = generate_market(n_assets=20, n_days=500, seed=7)
    assert m.prices.shape == (500, 20)
    assert m.returns.shape == (500, 20)
    assert m.vix.shape == (500,)
    assert m.epu.shape == (500,)
    assert m.fundamentals.shape == (20, 3)
    assert (m.prices.to_numpy() > 0).all()
    assert (m.vix.to_numpy() >= 9.0).all()


def test_regime_labels_present():
    m = generate_market(n_assets=10, n_days=400, seed=3)
    assert set(np.unique(m.regime)).issubset({0, 1, 2})
