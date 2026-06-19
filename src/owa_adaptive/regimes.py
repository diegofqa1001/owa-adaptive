"""Detección de régimen de mercado desde señales de incertidumbre (VIX, EPU).

El componente adaptativo (OE3) reacciona al **estrés de régimen** ``s(t) ∈ [0,1]``,
una combinación convexa de versiones estandarizadas y comprimidas (logística) del
VIX (volatilidad implícita) y el EPU (Economic Policy Uncertainty). ``s`` alto ⇒
mercado tensionado ⇒ el agregador se vuelve defensivo.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np

__all__ = ["stress_index", "classify", "RegimeResult", "regime"]

REGIME_LABELS = ["calma", "normal", "estres", "crisis"]
# Umbrales sobre s(t) para etiquetar el régimen.
REGIME_THRESHOLDS = (0.35, 0.55, 0.75)


def _zscore(x: np.ndarray, window: Optional[int]) -> np.ndarray:
    """Estandariza una serie. Si ``window`` es None, usa media/desv. globales;
    si es un entero, usa una media/desv. móvil causal (sin mirar el futuro)."""
    x = np.asarray(x, dtype=float)
    if window is None:
        mu, sd = x.mean(), x.std()
        sd = sd if sd > 1e-12 else 1.0
        return (x - mu) / sd
    # Estandarización móvil causal con relleno expansivo al inicio.
    out = np.zeros_like(x)
    for t in range(x.size):
        lo = max(0, t - window + 1)
        seg = x[lo:t + 1]
        mu = seg.mean()
        sd = seg.std()
        sd = sd if sd > 1e-12 else 1.0
        out[t] = (x[t] - mu) / sd
    return out


def stress_index(vix: Sequence[float],
                epu: Optional[Sequence[float]] = None,
                w_vix: float = 0.6,
                window: Optional[int] = None) -> np.ndarray:
    """Índice de estrés de régimen ``s(t) ∈ [0,1]``.

    Cada señal se estandariza (z-score) y se comprime con la logística
    ``σ(z)=1/(1+e^{-z})``; luego se combinan convexamente. Si no se aporta EPU,
    se usa solo el VIX.
    """
    z_vix = _zscore(vix, window)
    s_vix = 1.0 / (1.0 + np.exp(-z_vix))
    if epu is None:
        return np.clip(s_vix, 0.0, 1.0)
    z_epu = _zscore(epu, window)
    s_epu = 1.0 / (1.0 + np.exp(-z_epu))
    w_vix = float(np.clip(w_vix, 0.0, 1.0))
    s = w_vix * s_vix + (1.0 - w_vix) * s_epu
    return np.clip(s, 0.0, 1.0)


def classify(stress: Sequence[float]) -> np.ndarray:
    """Etiqueta cada periodo según el estrés: calma/normal/estres/crisis."""
    s = np.asarray(stress, dtype=float)
    t1, t2, t3 = REGIME_THRESHOLDS
    labels = np.empty(s.shape, dtype=object)
    labels[s < t1] = REGIME_LABELS[0]
    labels[(s >= t1) & (s < t2)] = REGIME_LABELS[1]
    labels[(s >= t2) & (s < t3)] = REGIME_LABELS[2]
    labels[s >= t3] = REGIME_LABELS[3]
    return labels


@dataclass
class RegimeResult:
    """Resultado de la detección de régimen."""
    stress: np.ndarray
    labels: np.ndarray

    @property
    def mean_stress(self) -> float:
        return float(self.stress.mean())

    def fraction(self, label: str) -> float:
        return float(np.mean(self.labels == label))


def regime(vix: Sequence[float],
          epu: Optional[Sequence[float]] = None,
          w_vix: float = 0.6,
          window: Optional[int] = None) -> RegimeResult:
    """Calcula estrés y etiquetas de régimen en un solo paso."""
    s = stress_index(vix, epu, w_vix=w_vix, window=window)
    return RegimeResult(stress=s, labels=classify(s))
