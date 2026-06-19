"""Ejemplo mínimo de uso del motor (ejecutar tras `pip install -e .`)."""
from owa_adaptive import (
    Backtester,
    Recommender,
    all_profiles,
    generate_market,
    inversion_analysis,
)

# 1) Panel sintético reproducible.
market = generate_market()

# 2) Recomendación para el último día, perfil Navigator.
rec = Recommender(market, adaptive=True, spectral=True)
out = rec.recommend_latest("Navigator")
print(f"Perfil {out.profile} | orness base {out.base_orness:.3f} "
    f"-> efectivo {out.effective_orness:.3f} (estrés {out.stress:.2f})")
print("Top-5 cartera:")
print(out.top(5).to_string())

# 3) Backtest del perfil más agresivo.
res = Backtester(market, adaptive=True, spectral=True).run("Visionary")
print("\nMétricas Visionary:", {k: round(v, 3) for k, v in res.metrics.items()})

# 4) ¿Se corrige la inversión multicriterio? (Artículo 3)
rep = inversion_analysis(market)
print(f"\nÍndice de inversión: sin corrección={rep.index_naive:.3f} | "
    f"con corrección={rep.index_corrected:.3f}")

# 5) Los 8 perfiles y su actitud.
print("\nTaxonomía:")
for p in all_profiles():
    print(f"  {p.index} {p.name:<10} orness={p.target_orness:.3f}")
