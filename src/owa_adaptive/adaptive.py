"""Agregación adaptativa IOWA inducida por el régimen de mercado (OE3).

Dos ideas centrales:

1. **Modulación de la actitud.** La actitud base del perfil (orness) se contrae
   hacia un piso defensivo en función del estrés de régimen ``s(t)``:

       α_eff(t) = α_base − λ · s(t) · (α_base − α_floor)

   Monótona y auditable: a mayor estrés, menor orness efectivo (más defensivo).

2. **Induced OWA (Yager & Filev, 1999).** Cuando se agrega con una variable
   inductora (p. ej., la fiabilidad del criterio bajo el régimen actual), el
   orden de ponderación lo fija dicha variable, no el propio valor.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

from .config import DEFAULT_ALPHA_FLOOR, DEFAULT_LAMBDA
from .owa import validate_weights
from .quantifiers import weights_for_orness

__all__ = ["effective_orness", "iowa", "AdaptiveOWA", "AdaptiveResult"]


def effective_orness(base_orness: float,
                    stress,
                    lam: float = DEFAULT_LAMBDA,
                    alpha_floor: float = DEFAULT_ALPHA_FLOOR):
    """Orness efectivo dado el estrés de régimen.

    Acepta escalar o array de estrés. El resultado nunca sube por encima de
    ``base_orness`` ni baja de ``alpha_floor``.
    """
    s = np.asarray(stress, dtype=float)
    base = float(base_orness)
    floor = min(float(alpha_floor), base)
    alpha = base - lam * s * (base - floor)
    alpha = np.clip(alpha, floor, base)
    return float(alpha) if alpha.ndim == 0 else alpha


def iowa(values: Sequence[float],
        inducing: Sequence[float],
        weights: Sequence[float]) -> float:
    """Operador Induced OWA: ordena ``values`` según la variable ``inducing``.

    El mayor valor de la variable inductora recibe el peso ``w_1``. Empates en la
    inductora se resuelven por el valor (criterio de Yager & Filev).
    """
    a = np.asarray(values, dtype=float).ravel()
    u = np.asarray(inducing, dtype=float).ravel()
    w = validate_weights(weights)
    if not (a.size == u.size == w.size):
        raise ValueError("values, inducing y weights deben tener igual longitud.")
    # Orden descendente por inductora; desempate por el propio valor.
    order = np.lexsort((-a, -u))  # clave primaria -u, secundaria -a
    return float(np.dot(w, a[order]))


@dataclass
class AdaptiveResult:
    """Trayectoria de orness efectivo y pesos por periodo."""
    base_orness: float
    effective_orness: np.ndarray  # [T]
    weights: np.ndarray           # [T × n_criterios]

    @property
    def mean_effective_orness(self) -> float:
        return float(self.effective_orness.mean())


class AdaptiveOWA:
    """Genera pesos OWA variables en el tiempo según perfil y régimen.

    Parameters
    ----------
    base_orness : actitud del perfil en calma (su orness objetivo).
    n_criteria  : número de criterios a agregar.
    lam         : intensidad de la reacción adaptativa (0 = estático).
    alpha_floor : piso defensivo de orness en estrés máximo.
    """

    def __init__(self, base_orness: float, n_criteria: int,
                lam: float = DEFAULT_LAMBDA,
                alpha_floor: float = DEFAULT_ALPHA_FLOOR):
        self.base_orness = float(base_orness)
        self.n_criteria = int(n_criteria)
        self.lam = float(lam)
        self.alpha_floor = float(alpha_floor)
        self._cache: dict = {}

    def weights_at(self, stress: float) -> np.ndarray:
        """Pesos OWA para un nivel de estrés puntual (con cache por redondeo)."""
        alpha = effective_orness(self.base_orness, stress, self.lam, self.alpha_floor)
        key = round(float(alpha), 4)
        if key not in self._cache:
            self._cache[key] = weights_for_orness(self.n_criteria, key)
        return self._cache[key]

    def run(self, stress_series: Sequence[float]) -> AdaptiveResult:
        """Calcula orness efectivo y matriz de pesos para toda la serie."""
        s = np.asarray(stress_series, dtype=float).ravel()
        alpha = effective_orness(self.base_orness, s, self.lam, self.alpha_floor)
        alpha = np.atleast_1d(alpha)
        W = np.vstack([self.weights_at(st) for st in s])
        return AdaptiveResult(base_orness=self.base_orness,
                            effective_orness=alpha, weights=W)
