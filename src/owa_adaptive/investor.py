"""Dinámica del inversor: clasificación, actualización conductual y explicación.

Cierra el lazo de realimentación que hace que **el inversor también sea
dinámico**: tras una "cosecha" (el resultado realizado en un horizonte), su
actitud (orness) se actualiza por sesgos conductuales (efecto recencia / dinero
de la casa: una buena racha lo vuelve más optimista y agresivo; las pérdidas, más
defensivo). Eso desplaza su perfil y reconfigura su portafolio.

Componentes:
- ``classify_investor`` — del cuestionario de 7 dimensiones a perfil.
- ``update_orness`` / ``behavioral_update`` — regla conductual de actualización.
- ``invest_and_hold`` — invierte y avanza el tiempo un horizonte.
- ``portfolio_tilts`` / ``explain_portfolio`` — el "porqué" en lenguaje natural.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from .profiles import (
    ALPHA_MAX,
    ALPHA_MIN,
    DIMENSION_LABELS,
    DIMENSIONS,
    Profile,
    all_profiles,
    orness_from_dimensions,
)
from .recommender import Recommendation, Recommender
from .scoring import CRITERIA, compute_criteria

__all__ = [
    "QUESTIONS",
    "CRITERIA_LABELS",
    "PROFILE_PHILOSOPHY",
    "InvestorState",
    "nearest_profile",
    "classify_investor",
    "update_orness",
    "behavioral_update",
    "invest_and_hold",
    "portfolio_tilts",
    "explain_orness",
    "explain_portfolio",
]

# Etiquetas legibles de criterios.
CRITERIA_LABELS: Dict[str, str] = {
    "momentum": "momentum (tendencia reciente)",
    "low_vol": "baja volatilidad",
    "value": "valor (precio atractivo)",
    "quality": "calidad del activo",
    "liquidity": "liquidez",
}

# Cuestionario amigable: (dimensión, pregunta, ancla 1, ancla 7).
QUESTIONS: List[Tuple[str, str, str, str]] = [
    ("aversion_perdida",
     "¿Cuánto te afecta emocionalmente una pérdida en tus inversiones?",
     "Casi nada", "Muchísimo"),
    ("tolerancia_riesgo",
     "¿Qué tan cómodo te sientes asumiendo riesgo para buscar más rentabilidad?",
     "Nada cómodo", "Muy cómodo"),
    ("horizonte_temporal",
     "¿Por cuánto tiempo planeas mantener tus inversiones?",
     "Muy corto plazo", "Muy largo plazo"),
    ("exceso_confianza",
     "¿Qué tanta confianza tienes en tu propio criterio para elegir inversiones?",
     "Muy poca", "Muchísima"),
    ("comportamiento_gregario",
     "¿Qué tanto te dejas llevar por lo que hace la mayoría del mercado?",
     "Nada", "Totalmente"),
    ("preferencia_liquidez",
     "¿Qué tan importante es poder retirar tu dinero rápidamente?",
     "Nada importante", "Imprescindible"),
    ("aversion_ambiguedad",
     "¿Cuánto te incomoda invertir cuando el futuro es incierto?",
     "Nada", "Muchísimo"),
]

# Filosofía breve por perfil (de conservador a agresivo).
PROFILE_PHILOSOPHY: Dict[str, str] = {
    "Guardian": "Protege el capital ante todo. Prioriza estabilidad y evitar pérdidas sobre el crecimiento.",
    "Sentinel": "Muy prudente. Acepta crecimiento modesto a cambio de un riesgo bajo y controlado.",
    "Custodian": "Conservador con apertura. Cuida el capital pero admite algo de exposición al crecimiento.",
    "Balancer": "Busca equilibrio entre proteger y crecer, sin inclinarse a ningún extremo.",
    "Navigator": "Equilibrado y flexible. Ajusta el rumbo entre estabilidad y oportunidad según el contexto.",
    "Strategist": "Orientado al crecimiento. Asume riesgo calculado para capturar oportunidades.",
    "Pioneer": "Agresivo. Persigue rentabilidades altas y tolera una volatilidad considerable.",
    "Visionary": "Muy agresivo. Maximiza el potencial de crecimiento aceptando alto riesgo.",
}


@dataclass
class InvestorState:
    """Estado evolutivo del inversor a lo largo de la simulación."""
    orness: float
    profile_name: str
    t: int
    round: int = 0
    history: List[dict] = field(default_factory=list)

    def snapshot(self) -> dict:
        return {"round": self.round, "t": self.t,
                "orness": self.orness, "profile": self.profile_name}


def nearest_profile(orness: float) -> Profile:
    """Perfil canónico cuyo orness objetivo es el más cercano al dado."""
    return min(all_profiles(), key=lambda p: abs(p.target_orness - orness))


def classify_investor(answers: Dict[str, float]) -> Tuple[float, Profile]:
    """Del cuestionario (7 dimensiones Likert 1-7) al orness y al perfil."""
    missing = [d for d in DIMENSIONS if d not in answers]
    if missing:
        raise ValueError(f"Faltan dimensiones en el cuestionario: {missing}")
    orn = orness_from_dimensions(answers)
    return orn, nearest_profile(orn)


def update_orness(orness: float, realized_return: float,
                eta: float = 0.15, ref: float = 0.05,
                lo: float = 0.12, hi: float = 0.90) -> float:
    """Actualiza la actitud (orness) tras la cosecha, por sesgos conductuales.

    Una buena racha (retorno positivo) eleva el orness — el inversor se vuelve más
    optimista y agresivo (efecto "dinero de la casa" / recencia); las pérdidas lo
    reducen. El cambio está acotado por ``tanh`` y recortado a [lo, hi].

    ``ref`` es la magnitud de retorno (por horizonte) que produce una reacción
    apreciable; ``eta`` es la sensibilidad máxima.
    """
    delta = eta * np.tanh(realized_return / ref)
    return float(np.clip(orness + delta, lo, hi))


def behavioral_update(state: InvestorState, realized_return: float,
                    new_t: int, **kw) -> InvestorState:
    """Aplica la actualización conductual y devuelve el nuevo estado."""
    new_orn = update_orness(state.orness, realized_return, **kw)
    prof = nearest_profile(new_orn)
    hist = list(state.history)
    hist.append({**state.snapshot(), "realized_return": float(realized_return)})
    return InvestorState(orness=new_orn, profile_name=prof.name, t=new_t,
                        round=state.round + 1, history=hist)


def portfolio_tilts(criteria_df: pd.DataFrame, portfolio: pd.Series) -> pd.Series:
    """Exposición media del portafolio a cada criterio (ponderada por peso).

    Indica hacia qué criterios se inclina la cartera elegida (el "porqué"
    concreto y distinto para cada perfil).
    """
    w = portfolio.reindex(criteria_df.index).fillna(0.0)
    s = w.sum()
    if s <= 1e-12:
        return criteria_df.mean()
    return (criteria_df.mul(w, axis=0).sum()) / s


def explain_orness(orness: float) -> str:
    """Explica, en lenguaje natural, qué significa la actitud OWA del inversor."""
    if orness >= 0.66:
        cabeza = ("Tu actitud es **optimista/agresiva**: el operador OWA pondera lo "
                "mejor de cada activo, así que tu cartera busca crecimiento y "
                "tolera más volatilidad.")
    elif orness >= 0.45:
        cabeza = ("Tu actitud es **equilibrada**: el operador OWA reparte el peso de "
                "forma pareja, balanceando crecimiento y estabilidad.")
    else:
        cabeza = ("Tu actitud es **defensiva/conservadora**: el operador OWA pondera lo "
                "peor de cada activo, penalizando debilidades, así que tu cartera "
                "prioriza estabilidad y protección del capital.")
    return f"{cabeza} (orness = {orness:.2f})."


def explain_portfolio(orness: float, tilts: pd.Series) -> str:
    """Texto del porqué: filosofía + criterios hacia los que se inclina la cartera."""
    top = tilts.sort_values(ascending=False)
    fuertes = [CRITERIA_LABELS.get(k, k) for k in top.index[:2]]
    debil = CRITERIA_LABELS.get(top.index[-1], top.index[-1])
    return (f"{explain_orness(orness)} En la práctica, tu portafolio se inclina hacia "
            f"**{fuertes[0]}** y **{fuertes[1]}**, y da menos peso a {debil}.")


def invest_and_hold(market, base_orness: float, t0: int, horizon: int,
                    top_n: int = 10, adaptive: bool = True, spectral: bool = True,
                    name: str = "Inversor") -> dict:
    """Construye la cartera en ``t0`` y la mantiene ``horizon`` días.

    Devuelve la recomendación, la curva de capital del horizonte, el retorno
    realizado (la "cosecha"), las exposiciones por criterio y el nuevo índice de
    tiempo. Avanza el reloj de la simulación.
    """
    rec = Recommender(market, top_n=top_n, adaptive=adaptive, spectral=spectral)
    recm: Recommendation = rec.recommend_orness(base_orness, t0, name=name)
    tickers = market.tickers
    w = recm.portfolio.reindex(tickers).fillna(0.0).to_numpy()

    end_t = min(t0 + horizon, market.n_days - 1)
    block = market.returns.iloc[t0 + 1:end_t + 1]
    if block.shape[0] == 0:
        daily = np.array([0.0])
        equity = pd.Series([1.0], index=[market.dates[t0]])
        realized = 0.0
    else:
        daily = block.reindex(columns=tickers).to_numpy() @ w
        equity = pd.Series((1.0 + daily).cumprod(), index=block.index)
        realized = float(equity.iloc[-1] - 1.0)

    crit = compute_criteria(market, t0, lookback=126)
    tilts = portfolio_tilts(crit, recm.portfolio)

    return {
        "recommendation": recm,
        "equity": equity,
        "daily": daily,
        "realized_return": realized,
        "end_t": end_t,
        "tilts": tilts,
        "criteria": crit,
    }
