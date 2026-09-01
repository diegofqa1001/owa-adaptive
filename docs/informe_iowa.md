# Informe de ejecución — componente adaptativo IOWA (§8.4.3)

**Fecha de ejecución:** 2026-08-31. **Snapshot de datos:** ver `data/MANIFEST.md`.
**Motor usado:** el paquete oficial archivado `owa-adaptive` (módulos
`recommender.py`, `adaptive.py`, `regimes.py`, `spectral.py`, `backtest.py`),
sin reimplementar ninguna pieza del núcleo. Se sustituyeron únicamente los
ocho perfiles genéricos de `profiles.py` (tabla equiespaciada del Artículo 2)
por los ocho perfiles canónicos y calibrados de la tesis (Capítulo 3 / Anexo
A): Guardián (0,158), Centinela (0,257), Pragmático (0,503), Estratega
(0,647), Aventurero (0,693), Analista (0,600), Innovador (0,738), Visionario
(0,865).

Parámetros: `lookback=252`, `rebalanceo=21`, `top_n=10`, `λ=0,85`
(`DEFAULT_LAMBDA`), `α_piso=0,12` (`DEFAULT_ALPHA_FLOOR`), ventana de estrés
causal de 252 días — todos los valores por defecto ya fijados en
`config.py` del repositorio archivado, sin recalibrar.

## Régimen inferido

El índice de estrés combina VIX y EPU (60/40, estandarización causal de 252
días, compresión logística). Fracción de ventanas por régimen (idéntica en
ambos mercados porque el régimen se infiere de señales macro globales):
calma 34,1 %, normal 31,8 %, estrés 23,7 %, crisis 10,2 %.

## Resultado 1 — Reducción de riesgo realizado (Diebold–Mariano)

Se comparó, ventana a ventana y perfil a perfil, la volatilidad realizada
(anualizada) del motor **adaptativo** (IOWA) contra el motor **estático**
(mismo motor, mismo perfil, sin modulación de régimen), mediante un
diferencial de pérdidas `d_t = vol_estático_t − vol_adaptativo_t` y su
estadístico t de Newey–West (H1: el adaptativo reduce el riesgo, `d̄ > 0`).

| Mercado | Ventanas de estrés/crisis: Δvol media | t (NW) | p (una cola) | Δmax-drawdown media | t (NW) | p (una cola) | Todas las ventanas: Δvol media | t (NW) | p |
|---|---|---|---|---|---|---|---|---|---|
| EE. UU. (S&P 500) | **+0,93 pp** | 3,46 | **0,0003** | +0,24 pp de caída máxima | 3,13 | **0,0009** | +0,92 pp | 6,64 | **<0,0001** |
| Colombia (BVC) | −0,17 pp | −0,88 | 0,81 (n. s.) | −0,01 pp | −0,14 | 0,55 (n. s.) | +0,10 pp | 1,07 | 0,14 (n. s.) |

**Lectura honesta.** En Estados Unidos, el componente IOWA cumple su promesa
de diseño: reduce de forma estadísticamente significativa la volatilidad
realizada y la profundidad de las caídas, precisamente en los regímenes de
estrés y crisis donde ese comportamiento defensivo importa. En Colombia, el
efecto tiene el signo correcto en la muestra completa pero **no alcanza
significancia estadística en ningún corte**: el mercado emergente, más
somero y concentrado, no ofrece evidencia suficiente de que la modulación por
régimen reduzca el riesgo realizado. Esta asimetría entre mercados profundos
y emergentes no estaba anticipada en el diseño formal de la §8.4.2 y se
declara aquí como un hallazgo, no como una limitación oculta.

## Resultado 2 — Coherencia condicional por régimen (Spearman entre orness y volatilidad, corte transversal por ventana)

Para cada ventana de rebalanceo se calculó la correlación de Spearman, **entre
los ocho perfiles**, de su orness (efectivo para el adaptativo, nominal para
el estático) contra su volatilidad realizada en esa ventana; luego se probó
la media de esas correlaciones dentro de cada partición de régimen con t de
Newey–West (H1: coherencia, ρ̄ > 0).

| Mercado | Motor | Calma/normal: ρ̄ | t (NW) | p | Estrés/crisis: ρ̄ | t (NW) | p |
|---|---|---|---|---|---|---|---|
| EE. UU. | Estático | 0,620 | 8,66 | **<0,0001** | 0,273 | 1,74 | **0,041** |
| EE. UU. | Adaptativo (IOWA) | 0,496 | 6,32 | **<0,0001** | **−0,252** | −1,57 | 0,94 (signo contrario) |
| Colombia | Estático | 0,050 | 0,51 | 0,30 (n. s.) | −0,085 | −0,61 | 0,73 (n. s.) |
| Colombia | Adaptativo (IOWA) | −0,200 | −1,84 | 0,97 (signo contrario) | −0,453 | −2,82 | 0,998 (signo contrario) |

**Lectura honesta — este es el resultado que más matiza la declaración de
diseño de la §8.4.2.** El criterio de éxito originalmente enunciado exigía que
la coherencia conductual (mayor orness → mayor volatilidad realizada,
consistentemente entre perfiles) **se preservara o no se degradara** en
estrés. En Estados Unidos eso no ocurre: la coherencia transversal es sólida
en calma (ρ̄ = 0,50, altamente significativa) pero se pierde y hasta cambia de
signo en estrés/crisis bajo el motor adaptativo — y, de forma reveladora, el
motor **estático** conserva mejor esa coherencia en estrés (ρ̄ = 0,27,
p = 0,041) que el adaptativo. En Colombia la coherencia transversal es débil
o nula incluso en el motor estático, de modo que no hay una línea base sólida
que el adaptativo pudiera preservar.

**Mecanismo identificado (Figura IOWA-2).** La causa es visible en el
diagrama de dispersión orness–volatilidad: al modular todos los perfiles
hacia el mismo piso defensivo (α_piso = 0,12) en función de un único estrés
de mercado agregado, el motor **comprime la dispersión transversal del orness
efectivo** precisamente cuando el estrés es alto (los ocho perfiles terminan
con orness efectivo mucho más parecido entre sí en crisis que en calma). Esa
compresión reduce la capacidad del orness efectivo para ordenar
correctamente el riesgo entre perfiles, aun cuando —como muestra el
Resultado 1— sí logra bajar el nivel absoluto de riesgo. En otras palabras:
el IOWA, tal como está calibrado (λ = 0,85, un solo piso común para los ocho
perfiles), **intercambia discriminación entre perfiles por protección
absoluta de nivel** en los momentos de mayor estrés.

## Resultado 3 — Verificación de la modulación (no es una prueba de hipótesis)

Por construcción algebraica, `α_efectivo(t) ≤ α_base` siempre que el estrés
sea positivo (Definición del §8.4.2 / `adaptive.py`). Esto se verificó: en el
100 % de las ventanas de estrés/crisis de ambos mercados, α_efectivo < α_base
(reducción media de 0,259 en EE. UU. y 0,263 en Colombia, t de Newey–West de
14,0 y 14,5 respectivamente). Este resultado confirma que la implementación
es fiel al diseño formal; no debe leerse como evidencia empírica adicional de
beneficio, porque la desigualdad es una consecuencia mecánica de la fórmula,
no un hallazgo contingente de los datos.

## Conclusión para el Capítulo 8 y síntesis honesta

1. El componente adaptativo IOWA **queda ejecutado** sobre datos reales
  versionados (snapshot fechado) con series auditadas de régimen (VIX/EPU vía
  FRED), cerrando el PENDIENTE de la §8.4.3 tal como estaba planteado.
2. La evidencia es **mixta, no uniformemente favorable**, y así se reporta:
  reduce significativamente el riesgo realizado en el mercado profundo
  (EE. UU.) pero no en el emergente (Colombia); y, en su calibración actual,
  sacrifica parte de la coherencia transversal entre perfiles durante el
  estrés a cambio de protección de nivel absoluto.
3. Esto matiza —sin invalidar— el diseño de la §8.4.2: el mecanismo de
  modulación funciona como amortiguador de riesgo agregado, pero su
  calibración (λ y piso comunes a los ocho perfiles) no está optimizada para
  preservar el ordenamiento conductual entre perfiles en crisis. Una
  extensión natural, señalada aquí como trabajo futuro y no ejecutada en esta
  corrida, es calibrar λ o el piso por perfil (o por dimensión de tolerancia
  a la ambigüedad) en lugar de usar un único piso global.
4. Los tres estadísticos de la §8.4.3 quedan reportados con su magnitud, su
  significancia y su mecanismo, en la misma tradición de honestidad
  metodológica que gobierna el resto de la tesis: se documenta lo que
  funciona, lo que no, y por qué.

Figuras: `fig_iowa_US_orness_modulation.png`, `fig_iowa_CO_orness_modulation.png`,
`fig_iowa_US_scatter.png`, `fig_iowa_CO_scatter.png`.
