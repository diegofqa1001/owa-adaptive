import numpy as np
import pytest

from owa_adaptive.owa import andness, dispersion, orness, owa, owa_matrix, validate_weights


def test_uniform_weights_equal_mean():
    a = [3.0, 1.0, 5.0, 2.0]
    w = [0.25] * 4
    assert owa(a, w) == pytest.approx(np.mean(a))


def test_orness_extremes():
    assert orness([1, 0, 0, 0]) == pytest.approx(1.0)   # max
    assert orness([0, 0, 0, 1]) == pytest.approx(0.0)   # min
    assert orness([0.25] * 4) == pytest.approx(0.5)     # media
    assert andness([1, 0, 0, 0]) == pytest.approx(0.0)


def test_owa_between_min_and_max():
    a = np.array([2.0, 9.0, 4.0, 1.0])
    w = [0.4, 0.3, 0.2, 0.1]
    val = owa(a, w)
    assert a.min() <= val <= a.max()


def test_owa_optimistic_ge_pessimistic():
    a = [1.0, 2.0, 3.0, 4.0]
    optimistic = owa(a, [0.7, 0.2, 0.1, 0.0])
    pessimistic = owa(a, [0.0, 0.1, 0.2, 0.7])
    assert optimistic > pessimistic


def test_owa_matrix_matches_rowwise():
    M = np.array([[1.0, 4.0, 2.0], [5.0, 0.0, 3.0]])
    w = [0.5, 0.3, 0.2]
    out = owa_matrix(M, w, axis=1)
    assert out[0] == pytest.approx(owa(M[0], w))
    assert out[1] == pytest.approx(owa(M[1], w))


def test_validate_weights_normalizes():
    w = validate_weights([2.0, 2.0])
    assert w.sum() == pytest.approx(1.0)


def test_validate_weights_rejects_negative():
    with pytest.raises(ValueError):
        validate_weights([-0.1, 1.1])


def test_dispersion_max_at_uniform():
    n = 5
    uni = dispersion([1.0 / n] * n)
    concentrated = dispersion([1.0, 0, 0, 0, 0])
    assert uni == pytest.approx(np.log(n))
    assert concentrated == pytest.approx(0.0)
