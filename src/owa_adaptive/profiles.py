"""Taxonomía difusa-OWA de 8 perfiles conductuales de riesgo (OE2 / Artículo 2).

Ocho perfiles ordenados de menor a mayor apetito de riesgo, descritos sobre
siete dimensiones conductuales. La contribución no es solo nominal: se modela un
**puente conductual → orness**, de modo que el vector de dimensiones de un
inversor *produce* la actitud OWA (y por tanto los pesos de agregación).

- Rango de orness objetivo: [0.158, 0.865] (reportado en el Artículo 2).
- Validación de concordancia entre jueces: W de Kendall.

El mapeo dimensiones→orness es una función fija (no depende del conjunto de
perfiles), por lo que admite cualquier cuestionario de inversor nuevo.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

import numpy as np

from .quantifiers import weights_for_orness

__all__ = [
    "DIMENSIONS",
    "DIMENSION_DIRECTION",
    "PROFILE_NAMES",
    "ALPHA_MIN",
    "ALPHA_MAX",
    "Profile",
    "all_profiles",
    "get_profile",
    "orness_from_dimensions",
    "kendall_w",
    "expert_agreement",
]

# --- Definición de dimensiones (clave -> etiqueta) ---------------------------
DIMENSIONS: List[str] = [
    "aversion_perdida",      # loss aversion
    "tolerancia_riesgo",     # risk tolerance
    "horizonte_temporal",    # time horizon
    "exceso_confianza",      # overconfidence
    "comportamiento_gregario",  # herding
    "preferencia_liquidez",  # liquidity preference
    "aversion_ambiguedad",   # ambiguity aversion
]

DIMENSION_LABELS: Dict[str, str] = {
    "aversion_perdida": "Aversión a la pérdida",
    "tolerancia_riesgo": "Tolerancia al riesgo",
    "horizonte_temporal": "Horizonte temporal",
    "exceso_confianza": "Exceso de confianza",
    "comportamiento_gregario": "Comportamiento gregario",
    "preferencia_liquidez": "Preferencia por liquidez",
    "aversion_ambiguedad": "Aversión a la ambigüedad",
}

# Dirección teórica de cada dimensión sobre el apetito de riesgo (orness).
# Positiva => más orness (más agresivo); negativa => menos orness (defensivo).
DIMENSION_DIRECTION: Dict[str, float] = {
    "aversion_perdida": -1.0,
    "tolerancia_riesgo": +1.0,
    "horizonte_temporal": +1.0,
    "exceso_confianza": +1.0,
    "comportamiento_gregario": -0.5,
    "preferencia_liquidez": -1.0,
    "aversion_ambiguedad": -1.0,
}

PROFILE_NAMES: List[str] = [
    "Guardian", "Sentinel", "Custodian", "Balancer",
    "Navigator", "Strategist", "Pioneer", "Visionary",
]

ALPHA_MIN: float = 0.158
ALPHA_MAX: float = 0.865

# Escala Likert de las dimensiones.
_LIKERT_MIN, _LIKERT_MAX = 1.0, 7.0

# Extremos conductuales (perfil más conservador y más agresivo) en escala Likert.
# El resto de perfiles se interpola linealmente entre ambos.
_GUARDIAN = {
    "aversion_perdida": 7.0, "tolerancia_riesgo": 1.0, "horizonte_temporal": 2.0,
    "exceso_confianza": 1.0, "comportamiento_gregario": 6.0,
    "preferencia_liquidez": 7.0, "aversion_ambiguedad": 7.0,
}
_VISIONARY = {
    "aversion_perdida": 1.0, "tolerancia_riesgo": 7.0, "horizonte_temporal": 7.0,
    "exceso_confianza": 7.0, "comportamiento_gregario": 2.0,
    "preferencia_liquidez": 1.0, "aversion_ambiguedad": 1.0,
}


def _normalize_dim(value: float) -> float:
    """Escala Likert [1,7] -> [0,1]."""
    return (value - _LIKERT_MIN) / (_LIKERT_MAX - _LIKERT_MIN)


def _latent(dim_values: Dict[str, float]) -> float:
    """Puntaje latente conductual: combinación con signo de las dimensiones.

    latent = (1/Σ|d|) Σ_k d_k (x_k − 0.5),  con x_k normalizado en [0,1].
    Centrado en 0 para el inversor neutral.
    """
    total = sum(abs(v) for v in DIMENSION_DIRECTION.values())
    acc = 0.0
    for k, d in DIMENSION_DIRECTION.items():
        x = _normalize_dim(dim_values[k])
        acc += d * (x - 0.5)
    return acc / total


# Calibración afín de dos puntos sobre los extremos canónicos. Mapea
# exactamente Guardian -> ALPHA_MIN y Visionary -> ALPHA_MAX. Como las
# dimensiones de los 8 perfiles se interpolan linealmente, el orness
# reconstruido coincide con el orness objetivo equiespaciado.
_LATENT_MIN = _latent(_GUARDIAN)
_LATENT_MAX = _latent(_VISIONARY)
_LATENT_SPAN = _LATENT_MAX - _LATENT_MIN


def orness_from_dimensions(dim_values: Dict[str, float]) -> float:
    """Mapea un vector conductual (7 dimensiones Likert) a un orness en [0,1].

    Función fija y monótona: sirve para clasificar a cualquier inversor a partir
    de su cuestionario, no solo a los 8 perfiles canónicos. Recortada a
    [ALPHA_MIN, ALPHA_MAX] para mantener el rango de la taxonomía.
    """
    lat = _latent(dim_values)
    frac = (lat - _LATENT_MIN) / _LATENT_SPAN
    val = ALPHA_MIN + (ALPHA_MAX - ALPHA_MIN) * frac
    return float(np.clip(val, ALPHA_MIN, ALPHA_MAX))


@dataclass(frozen=True)
class Profile:
    """Un perfil conductual de la taxonomía."""
    index: int
    name: str
    dimensions: Dict[str, float]
    target_orness: float

    @property
    def orness_bridge(self) -> float:
        """Orness reconstruido desde las dimensiones (validación del puente)."""
        return orness_from_dimensions(self.dimensions)

    def weights(self, n: int) -> np.ndarray:
        """Pesos OWA del perfil para ``n`` criterios (vía cuantificador RIM)."""
        return weights_for_orness(n, self.target_orness)

    def as_row(self) -> Dict[str, float]:
        row = {"perfil": self.name, "orness": self.target_orness}
        row.update(self.dimensions)
        return row


def _build_profiles() -> List[Profile]:
    profiles: List[Profile] = []
    m = len(PROFILE_NAMES)
    for i, name in enumerate(PROFILE_NAMES):
        t = i / (m - 1)  # 0..1
        dims = {
            k: float(_GUARDIAN[k] + t * (_VISIONARY[k] - _GUARDIAN[k]))
            for k in DIMENSIONS
        }
        target = ALPHA_MIN + t * (ALPHA_MAX - ALPHA_MIN)
        profiles.append(Profile(index=i, name=name, dimensions=dims,
                                target_orness=round(target, 3)))
    return profiles


_PROFILES: List[Profile] = _build_profiles()


def all_profiles() -> List[Profile]:
    """Lista de los 8 perfiles canónicos, de conservador a agresivo."""
    return list(_PROFILES)


def get_profile(name_or_index) -> Profile:
    """Recupera un perfil por nombre (case-insensitive) o por índice 0..7."""
    if isinstance(name_or_index, int):
        return _PROFILES[name_or_index]
    key = str(name_or_index).strip().lower()
    for p in _PROFILES:
        if p.name.lower() == key:
            return p
    raise KeyError(f"Perfil desconocido: {name_or_index!r}. "
                   f"Opciones: {', '.join(PROFILE_NAMES)}")


# --- Validación de concordancia (W de Kendall) -------------------------------
def kendall_w(ratings: Sequence[Sequence[float]]) -> float:
    """Coeficiente de concordancia W de Kendall.

    ``ratings``: matriz [m jueces × k ítems]. Devuelve W ∈ [0,1] (0 = sin
    acuerdo, 1 = acuerdo perfecto). Incluye corrección por empates.
    """
    R = np.asarray(ratings, dtype=float)
    if R.ndim != 2:
        raise ValueError("ratings debe ser una matriz [jueces × ítems].")
    m, k = R.shape
    if k < 2:
        raise ValueError("Se requieren al menos 2 ítems.")

    # Rangos por juez (promedio en empates).
    ranks = np.empty_like(R)
    tie_correction = 0.0
    for j in range(m):
        order = R[j].argsort()
        rr = np.empty(k, dtype=float)
        rr[order] = np.arange(1, k + 1)
        # Promediar rangos en valores empatados.
        vals, inv, counts = np.unique(R[j], return_inverse=True, return_counts=True)
        for vi, c in enumerate(counts):
            if c > 1:
                mask = inv == vi
                rr[mask] = rr[mask].mean()
                tie_correction += c ** 3 - c
        ranks[j] = rr

    rank_sums = ranks.sum(axis=0)
    mean_rs = rank_sums.mean()
    S = float(np.sum((rank_sums - mean_rs) ** 2))
    denom = m ** 2 * (k ** 3 - k) - m * tie_correction
    if denom <= 0:
        return 0.0
    return float(12.0 * S / denom)


def expert_agreement(csv_path: str, item_col: Optional[str] = None) -> Dict[str, float]:
    """Carga respuestas de expertos y calcula la concordancia (W de Kendall).

    El CSV debe tener una fila por juez y una columna por ítem (perfil o
    dimensión). Punto de entrada para la ronda formal de validación de OE2.
    """
    import pandas as pd

    df = pd.read_csv(csv_path)
    if item_col is not None and item_col in df.columns:
        df = df.drop(columns=[item_col])
    numeric = df.select_dtypes(include="number")
    W = kendall_w(numeric.to_numpy())
    return {"kendall_w": W, "n_jueces": int(numeric.shape[0]),
            "n_items": int(numeric.shape[1])}
