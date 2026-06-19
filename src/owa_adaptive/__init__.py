"""owa_adaptive — Motor de recomendación adaptativo OWA con perfiles conductuales.

Modelo adaptativo de recomendación para diseño de portafolios en renta variable
bajo incertidumbre, mediante operadores OWA/IOWA y perfiles conductuales de
riesgo. Tesis doctoral — Universidad Nacional de Colombia, Sede Manizales.

API pública principal::

    from owa_adaptive import (
        generate_market, all_profiles, get_profile,
        Recommender, Backtester, inversion_analysis,
    )
"""
from __future__ import annotations

from .config import OKABE_ITO, SEED, apply_mpl_style
from .owa import andness, dispersion, orness, owa, owa_matrix
from .quantifiers import max_entropy_weights, rim_weights, weights_for_orness
from .profiles import (
    DIMENSIONS,
    PROFILE_NAMES,
    Profile,
    all_profiles,
    get_profile,
    kendall_w,
    orness_from_dimensions,
)
from .regimes import RegimeResult, classify, regime, stress_index
from .adaptive import AdaptiveOWA, effective_orness, iowa
from .spectral import InversionReport, inversion_index, spectral_correction
from .scoring import CRITERIA, aggregate_scores, compute_criteria
from .recommender import Recommendation, Recommender
from .investor import (
    InvestorState,
    behavioral_update,
    classify_investor,
    explain_portfolio,
    invest_and_hold,
    nearest_profile,
    update_orness,
)
from .backtest import (
    BacktestResult,
    Backtester,
    compare_adaptive_static,
    inversion_analysis,
)
from .data import MarketData, generate_market

__version__ = "1.0.0"

__all__ = [
    "__version__",
    # config
    "SEED", "OKABE_ITO", "apply_mpl_style",
    # owa
    "owa", "owa_matrix", "orness", "andness", "dispersion",
    # quantifiers
    "weights_for_orness", "max_entropy_weights", "rim_weights",
    # profiles
    "Profile", "all_profiles", "get_profile", "orness_from_dimensions",
    "kendall_w", "PROFILE_NAMES", "DIMENSIONS",
    # regimes / adaptive
    "stress_index", "classify", "regime", "RegimeResult",
    "effective_orness", "iowa", "AdaptiveOWA",
    # spectral
    "spectral_correction", "inversion_index", "InversionReport",
    # scoring / recommender / backtest
    "CRITERIA", "compute_criteria", "aggregate_scores",
    "Recommender", "Recommendation",
    # investor dynamics
    "InvestorState", "classify_investor", "nearest_profile", "update_orness",
    "behavioral_update", "invest_and_hold", "explain_portfolio",
    "Backtester", "BacktestResult", "compare_adaptive_static", "inversion_analysis",
    # data
    "generate_market", "MarketData",
]
