# Guía rápida para el jurado evaluador

Esta guía permite verificar, en pocos minutos y sin conexión, que el software cumple los objetivos del
anteproyecto. Todo se ejecuta sobre un panel sintético reproducible (semilla fija): los resultados son
idénticos en cualquier computador.

## Requisitos

- Python 3.9 o superior.
- Instalación: en la carpeta del repositorio, ejecutar `pip install -e ".[all]"`.

## 1. Pruebas formales (2 min)

```bash
pytest
```

Verifica propiedades matemáticas del operador OWA (rango, orness, monotonía), la calibración del cuantificador
RIM al orness objetivo, la reconstrucción conductual del orness (puente dimensiones→orness), la modulación
adaptativa, la decorrelación espectral y la reproducibilidad del panel.

## 2. Demostración completa (1 min)

```bash
python scripts/run_demo.py
```

Genera en `outputs/`:
- `reporte.html` — informe autocontenido con todas las figuras y métricas.
- `fig_orness.png`, `fig_stress.png`, `fig_equity.png`, `fig_adaptive.png`, `fig_inversion.png` (300 dpi).

Abrir `outputs/reporte.html` en el navegador. Puntos a observar:
- **Orness por perfil**: actitud creciente de Guardian (defensivo) a Visionary (agresivo).
- **Detección de régimen**: el estrés s(t) sube en los periodos de alta volatilidad.
- **Backtest**: tabla de Sharpe, volatilidad, drawdown y RMSE de volatilidad por perfil.
- **Adaptativo vs estático**: el adaptativo reduce el máximo drawdown.
- **Inversión (A3)**: el índice de inversión pasa de bajo/no-monótono a ≈ +1 tras la corrección espectral.

## 3. Asistente interactivo (en vivo, recomendado para la defensa)

```bash
streamlit run app/streamlit_app.py
```

Recorrido guiado de 5 pasos que cuenta la historia completa del modelo:

1. **Conoce los 8 perfiles** conductuales y su filosofía.
2. **Cuestionario**: 7 preguntas clasifican al inversor (cuestionario → orness → perfil).
3. **Tu portafolio y el porqué**: cartera recomendada con explicación en lenguaje natural y comparación lado a
   lado con un perfil más conservador y otro más agresivo (mismo mercado, carteras distintas).
4. **Invierte y avanza el tiempo**: se mantiene la cartera un horizonte y se cosechan resultados vs. un
   benchmark equiponderado.
5. **Reevaluación — el inversor es dinámico**: si la cosecha fue buena, el optimismo eleva el apetito de riesgo
   (sube el orness), el inversor **migra de perfil** y su portafolio se reconfigura (activos que entran/salen).
   Se puede repetir el ciclo y observar la **trayectoria del inversor** (orness y riqueza acumulada).

Demuestra la tesis central: **no solo el mercado es dinámico; el inversor también lo es.**

## 4. API REST (opcional)

```bash
uvicorn owa_adaptive.api:app --reload
```

Documentación interactiva en `http://127.0.0.1:8000/docs`. Endpoints: `/profiles`, `/recommend`, `/backtest/{perfil}`.

## Trazabilidad

La correspondencia objetivo específico → módulo de código → prueba ejecutable está en `docs/OE_mapping.md`.
El diseño y el modelo matemático, en `docs/blueprint.md`.
