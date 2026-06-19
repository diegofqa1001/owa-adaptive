import numpy as np
import pytest

from owa_adaptive.data import generate_market
from owa_adaptive.recommender import Recommender


@pytest.fixture(scope="module")
def market():
    return generate_market(n_assets=15, n_days=400, seed=42)


def test_portfolio_weights_sum_to_one(market):
    rec = Recommender(market, top_n=8)
    out = rec.recommend_latest("Navigator")
    assert out.portfolio.sum() == pytest.approx(1.0, abs=1e-9)
    assert (out.portfolio >= 0).all()
    assert (out.portfolio > 0).sum() <= 8


def test_scores_cover_all_assets(market):
    rec = Recommender(market, top_n=8)
    out = rec.recommend_latest("Guardian")
    assert len(out.scores) == market.n_assets


def test_adaptive_reduces_effective_orness(market):
    rec = Recommender(market, adaptive=True)
    out = rec.recommend_latest("Visionary")
    assert out.effective_orness <= out.base_orness + 1e-9


def test_static_keeps_base_orness(market):
    rec = Recommender(market, adaptive=False)
    out = rec.recommend_latest("Strategist")
    assert out.effective_orness == pytest.approx(out.base_orness)


def test_top_helper(market):
    rec = Recommender(market, top_n=10)
    out = rec.recommend_latest("Balancer")
    assert len(out.top(5)) == 5
