"""Cargadores de datos reales (opcionales) — ruta hacia fuente auditada.

El sustrato por defecto del proyecto es el panel sintético (reproducible). Estos
cargadores permiten alimentar el motor con datos reales (CSV auditado o
yfinance) cuando hay conexión. Se mantienen deliberadamente simples y aislados:
el núcleo del modelo nunca depende de ellos.
"""
from __future__ import annotations

from typing import Optional, Sequence

import numpy as np
import pandas as pd

from ..config import TRADING_DAYS
from .synthetic import MarketData

__all__ = ["load_prices_csv", "load_yfinance", "market_from_prices"]


def load_prices_csv(path: str, date_col: Optional[str] = None) -> pd.DataFrame:
    """Carga un CSV de precios [fechas × activos] con índice de fechas."""
    df = pd.read_csv(path)
    if date_col is None:
        date_col = df.columns[0]
    df[date_col] = pd.to_datetime(df[date_col])
    df = df.set_index(date_col).sort_index()
    return df.astype(float)


def load_yfinance(tickers: Sequence[str], start: str, end: Optional[str] = None,
                  field: str = "Adj Close") -> pd.DataFrame:
    """Descarga precios de yfinance (requiere el extra ``[data]`` instalado)."""
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "yfinance no está instalado. Instale el extra: pip install 'owa-adaptive[data]'."
        ) from exc
    raw = yf.download(list(tickers), start=start, end=end, progress=False)
    if isinstance(raw.columns, pd.MultiIndex):
        prices = raw[field].copy()
    else:
        prices = raw[[field]].copy()
        prices.columns = list(tickers)[:1]
    return prices.dropna(how="all").astype(float)


def _proxy_fundamentals(prices: pd.DataFrame, returns: pd.DataFrame) -> pd.DataFrame:
    """Proxies estáticos de value/quality/liquidity a partir de precios.

    Documentados como aproximaciones: con datos reales conviene sustituirlos por
    fundamentales auditados. value = -retorno acumulado (contrarian);
    quality = -volatilidad; liquidity = -|retorno| medio.
    """
    cum_ret = prices.iloc[-1] / prices.iloc[0] - 1.0
    vol = returns.std() * np.sqrt(TRADING_DAYS)
    liq = returns.abs().mean()
    fund = pd.DataFrame({
        "value": -cum_ret,
        "quality": -vol,
        "liquidity": -liq,
    })
    return fund


def market_from_prices(prices: pd.DataFrame,
                      vix: Optional[pd.Series] = None,
                      epu: Optional[pd.Series] = None,
                      fundamentals: Optional[pd.DataFrame] = None,
                      vol_window: int = 21) -> MarketData:
    """Construye un :class:`MarketData` a partir de precios reales.

    Si no se aporta VIX, se aproxima con la volatilidad anualizada (ventana
    móvil) de un índice equiponderado. Si no se aporta EPU, se usa el VIX
    reescalado como sustituto neutro. Los fundamentales se aproximan desde
    precios salvo que se aporten.
    """
    prices = prices.sort_index().astype(float)
    returns = prices.pct_change().fillna(0.0)
    dates = prices.index

    if vix is None:
        idx_ret = returns.mean(axis=1)
        roll_vol = idx_ret.rolling(vol_window, min_periods=1).std()
        vix = (roll_vol * np.sqrt(TRADING_DAYS) * 100.0).rename("VIX")
        vix = vix.clip(lower=5.0)
    if epu is None:
        # Sustituto neutro: VIX normalizado a una escala tipo EPU.
        epu = ((vix - vix.mean()) / (vix.std() + 1e-9) * 30.0 + 120.0).rename("EPU")

    if fundamentals is None:
        fundamentals = _proxy_fundamentals(prices, returns)

    return MarketData(
        dates=dates, prices=prices, returns=returns,
        vix=vix.reindex(dates).ffill().bfill(),
        epu=epu.reindex(dates).ffill().bfill(),
        fundamentals=fundamentals,
        regime=np.zeros(len(dates), dtype=int),
    )
