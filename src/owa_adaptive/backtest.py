"""Backtesting de ventana rodante y métricas de validación (OE4).

Construye carteras en cada fecha de rebalanceo con el :class:`Recommender`, las
mantiene hasta el siguiente rebalanceo y acumula retornos. Reporta métricas
estándar (retorno, volatilidad, Sharpe, máximo drawdown) y el **RMSE** entre la
volatilidad ex-ante (predicha desde la covarianza móvil) y la realizada, como
medida de calibración del riesgo.

Incluye utilidades para (i) comparar adaptativo vs estático y (ii) evidenciar la
corrección de la inversión multicriterio del Artículo 3.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import DEFAULT_ALPHA_FLOOR, DEFAULT_LAMBDA, DEFAULT_TOP_N, TRADING_DAYS
from .profiles import Profile, all_profiles, get_profile
from .recommender import Recommender
from .spectral import InversionReport, inversion_index

__all__ = [
    "BacktestResult",
    "Backtester",
    "compare_adaptive_static",
    "inversion_analysis",
]


# --- Métricas -----------------------------------------------------------------
def max_drawdown(equity: pd.Series) -> float:
    """Máximo drawdown (valor negativo o cero) de una curva de capital."""
    roll_max = equity.cummax()
    dd = equity / roll_max - 1.0
    return float(dd.min())


def annualized_return(returns: pd.Series) -> float:
    n = len(returns)
    if n == 0:
        return 0.0
    total = float((1.0 + returns).prod())
    if total <= 0:
        return -1.0
    return total ** (TRADING_DAYS / n) - 1.0


def annualized_vol(returns: pd.Series) -> float:
    return float(returns.std(ddof=0) * np.sqrt(TRADING_DAYS))


def sharpe_ratio(returns: pd.Series, rf: float = 0.0) -> float:
    vol = annualized_vol(returns)
    if vol < 1e-12:
        return 0.0
    return (annualized_return(returns) - rf) / vol


@dataclass
class BacktestResult:
    """Resultado de un backtest para un perfil."""
    profile: str
    returns: pd.Series
    equity: pd.Series
    effective_orness: pd.Series
    metrics: Dict[str, float] = field(default_factory=dict)

    @property
    def realized_risk(self) -> float:
        return self.metrics.get("ann_vol", float("nan"))


class Backtester:
    """Motor de backtesting de ventana rodante."""

    def __init__(self, market, top_n: int = DEFAULT_TOP_N, lookback: int = 126,
                rebalance: int = 21, adaptive: bool = True, spectral: bool = True,
                lam: float = DEFAULT_LAMBDA, alpha_floor: float = DEFAULT_ALPHA_FLOOR,
                start: Optional[int] = None):
        self.market = market
        self.rebalance = int(rebalance)
        self.lookback = int(lookback)
        self.rec = Recommender(market, top_n=top_n, lookback=lookback,
                            adaptive=adaptive, spectral=spectral,
                            lam=lam, alpha_floor=alpha_floor)
        self.start = int(start) if start is not None else int(lookback)

    def run(self, profile) -> BacktestResult:
        prof: Profile = profile if isinstance(profile, Profile) else get_profile(profile)
        n = self.market.n_days
        tickers = self.market.tickers
        R = self.market.returns

        ret_dates: List = []
        ret_vals: List[float] = []
        eff_dates: List = []
        eff_vals: List[float] = []
        ex_ante: List[float] = []
        realized: List[float] = []

        rebal_days = list(range(self.start, n - 1, self.rebalance))
        for k, t0 in enumerate(rebal_days):
            t1 = rebal_days[k + 1] if k + 1 < len(rebal_days) else n - 1
            rec = self.rec.recommend(prof, t0)
            w = rec.portfolio.reindex(tickers).fillna(0.0).to_numpy()
            eff_dates.append(self.market.dates[t0])
            eff_vals.append(rec.effective_orness)

            # Volatilidad ex-ante desde covarianza móvil.
            lo = max(0, t0 - self.lookback + 1)
            cov = R.iloc[lo:t0 + 1].cov().reindex(index=tickers, columns=tickers).to_numpy()
            var = float(w @ cov @ w)
            ex_ante.append(np.sqrt(max(var, 0.0)) * np.sqrt(TRADING_DAYS))

            # Retornos del periodo de tenencia (t0+1 .. t1).
            block = R.iloc[t0 + 1:t1 + 1]
            if block.shape[0] == 0:
                continue
            block_vals = block.reindex(columns=tickers).to_numpy()
            r_block = block_vals @ w
            ret_dates.extend(list(block.index))
            ret_vals.extend(list(r_block))
            realized.append(float(np.std(r_block, ddof=0) * np.sqrt(TRADING_DAYS)))

        returns = pd.Series(ret_vals, index=pd.Index(ret_dates), name=prof.name)
        equity = (1.0 + returns).cumprod()
        eff_series = pd.Series(eff_vals, index=pd.Index(eff_dates), name="orness_eff")

        ex_ante_arr = np.asarray(ex_ante)
        realized_arr = np.asarray(realized[:len(ex_ante)])
        m = min(len(ex_ante_arr), len(realized_arr))
        rmse_vol = (float(np.sqrt(np.mean((ex_ante_arr[:m] - realized_arr[:m]) ** 2)))
                    if m > 0 else float("nan"))

        metrics = {
            "total_return": float((1.0 + returns).prod() - 1.0) if len(returns) else 0.0,
            "ann_return": annualized_return(returns),
            "ann_vol": annualized_vol(returns),
            "sharpe": sharpe_ratio(returns),
            "max_drawdown": max_drawdown(equity) if len(equity) else 0.0,
            "rmse_vol": rmse_vol,
            "mean_orness_eff": float(eff_series.mean()) if len(eff_series) else float("nan"),
        }
        return BacktestResult(profile=prof.name, returns=returns, equity=equity,
                            effective_orness=eff_series, metrics=metrics)

    def run_all(self) -> Dict[str, BacktestResult]:
        return {p.name: self.run(p) for p in all_profiles()}


def compare_adaptive_static(market, profile, **kw):
    """Backtest del mismo perfil con y sin componente adaptativo."""
    kw_static = dict(kw)
    kw_static["adaptive"] = False
    kw_adapt = dict(kw)
    kw_adapt["adaptive"] = True
    adaptive = Backtester(market, **kw_adapt).run(profile)
    static = Backtester(market, **kw_static).run(profile)
    return {"adaptive": adaptive, "static": static}


def inversion_analysis(market, spectral_kw: Optional[dict] = None,
                       **kw) -> InversionReport:
    """Evidencia la corrección de la inversión multicriterio (A3).

    Corre todos los perfiles con y sin corrección espectral y compara el índice
    de inversión (Spearman entre orness del perfil y volatilidad realizada).
    """
    base_kw = dict(kw)
    base_kw.pop("spectral", None)

    profiles = all_profiles()
    orness_vals = [p.target_orness for p in profiles]

    bt_naive = Backtester(market, spectral=False, **base_kw)
    bt_corr = Backtester(market, spectral=True, **base_kw)

    risk_naive = [bt_naive.run(p).realized_risk for p in profiles]
    risk_corr = [bt_corr.run(p).realized_risk for p in profiles]

    return InversionReport(
        index_naive=inversion_index(orness_vals, risk_naive),
        index_corrected=inversion_index(orness_vals, risk_corr),
    )
