# Blueprint de arquitectura — `repo_OWA`
### Modelo adaptativo de recomendación para portafolios de renta variable bajo incertidumbre (OWA + perfiles conductuales)

**Autor:** Diego Fernando Quintero Avellaneda · **Dir.:** P. J. Ramírez-Angulo · **Co-dir.:** E. León-Castro
**Universidad Nacional de Colombia, Sede Manizales**

Este documento congela el alcance del software *antes* de implementarlo (regla "estructura antes de redactar" y
hito de junio del tablero de avance). Es el frente único que cierra **OE2** (validación definitiva), **OE3**
(componente adaptativo) y **OE4** (producto reproducible) e integra los hallazgos de los artículos A1–A3.

---

## 1. Objetivo del software

Construir un **motor de recomendación adaptativo** que, dado (i) un **perfil conductual de riesgo** (taxonomía
difusa-OWA de 8 perfiles, A2) y (ii) el **régimen de mercado** inferido de señales de incertidumbre (VIX/EPU),
recomiende una **cartera de renta variable** mediante agregación OWA inducida (IOWA), corrigiendo la **inversión
multicriterio** demostrada en A3 (corrección espectral), y se **valide empíricamente** vía backtesting reproducible.

El producto debe poder ejecutarse **end-to-end, offline y con un solo comando** el día de la defensa, sin depender
de servicios externos ni de claves. Esto se logra con un **panel sintético reproducible (semilla fija)** como
sustrato de validación por defecto, manteniendo cargadores opcionales de datos reales como ruta a fuente auditada.

---

## 2. Modelo matemático (resumen)

### 2.1 Operador OWA y orness
Para un vector de argumentos `a = (a_1,…,a_n)` y pesos `w = (w_1,…,w_n)`, `w_i ≥ 0`, `Σ w_i = 1`:

```
OWA(a; w) = Σ_i w_i · b_i ,   con b = sort_desc(a)
```

La **actitud** del agregador se mide con el *orness* (Yager, 1988):

```
orness(w) = (1/(n-1)) · Σ_{i=1}^{n} (n - i) · w_i ∈ [0, 1]
```

`orness = 1` → operador "max" (optimista/agresivo); `orness = 0` → "min" (pesimista/defensivo);
`orness = 0.5` → promedio (neutral).

### 2.2 Pesos por cuantificador lingüístico RIM
Los pesos se derivan de un cuantificador difuso *Regular Increasing Monotone* (RIM) `Q(r)` (Yager):

```
w_i = Q(i/n) − Q((i−1)/n)
```

Usamos la familia potencia `Q(r) = r^p`, `p > 0`. El exponente `p` controla la actitud: `p<1` → optimista,
`p>1` → pesimista. Para un **orness objetivo** `α*` resolvemos numéricamente (bisección) el `p` tal que
`orness(w(p)) = α*`. Esto da el puente **perfil → actitud → pesos**.

### 2.3 Perfiles conductuales (OE2)
Ocho perfiles ordenados de menor a mayor apetito de riesgo:
`Guardian → Sentinel → Custodian → Balancer → Navigator → Strategist → Pioneer → Visionary`,
con *orness* objetivo equiespaciado en **[0.158, 0.865]** (rango reportado en A2). Cada perfil se describe sobre
**7 dimensiones conductuales** (aversión a la pérdida, tolerancia al riesgo, horizonte temporal, exceso de
confianza, comportamiento gregario, preferencia por liquidez, aversión a la ambigüedad). El puente
**dimensiones → orness** se modela como una combinación lineal normalizada de las dimensiones (signos según
dirección teórica), de modo que la taxonomía no es solo etiquetas: el vector conductual *produce* la actitud OWA.

### 2.4 Componente adaptativo IOWA (OE3)
Sea `s(t) ∈ [0,1]` el **estrés de régimen** en el periodo `t`, derivado de VIX y EPU estandarizados
(combinación convexa, recortada a [0,1]). La actitud efectiva del perfil se contrae hacia un piso defensivo:

```
α_eff(t) = α_base − λ · s(t) · (α_base − α_floor) ,   λ ∈ [0,1]
```

En regímenes de estrés alto, `α_eff` baja (cartera más defensiva); en calma, `α_eff → α_base`. La agregación es
un **IOWA** (Yager & Filev): la variable inductora reordena/repondera los criterios en función del régimen. El
mecanismo es **monótono y auditable**: a mayor estrés, menor orness efectivo, nunca al revés.

### 2.5 Corrección espectral / teorema de inversión (A3)
A3 demuestra que, bajo cierta estructura de correlación entre criterios, el scoring multicriterio puede **invertir**
el ordenamiento de riesgo pretendido (un perfil conservador termina con una cartera más agresiva que uno
arriesgado). Definimos un **índice de inversión** como la correlación de rangos (Spearman) entre el *orness* del
perfil y el **riesgo realizado** de su cartera; idealmente debería ser positiva y monótona. La **corrección
espectral** decorrelaciona los criterios (blanqueo ZCA basado en la matriz de correlación de criterios) antes de
la agregación OWA, **eliminando la correlación que puede inducir la inversión**. El módulo reporta el índice
antes/después.

**Alcance (importante).** El blanqueo ZCA decorrelaciona los criterios de forma verificable. La **restauración
plena** de la monotonía `orness → riesgo` es el resultado del teorema de A3 bajo inversión *inducida por
correlación*, y se demuestra en **escenarios construidos** con esa estructura. En el panel sintético genérico el
índice de inversión solo **diagnostica** el efecto y puede permanecer negativo: la decorrelación por sí sola no
garantiza la corrección. La construcción del escenario A3 fiel está pendiente de alinearse con el método del
artículo A3.

### 2.6 Dinámica del inversor (lazo de realimentación conductual)
No solo el mercado es dinámico: el inversor también. Tras cada horizonte de inversión, la actitud se actualiza
por sesgos conductuales (recencia / "dinero de la casa"):

```
α_inv ← clip( α_inv + η · tanh(retorno_realizado / ref),  α_lo,  α_hi )
```

Una buena cosecha eleva el orness (optimismo → más agresivo) y puede **migrar el perfil** (p. ej.,
Navigator → Strategist), reconfigurando el portafolio; una pérdida lo reduce (prudencia → más defensivo). Es la
narrativa central del asistente (`investor.py` + `app/streamlit_app.py`).

### 2.7 Validación empírica (OE4)
Backtesting de ventana rodante sobre el panel: en cada periodo se calculan criterios (momentum, valor, baja
volatilidad, calidad, liquidez), se agregan vía OWA/IOWA según perfil y régimen, se construye la cartera (top-N o
peso ∝ score) y se acumulan retornos. Métricas: retorno acumulado, volatilidad, **Sharpe**, máximo drawdown, y
**RMSE** del riesgo predicho vs. realizado. Comparación **adaptativo vs. estático** y verificación de
no-inversión tras la corrección espectral.

---

## 3. Arquitectura de módulos

```
repo_OWA/
├── src/owa_adaptive/
│   ├── owa.py            # operador OWA, orness, pesos máx-entropía
│   ├── quantifiers.py    # cuantificadores RIM, solver de orness objetivo
│   ├── profiles.py       # 8 perfiles, 7 dimensiones, puente dims→orness   (OE2)
│   ├── regimes.py        # estrés de régimen desde VIX/EPU                  (OE3)
│   ├── adaptive.py       # IOWA inducido, modulación de orness             (OE3)
│   ├── spectral.py       # índice de inversión + corrección espectral      (A3)
│   ├── scoring.py        # criterios multicriterio por activo
│   ├── recommender.py    # motor end-to-end perfil+régimen→cartera
│   ├── investor.py       # dinámica del inversor: test, actualización conductual, migración
│   ├── backtest.py       # backtesting y métricas (RMSE, Sharpe, MDD)      (OE4)
│   ├── viz.py            # figuras Okabe-Ito, fondo blanco
│   ├── api.py            # FastAPI: /profiles, /recommend, /backtest
│   ├── config.py         # constantes, paleta Okabe-Ito, semilla global
│   └── data/
│       ├── synthetic.py  # panel sintético reproducible + VIX/EPU
│       └── loaders.py    # yfinance/CSV opcional (ruta a fuente auditada)
├── app/streamlit_app.py  # dashboard interactivo para la defensa
├── scripts/run_demo.py   # pipeline completo de un comando → figuras + reporte HTML
├── tests/                # pytest por módulo
├── paper/                # borrador JOSS (publicación OE4 opcional)
└── docs/                 # blueprint, mapeo OE, guía para el jurado
```

---

## 4. Trazabilidad OE → código (resumen; detalle en `OE_mapping.md`)

| OE del anteproyecto | Evidencia en el software | Archivos |
|---|---|---|
| **OE1** — estado del arte / topología | Marco que estructura criterios y operadores (alimentado por A1) | `scoring.py`, `docs/` |
| **OE2** — taxonomía difusa-OWA + validación | 8 perfiles, 7 dimensiones, puente dims→orness, W de Kendall | `profiles.py`, `tests/test_profiles.py` |
| **OE3** — modelo adaptativo OWA-difuso | IOWA inducido por VIX/EPU, modulación de orness | `regimes.py`, `adaptive.py` |
| **OE4** — validación empírica + software OSS | backtest, métricas, repo+tests+API+DOI | `backtest.py`, `recommender.py`, todo el repo |
| **A3** — teorema de inversión | índice de inversión + corrección espectral | `spectral.py` |

---

## 5. Decisiones de diseño

1. **Reproducibilidad primero.** Semilla global única (`config.SEED`). El panel sintético y todas las figuras se
   regeneran idénticos. El día de la defensa no hay dependencia de red.
2. **Determinismo numérico.** Solo `numpy/pandas/scipy`. Sin GPU, sin estado oculto.
3. **Datos reales opcionales.** `loaders.py` permite yfinance/CSV; documentado como deuda hacia fuente auditada.
4. **Separación motor / interfaz.** El núcleo no sabe nada de Streamlit ni FastAPI: la lógica es testeable de forma
   aislada; las interfaces solo orquestan.
5. **Estética de tesis.** Paleta **Okabe-Ito**, fondo blanco, sin dependencias de estilo externas.
6. **Verificabilidad por terceros.** Tests por módulo + demo de un comando + reporte HTML autocontenido, para que
   el jurado y la comunidad internacional reproduzcan los resultados sin fricción.

---

## 6. Plan de validación (lo que el jurado puede ejecutar)

| Prueba | Comando | Resultado esperado |
|---|---|---|
| Suite de tests | `pytest` | Todos verdes; propiedades OWA, monotonía, no-inversión |
| Demo completa | `python scripts/run_demo.py` | Figuras Okabe-Ito + `reporte.html` + métricas en consola |
| Dashboard | `streamlit run app/streamlit_app.py` | Selección de perfil/régimen → cartera recomendada en vivo |
| API | `uvicorn owa_adaptive.api:app` | `/recommend` devuelve cartera; `/backtest` métricas |

**Criterios de éxito (validación definitiva OE2/OE3/OE4):**
- El blanqueo ZCA decorrelaciona los criterios (verificable en `tests/test_spectral.py`).
- Monotonía `orness(perfil) → riesgo realizado` (Spearman ≥ 0.9) en el **escenario construido** A3 con inversión inducida por correlación (pendiente de implementar conforme al artículo A3).
- El adaptativo reduce el máximo drawdown frente al estático en regímenes de estrés.
- W de Kendall de concordancia de las dimensiones por perfil sobre el umbral de acuerdo.
