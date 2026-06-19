import numpy as np
import pytest

from owa_adaptive.spectral import (
    criterion_correlation,
    inversion_index,
    spectral_correction,
)


def _correlated_scores(seed=0, n=200):
    rng = np.random.default_rng(seed)
    z = rng.normal(size=n)
    # Tres criterios fuertemente correlacionados + dos independientes.
    c1 = z + 0.1 * rng.normal(size=n)
    c2 = z + 0.1 * rng.normal(size=n)
    c3 = z + 0.1 * rng.normal(size=n)
    c4 = rng.normal(size=n)
    c5 = rng.normal(size=n)
    return np.column_stack([c1, c2, c3, c4, c5])


def test_correction_decorrelates():
    X = _correlated_scores()
    corr_before = criterion_correlation(X)
    Xc = spectral_correction(X)
    corr_after = criterion_correlation(Xc)
    off_before = np.abs(corr_before - np.eye(5)).max()
    off_after = np.abs(corr_after - np.eye(5)).max()
    assert off_before > 0.8       # había fuerte correlación
    assert off_after < 1e-6       # ZCA en-muestra deja covarianza identidad


def test_correction_preserves_shape():
    X = _correlated_scores()
    assert spectral_correction(X).shape == X.shape


def test_correction_sign_alignment():
    # Cada criterio corregido mantiene correlación positiva con el original.
    X = _correlated_scores()
    Xc = spectral_correction(X)
    for j in range(X.shape[1]):
        assert np.corrcoef(Xc[:, j], X[:, j])[0, 1] > 0


def test_inversion_index_monotone():
    assert inversion_index([0.1, 0.2, 0.3, 0.4], [1.0, 2.0, 3.0, 4.0]) == pytest.approx(1.0)
    assert inversion_index([0.1, 0.2, 0.3, 0.4], [4.0, 3.0, 2.0, 1.0]) == pytest.approx(-1.0)


def test_single_criterion_returns_zscore():
    X = np.array([[1.0], [2.0], [3.0]])
    Xc = spectral_correction(X)
    assert Xc.mean() == pytest.approx(0.0, abs=1e-9)
