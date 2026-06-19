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
| `fig_inversion.png` | Índice de inversión multicriterio (A3) antes/después del blanqueo espectral (diagnóstico) | A3 |

## Métricas de referencia (corrida con semilla 20260615)

- Índice de inversión (Spearman orness→riesgo realizado) sin corrección: **-0.595** → con corrección espectral: **-0.690** (A3).
  El blanqueo ZCA decorrelaciona los criterios (verificable), pero **en este panel sintético genérico la
  decorrelación por sí sola no restaura la monotonía positiva**: el índice permanece negativo. La restauración
  plena corresponde al escenario construido del teorema A3 (pendiente de implementar conforme al artículo). Véase
  la nota de alcance en `src/owa_adaptive/spectral.py` y `docs/blueprint.md`.
- Máximo drawdown perfil Navigator — adaptativo: **-20.05%** vs estático: **-22.41%**.

Para reproducir: instalar el paquete (`pip install -e ".[all]"`) y ejecutar
`python scripts/run_demo.py`; los resultados son idénticos en cualquier máquina.
