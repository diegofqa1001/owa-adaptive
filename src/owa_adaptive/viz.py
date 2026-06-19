"""Visualizaciones con estética de tesis: paleta Okabe-Ito, fondo blanco.

Todas las funciones devuelven un objeto ``matplotlib.figure.Figure`` para poder
guardarlo a 300 dpi o incrustarlo en el dashboard/reporte. matplotlib es una
dependencia opcional (extra ``[viz]``).
"""
from __future__ import annotations

from typing import Dict, Optional, Sequence

import numpy as np

from .config import OKABE_ITO, apply_mpl_style

__all__ = [
    "plot_profiles_orness",
    "plot_stress",
    "plot_equity_curves",
    "plot_adaptive_vs_static",
    "plot_inversion",
    "save_fig",
]


def _mpl():
    try:
        import matplotlib.pyplot as plt
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "matplotlib no está instalado. Instale el extra: pip install 'owa-adaptive[viz]'."
        ) from exc
    apply_mpl_style()
    return plt


def plot_profiles_orness(profiles=None):
    """Barra del orness objetivo de los 8 perfiles."""
    from .profiles import all_profiles
    plt = _mpl()
    profiles = profiles or all_profiles()
    names = [p.name for p in profiles]
    orn = [p.target_orness for p in profiles]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.bar(names, orn, color=OKABE_ITO["blue"])
    ax.axhline(0.5, color=OKABE_ITO["vermillion"], linestyle="--", linewidth=1,
            label="Neutral (0.5)")
    ax.set_ylabel("Orness objetivo")
    ax.set_title("Actitud OWA por perfil conductual")
    ax.set_ylim(0, 1)
    ax.tick_params(axis="x", rotation=35)
    ax.legend()
    fig.tight_layout()
    return fig


def plot_stress(dates, stress, vix=None):
    """Serie temporal del estrés de régimen (y VIX opcional)."""
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(dates, stress, color=OKABE_ITO["vermillion"], label="Estrés de régimen s(t)")
    ax.fill_between(dates, 0, stress, color=OKABE_ITO["orange"], alpha=0.15)
    ax.set_ylabel("Estrés s(t) ∈ [0,1]")
    ax.set_ylim(0, 1)
    if vix is not None:
        ax2 = ax.twinx()
        ax2.plot(dates, vix, color=OKABE_ITO["sky_blue"], linewidth=0.9,
                alpha=0.8, label="VIX")
        ax2.set_ylabel("VIX")
        ax2.grid(False)
    ax.set_title("Detección de régimen desde señales de incertidumbre")
    ax.legend(loc="upper left")
    fig.tight_layout()
    return fig


def plot_equity_curves(results: Dict[str, "object"], subset: Optional[Sequence[str]] = None):
    """Curvas de capital de varios perfiles."""
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(9, 5))
    items = results.items()
    if subset is not None:
        items = [(k, results[k]) for k in subset if k in results]
    cycle = list(OKABE_ITO.values())
    for i, (name, res) in enumerate(items):
        ax.plot(res.equity.index, res.equity.values, label=name,
                color=cycle[i % len(cycle)])
    ax.set_ylabel("Capital (base 1.0)")
    ax.set_title("Curvas de capital por perfil (backtest)")
    ax.legend(ncol=2, fontsize=9)
    fig.tight_layout()
    return fig


def plot_adaptive_vs_static(compare: Dict[str, "object"]):
    """Compara curvas de capital adaptativo vs estático para un perfil."""
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(9, 5))
    a = compare["adaptive"]
    s = compare["static"]
    ax.plot(a.equity.index, a.equity.values, color=OKABE_ITO["bluish_green"],
            label=f"Adaptativo (MDD {a.metrics['max_drawdown']:.1%})")
    ax.plot(s.equity.index, s.equity.values, color=OKABE_ITO["vermillion"],
            linestyle="--", label=f"Estático (MDD {s.metrics['max_drawdown']:.1%})")
    ax.set_ylabel("Capital (base 1.0)")
    ax.set_title(f"Adaptativo vs estático — perfil {a.profile}")
    ax.legend()
    fig.tight_layout()
    return fig


def plot_inversion(orness_vals, risk_naive, risk_corr):
    """Dispersión orness→riesgo realizado, antes y después de la corrección."""
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(7.5, 5))
    ax.scatter(orness_vals, risk_naive, color=OKABE_ITO["vermillion"],
            label="Sin corrección", s=55, marker="o")
    ax.scatter(orness_vals, risk_corr, color=OKABE_ITO["bluish_green"],
            label="Corrección espectral", s=55, marker="s")
    ax.set_xlabel("Orness del perfil (apetito de riesgo)")
    ax.set_ylabel("Volatilidad realizada (anualizada)")
    ax.set_title("Inversión multicriterio: orness → riesgo")
    ax.legend()
    fig.tight_layout()
    return fig


def save_fig(fig, path: str, dpi: int = 300) -> str:
    """Guarda una figura a disco (300 dpi por defecto, fondo blanco)."""
    fig.savefig(path, dpi=dpi, bbox_inches="tight", facecolor="#FFFFFF")
    return path
