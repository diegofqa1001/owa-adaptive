import numpy as np
import pytest

from owa_adaptive.owa import orness
from owa_adaptive.quantifiers import (
    max_entropy_weights,
    rim_weights,
    weights_for_orness,
)


@pytest.mark.parametrize("n", [3, 5, 8])
@pytest.mark.parametrize("target", [0.158, 0.3, 0.5, 0.7, 0.865])
def test_weights_for_orness_hits_target(n, target):
    w = weights_for_orness(n, target)
    assert w.sum() == pytest.approx(1.0)
    assert orness(w) == pytest.approx(target, abs=1e-3)


@pytest.mark.parametrize("n", [3, 5, 8])
@pytest.mark.parametrize("target", [0.2, 0.5, 0.8])
def test_max_entropy_hits_target(n, target):
    w = max_entropy_weights(n, target)
    assert w.sum() == pytest.approx(1.0)
    assert orness(w) == pytest.approx(target, abs=1e-3)


def test_rim_weights_uniform_at_p1():
    w = rim_weights(5, 1.0)
    assert np.allclose(w, 0.2)


def test_rim_monotone_attitude():
    # p<1 optimista (orness>0.5); p>1 pesimista (orness<0.5)
    assert orness(rim_weights(6, 0.5)) > 0.5
    assert orness(rim_weights(6, 2.0)) < 0.5


def test_max_entropy_uniform_at_half():
    w = max_entropy_weights(7, 0.5)
    assert np.allclose(w, 1.0 / 7)
