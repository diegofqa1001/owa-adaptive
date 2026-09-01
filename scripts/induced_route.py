"""Corrida definitiva del componente adaptativo IOWA (Capitulo 8, S8.4.3).

Ejecutar desde la raiz del repositorio: python scripts/induced_route.py
Resultados: results/iowa/*.csv y *.json. Interpretacion: docs/informe_iowa.md.

Usa el motor OFICIAL archivado en el paquete owa-adaptive (src/owa_adaptive):
Recommender, Backtester, adaptive.effective_orness, regimes.stress_index /
classify, spectral.spectral_correction. No se reimplementa ninguna pieza del
nucleo del modelo; este script solo orquesta datos reales + el motor existente
y calcula las pruebas estadisticas de coherencia condicional pedidas en la
tesis.

Snapshot de datos: ver data/MANIFEST.md (fecha de descarga, fuentes, hashes).
"""
from __future__ import annotations

import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import numpy as np
import pandas as pd
from scipy import stats as sstats
import statsmodels.api as sm

from owa_adaptive.data.loaders import market_from_prices
from owa_adaptive.profiles import Profile
from owa_adaptive.recommender import Recommender
from owa_adaptive.regimes import regime as regime_fn
from owa_adaptive.config import DEFAULT_ALPHA_FLOOR, DEFAULT_LAMBDA, TRADING_DAYS

RNG_SEED = 20260615  # semilla global del paquete (config.SEED)
LOOKBACK = 252
REBALANCE = 21
TOP_N = 10
STRESS_WINDOW = 252

# --- Taxonomia canonica de la tesis (Capitulo 3 / Anexo A), NO la tabla
# generica equiespaciada que trae profiles.py por defecto (esa es la del
# Articulo 2, con nombres en ingles Guardian..Visionary y orness distintos).
THESIS_PROFILES = [
    Profile(index=0, name="Guardián",   dimensions={}, target_orness=0.158),
    Profile(index=1, name="Centinela",  dimensions={}, target_orness=0.257),
    Profile(index=2, name="Pragmático", dimensions={}, target_orness=0.503),
    Profile(index=3, name="Estratega",  dimensions={}, target_orness=0.647),
    Profile(index=4, name="Aventurero", dimensions={}, target_orness=0.693),
    Profile(index=5, name="Analista",   dimensions={}, target_orness=0.600),
    Profile(index=6, name="Innovador",  dimensions={}, target_orness=0.738),
    Profile(index=7, name="Visionario", dimensions={}, target_orness=0.865),
]


def load_market(price_csv: str, vix_csv: str, epu_csv: str) -> "MarketData":
    prices = pd.read_csv(price_csv, index_col=0, parse_dates=True).sort_index()
    prices = prices.dropna(axis=0, how="all").ffill().dropna(axis=1)

    vix = pd.read_csv(vix_csv)
    vix.columns = ["date", "VIXCLS"]
    vix["date"] = pd.to_datetime(vix["date"])
    vix = vix.set_index("date")["VIXCLS"].astype(float)
    vix = vix.reindex(prices.index).ffill().bfill()

    epu = pd.read_csv(epu_csv)
    epu.columns = ["date", "USEPUINDXM"]
    epu["date"] = pd.to_datetime(epu["date"])
    epu = epu.set_index("date")["USEPUINDXM"].astype(float)
    epu = epu.reindex(prices.index).ffill().bfill()

    return market_from_prices(prices, vix=vix, epu=epu)


def windowed_run(market, profile: Profile, adaptive: bool, lam: float = DEFAULT_LAMBDA,
                alpha_floor: float = DEFAULT_ALPHA_FLOOR):
    """Replica el bucle interno de Backtester.run pero devuelve granularidad
    por ventana (necesaria para las pruebas condicionales por régimen)."""
    rec = Recommender(market, top_n=TOP_N, lookback=LOOKBACK, adaptive=adaptive,
                    spectral=True, lam=lam, alpha_floor=alpha_floor,
                    stress_window=STRESS_WINDOW)
    n = market.n_days
    tickers = market.tickers
    R = market.returns
    rebal_days = list(range(LOOKBACK, n - 1, REBALANCE))

    rows = []
    for k, t0 in enumerate(rebal_days):
        t1 = rebal_days[k + 1] if k + 1 < len(rebal_days) else n - 1
        r = rec.recommend(profile, t0)
        w = r.portfolio.reindex(tickers).fillna(0.0).to_numpy()
        block = R.iloc[t0 + 1:t1 + 1]
        if block.shape[0] == 0:
            continue
        r_block = block.reindex(columns=tickers).to_numpy() @ w
        vol_w = float(np.std(r_block, ddof=0) * np.sqrt(TRADING_DAYS))
        cum = np.cumprod(1.0 + r_block)
        dd = float((cum / np.maximum.accumulate(cum) - 1.0).min()) if len(cum) else 0.0
        rows.append({
            "date": market.dates[t0], "profile": profile.name,
            "base_orness": profile.target_orness, "eff_orness": r.effective_orness,
            "stress": r.stress, "vol": vol_w, "maxdd": dd,
            "mean_ret": float(np.mean(r_block)) if len(r_block) else np.nan,
        })
    return pd.DataFrame(rows)


def newey_west_t(x: np.ndarray, maxlags: int | None = None):
    """t-estadístico de Newey-West para H0: media(x) = 0."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    T = len(x)
    if T < 5:
        return np.nan, np.nan, T
    if maxlags is None:
        maxlags = int(np.floor(4 * (T / 100.0) ** (2.0 / 9.0)))
        maxlags = max(maxlags, 1)
    model = sm.OLS(x, np.ones(T)).fit(cov_type="HAC", cov_kwds={"maxlags": maxlags})
    return float(model.tvalues[0]), float(model.pvalues[0]), T


def diebold_mariano(loss_static: np.ndarray, loss_adaptive: np.ndarray, maxlags: int | None = None):
    """DM: d_t = loss_static - loss_adaptive; H0: media(d)=0 (sin ventaja); H1: media(d)>0 (adaptativo gana)."""
    d = np.asarray(loss_static, dtype=float) - np.asarray(loss_adaptive, dtype=float)
    t, p_two, T = newey_west_t(d, maxlags)
    p_one = p_two / 2.0 if t > 0 else 1.0 - p_two / 2.0
    return {"dm_stat": t, "p_value_one_sided": p_one, "mean_diff": float(np.nanmean(d)), "T": T}


def cross_profile_spearman_by_window(df_all: pd.DataFrame) -> pd.DataFrame:
    """Para cada fecha de ventana, Spearman entre orness (across perfiles) y vol realizada."""
    out = []
    for date, g in df_all.groupby("date"):
        if g["eff_orness"].nunique() < 3:
            continue
        rho, _ = sstats.spearmanr(g["eff_orness"], g["vol"])
        out.append({"date": date, "rho": rho, "stress": g["stress"].mean(),
                    "regime": g["regime"].mode().iat[0] if "regime" in g else None})
    return pd.DataFrame(out).sort_values("date")


def run_market(name: str, price_csv: str, vix_csv: str, epu_csv: str) -> dict:
    market = load_market(price_csv, vix_csv, epu_csv)
    reg = regime_fn(market.vix.to_numpy(), market.epu.to_numpy(), window=STRESS_WINDOW)
    regime_by_date = pd.Series(reg.labels, index=market.dates)

    adap_frames, stat_frames = [], []
    for prof in THESIS_PROFILES:
        da = windowed_run(market, prof, adaptive=True)
        ds = windowed_run(market, prof, adaptive=False)
        da["regime"] = da["date"].map(regime_by_date)
        ds["regime"] = ds["date"].map(regime_by_date)
        adap_frames.append(da)
        stat_frames.append(ds)
    adap = pd.concat(adap_frames, ignore_index=True)
    stat = pd.concat(stat_frames, ignore_index=True)

    is_stress = adap["regime"].isin(["estres", "crisis"])
    is_calm = adap["regime"].isin(["calma", "normal"])

    # --- Test A: coherencia condicional (Spearman orness~vol por ventana, NW-t) ---
    rho_adap = cross_profile_spearman_by_window(adap)
    rho_stat = cross_profile_spearman_by_window(stat)

    def block_test(rho_df, mask_regimes):
        sub = rho_df[rho_df["regime"].isin(mask_regimes)]
        t, p, T = newey_west_t(sub["rho"].to_numpy())
        return {"mean_rho": float(sub["rho"].mean()) if len(sub) else np.nan,
                "nw_t": t, "p_value_one_sided": (p / 2 if t and t > 0 else (1 - p / 2 if p == p else np.nan)),
                "n_windows": int(len(sub))}

    testA = {
        "adaptive_stress": block_test(rho_adap, ["estres", "crisis"]),
        "adaptive_calm": block_test(rho_adap, ["calma", "normal"]),
        "static_stress": block_test(rho_stat, ["estres", "crisis"]),
        "static_calm": block_test(rho_stat, ["calma", "normal"]),
    }

    # --- Test B: adaptacion efectiva (alpha_eff < alpha_perfil en estres) ---
    stress_rows = adap[is_stress]
    diff = stress_rows["base_orness"] - stress_rows["eff_orness"]
    t_b, p_b, T_b = newey_west_t(diff.to_numpy())
    testB = {"mean_reduction": float(diff.mean()), "nw_t": t_b,
            "p_value_one_sided": (p_b / 2 if t_b > 0 else 1 - p_b / 2), "n": int(T_b),
            "frac_alpha_eff_lt_base": float((stress_rows["eff_orness"] < stress_rows["base_orness"]).mean())}

    # vol adaptativo vs estatico en ventanas de estres, pareado por perfil+fecha
    merged_stress = adap[is_stress].merge(
        stat[stat["regime"].isin(["estres", "crisis"])][["date", "profile", "vol", "maxdd"]],
        on=["date", "profile"], suffixes=("_adap", "_stat"))
    dm_vol_stress = diebold_mariano(merged_stress["vol_stat"], merged_stress["vol_adap"])
    dm_dd_stress = diebold_mariano(-merged_stress["maxdd_stat"], -merged_stress["maxdd_adap"])  # dd es negativo; -dd = magnitud de caida

    # --- Test C: Diebold-Mariano global (todas las ventanas) ---
    merged_all = adap.merge(stat[["date", "profile", "vol", "maxdd"]], on=["date", "profile"], suffixes=("_adap", "_stat"))
    dm_vol_all = diebold_mariano(merged_all["vol_stat"], merged_all["vol_adap"])

    return {
        "market": name,
        "n_days": int(market.n_days), "n_assets": int(market.n_assets),
        "regime_fractions": {lab: float(reg.fraction(lab)) for lab in ["calma", "normal", "estres", "crisis"]},
        "testA_coherencia_condicional": testA,
        "testB_adaptacion_efectiva": testB,
        "testC_diebold_mariano": {"stress_vol": dm_vol_stress, "stress_maxdd": dm_dd_stress, "all_windows_vol": dm_vol_all},
        "adap_df": adap, "stat_df": stat,
    }


if __name__ == "__main__":
    SNAP = os.path.join(os.path.dirname(__file__), "..", "data", "iowa_snapshot_2026-08-31")
    OUT = os.path.join(os.path.dirname(__file__), "..", "results", "iowa")
    os.makedirs(OUT, exist_ok=True)

    res_us = run_market("US", f"{SNAP}/us_prices_snapshot.csv", f"{SNAP}/vix_raw.csv", f"{SNAP}/epu_raw.csv")
    res_co = run_market("CO", f"{SNAP}/co_prices_snapshot.csv", f"{SNAP}/vix_raw.csv", f"{SNAP}/epu_raw.csv")

    for res in (res_us, res_co):
        res["adap_df"].to_csv(f"{OUT}/results_{res['market']}_adaptive_windows.csv", index=False)
        res["stat_df"].to_csv(f"{OUT}/results_{res['market']}_static_windows.csv", index=False)
        summary = {k: v for k, v in res.items() if k not in ("adap_df", "stat_df")}
        with open(f"{OUT}/results_{res['market']}_summary.json", "w") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
        print("====", res["market"], "====")
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))

    print("\nVer docs/informe_iowa.md para la interpretacion completa de estos resultados.")
