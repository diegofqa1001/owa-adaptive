import numpy as np
import pytest

from owa_adaptive.backtest import Backtester, compare_adaptive_static
from owa_adaptive.data import generate_market


@pytest.fixture(scope="module")
def market():
    return generate_market(n_assets=15, n_days=500, seed=11)


def test_backtest_metrics_present(market):
    bt = Backtester(market, top_n=8)
    res = bt.run("Navigator")
    for key in ["total_return", "ann_return", "ann_vol", "sharpe",
                "max_drawdown", "rmse_vol", "mean_orness_eff"]:
        assert key in res.metrics
    assert len(res.equity) > 0
    assert res.metrics["ann_vol"] > 0
    assert np.isfinite(res.metrics["rmse_vol"])


def test_max_drawdown_non_positive(market):
    bt = Backtester(market, top_n=8)
    res = bt.run("Guardian")
    assert res.metrics["max_drawdown"] <= 0.0


def test_compare_adaptive_static(market):
    comp = compare_adaptive_static(market, "Navigator", top_n=8)
    assert set(comp.keys()) == {"adaptive", "static"}
    assert comp["adaptive"].profile == "Navigator"
    # El estático mantiene el orness base del perfil (Navigator = 0.562).
    assert comp["static"].metrics["mean_orness_eff"] == pytest.approx(0.562, abs=1e-3)
    # El adaptativo nunca sube el orness por encima del estático.
    assert comp["adaptive"].metrics["mean_orness_eff"] <= \
        comp["static"].metrics["mean_orness_eff"] + 1e-9


def test_run_all_profiles(market):
    bt = Backtester(market, top_n=8)
    results = bt.run_all()
    assert len(results) == 8
