import numpy as np
import pytest

from owa_adaptive.data import generate_market
from owa_adaptive.investor import (
    InvestorState,
    behavioral_update,
    classify_investor,
    invest_and_hold,
    nearest_profile,
    portfolio_tilts,
    update_orness,
)
from owa_adaptive.profiles import DIMENSIONS
from owa_adaptive.scoring import CRITERIA, compute_criteria


CONSERVATIVE = {
    "aversion_perdida": 7, "tolerancia_riesgo": 1, "horizonte_temporal": 1,
    "exceso_confianza": 1, "comportamiento_gregario": 7,
    "preferencia_liquidez": 7, "aversion_ambiguedad": 7,
}
AGGRESSIVE = {
    "aversion_perdida": 1, "tolerancia_riesgo": 7, "horizonte_temporal": 7,
    "exceso_confianza": 7, "comportamiento_gregario": 1,
    "preferencia_liquidez": 1, "aversion_ambiguedad": 1,
}


def test_classify_extremes():
    orn_c, prof_c = classify_investor(CONSERVATIVE)
    orn_a, prof_a = classify_investor(AGGRESSIVE)
    assert orn_c < orn_a
    assert prof_c.index <= 1            # Guardian / Sentinel
    assert prof_a.index >= 6            # Pioneer / Visionary


def test_classify_requires_all_dimensions():
    with pytest.raises(ValueError):
        classify_investor({"aversion_perdida": 4})


def test_nearest_profile_monotone():
    assert nearest_profile(0.16).index < nearest_profile(0.86).index


def test_update_orness_direction_and_bounds():
    assert update_orness(0.5, 0.10) > 0.5     # buena cosecha -> más agresivo
    assert update_orness(0.5, -0.10) < 0.5    # pérdida -> más defensivo
    assert update_orness(0.88, 5.0) <= 0.90   # tope
    assert update_orness(0.13, -5.0) >= 0.12  # piso


def test_behavioral_update_advances_state():
    s0 = InvestorState(orness=0.5, profile_name="Navigator", t=300, round=0, history=[])
    s1 = behavioral_update(s0, realized_return=0.15, new_t=420)
    assert s1.round == 1
    assert s1.t == 420
    assert len(s1.history) == 1
    assert s1.orness > s0.orness
    assert s1.profile_name == nearest_profile(s1.orness).name


def test_invest_and_hold_keys():
    market = generate_market(n_assets=15, n_days=600, seed=5)
    res = invest_and_hold(market, base_orness=0.56, t0=252, horizon=126, top_n=8)
    for key in ["recommendation", "equity", "realized_return", "end_t", "tilts"]:
        assert key in res
    assert np.isfinite(res["realized_return"])
    assert len(res["equity"]) > 0
    assert res["end_t"] == 252 + 126


def test_portfolio_tilts_covers_criteria():
    market = generate_market(n_assets=15, n_days=400, seed=9)
    crit = compute_criteria(market, 300, lookback=126)
    res = invest_and_hold(market, 0.6, 252, 100, top_n=8)
    tilts = portfolio_tilts(crit, res["recommendation"].portfolio)
    assert list(tilts.index) == CRITERIA
