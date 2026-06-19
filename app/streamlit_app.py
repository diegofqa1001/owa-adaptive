"""Asistente interactivo del motor de recomendación adaptativo OWA.

Recorrido guiado (amigable para el inversor y para el jurado):

  1. Conoce los 8 perfiles conductuales.
  2. Responde un cuestionario y el sistema te clasifica.
  3. Recibe tu portafolio y entiende **por qué** es ese (distinto para cada perfil).
  4. Invierte y avanza el tiempo: cosecha resultados en un horizonte.
  5. Reevaluación: si la cosecha fue buena, tu optimismo te vuelve más agresivo,
     migras de perfil y tu portafolio cambia. El inversor también es dinámico.

Ejecutar::

    streamlit run app/streamlit_app.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from owa_adaptive import generate_market, nearest_profile
from owa_adaptive.profiles import ALPHA_MAX, ALPHA_MIN, all_profiles, get_profile
from owa_adaptive.investor import (
    PROFILE_PHILOSOPHY,
    QUESTIONS,
    InvestorState,
    behavioral_update,
    classify_investor,
    explain_portfolio,
    invest_and_hold,
)
from owa_adaptive.recommender import Recommender

st.set_page_config(page_title="Asesor OWA Adaptativo", layout="wide",
                page_icon="🧭")

OKABE = {"blue": "#0072B2", "green": "#009E73", "orange": "#E69F00",
        "vermillion": "#D55E00", "sky": "#56B4E9", "purple": "#CC79A7"}


# ----------------------------------------------------------------------------- #
#  Utilidades                                                                    #
# ----------------------------------------------------------------------------- #
@st.cache_data(show_spinner=False)
def load_market(n_assets: int, n_days: int, seed: int):
    return generate_market(n_assets=n_assets, n_days=n_days, seed=seed)


def init_state():
    ss = st.session_state
    ss.setdefault("step", 1)
    ss.setdefault("answers", {dim: 4 for dim, *_ in QUESTIONS})
    ss.setdefault("investor", None)
    ss.setdefault("last_result", None)
    ss.setdefault("orness_path", [])
    ss.setdefault("wealth", 1.0)
    ss.setdefault("wealth_path", [])


def _rerun():
    """Compatibilidad entre versiones de Streamlit."""
    (st.rerun if hasattr(st, "rerun") else st.experimental_rerun)()


def goto(step: int):
    st.session_state.step = step
    _rerun()


def reset_all():
    for k in ["step", "answers", "investor", "last_result", "orness_path",
            "wealth", "wealth_path"]:
        st.session_state.pop(k, None)
    init_state()
    _rerun()


def portfolio_bar(portfolio: pd.Series, top: int = 10, color: str = OKABE["blue"]):
    s = portfolio[portfolio > 0].sort_values(ascending=False).head(top)
    return s.rename("peso")


def profile_badge(name: str, orness: float) -> str:
    return (f"<span style='background:{OKABE['blue']};color:#fff;padding:.2rem .6rem;"
            f"border-radius:6px;font-weight:600'>{name}</span> "
            f"<span style='color:#555'>orness {orness:.2f}</span>")


# ----------------------------------------------------------------------------- #
#  Barra lateral (configuración de la simulación)                               #
# ----------------------------------------------------------------------------- #
init_state()
with st.sidebar:
    st.header("⚙️ Simulación")
    st.caption("Mercado sintético reproducible. Ajusta antes de empezar.")
    n_assets = st.number_input("N.º de activos", 10, 100, 30, 5)
    n_days = st.number_input("Días de mercado", 800, 3000, 1500, 100)
    seed = st.number_input("Semilla", 0, 10**9, 20260615, 1)
    top_n = st.slider("Activos por portafolio", 4, 25, 10)
    horizon = st.slider("Horizonte por periodo (días ≈ meses)", 42, 252, 126, 21)
    adaptive = st.toggle("Adaptación al régimen de mercado (OE3)", value=True)
    spectral = st.toggle("Corrección espectral (A3)", value=True)
    st.divider()
    progreso = ["1·Perfiles", "2·Test", "3·Portafolio", "4·Resultados", "5·Reevaluación"]
    st.markdown("**Progreso**")
    st.markdown(" → ".join(
        f"**{p}**" if i + 1 == st.session_state.step else f"<span style='color:#999'>{p}</span>"
        for i, p in enumerate(progreso)), unsafe_allow_html=True)
    if st.button("🔄 Reiniciar"):
        reset_all()

market = load_market(int(n_assets), int(n_days), int(seed))
START_T = min(252, market.n_days - horizon - 2)

st.title("🧭 Asesor de inversión adaptativo OWA")
st.caption("Perfiles conductuales · OWA/IOWA · el mercado y el inversor son dinámicos. "
        "Universidad Nacional de Colombia, Sede Manizales.")

step = st.session_state.step


# ----------------------------------------------------------------------------- #
#  PASO 1 — Conoce los perfiles                                                  #
# ----------------------------------------------------------------------------- #
if step == 1:
    st.header("1 · Los 8 perfiles conductuales de riesgo")
    st.write("Cada inversor tiene una **actitud** ante el riesgo, que medimos con el "
            "*orness* del operador OWA: de 0 (defensivo, protege el capital) a 1 "
            "(agresivo, busca crecimiento). Estos son los ocho perfiles, de más "
            "conservador a más arriesgado:")
    profs = all_profiles()
    cols = st.columns(4)
    for i, p in enumerate(profs):
        with cols[i % 4]:
            st.markdown(
                f"""<div style='border:1px solid #ddd;border-radius:10px;padding:.8rem;
                    margin-bottom:.6rem;background:#fff;min-height:170px'>
                <div style='font-size:1.05rem;font-weight:700;color:{OKABE['blue']}'>{p.index+1}. {p.name}</div>
                <div style='color:#444;font-size:.85rem;margin:.3rem 0'>{PROFILE_PHILOSOPHY[p.name]}</div>
                <div style='font-size:.8rem;color:#666'>orness objetivo: <b>{p.target_orness:.3f}</b></div>
                </div>""", unsafe_allow_html=True)
    st.info("¿Cuál crees que eres? Hagamos el test para descubrirlo con tus respuestas.")
    if st.button("Comenzar el test →", type="primary"):
        goto(2)


# ----------------------------------------------------------------------------- #
#  PASO 2 — Cuestionario                                                         #
# ----------------------------------------------------------------------------- #
elif step == 2:
    st.header("2 · Cuestionario de perfilamiento")
    st.write("Responde con sinceridad (1 a 7). El sistema convertirá tus respuestas "
            "en una actitud OWA y te asignará un perfil.")
    answers = {}
    for dim, question, a1, a7 in QUESTIONS:
        answers[dim] = st.slider(question, 1, 7, st.session_state.answers.get(dim, 4),
                                help=f"1 = {a1}  ·  7 = {a7}")
        st.caption(f"⟵ {a1}  ·  {a7} ⟶")
    st.session_state.answers = answers
    c1, c2 = st.columns([1, 1])
    if c1.button("← Volver a perfiles"):
        goto(1)
    if c2.button("Clasificarme →", type="primary"):
        orn, prof = classify_investor(answers)
        st.session_state.investor = InvestorState(
            orness=orn, profile_name=prof.name, t=START_T, round=0, history=[])
        st.session_state.orness_path = [{"round": 0, "orness": orn, "profile": prof.name}]
        st.session_state.wealth = 1.0
        st.session_state.wealth_path = []
        goto(3)


# ----------------------------------------------------------------------------- #
#  PASO 3 — Tu perfil y tu portafolio (y por qué)                               #
# ----------------------------------------------------------------------------- #
elif step == 3:
    inv = st.session_state.investor
    if inv is None:
        goto(2)
    prof = get_profile(inv.profile_name)
    st.header("3 · Tu perfil y tu portafolio")
    st.markdown(f"Tu resultado: {profile_badge(inv.profile_name, inv.orness)}",
                unsafe_allow_html=True)
    st.write(f"**{inv.profile_name}** — {PROFILE_PHILOSOPHY[inv.profile_name]}")

    rec = Recommender(market, top_n=int(top_n), adaptive=adaptive, spectral=spectral)
    mine = rec.recommend_orness(inv.orness, inv.t, name=inv.profile_name)

    from owa_adaptive.scoring import compute_criteria
    from owa_adaptive.investor import portfolio_tilts
    crit = compute_criteria(market, inv.t, lookback=126)
    tilts = portfolio_tilts(crit, mine.portfolio)

    c1, c2 = st.columns([1.1, 1])
    with c1:
        st.subheader("Tu portafolio recomendado")
        st.bar_chart(portfolio_bar(mine.portfolio, top_n, OKABE["blue"]))
    with c2:
        st.subheader("¿Por qué este portafolio?")
        st.markdown(explain_portfolio(inv.orness, tilts))
        st.caption("Exposición de tu cartera por criterio (z-score ponderado):")
        st.bar_chart(tilts.rename("exposición"))

    # Comparación: el mismo mercado, distintos perfiles -> distintos portafolios.
    st.subheader("Cada perfil obtiene un portafolio diferente")
    o_cons = max(ALPHA_MIN, inv.orness - 0.18)
    o_aggr = min(ALPHA_MAX, inv.orness + 0.18)
    p_cons = nearest_profile(o_cons)
    p_aggr = nearest_profile(o_aggr)
    rc = rec.recommend_orness(o_cons, inv.t, name=p_cons.name)
    ra = rec.recommend_orness(o_aggr, inv.t, name=p_aggr.name)
    cc = st.columns(3)
    for col, label, r, o in [
        (cc[0], f"Más conservador ({p_cons.name})", rc, o_cons),
        (cc[1], f"TÚ ({inv.profile_name})", mine, inv.orness),
        (cc[2], f"Más agresivo ({p_aggr.name})", ra, o_aggr)]:
        with col:
            st.markdown(f"**{label}**  ·  orness {o:.2f}")
            st.bar_chart(portfolio_bar(r.portfolio, 6))
    st.caption("Mismo mercado, misma fecha: el operador OWA reordena las prioridades "
            "según la actitud, por eso las carteras difieren.")

    b1, b2 = st.columns([1, 1])
    if b1.button("← Repetir test"):
        goto(2)
    if b2.button("Invertir y avanzar el tiempo →", type="primary"):
        goto(4)


# ----------------------------------------------------------------------------- #
#  PASO 4 — Resultados en el horizonte                                          #
# ----------------------------------------------------------------------------- #
elif step == 4:
    inv = st.session_state.investor
    if inv is None:
        goto(2)
    st.header(f"4 · Resultados — periodo {inv.round + 1}")
    st.markdown(f"Inviertes como {profile_badge(inv.profile_name, inv.orness)} "
                f"y dejas correr el tiempo {horizon} días.", unsafe_allow_html=True)

    res = invest_and_hold(market, inv.orness, inv.t, horizon, top_n=int(top_n),
                        adaptive=adaptive, spectral=spectral, name=inv.profile_name)
    st.session_state.last_result = res

    # Benchmark equiponderado en la misma ventana.
    block = market.returns.iloc[inv.t + 1:res["end_t"] + 1]
    bench = (1.0 + block.mean(axis=1)).cumprod()

    eq = res["equity"]
    realized = res["realized_return"]
    dd = float((eq / eq.cummax() - 1.0).min())

    m1, m2, m3 = st.columns(3)
    m1.metric("Cosecha (retorno del periodo)", f"{realized:+.2%}")
    m2.metric("Máx. caída en el periodo", f"{dd:.2%}")
    m3.metric("Benchmark equiponderado", f"{float(bench.iloc[-1] - 1):+.2%}")

    chart_df = pd.DataFrame({"Tu cartera": eq, "Benchmark": bench})
    st.line_chart(chart_df)
    if realized >= 0:
        st.success(f"Buena cosecha: +{realized:.2%}. Veamos cómo eso cambia tu mentalidad.")
    else:
        st.warning(f"Cosecha negativa: {realized:.2%}. Veamos cómo eso cambia tu mentalidad.")

    if st.button("Reevaluar mi perfil →", type="primary"):
        goto(5)


# ----------------------------------------------------------------------------- #
#  PASO 5 — Reevaluación: el inversor es dinámico                               #
# ----------------------------------------------------------------------------- #
elif step == 5:
    inv = st.session_state.investor
    res = st.session_state.last_result
    if inv is None or res is None:
        goto(4)
    st.header("5 · Reevaluación — el inversor también es dinámico")

    realized = res["realized_return"]
    old_orness = inv.orness
    old_profile = inv.profile_name
    new_state = behavioral_update(inv, realized, new_t=res["end_t"])

    # Acumular trayectoria.
    st.session_state.wealth *= (1.0 + realized)
    st.session_state.wealth_path.append(
        {"periodo": inv.round + 1, "riqueza": st.session_state.wealth,
        "orness": new_state.orness, "perfil": new_state.profile_name})
    st.session_state.orness_path.append(
        {"round": new_state.round, "orness": new_state.orness,
        "profile": new_state.profile_name})

    delta = new_state.orness - old_orness
    migr = new_state.profile_name != old_profile
    c1, c2, c3 = st.columns(3)
    c1.metric("Actitud (orness)", f"{new_state.orness:.3f}", delta=f"{delta:+.3f}")
    c2.metric("Perfil", new_state.profile_name,
            delta=("cambió" if migr else "se mantiene"))
    c3.metric("Riqueza acumulada", f"{st.session_state.wealth:.2f}×")

    if realized >= 0 and delta > 0:
        st.success(f"Tu buena cosecha (+{realized:.2%}) elevó tu optimismo: el apetito "
                f"de riesgo sube (orness {old_orness:.2f} → {new_state.orness:.2f}). "
                + (f"**Migras de {old_profile} a {new_state.profile_name}**: ahora "
                    "tu cartera será más agresiva." if migr else
                    f"Sigues como {new_state.profile_name}, pero más cerca del siguiente nivel."))
    elif realized < 0 and delta < 0:
        st.warning(f"La pérdida ({realized:.2%}) aumentó tu prudencia: el apetito de "
                f"riesgo baja (orness {old_orness:.2f} → {new_state.orness:.2f}). "
                + (f"**Migras de {old_profile} a {new_state.profile_name}**: tu cartera "
                    "se vuelve más defensiva." if migr else
                    f"Sigues como {new_state.profile_name}, pero más cauteloso."))
    else:
        st.info(f"Tu actitud se ajusta levemente (orness {old_orness:.2f} → "
                f"{new_state.orness:.2f}).")

    # Antes vs después: el portafolio cambia.
    st.subheader("Tu portafolio se reconfigura")
    rec = Recommender(market, top_n=int(top_n), adaptive=adaptive, spectral=spectral)
    new_rec = rec.recommend_orness(new_state.orness, new_state.t, name=new_state.profile_name)
    old_port = res["recommendation"].portfolio
    cc = st.columns(2)
    with cc[0]:
        st.markdown(f"**Antes** — {old_profile} (orness {old_orness:.2f})")
        st.bar_chart(portfolio_bar(old_port, top_n, OKABE["sky"]))
    with cc[1]:
        st.markdown(f"**Después** — {new_state.profile_name} (orness {new_state.orness:.2f})")
        st.bar_chart(portfolio_bar(new_rec.portfolio, top_n, OKABE["green"]))

    entered = sorted(set(new_rec.portfolio[new_rec.portfolio > 0].index) -
                    set(old_port[old_port > 0].index))
    left = sorted(set(old_port[old_port > 0].index) -
                set(new_rec.portfolio[new_rec.portfolio > 0].index))
    st.caption(f"Entran al portafolio: {', '.join(entered) or '—'}  ·  "
            f"Salen: {', '.join(left) or '—'}")

    # Trayectoria del inversor.
    st.subheader("Trayectoria: cómo evoluciona el inversor")
    path = pd.DataFrame(st.session_state.orness_path).set_index("round")
    st.line_chart(path["orness"].rename("orness del inversor"))
    if st.session_state.wealth_path:
        wp = pd.DataFrame(st.session_state.wealth_path).set_index("periodo")
        st.line_chart(wp["riqueza"].rename("riqueza acumulada (×)"))
        st.dataframe(wp.style.format({"riqueza": "{:.3f}", "orness": "{:.3f}"}),
                    use_container_width=True)

    # Avanzar o terminar.
    st.session_state.investor = new_state
    enough_room = new_state.t < market.n_days - horizon - 2
    b1, b2 = st.columns([1, 1])
    if enough_room:
        if b1.button("Seguir invirtiendo otro periodo →", type="primary"):
            goto(4)
    else:
        b1.info("Se acabó el horizonte de mercado disponible.")
    if b2.button("🔄 Empezar de nuevo"):
        reset_all()
