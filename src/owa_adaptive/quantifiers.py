"""Cuantificadores lingüísticos RIM y generación de pesos OWA.

Dos rutas para construir pesos con una actitud (orness) deseada:

1. ``rim_weights`` / ``weights_for_orness`` — cuantificador difuso *Regular
   Increasing Monotone* de la familia potencia ``Q(r)=r^p`` (Yager, 1996). Es la
   ruta usada en el Artículo 2 ("cuantificador RIM").
2. ``max_entropy_weights`` — pesos de máxima entropía para un orness dado
   (Fullér & Majlender, 2001). Solución geométrica exacta: w_j ∝ β^{n-j}.

Ambas resuelven el parámetro libre por bisección monótona, sin dependencias
externas más allá de numpy.
"""
from __future__ import annotations

import numpy as np

from .owa import orness, validate_weights

__all__ = [
    "rim_weights",
    "weights_for_orness",
    "max_entropy_weights",
    "exponent_for_orness",
]


# --- Cuantificador RIM potencia ----------------------------------------------
def rim_weights(n: int, p: float) -> np.ndarray:
    """Pesos OWA del cuantificador RIM ``Q(r) = r^p`` con ``p > 0``.

    ``w_i = Q(i/n) - Q((i-1)/n)``. ``p<1`` → optimista (orness>0.5);
    ``p=1`` → uniforme (orness=0.5); ``p>1`` → pesimista (orness<0.5).
    """
    if n < 1:
        raise ValueError("n debe ser >= 1.")
    if p <= 0:
        raise ValueError("El exponente p debe ser positivo.")
    if n == 1:
        return np.array([1.0])
    i = np.arange(1, n + 1)
    q = (i / n) ** p
    q_prev = ((i - 1) / n) ** p
    w = q - q_prev
    return validate_weights(w)


def exponent_for_orness(n: int, target: float, tol: float = 1e-10,
                        max_iter: int = 200) -> float:
    """Exponente ``p`` del cuantificador RIM que produce el ``target`` de orness.

    El orness es estrictamente decreciente en ``p``, lo que garantiza una
    bisección bien definida en ``p ∈ (0, P_max]``.
    """
    target = float(np.clip(target, 1e-6, 1 - 1e-6))
    if n == 1:
        return 1.0
    # orness(p=1)=0.5. Acotamos según el lado del objetivo.
    lo, hi = 1e-6, 1.0e6
    # orness decrece con p: en lo->orness~1, en hi->orness~0.
    f = lambda p: orness(rim_weights(n, p)) - target
    f_lo, f_hi = f(lo), f(hi)
    if f_lo < 0:  # incluso el más optimista no alcanza el target (target~1)
        return lo
    if f_hi > 0:  # incluso el más pesimista lo supera (target~0)
        return hi
    for _ in range(max_iter):
        mid = np.sqrt(lo * hi)  # bisección geométrica (p abarca varios órdenes)
        fm = f(mid)
        if abs(fm) < tol:
            return float(mid)
        if fm > 0:
            lo = mid
        else:
            hi = mid
    return float(np.sqrt(lo * hi))


def weights_for_orness(n: int, target: float) -> np.ndarray:
    """Pesos OWA vía cuantificador RIM que materializan un orness objetivo."""
    p = exponent_for_orness(n, target)
    return rim_weights(n, p)


# --- Máxima entropía (Fullér & Majlender) ------------------------------------
def _geometric_weights(n: int, beta: float) -> np.ndarray:
    """w_j ∝ β^{n-j}, j=1..n. β>1 optimista, β<1 pesimista, β=1 uniforme."""
    j = np.arange(1, n + 1)
    exponents = (n - j).astype(float)
    # Estabilidad numérica en escala log.
    log_w = exponents * np.log(beta)
    log_w -= log_w.max()
    w = np.exp(log_w)
    return w / w.sum()


def max_entropy_weights(n: int, target: float, tol: float = 1e-12,
                        max_iter: int = 200) -> np.ndarray:
    """Pesos OWA de máxima entropía para un ``target`` de orness dado.

    Solución analítica de Fullér & Majlender (2001): los pesos son geométricos
    ``w_j ∝ β^{n-j}``. Se halla ``β`` por bisección (orness creciente en β).
    """
    target = float(np.clip(target, 1e-6, 1 - 1e-6))
    if n == 1:
        return np.array([1.0])
    if abs(target - 0.5) < 1e-12:
        return np.full(n, 1.0 / n)
    lo, hi = 1e-8, 1e8
    f = lambda b: orness(_geometric_weights(n, b)) - target
    for _ in range(max_iter):
        mid = np.sqrt(lo * hi)
        fm = f(mid)
        if abs(fm) < tol:
            return _geometric_weights(n, mid)
        if fm < 0:   # orness muy bajo -> subir beta
            lo = mid
        else:
            hi = mid
    return _geometric_weights(n, np.sqrt(lo * hi))
