"""Motor de recomendación end-to-end: perfil + régimen → cartera.

Integra todas las piezas: criterios multicriterio (``scoring``), actitud del
perfil (``profiles``), modulación adaptativa por régimen (``regimes`` +
``adaptive``) y corrección espectral (``spectral``). Es la cara funcional del
modelo (OE3+OE4) que consumen la API y el dashboard.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from .adaptive import effective_orness
from .config import DEFAULT_ALPHA_FLOOR, DEFAULT_LAMBDA, DEFAULT_TOP_N
from .profiles import Profile, get_profile
from .quantifiers import weights_for_orness
from .regimes import stress_index
from .scoring import CRITERIA, aggregate_scores, compute_criteria

__all__ = ["Recommendation", "Recommender"]


@dataclass
class Recommendation:
    """Cartera recomendada para una fecha."""
    date: object
    profile: str
    base_orness: float
    effective_orness: float
    stress: float
    weights_owa: np.ndarray          # pesos del operador OWA (sobre criterios)
    portfolio: pd.Series             # ticker -> peso de cartera
    scores: pd.Series                # ticker -> score OWA

    def top(self, k: int = 10) -> pd.Series:
        return self.portfolio.sort_values(ascending=False).head(k)


class Recommender:
    """Genera recomendaciones de cartera.

    Parameters
    ----------
    market      : objeto MarketData (sintético o real).
    top_n       : número de activos en la cartera.
    lookback    : ventana (días) para los criterios de precio.
    adaptive    : si True, modula el orness según el estrés de régimen (OE3).
    spectral    : si True, aplica la corrección espectral (A3).
    lam, alpha_floor : parámetros de la modulación adaptativa.
    stress_window    : ventana de estandarización causal para el estrés.
    """

    def __init__(self, market, top_n: int = DEFAULT_TOP_N, lookback: int = 126,
                adaptive: bool = True, spectral: bool = True,
                lam: float = DEFAULT_LAMBDA, alpha_floor: float = DEFAULT_ALPHA_FLOOR,
                stress_window: Optional[int] = 252):
        self.market = market
        self.top_n = int(top_n)
        self.lookback = int(lookback)
        self.adaptive = bool(adaptive)
        self.spectral = bool(spectral)
        self.lam = float(lam)
        self.alpha_floor = float(alpha_floor)
        self.stress_window = stress_window
        self.n_criteria = len(CRITERIA)
        # Estrés de régimen pre-calculado para toda la serie.
        self._stress = stress_index(
            market.vix.to_numpy(),
            market.epu.to_numpy() if market.epu is not None else None,
            window=stress_window,
        )

    def stress_at(self, t: int) -> float:
        return float(self._stress[t])

    def _weights_for(self, base_orness: float, t: int):
        """Pesos OWA para un orness base, modulados por el régimen si adaptativo."""
        if self.adaptive:
            alpha = effective_orness(base_orness, self._stress[t], self.lam, self.alpha_floor)
        else:
            alpha = float(base_orness)
        w = weights_for_orness(self.n_criteria, alpha)
        return w, float(alpha)

    def _assemble(self, base_orness: float, t: int, name: str) -> Recommendation:
        """Construye la recomendación a partir de un orness base y una fecha."""
        crit = compute_criteria(self.market, t, lookback=self.lookback)
        w, alpha = self._weights_for(base_orness, t)
        scores = aggregate_scores(crit, w, correct=self.spectral)

        # Selección top-N y ponderación proporcional al score positivo.
        ranked = scores.sort_values(ascending=False)
        chosen = ranked.head(self.top_n)
        shifted = chosen - chosen.min()
        if shifted.sum() <= 1e-12:
            weights_port = pd.Series(1.0 / len(chosen), index=chosen.index)
        else:
            weights_port = shifted / shifted.sum()
        portfolio = weights_port.reindex(self.market.tickers).fillna(0.0)

        return Recommendation(
            date=self.market.dates[t], profile=name,
            base_orness=float(base_orness), effective_orness=alpha,
            stress=self.stress_at(t), weights_owa=w,
            portfolio=portfolio, scores=scores,
        )

    def recommend(self, profile, t: int) -> Recommendation:
        """Recomendación para el día índice ``t`` usando un perfil canónico."""
        prof = profile if isinstance(profile, Profile) else get_profile(profile)
        return self._assemble(prof.target_orness, t, prof.name)

    def recommend_orness(self, base_orness: float, t: int,
                        name: str = "Inversor") -> Recommendation:
        """Recomendación para un orness arbitrario (inversor dinámico, no canónico)."""
        return self._assemble(float(base_orness), t, name)

    def recommend_latest(self, profile) -> Recommendation:
        """Recomendación para el último día disponible."""
        return self.recommend(profile, self.market.n_days - 1)
