# Trazabilidad: Objetivos Específicos → código → evidencia

Tabla para el comité evaluador. Cada objetivo del anteproyecto se materializa en módulos concretos, con una
prueba ejecutable que lo evidencia.

| OE | Enunciado (anteproyecto) | Materialización en software | Archivo(s) | Prueba ejecutable |
|----|--------------------------|------------------------------|-----------|-------------------|
| **OE1** | Caracterizar el estado del arte / topología de la selección de portafolios bajo incertidumbre | Conjunto de criterios multicriterio y operadores que estructuran la decisión (marco alimentado por A1, "Trilema Irreducible") | `scoring.py`, `owa.py`, `docs/blueprint.md` | `pytest tests/test_owa.py` |
| **OE2** | Construir y validar una taxonomía difusa-OWA de 8 perfiles conductuales | 8 perfiles × 7 dimensiones; puente conductual→orness; concordancia (W de Kendall) | `profiles.py` | `pytest tests/test_profiles.py` |
| **OE3** | Diseñar el modelo adaptativo de recomendación OWA-difuso | IOWA inducido por VIX/EPU; modulación monótona del orness por estrés de régimen | `regimes.py`, `adaptive.py` | `pytest tests/test_adaptive.py` |
| **OE4** | Validar empíricamente y entregar software de código abierto | Backtest reproducible (Sharpe, MDD, RMSE), adaptativo vs estático; repo + tests + API + DOI | `backtest.py`, `recommender.py`, `api.py`, todo el repo | `python scripts/run_demo.py` |
| **A3** | Teorema de inversión multicriterio + corrección espectral | Índice de inversión y blanqueo espectral que restaura monotonía orness→riesgo | `spectral.py` | `pytest tests/test_spectral.py` |

## Cómo lo verifica el jurado en 4 pasos

1. `pip install -e .` — instala el paquete `owa_adaptive`.
2. `pytest` — todas las propiedades formales (OWA, perfiles, adaptación, no-inversión) en verde.
3. `python scripts/run_demo.py` — corre el pipeline completo offline y genera `outputs/reporte.html` + figuras.
4. `streamlit run app/streamlit_app.py` — explora en vivo: elige perfil y régimen, observa la cartera recomendada.

## Nota sobre validación "definitiva" de OE2

El anteproyecto contempla juicio experto humano (Likert + W de Kendall). El software incluye el **instrumento
computacional** (cálculo de W de Kendall, panel sintético reproducible) que ya respaldó el envío a congreso. La
ronda con expertos humanos se integra cargando sus respuestas en `profiles.expert_agreement()` — el código está
listo para recibir el CSV de expertos cuando se realice la ronda formal.
