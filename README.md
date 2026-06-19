# owa-adaptive · Motor de recomendación adaptativo OWA

Modelo adaptativo de recomendación para el diseño de portafolios en renta variable **bajo incertidumbre**,
mediante operadores **OWA/IOWA** y **perfiles conductuales de riesgo**. Software de la tesis doctoral de
Diego Fernando Quintero Avellaneda — Universidad Nacional de Colombia, Sede Manizales.

Este repositorio es el **frente único** que materializa y valida los objetivos específicos del anteproyecto:

| Objetivo | Qué entrega el software |
|---|---|
| **OE2** | Taxonomía difusa-OWA de 8 perfiles conductuales (7 dimensiones) + concordancia (W de Kendall). |
| **OE3** | Componente **adaptativo IOWA** inducido por el régimen de mercado (VIX/EPU). |
| **OE4** | **Validación empírica** (backtest) + producto de software de código abierto (tests, API, dashboard). |
| **A3**  | **Corrección espectral** que evita la inversión multicriterio del inversor. |

---

## Instalación

```bash
pip install -e ".[all]"     # núcleo + viz + dashboard + API + datos + tests
# o mínimo:
pip install -e .
```

Requiere Python ≥ 3.9. Dependencias núcleo: `numpy`, `pandas`, `scipy`.

## Verificación en 4 pasos (para el jurado)

```bash
pytest                                   # 1) propiedades formales en verde
python scripts/run_demo.py               # 2) pipeline completo offline -> outputs/reporte.html
streamlit run app/streamlit_app.py       # 3) asistente guiado (test -> portafolio -> invertir -> reevaluar)
uvicorn owa_adaptive.api:app --reload     # 4) API REST  (http://127.0.0.1:8000/docs)
```

Todo corre **offline** sobre un **panel sintético reproducible** (semilla fija), por lo que el resultado es
idéntico en cualquier máquina. No requiere claves ni conexión.

## Uso programático

```python
from owa_adaptive import generate_market, Recommender, Backtester, inversion_analysis

market = generate_market()                       # panel sintético reproducible
rec = Recommender(market, adaptive=True, spectral=True)
out = rec.recommend_latest("Navigator")          # cartera para el último día
print(out.effective_orness, out.top(10))

bt = Backtester(market, adaptive=True, spectral=True)
print(bt.run("Visionary").metrics)               # Sharpe, MDD, RMSE de vol, ...

print(inversion_analysis(market))                # índice de inversión antes/después (A3)
```

### Datos reales (opcional — ruta a fuente auditada)

```python
from owa_adaptive.data import load_prices_csv, market_from_prices
prices = load_prices_csv("precios_auditados.csv")     # [fechas × activos]
market = market_from_prices(prices)                   # VIX/EPU aproximados si faltan
```

## Estructura

```
src/owa_adaptive/   núcleo (owa, quantifiers, profiles, regimes, adaptive,
                    spectral, scoring, recommender, backtest, viz, api, data/)
app/                dashboard Streamlit
scripts/            demo de un comando
tests/              suite pytest por módulo
docs/               blueprint de arquitectura y mapeo OE -> código
paper/              borrador de artículo (JOSS, opcional)
```

## Reproducibilidad

- Semilla global única en `owa_adaptive.config.SEED`.
- Visualizaciones con paleta **Okabe-Ito** (daltónica-segura), fondo blanco, 300 dpi.
- Sin estado oculto ni dependencias de red en el camino por defecto.

## Cómo citar

Ver `CITATION.cff`. Licencia **MIT** (`LICENSE`).

## Documentación

- `docs/manual_usuario.md` — **manual de uso completo** (instalación, recorrido, interpretación, glosario).
- `docs/blueprint.md` — arquitectura y modelo matemático.
- `docs/OE_mapping.md` — trazabilidad objetivo → código → prueba.
- `docs/guia_jurado.md` — guía rápida para la evaluación.
