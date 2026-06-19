import numpy as np
import pytest

from owa_adaptive.adaptive import AdaptiveOWA, effective_orness, iowa
from owa_adaptive.owa import owa


def test_effective_orness_no_stress_equals_base():
    assert effective_orness(0.7, 0.0, lam=0.85, alpha_floor=0.12) == pytest.approx(0.7)


def test_effective_orness_decreasing_in_stress():
    a0 = effective_orness(0.7, 0.0)
    a1 = effective_orness(0.7, 0.5)
    a2 = effective_orness(0.7, 1.0)
    assert a0 > a1 > a2
    assert a2 >= 0.12 - 1e-9  # respeta el piso


def test_effective_orness_vectorized():
    s = np.array([0.0, 0.5, 1.0])
    out = effective_orness(0.8, s)
    assert out.shape == (3,)
    assert out[0] > out[1] > out[2]


def test_iowa_equals_owa_when_inducing_is_value():
    a = [2.0, 9.0, 4.0, 1.0]
    w = [0.4, 0.3, 0.2, 0.1]
    assert iowa(a, a, w) == pytest.approx(owa(a, w))


def test_iowa_orders_by_inducing():
    a = [10.0, 20.0, 30.0]
    u = [3.0, 1.0, 2.0]   # mayor inductora -> primer peso
    w = [1.0, 0.0, 0.0]
    assert iowa(a, u, w) == pytest.approx(10.0)  # a con mayor u


def test_adaptive_owa_run_weights_normalized():
    ad = AdaptiveOWA(base_orness=0.7, n_criteria=5)
    res = ad.run([0.0, 0.3, 0.9])
    assert res.weights.shape == (3, 5)
    assert np.allclose(res.weights.sum(axis=1), 1.0)
    assert res.effective_orness[0] >= res.effective_orness[-1]
