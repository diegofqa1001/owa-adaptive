"""API REST (FastAPI) que expone el motor de recomendación.

Arranque::

    uvicorn owa_adaptive.api:app --reload

Endpoints:
- ``GET  /profiles``            -> los 8 perfiles y su orness.
- ``POST /recommend``           -> cartera recomendada para el último día.
- ``GET  /backtest/{profile}``  -> métricas de backtest de un perfil.

FastAPI/uvicorn son dependencias opcionales (extra ``[api]``).
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "FastAPI/pydantic no están instalados. Instale el extra: pip install 'owa-adaptive[api]'."
    ) from exc

from .backtest import Backtester
from .data import generate_market
from .profiles import all_profiles, get_profile
from .recommender import Recommender

app = FastAPI(
    title="OWA Adaptive Recommender",
    version="1.0.0",
    description="Motor de recomendación adaptativo para portafolios bajo incertidumbre.",
)


@lru_cache(maxsize=1)
def _market():
    return generate_market()


class RecommendRequest(BaseModel):
    profile: str = Field(..., description="Nombre del perfil (Guardian..Visionary).")
    adaptive: bool = Field(True, description="Modular orness por régimen (OE3).")
    spectral: bool = Field(True, description="Aplicar corrección espectral (A3).")
    top_n: int = Field(10, ge=1, le=50, description="Activos en la cartera.")


class Holding(BaseModel):
    ticker: str
    weight: float


class RecommendResponse(BaseModel):
    profile: str
    date: str
    base_orness: float
    effective_orness: float
    stress: float
    holdings: List[Holding]


@app.get("/profiles")
def profiles():
    return [
        {"name": p.name, "index": p.index, "orness": p.target_orness,
         "dimensions": p.dimensions}
        for p in all_profiles()
    ]


@app.post("/recommend", response_model=RecommendResponse)
def recommend(req: RecommendRequest):
    try:
        prof = get_profile(req.profile)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    rec = Recommender(_market(), top_n=req.top_n, adaptive=req.adaptive,
                    spectral=req.spectral)
    out = rec.recommend_latest(prof)
    holdings = [Holding(ticker=t, weight=float(w))
                for t, w in out.top(req.top_n).items()]
    return RecommendResponse(
        profile=out.profile, date=str(out.date)[:10],
        base_orness=out.base_orness, effective_orness=out.effective_orness,
        stress=out.stress, holdings=holdings,
    )


@app.get("/backtest/{profile}")
def backtest(profile: str, adaptive: bool = True, spectral: bool = True):
    try:
        prof = get_profile(profile)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    bt = Backtester(_market(), adaptive=adaptive, spectral=spectral)
    res = bt.run(prof)
    return {"profile": res.profile, "metrics": res.metrics}
