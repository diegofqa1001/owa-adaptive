import numpy as np
import pytest

from owa_adaptive.profiles import (
    ALPHA_MAX,
    ALPHA_MIN,
    DIMENSIONS,
    PROFILE_NAMES,
    all_profiles,
    get_profile,
    kendall_w,
    orness_from_dimensions,
)


def test_eight_profiles():
    profs = all_profiles()
    assert len(profs) == 8
    assert [p.name for p in profs] == PROFILE_NAMES


def test_orness_increasing_and_endpoints():
    orn = [p.target_orness for p in all_profiles()]
    assert orn == sorted(orn)
    assert orn[0] == pytest.approx(ALPHA_MIN, abs=1e-3)
    assert orn[-1] == pytest.approx(ALPHA_MAX, abs=1e-3)


def test_bridge_reconstructs_target():
    # El puente conductual reproduce el orness objetivo (calibración del modelo).
    for p in all_profiles():
        assert p.orness_bridge == pytest.approx(p.target_orness, abs=3e-3)


def test_bridge_monotone_in_risk_tolerance():
    base = {k: 4.0 for k in DIMENSIONS}
    low = dict(base, tolerancia_riesgo=1.0)
    high = dict(base, tolerancia_riesgo=7.0)
    assert orness_from_dimensions(high) > orness_from_dimensions(low)


def test_profile_weights_shape_and_orness():
    from owa_adaptive.owa import orness
    p = get_profile("Navigator")
    w = p.weights(5)
    assert len(w) == 5
    assert orness(w) == pytest.approx(p.target_orness, abs=1e-3)


def test_kendall_w_perfect_agreement():
    # Tres jueces con el mismo orden -> W = 1.
    ratings = [[1, 2, 3, 4], [1, 2, 3, 4], [1, 2, 3, 4]]
    assert kendall_w(ratings) == pytest.approx(1.0)


def test_kendall_w_in_unit_interval():
    rng = np.random.default_rng(0)
    ratings = rng.integers(1, 8, size=(5, 6))
    w = kendall_w(ratings)
    assert 0.0 <= w <= 1.0


def test_get_profile_by_index_and_name():
    assert get_profile(0).name == "Guardian"
    assert get_profile("visionary").name == "Visionary"
    with pytest.raises(KeyError):
        get_profile("NoExiste")
