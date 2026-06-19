# Manual de usuario — Asesor de inversión adaptativo OWA

**Software de la tesis doctoral de Diego Fernando Quintero Avellaneda**
Universidad Nacional de Colombia, Sede Manizales · Dir.: P. J. Ramírez-Angulo · Co-dir.: E. León-Castro

Este manual explica cómo instalar, abrir y usar el asistente, cómo interpretar lo que muestra y cómo resolver
problemas frecuentes. Está pensado tanto para el jurado evaluador como para cualquier usuario sin perfil técnico.

> Las figuras se guardan en `docs/img/`. Si alguna no aparece, captúrala siguiendo su pie de figura (ver
> [Apéndice: cómo añadir las capturas](#apéndice-cómo-añadir-las-capturas)).

---

## 1. ¿Qué es esta aplicación?

Es un **asistente de recomendación de portafolios** que demuestra la tesis central del proyecto:
**no solo el mercado es dinámico; el inversor también lo es.** El asistente:

1. clasifica al inversor en uno de **8 perfiles conductuales** a partir de un cuestionario,
2. construye un **portafolio a su medida** y le explica *por qué*,
3. lo deja **invertir y avanzar en el tiempo** para cosechar resultados, y
4. **reevalúa su perfil**: si la cosecha es buena, el optimismo eleva su apetito de riesgo, el inversor
   **migra de perfil** y su portafolio se reconfigura.

Funciona **offline** sobre un mercado sintético reproducible (semilla fija), por lo que da resultados idénticos
en cualquier computador y no necesita conexión ni claves.

---

## 2. Requisitos

- **Sistema operativo:** Windows 10/11 (también funciona en macOS/Linux con los comandos equivalentes).
- **Python 3.9 o superior** instalado y agregado al PATH.
  Para comprobarlo, abre PowerShell y ejecuta `python --version`. Si no responde una versión, instálalo desde
  <https://www.python.org/downloads/> marcando **"Add Python to PATH"**.
- Conexión a internet **solo la primera vez** (para descargar las dependencias).

---

## 3. Instalación (solo la primera vez)

### Opción A — con un doble clic (recomendada)

1. Abre la carpeta del proyecto: `D:\Downloads\repo_OWA`.
2. Haz doble clic en **`Iniciar_Asesor.bat`**.
   El script verifica Python, instala las dependencias (1–2 minutos) y abre el asistente.

### Opción B — manual (PowerShell)

```powershell
cd D:\Downloads\repo_OWA
pip install -e ".[all]"
```

Esto instala el paquete `owa_adaptive` y todo lo necesario (numpy, pandas, scipy, streamlit, etc.).

---

## 4. Abrir el asistente

Una vez instalado, **no hace falta reinstalar**. Para abrirlo:

- Haz doble clic en **`Abrir_Asesor.bat`**, o
- ejecútalo manualmente:

```powershell
cd D:\Downloads\repo_OWA
python -m streamlit run app/streamlit_app.py
```

Se abrirá en tu navegador en **<http://localhost:8501>**. Si no se abre solo, copia esa dirección en cualquier
navegador.

> **Deja abierta la ventana negra** (la consola) mientras usas el asistente: es el servidor. Para cerrarlo al
> terminar, simplemente cierra esa ventana.

---

## 5. Recorrido del asistente (los 5 pasos)

La barra superior muestra siempre el progreso:
`1·Perfiles → 2·Test → 3·Portafolio → 4·Resultados → 5·Reevaluación`.

### Paso 1 · Conoce los 8 perfiles

![Paso 1 — Los ocho perfiles conductuales y su orness](img/01_perfiles.png)
*Figura 1. Pantalla inicial: tarjetas de los 8 perfiles, de Guardian (orness 0.158, defensivo) a Visionary
(orness 0.865, agresivo).*

Aquí te familiarizas con la taxonomía. La **actitud** ante el riesgo se mide con el *orness* del operador OWA:
de **0** (defensivo, protege el capital) a **1** (agresivo, busca crecimiento). Cuando estés listo, pulsa
**"Comenzar el test"**.

### Paso 2 · Cuestionario de perfilamiento

![Paso 2 — Cuestionario de 7 preguntas](img/02_cuestionario.png)
*Figura 2. Siete preguntas (escala 1 a 7) sobre las dimensiones conductuales del inversor.*

Responde con sinceridad las **7 preguntas** (aversión a la pérdida, tolerancia al riesgo, horizonte, confianza,
comportamiento gregario, liquidez y aversión a la ambigüedad). Cada barra va de 1 a 7, con sus anclas (por
ejemplo, *"Casi nada" ⟵ … ⟶ "Muchísimo"*). El sistema convierte tus respuestas en un **orness** y te asigna el
perfil más cercano. Pulsa **"Clasificarme"**.

### Paso 3 · Tu perfil y tu portafolio (con el porqué)

![Paso 3 — Perfil asignado, portafolio y explicación](img/03_portafolio.png)
*Figura 3. Resultado del test (p. ej., Balancer · orness 0.50), portafolio recomendado, explicación en lenguaje
natural y comparación con un perfil más conservador y otro más agresivo.*

Esta pantalla muestra:

- **Tu perfil** y su orness (ejemplo: *Balancer · orness 0.50*).
- **Tu portafolio recomendado** (los activos y su peso).
- **El porqué**, en lenguaje natural y con datos: por ejemplo, *"tu portafolio se inclina hacia liquidez y
  momentum, y da menos peso a valor"*, acompañado de la gráfica de **exposición por criterio**.
- **La comparación clave:** el mismo mercado y fecha producen **carteras distintas** para un perfil más
  conservador, el tuyo y uno más agresivo. Esto evidencia que el operador OWA reordena las prioridades según la
  actitud.

Pulsa **"Invertir y avanzar el tiempo"**.

### Paso 4 · Resultados en el horizonte

![Paso 4 — Resultados del periodo frente al benchmark](img/04_resultados.png)
*Figura 4. Cosecha del periodo (p. ej., +11.90%), máxima caída y comparación con un benchmark equiponderado.*

Inviertes con tu cartera y dejas correr el tiempo (por defecto **126 días ≈ 6 meses**). Verás:

- **Cosecha (retorno del periodo):** lo que ganó o perdió tu cartera.
- **Máxima caída en el periodo (drawdown):** el peor bajón sufrido.
- **Benchmark equiponderado:** una cartera ingenua de referencia, para comparar.
- La **curva de capital** de tu cartera frente al benchmark.

Pulsa **"Reevaluar mi perfil"**.

### Paso 5 · Reevaluación — el inversor también es dinámico

![Paso 5 — Migración de perfil y reconfiguración del portafolio](img/05_reevaluacion.png)
*Figura 5. Tras una buena cosecha, el orness sube, el inversor migra de perfil (p. ej., Balancer → Strategist) y
el portafolio se reconfigura (activos que entran y salen). Abajo, la trayectoria del inversor.*

Aquí se ve la idea central de la tesis:

- **La actitud cambia:** una buena cosecha **eleva el orness** (más optimista y agresivo); una pérdida lo
  **reduce** (más prudente).
- **El inversor migra de perfil** (ejemplo real de la demo: *Balancer 0.50 → Strategist 0.65 → Pioneer 0.80 →
  Visionary 0.90* tras cosechas buenas sucesivas).
- **El portafolio se reconfigura:** la pantalla muestra el portafolio *antes* y *después*, y qué activos
  **entran** y **salen**.
- La **trayectoria** grafica cómo evolucionan el orness y la riqueza acumulada periodo a periodo.

Puedes **"Seguir invirtiendo otro periodo"** para encadenar más ciclos, o **"Empezar de nuevo"** para reiniciar.

---

## 6. La barra lateral (parámetros de la simulación)

Ajústalos **antes de empezar** el recorrido:

| Control | Qué hace |
|---|---|
| **N.º de activos** | Tamaño del universo de inversión sintético. |
| **Días de mercado** | Longitud de la serie histórica simulada. |
| **Semilla** | Fija la aleatoriedad: misma semilla ⇒ mismo mercado (reproducibilidad). Cámbiala para ver otra historia. |
| **Activos por portafolio** | Cuántos activos entran en la cartera (top-N). |
| **Horizonte por periodo** | Días que se mantiene la cartera en cada periodo (≈ meses). |
| **Adaptación al régimen de mercado (OE3)** | Si está activo, en mercados tensos (VIX/EPU altos) la cartera se vuelve más defensiva. |
| **Corrección espectral (A3)** | Evita la "inversión multicriterio": que un perfil conservador termine con más riesgo que uno agresivo. |
| **🔄 Reiniciar** | Vuelve al paso 1 y borra el progreso. |

> **Consejo:** para ver un camino donde alguna cosecha sea **negativa** (y el inversor migre hacia un perfil
> **más defensivo**), cambia la **semilla** o reduce el **horizonte**. El mecanismo es simétrico.

---

## 7. Cómo interpretar los resultados

- **Orness (0 a 1):** la actitud. Bajo = defensivo (pondera lo "peor" de cada activo, penaliza debilidades);
  alto = agresivo (pondera lo "mejor", busca crecimiento); 0.5 = equilibrado.
- **Cosecha:** retorno de tu cartera en el horizonte. La señal que actualiza tu perfil.
- **Máxima caída (drawdown):** medida de riesgo; cuánto cayó la cartera desde un máximo.
- **Benchmark equiponderado:** referencia neutra (todos los activos por igual). Superarlo indica que la
  selección por perfil aportó valor.
- **Exposición por criterio:** hacia qué factores se inclina tu cartera (momentum, baja volatilidad, valor,
  calidad, liquidez).
- **Trayectoria del inversor:** la evolución del orness y de la riqueza; ilustra que el inversor es dinámico.

---

## 8. La regla de la dinámica del inversor

Tras cada horizonte, la actitud se actualiza por sesgos conductuales (recencia / "dinero de la casa"):

```
orness_nuevo = recortar( orness + η · tanh(retorno_realizado / ref) ,  límite_inferior,  límite_superior )
```

Es decir: una buena cosecha sube el orness (hasta un tope) y una pérdida lo baja (hasta un piso), de forma suave
y acotada. El cambio de orness puede hacer que el inversor **migre** al perfil canónico más cercano. Los
parámetros por defecto (`η = 0.15`, `ref = 0.05`) son razonables y se pueden calibrar con literatura conductual.

---

## 9. Otras formas de usar el software (opcional)

- **Reporte automático (figuras + HTML):**
  ```powershell
  python scripts/run_demo.py
  ```
  Genera `outputs/reporte.html` con todas las figuras (paleta Okabe-Ito, 300 dpi).
- **API REST:**
  ```powershell
  uvicorn owa_adaptive.api:app --reload
  ```
  Documentación interactiva en <http://127.0.0.1:8000/docs> (endpoints `/profiles`, `/recommend`, `/backtest`).
- **Pruebas automáticas:**
  ```powershell
  pytest
  ```

---

## 10. Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `python` no se reconoce | Python no está instalado o no está en el PATH | Instala Python 3.9+ marcando "Add Python to PATH" y reinicia la terminal. |
| La consola pide un **correo** ("Welcome to Streamlit! … Email:") y se queda esperando | Es el mensaje del primer arranque de Streamlit | Usa **`Abrir_Asesor.bat`** (arranca en modo *headless* y omite ese mensaje) o pulsa Enter dejando el campo vacío. |
| El navegador no abre solo | Modo headless o navegador por defecto | Abre manualmente <http://localhost:8501>. |
| "Port 8501 is already in use" | Ya hay un asistente corriendo | Cierra la otra ventana negra, o usa otro puerto: `python -m streamlit run app/streamlit_app.py --server.port 8502`. |
| La instalación falla en algún paquete | Versión de Python muy nueva sin "ruedas" precompiladas | Instala una versión estable (p. ej., Python 3.11/3.12) y reintenta `pip install -e ".[all]"`. |
| La página queda en blanco o "cargando" | Streamlit aún está iniciando | Espera unos segundos y refresca; revisa que la ventana negra no muestre errores. |

---

## 11. Glosario

- **OWA (Ordered Weighted Averaging):** operador que agrega varios criterios ordenándolos y ponderándolos según
  una actitud.
- **Orness:** grado de optimismo del operador (0 = pesimista/defensivo, 1 = optimista/agresivo).
- **IOWA (Induced OWA):** variante en la que una variable externa (aquí, el régimen de mercado) decide el orden
  de ponderación.
- **Perfil conductual:** uno de los 8 tipos de inversor (Guardian → Visionary), definido por 7 dimensiones.
- **VIX / EPU:** señales de incertidumbre (volatilidad implícita / incertidumbre de política económica) que
  definen el **régimen** de mercado.
- **Corrección espectral:** técnica que decorrelaciona los criterios para evitar la inversión del inversor.
- **Drawdown:** caída desde un máximo; medida de riesgo.
- **Benchmark equiponderado:** cartera de referencia con todos los activos por igual.

---

## 12. Créditos y cita

Software desarrollado por **Diego Fernando Quintero Avellaneda** como parte de su tesis doctoral en
Administración (Universidad Nacional de Colombia, Sede Manizales). Licencia MIT. Para citar, ver `CITATION.cff`.

---

## Apéndice: cómo añadir las capturas

Las imágenes de las Figuras 1 a 5 deben guardarse en la carpeta `docs/img/` con estos nombres exactos:

`01_perfiles.png`, `02_cuestionario.png`, `03_portafolio.png`, `04_resultados.png`, `05_reevaluacion.png`.

Para capturarlas (Windows), con el asistente abierto en cada paso:

1. Pulsa **`Win + Shift + S`** (Recorte de pantalla).
2. Selecciona el área del asistente.
3. Pega en Paint (`Ctrl + V`) y guarda como PNG con el nombre indicado dentro de `docs/img/`.

Una vez guardadas, las figuras de este manual se mostrarán automáticamente.
