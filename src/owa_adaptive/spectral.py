"""Corrección espectral y diagnóstico de inversión multicriterio (Artículo 3).

A3 ("When Multicriteria Scoring Inverts the Investor") muestra que, bajo cierta
estructura de correlación entre criterios, la agregación OWA puede **invertir** el
ordenamiento de riesgo pretendido: un perfil conservador termina con una cartera
más agresiva que uno arriesgado. Este módulo:

- mide la inversión con un **índice de inversión** (correlación de rangos entre el
  orness del perfil y el riesgo realizado de su cartera);
- la **mitiga** decorrelacionando los criterios (blanqueo ZCA) antes de agregar,
  eliminando la correlación que puede inducir la inversión.

Nota de alcance: el blanqueo ZCA decorrelaciona los criterios (verificable en
``tests/test_spectral.py``). La **restauración plena** de la monotonía
``orness → riesgo`` corresponde al teorema de A3 bajo inversión inducida por
correlación; en el panel sintético genérico el índice de inversión solo
**diagnostica** el efecto y no garantiza su corrección.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import numpy as np

__all__ = [
    "criterion_correlation",
    "whitening_matrix",
    "spectral_correction",
    "inversion_index",
    "InversionReport",
]


def _zscore_cols(X: np.ndarray) -> np.ndarray:
    mu = X.mean(axis=0)
    sd = X.std(axis=0)
    sd = np.where(sd > 1e-12, sd, 1.0)
    return (X - mu) / sd


def criterion_correlation(scores: np.ndarray) -> np.ndarray:
    """Matriz de correlación entre criterios (columnas de ``scores``)."""
    X = np.asarray(scores, dtype=float)
    if X.ndim != 2:
        raise ValueError("scores debe ser [n_activos × n_criterios].")
    return np.corrcoef(X, rowvar=False)


def whitening_matrix(scores: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Matriz de blanqueo ZCA a partir de la covarianza de los criterios.

    ``W = V · diag(1/√λ) · Vᵀ`` con ``(λ, V)`` la descomposición espectral de la
    covarianza. ZCA es el blanqueo "mínimamente rotacional": conserva al máximo la
    orientación original de los criterios, lo que preserva su interpretabilidad.
    """
    X = np.asarray(scores, dtype=float)
    Xc = X - X.mean(axis=0)
    C = np.cov(Xc, rowvar=False)
    C = np.atleast_2d(C)
    vals, vecs = np.linalg.eigh(C)
    vals = np.clip(vals, eps, None)
    return vecs @ np.diag(1.0 / np.sqrt(vals)) @ vecs.T


def spectral_correction(scores: np.ndarray, eps: float = 1e-8) -> np.ndarray:
    """Decorrelaciona los criterios y devuelve scores corregidos y estandarizados.

    Pasos: (1) blanqueo ZCA; (2) re-alineación de signo de cada criterio con su
    versión original (para conservar la semántica "mayor = mejor"); (3)
    estandarización por columnas para que la agregación OWA entre criterios sea
    comparable.
    """
    X = np.asarray(scores, dtype=float)
    if X.ndim != 2:
        raise ValueError("scores debe ser [n_activos × n_criterios].")
    if X.shape[1] == 1:
        return _zscore_cols(X)
    Xc = X - X.mean(axis=0)
    W = whitening_matrix(X, eps=eps)
    Xw = Xc @ W
    # Realinear signos con los criterios originales.
    for j in range(Xw.shape[1]):
        num = np.dot(Xw[:, j], Xc[:, j])
        if num < 0:
            Xw[:, j] = -Xw[:, j]
    return _zscore_cols(Xw)


def inversion_index(orness_values: Sequence[float],
                    realized_risk: Sequence[float]) -> float:
    """Índice de inversión: correlación de rangos (Spearman) entre el orness de
    los perfiles y el riesgo realizado de sus carteras.

    ≈ +1 ⇒ ordenamiento correcto (más agresivo ⇒ más riesgo).
    ≤ 0  ⇒ inversión (el scoring invierte al inversor).
    """
    a = np.asarray(orness_values, dtype=float)
    r = np.asarray(realized_risk, dtype=float)
    if a.size != r.size or a.size < 2:
        raise ValueError("Se requieren vectores del mismo tamaño (>=2).")
    try:
        from scipy.stats import spearmanr
        rho, _ = spearmanr(a, r)
        return float(rho)
    except Exception:  # pragma: no cover - fallback sin scipy
        ar = _rankdata(a)
        rr = _rankdata(r)
        return float(np.corrcoef(ar, rr)[0, 1])


def _rankdata(x: np.ndarray) -> np.ndarray:
    order = np.asarray(x, dtype=float).argsort()
    ranks = np.empty(len(x), dtype=float)
    ranks[order] = np.arange(1, len(x) + 1)
    return ranks


@dataclass
class InversionReport:
    """Comparación del índice de inversión antes y después de la corrección."""
    index_naive: float
    index_corrected: float

    @property
    def fixed(self) -> bool:
        """True si la corrección restauró la monotonía (índice alto y positivo)."""
        return self.index_corrected >= 0.9 and self.index_corrected > self.index_naive
