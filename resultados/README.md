# Resultados precomputados (para revisión sin ejecutar código)

Estas figuras y el reporte se generan con `python scripts/run_demo.py` sobre el panel
sintético reproducible (semilla fija). Se incluyen aquí para que el jurado pueda revisar
los resultados directamente, sin necesidad de instalar nada. Todas las figuras usan la
paleta **Okabe-Ito** (segura para daltonismo), fondo blanco, 300 dpi.

| Archivo | Qué muestra | Objetivo |
|---|---|---|
| `reporte.html` | Informe autocontenido con todas las figuras y métricas | OE2–OE4 |
| `fig_orness.png` | Orness por perfil: actitud creciente de Guardian (defensivo) a Visionary (agresivo) | OE2 |
| `fig_stress.png` | Detección de régimen: el estrés s(t) sube en periodos de alta volatilidad | OE3 |
| `fig_equity.png` | Curvas de capital (backtest) por perfil | OE4 |
| `fig_adaptive.png` | Adaptativo vs estático: el adaptativo reduce el máximo drawdown | OE3/OE4 |
| `fig_inversion.png` | Corrección espectral (A3): índice de inversión multicriterio antes/después | A3 |

## Métricas de referencia (corrida con semilla 20260615)

- Índice de inversión sin corrección: **-0.595** → con corrección espectral: **-0.690** (A3).
- Máximo drawdown perfil Navigator — adaptativo: **-20.05%** vs estático: **-22.41%**.

Para reproducir: instalar el paquete (`pip install -e ".[all]"`) y ejecutar
`python scripts/run_demo.py`; los resultados son idénticos en cualquier máquina.
