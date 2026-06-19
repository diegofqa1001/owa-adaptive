"""Pipeline de demostración de un comando: genera figuras + reporte HTML.

Reproduce, offline y con semilla fija, toda la evidencia que el jurado puede
revisar: actitud por perfil, detección de régimen, backtest por perfil,
adaptativo vs estático y corrección de la inversión multicriterio.
"""
from __future__ import annotations

import os
from typing import Optional

import numpy as np

from .backtest import Backtester
from .config import SEED
from .data import generate_market
from .profiles import all_profiles
from .regimes import stress_index


def _fmt_pct(x: float) -> str:
    return f"{x:.2%}" if np.isfinite(x) else "n/d"


def _fmt_num(x: float) -> str:
    return f"{x:.3f}" if np.isfinite(x) else "n/d"


def run(output_dir: str = "outputs", n_assets: int = 30, n_days: int = 1500,
        seed: int = SEED, make_figures: bool = True) -> dict:
    """Ejecuta la demostración completa. Devuelve un dict con resultados clave."""
    os.makedirs(output_dir, exist_ok=True)
    print(f"[1/5] Generando panel sintético reproducible (seed={seed}) ...")
    market = generate_market(n_assets=n_assets, n_days=n_days, seed=seed)
    stress = stress_index(market.vix.to_numpy(), market.epu.to_numpy(), window=252)

    print("[2/5] Backtest de los 8 perfiles (adaptativo + corrección espectral) ...")
    bt = Backtester(market, adaptive=True, spectral=True)
    results = bt.run_all()

    print("[3/5] Adaptativo vs estático (perfil Navigator) ...")
    from .backtest import compare_adaptive_static
    comp = compare_adaptive_static(market, "Navigator")

    print("[4/5] Análisis de inversión multicriterio (A3) ...")
    profiles = all_profiles()
    orn = [p.target_orness for p in profiles]
    bt_naive = Backtester(market, adaptive=True, spectral=False)
    bt_corr = Backtester(market, adaptive=True, spectral=True)
    risk_naive = [bt_naive.run(p).realized_risk for p in profiles]
    risk_corr = [bt_corr.run(p).realized_risk for p in profiles]
    from .spectral import inversion_index
    idx_naive = inversion_index(orn, risk_naive)
    idx_corr = inversion_index(orn, risk_corr)

    figures = {}
    if make_figures:
        print("[5/5] Generando figuras Okabe-Ito (300 dpi) y reporte HTML ...")
        try:
            from . import viz
            figures["orness"] = viz.save_fig(
                viz.plot_profiles_orness(profiles), os.path.join(output_dir, "fig_orness.png"))
            figures["stress"] = viz.save_fig(
                viz.plot_stress(market.dates, stress, market.vix.to_numpy()),
                os.path.join(output_dir, "fig_stress.png"))
            figures["equity"] = viz.save_fig(
                viz.plot_equity_curves(results), os.path.join(output_dir, "fig_equity.png"))
            figures["adaptive"] = viz.save_fig(
                viz.plot_adaptive_vs_static(comp), os.path.join(output_dir, "fig_adaptive.png"))
            figures["inversion"] = viz.save_fig(
                viz.plot_inversion(orn, risk_naive, risk_corr),
                os.path.join(output_dir, "fig_inversion.png"))
        except ImportError as exc:
            print(f"    (matplotlib no disponible: {exc}) — se omiten figuras.")
            make_figures = False

    report_path = _write_html(output_dir, results, comp, idx_naive, idx_corr,
                              figures if make_figures else {})
    print("\nResumen:")
    print(f"  Índice de inversión sin corrección : {idx_naive:.3f}")
    print(f"  Índice de inversión con corrección : {idx_corr:.3f}")
    print(f"  MDD adaptativo (Navigator): {comp['adaptive'].metrics['max_drawdown']:.2%}")
    print(f"  MDD estático   (Navigator): {comp['static'].metrics['max_drawdown']:.2%}")
    print(f"  Reporte: {report_path}")

    return {
        "market": market, "results": results, "compare": comp,
        "inversion_naive": idx_naive, "inversion_corrected": idx_corr,
        "report": report_path, "figures": figures,
    }


def _write_html(output_dir, results, comp, idx_naive, idx_corr, figures) -> str:
    rows = ""
    for name, res in results.items():
        m = res.metrics
        rows += (
            f"<tr><td>{name}</td>"
            f"<td>{_fmt_pct(m['ann_return'])}</td>"
            f"<td>{_fmt_pct(m['ann_vol'])}</td>"
            f"<td>{_fmt_num(m['sharpe'])}</td>"
            f"<td>{_fmt_pct(m['max_drawdown'])}</td>"
            f"<td>{_fmt_num(m['rmse_vol'])}</td>"
            f"<td>{_fmt_num(m['mean_orness_eff'])}</td></tr>\n"
        )

    def img(key, caption):
        if key in figures:
            fn = os.path.basename(figures[key])
            return f'<figure><img src="{fn}" style="max-width:100%"><figcaption>{caption}</figcaption></figure>'
        return ""

    fixed = "sí" if (idx_corr >= 0.9 and idx_corr > idx_naive) else "no (panel genérico)"
    html = f"""<!DOCTYPE html>
<html lang="es"><head><meta charset="utf-8">
<title>Reporte — Motor OWA Adaptativo</title>
<style>
 body{{font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;max-width:980px;
      margin:2rem auto;padding:0 1rem;color:#111;background:#fff;line-height:1.5}}
 h1{{color:#0072B2}} h2{{color:#0072B2;border-bottom:2px solid #56B4E9;padding-bottom:.2rem}}
 table{{border-collapse:collapse;width:100%;margin:1rem 0}}
 th,td{{border:1px solid #ccc;padding:.4rem .6rem;text-align:right}}
 th:first-child,td:first-child{{text-align:left}}
 th{{background:#f2f8fc}} figure{{margin:1.5rem 0}} figcaption{{color:#555;font-size:.9rem}}
 .kpi{{display:inline-block;background:#f2f8fc;border:1px solid #56B4E9;border-radius:8px;
      padding:.6rem 1rem;margin:.3rem}}
</style></head><body>
<h1>Motor de recomendación adaptativo OWA — reporte reproducible</h1>
<p>Panel sintético reproducible (semilla fija). Generado por
<code>scripts/run_demo.py</code>. Cierra OE2 (validación), OE3 (adaptativo) y OE4
(producto + validación empírica).</p>

<div>
 <span class="kpi"><b>Índice de inversión</b><br>sin corrección: {idx_naive:.3f}</span>
 <span class="kpi"><b>Índice de inversión</b><br>con corrección: {idx_corr:.3f}</span>
 <span class="kpi"><b>¿Monotonía restaurada?</b><br>{fixed}</span>
</div>

<h2>1. Actitud por perfil (OE2)</h2>
{img('orness', 'Orness objetivo de los 8 perfiles conductuales.')}

<h2>2. Detección de régimen (OE3)</h2>
{img('stress', 'Estrés de régimen s(t) derivado de VIX/EPU.')}

<h2>3. Backtest por perfil (OE4)</h2>
<table><thead><tr><th>Perfil</th><th>Retorno an.</th><th>Vol an.</th>
<th>Sharpe</th><th>Máx DD</th><th>RMSE vol</th><th>Orness ef. medio</th></tr></thead>
<tbody>
{rows}</tbody></table>
{img('equity', 'Curvas de capital por perfil.')}

<h2>4. Adaptativo vs estático (OE3)</h2>
{img('adaptive', 'El componente adaptativo reduce el drawdown en regímenes de estrés.')}

<h2>5. Corrección de la inversión multicriterio (Artículo 3)</h2>
{img('inversion', 'Índice de inversión (Spearman orness → riesgo realizado) antes y después del blanqueo espectral. La corrección decorrelaciona los criterios; el índice diagnostica la inversión multicriterio. En este panel sintético genérico la decorrelación por sí sola no restaura la monotonía positiva (ver nota de alcance en spectral.py).')}

<hr><p style="color:#777;font-size:.85rem">Quintero Avellaneda, D. — Universidad Nacional de Colombia, Sede Manizales.</p>
</body></html>"""
    path = os.path.join(output_dir, "reporte.html")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return path
