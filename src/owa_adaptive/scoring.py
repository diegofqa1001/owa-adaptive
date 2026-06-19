"""Scoring multicriterio de activos y agregación OWA.

Cinco criterios estandarizados de forma transversal (z-score entre activos), de
modo que "mayor = más atractivo" y la agregación OWA entre criterios es
comparable. Los criterios mezclan información de precios (momentum, baja
volatilidad) y fundamentales (valor, calidad, liquidez).
"""
from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from .owa import owa_matrix
from .spectral import spectral_correction

__all__ = ["CRITERIA", "compute_criteria", "aggregate_scores"]

CRITERIA: List[str] = ["momentum", "low_vol", "value", "quality", "liquidity"]


def _zscore_cross_section(df: pd.DataFrame) -> pd.DataFrame:
    mu = df.mean()
    sd = df.std(ddof=0).replace(0.0, 1.0)
    return (df - mu) / sd


def compute_criteria(market, t: int, lookback: int = 126) -> pd.DataFrame:
    """Matriz de criterios [activos × criterios] usando datos hasta el día ``t``.

    Solo mira el pasado (``... t`` inclusive), evitando look-ahead. Devuelve los
    criterios estandarizados transversalmente, en el orden de :data:`CRITERIA`.
    """
    if t < 1:
        raise ValueError("t debe ser >= 1 para calcular criterios.")
    lo = max(0, t - lookback + 1)
    window = market.returns.iloc[lo:t + 1]

    momentum = (1.0 + window).prod() - 1.0
    vol = window.std(ddof=0) * np.sqrt(252)
    low_vol = -vol

    fund = market.fundamentals
    df = pd.DataFrame({
        "momentum": momentum,
        "low_vol": low_vol,
        "value": fund["value"],
        "quality": fund["quality"],
        "liquidity": fund["liquidity"],
    })
    df = df.reindex(market.tickers)
    z = _zscore_cross_section(df)
    return z[CRITERIA]


def aggregate_scores(criteria_df: pd.DataFrame, weights, correct: bool = False) -> pd.Series:
    """Agrega los criterios por activo con OWA.

    Si ``correct`` es True, aplica la corrección espectral (A3) antes de agregar,
    decorrelacionando los criterios para evitar la inversión del inversor.
    """
    X = criteria_df.to_numpy(dtype=float)
    if correct:
        X = spectral_correction(X)
    scores = owa_matrix(X, weights, axis=1)
    return pd.Series(scores, index=criteria_df.index, name="score")
