"""Capa de datos: panel sintético reproducible y cargadores de datos reales."""
from .synthetic import MarketData, generate_market
from .loaders import load_prices_csv, load_yfinance, market_from_prices

__all__ = [
    "MarketData",
    "generate_market",
    "load_prices_csv",
    "load_yfinance",
    "market_from_prices",
]
