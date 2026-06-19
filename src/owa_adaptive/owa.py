"""Operador OWA (Ordered Weighted Averaging) y medidas asociadas.

Implementa el operador de Yager (1988) y sus indicadores de actitud (orness) y
de dispersión (entropía). Es la pieza algebraica sobre la que se construyen los
perfiles conductuales, el componente adaptativo y la corrección espectral.

Referencia: Yager, R. R. (1988). On ordered weighted averaging aggregation
operators in multicriteria decisionmaking. IEEE TSMC, 18(1), 183-190.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

__all__ = ["owa", "orness", "andness", "dispersion", "validate_weights", "owa_matrix"]


def validate_weights(weights: Sequence[float], tol: float = 1e-8) -> np.ndarray:
    """Valida y normaliza un vector de pesos OWA.

    Los pesos deben ser no negativos y sumar 1. Si la suma difiere de 1 dentro
    de una tolerancia razonable se renormaliza; si hay negativos se lanza error.
    """
    w = np.asarray(weights, dtype=float).ravel()
    if w.size == 0:
        raise ValueError("El vector de pesos no puede estar vacío.")
    if np.any(w < -tol):
        raise ValueError("Los pesos OWA no pueden ser negativos.")
    w = np.clip(w, 0.0, None)
    s = w.sum()
    if s <= 0:
        raise ValueError("La suma de pesos debe ser positiva.")
    return w / s


def owa(values: Sequence[float], weights: Sequence[float]) -> float:
    """Agrega ``values`` con el operador OWA de pesos ``weights``.

    Los argumentos se ordenan de forma descendente y se ponderan: el peso w_1
    acompaña al mayor valor, w_n al menor. Así, pesos concentrados arriba
    (orness alto) producen una agregación optimista.
    """
    a = np.asarray(values, dtype=float).ravel()
    w = validate_weights(weights)
    if a.size != w.size:
        raise ValueError(f"Dimensiones incompatibles: {a.size} valores vs {w.size} pesos.")
    b = np.sort(a)[::-1]  # descendente
    return float(np.dot(w, b))


def owa_matrix(matrix: np.ndarray, weights: Sequence[float], axis: int = 1) -> np.ndarray:
    """Aplica OWA fila a fila (o columna a columna) de forma vectorizada.

    Útil para agregar una matriz [activos × criterios] en un score por activo.
    Ordena descendentemente a lo largo de ``axis`` y pondera.
    """
    M = np.asarray(matrix, dtype=float)
    w = validate_weights(weights)
    if M.shape[axis] != w.size:
        raise ValueError(
            f"El eje {axis} tiene tamaño {M.shape[axis]} pero hay {w.size} pesos."
        )
    ordered = np.sort(M, axis=axis)
    ordered = np.flip(ordered, axis=axis)  # descendente
    return np.tensordot(ordered, w, axes=([axis], [0]))


def orness(weights: Sequence[float]) -> float:
    """Grado de optimismo del operador (Yager). 0 = min, 0.5 = media, 1 = max."""
    w = validate_weights(weights)
    n = w.size
    if n == 1:
        return 0.5
    idx = np.arange(n)  # 0..n-1 -> posición i=idx+1, (n-i)=n-1-idx
    return float(np.dot(n - 1 - idx, w) / (n - 1))


def andness(weights: Sequence[float]) -> float:
    """Grado de pesimismo: ``1 - orness``."""
    return 1.0 - orness(weights)


def dispersion(weights: Sequence[float]) -> float:
    """Entropía de Shannon de los pesos (uso de información). Máx = ln(n)."""
    w = validate_weights(weights)
    nz = w[w > 0]
    return float(-np.sum(nz * np.log(nz)))
