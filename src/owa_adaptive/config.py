"""Constantes globales, semilla y paleta Okabe-Ito.

Centralizar aquí garantiza reproducibilidad: un único punto de control para la
semilla y la estética. Importado por todos los módulos que generan aleatoriedad
o figuras.
"""
from __future__ import annotations

# --- Reproducibilidad ---------------------------------------------------------
SEED: int = 20260615
"""Semilla global. Todo proceso estocástico la deriva de aquí."""

# --- Paleta Okabe-Ito (daltónica-segura), fondo blanco ------------------------
# Orden estándar Okabe & Ito (2008).
OKABE_ITO = {
    "black":        "#000000",
    "orange":       "#E69F00",
    "sky_blue":     "#56B4E9",
    "bluish_green": "#009E73",
    "yellow":       "#F0E442",
    "blue":         "#0072B2",
    "vermillion":   "#D55E00",
    "reddish_purple": "#CC79A7",
    "grey":         "#999999",
}
OKABE_ITO_CYCLE = [
    "#E69F00", "#56B4E9", "#009E73", "#F0E442",
    "#0072B2", "#D55E00", "#CC79A7", "#000000",
]
FIGURE_FACECOLOR = "#FFFFFF"
AXES_FACECOLOR = "#FFFFFF"

# --- Parámetros por defecto del modelo ---------------------------------------
DEFAULT_ALPHA_FLOOR: float = 0.12
"""Piso de orness defensivo al que converge el adaptativo en estrés máximo."""

DEFAULT_LAMBDA: float = 0.85
"""Intensidad de la modulación adaptativa (0 = estático, 1 = máxima reacción)."""

DEFAULT_TOP_N: int = 10
"""Número de activos en la cartera por defecto."""

TRADING_DAYS: int = 252
"""Días de negociación por año (anualización)."""


def apply_mpl_style() -> None:
    """Aplica el estilo de figuras de la tesis (Okabe-Ito, fondo blanco).

    Seguro de llamar aunque matplotlib no esté instalado (no-op silencioso).
    """
    try:
        import matplotlib as mpl
        from cycler import cycler
    except Exception:  # pragma: no cover - matplotlib opcional
        return
    mpl.rcParams.update({
        "figure.facecolor": FIGURE_FACECOLOR,
        "axes.facecolor": AXES_FACECOLOR,
        "savefig.facecolor": FIGURE_FACECOLOR,
        "axes.prop_cycle": cycler(color=OKABE_ITO_CYCLE),
        "axes.grid": True,
        "grid.color": "#DDDDDD",
        "grid.linewidth": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "font.size": 11,
        "figure.dpi": 110,
        "savefig.dpi": 300,
    })
