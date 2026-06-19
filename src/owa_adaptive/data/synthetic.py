"""Panel de mercado sintético reproducible con regímenes y señales VIX/EPU.

Sustrato de validación por defecto: 100% offline, semilla fija, auditable. Es
coherente con el "panel sintético de simulación" usado en el Artículo 2. El
proceso generador es transparente:

- Cadena de Markov de 3 regímenes (calma, estrés, crisis) con persistencia.
- Factor de mercado por régimen (deriva y volatilidad); en crisis sube la
  volatilidad y la correlación entre activos (menor componente idiosincrático).
- Activos con beta, y primas latentes de calidad/valor que **predicen** el
  retorno → los criterios multicriterio tienen señal real.
- VIX ligado a la volatilidad anualizada del régimen; EPU persistente y elevado
  en estrés/crisis.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..config import SEED, TRADING_DAYS

__all__ = ["MarketData", "generate_market"]


@dataclass
class MarketData:
    """Contenedor de datos de mercado (sintéticos o reales)."""
    dates: pd.DatetimeIndex
    prices: pd.DataFrame      # [días × activos]
    returns: pd.DataFrame     # [días × activos]
    vix: pd.Series            # [días]
    epu: pd.Series            # [días]
    fundamentals: pd.DataFrame  # [activos × {value, quality, liquidity}]
    regime: np.ndarray        # [días] etiqueta entera 0/1/2 (verdad latente)

    @property
    def tickers(self):
        return list(self.prices.columns)

    @property
    def n_assets(self) -> int:
        return self.prices.shape[1]

    @property
    def n_days(self) -> int:
        return self.prices.shape[0]


def generate_market(n_assets: int = 30,
                    n_days: int = 1500,
                    seed: int = SEED,
                    start: str = "2018-01-02") -> MarketData:
    """Genera un :class:`MarketData` sintético reproducible.

    Parameters
    ----------
    n_assets : número de activos.
    n_days   : número de días de negociación.
    seed     : semilla (por defecto la global del proyecto).
    start    : fecha inicial (días hábiles).
    """
    rng = np.random.default_rng(seed)

    # --- Cadena de Markov de regímenes (0 calma, 1 estrés, 2 crisis) ---------
    P = np.array([
        [0.970, 0.025, 0.005],
        [0.100, 0.860, 0.040],
        [0.060, 0.140, 0.800],
    ])
    regimes = np.zeros(n_days, dtype=int)
    for t in range(1, n_days):
        regimes[t] = rng.choice(3, p=P[regimes[t - 1]])

    # --- Factor de mercado por régimen (diario) ------------------------------
    mu_m = np.array([0.0006, -0.0002, -0.0015])
    vol_m = np.array([0.007, 0.014, 0.028])
    rm = rng.normal(mu_m[regimes], vol_m[regimes])

    # --- Parámetros de activos ----------------------------------------------
    beta = rng.uniform(0.4, 1.6, n_assets)
    quality = rng.normal(0.0, 1.0, n_assets)   # latente, predice retorno
    value = rng.normal(0.0, 1.0, n_assets)     # latente, predice retorno
    liquidity = rng.normal(0.0, 1.0, n_assets)
    idio_vol = rng.uniform(0.008, 0.020, n_assets)
    alpha_i = 0.00045 * quality + 0.00030 * value  # prima de deriva latente

    # En crisis baja el componente idiosincrático (sube la correlación).
    idio_scale = np.array([1.0, 0.85, 0.60])[regimes]  # [n_days]

    R = np.zeros((n_days, n_assets))
    for i in range(n_assets):
        idio = rng.normal(0.0, idio_vol[i], n_days) * idio_scale
        R[:, i] = alpha_i[i] + beta[i] * rm + idio

    prices = 100.0 * np.cumprod(1.0 + R, axis=0)

    # --- Señales de incertidumbre -------------------------------------------
    ann_vol_pts = vol_m[regimes] * np.sqrt(TRADING_DAYS) * 100.0
    vix = ann_vol_pts + rng.normal(0.0, 1.5, n_days)
    vix = np.clip(vix, 9.0, None)

    epu_base = np.array([80.0, 130.0, 200.0])[regimes]
    e = np.zeros(n_days)
    for t in range(1, n_days):
        e[t] = 0.90 * e[t - 1] + rng.normal(0.0, 15.0)
    epu = np.clip(epu_base + e, 30.0, None)

    # --- Ensamblado en estructuras pandas -----------------------------------
    dates = pd.bdate_range(start=start, periods=n_days)
    tickers = [f"A{i:02d}" for i in range(n_assets)]

    prices_df = pd.DataFrame(prices, index=dates, columns=tickers)
    returns_df = pd.DataFrame(R, index=dates, columns=tickers)
    vix_s = pd.Series(vix, index=dates, name="VIX")
    epu_s = pd.Series(epu, index=dates, name="EPU")

    fundamentals = pd.DataFrame(
        {
            "value": value + rng.normal(0.0, 0.30, n_assets),
            "quality": quality + rng.normal(0.0, 0.30, n_assets),
            "liquidity": liquidity + rng.normal(0.0, 0.30, n_assets),
        },
        index=tickers,
    )

    return MarketData(
        dates=dates, prices=prices_df, returns=returns_df,
        vix=vix_s, epu=epu_s, fundamentals=fundamentals, regime=regimes,
    )
