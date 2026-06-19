# Nota de verificación

El repositorio se construyó con el entorno de ejecución (sandbox Linux) caído por falta de disco —el mismo
riesgo señalado en el tablero de avance—, por lo que la suite `pytest` **no se pudo correr en la sesión de
construcción**. En su lugar se hizo una revisión estática de coherencia. Al recibir el repo, el primer paso
recomendado es ejecutar `pytest` localmente: está diseñado para pasar en verde.

## Revisión estática realizada

- **Grafo de imports.** El paquete `owa_adaptive.__init__` solo importa el núcleo (numpy/pandas/scipy). Las
  dependencias opcionales (matplotlib, streamlit, fastapi) se importan de forma perezosa dentro de `viz`,
  `api`, `demo` y la app, nunca al importar el paquete. `scipy.stats` se usa con *fallback* en `spectral`.
- **Firmas cruzadas.** `Recommender`, `Backtester`, `compare_adaptive_static` e `inversion_analysis` se
  revisaron contra sus llamadas en `demo.py`, `api.py`, la app y los tests.
- **Propiedades numéricas comprobadas analíticamente:**
  - OWA con pesos uniformes = media; orness de max/min/uniforme = 1/0/0.5.
  - El cuantificador RIM y la solución de máxima entropía alcanzan el orness objetivo por bisección monótona.
  - El **blanqueo ZCA** deja la covarianza muestral en la identidad ⇒ correlación cruzada de criterios ≈ 0
    (verificado álgebraicamente: `W·C·W = I`).
  - La modulación adaptativa es estrictamente decreciente en el estrés y respeta el piso defensivo.
  - El **puente conductual→orness** usa calibración afín de dos puntos: reconstruye exactamente el orness
    objetivo de los 8 perfiles (Guardian = 0.158, Visionary = 0.865).
- **Reproducibilidad.** Toda la aleatoriedad deriva de `config.SEED`; `generate_market` es determinista.

## Pendiente al recuperar el entorno

1. `pip install -e ".[all]"` y `pytest` (se espera todo verde).
2. `python scripts/run_demo.py` y revisar `outputs/reporte.html`.
3. (Opcional, para publicar A3) recomputar figuras a 300 dpi —`viz.save_fig` ya las guarda a 300 dpi— y
   migrar de yfinance a fuente auditada vía `data.loaders`.
