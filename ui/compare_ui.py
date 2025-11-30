# ui/compare_ui.py

import streamlit as st
from datetime import datetime, timedelta
import plotly.graph_objects as go

# --- Importaciones del core ---
from core.compare_pro import compare_pro
from core.etf_finder import suggest_etfs_by_keyword, get_etf_metadata
from core.fundamentals import fetch_fundamentals
from core.data_fetch import fetch_ohlc


# ======================================================
# 🟦 1) ETF FINDER UI
# ======================================================
def render_etf_finder_ui():
    st.header("🔎 ETF Finder por temática")

    query = st.text_input("Buscar temática o palabra clave (Ej: 'gold', 'metals', 'technology')")

    if not query:
        st.info("Ingresa una palabra clave para obtener sugerencias.")
        return

    suggestions = suggest_etfs_by_keyword(query, max_results=12)

    if not suggestions:
        st.warning("No se encontraron ETFs para esa temática.")
        return

    st.subheader("Resultados:")

    for s in suggestions:
        ticker = s.get("ticker")
        name = s.get("name")
        desc = s.get("desc")
        theme = s.get("theme", "—")

        cols = st.columns([1, 4, 1])

        with cols[0]:
            st.markdown(f"### **{ticker}**")

        with cols[1]:
            st.markdown(f"""
                **{name}**  
                {desc}  
                _Tema: {theme}_
            """)

        with cols[2]:
            if st.button(f"Ver {ticker}", key=f"etf_meta_{ticker}"):
                meta = get_etf_metadata(ticker)
                st.json(meta)

        st.divider()


# ======================================================
# 🟦 2) COMPARACIÓN PRO UI
# ======================================================
def render_compare_pro_ui():
    st.header("⚔️ Comparación Pro (2 tickers)")

    col1, col2 = st.columns(2)
    t1 = col1.text_input("Ticker A", "MELI.US")
    t2 = col2.text_input("Ticker B", "AMZN.US")

    col3, col4 = st.columns(2)
    from_date = col3.date_input("Desde:", datetime.now().date() - timedelta(days=365))
    to_date = col4.date_input("Hasta:", datetime.now().date())

    if st.button("Comparar"):
        result = compare_pro(t1.upper(), t2.upper(), from_date, to_date)

        if not result:
            st.error("No se pudieron obtener datos para la comparación.")
            return

        A = result["df_a"]
        B = result["df_b"]

        # -----------------------
        # Gráfico normalizado
        # -----------------------
        st.subheader("📈 Evolución Normalizada (%)")

        A["norm"] = (A["close"] / A["close"].iloc[0] - 1) * 100
        B["norm"] = (B["close"] / B["close"].iloc[0] - 1) * 100

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=A["date"], y=A["norm"], name=t1, mode="lines"))
        fig.add_trace(go.Scatter(x=B["date"], y=B["norm"], name=t2, mode="lines"))

        fig.update_layout(template="plotly_dark", height=350)
        st.plotly_chart(fig, use_container_width=True)

        # -----------------------
        # Indicadores
        # -----------------------
        st.subheader("📊 Indicadores técnicos (último valor)")

        indicators = ["SMA20", "SMA50", "EMA20", "RSI14"]

        def resume(df):
            return {ind: float(df[ind].iloc[-1]) if ind in df.columns else None for ind in indicators}

        st.write({
            t1: resume(A),
            t2: resume(B)
        })

        # -----------------------
        # Sentimiento
        # -----------------------
        st.subheader("🧠 Sentimiento comparado")

        st.write(result["sentiment"])

        # -----------------------
        # Fundamentales
        # -----------------------
        st.subheader("🏢 Fundamentales principales")

        st.json(result["fundamentals"])

        st.success("Comparación Pro generada correctamente.")


# ======================================================
# 🟦 3) COMPETIDORES UI
# ======================================================
def render_competitors_ui():
    st.header("🧭 Competidores automáticos")

    ticker = st.text_input("Ticker para buscar competidores", "MELI.US")

    if not ticker:
        return

    fundamentals, competitors = fetch_fundamentals(ticker.upper())

    st.subheader(f"Competidores sugeridos para {ticker.upper()}")

    if not competitors:
        st.info("No se encontraron competidores.")
        return

    st.write(", ".join(competitors))

    st.markdown("### Mini-perfiles:")

    for c in competitors[:8]:
        f, _ = fetch_fundamentals(c)

        # Intentamos obtener precio reciente
        try:
            df = fetch_ohlc(
                c,
                from_date=datetime.now().date() - timedelta(days=30),
                to_date=datetime.now().date()
            )
            price = df["close"].iloc[-1] if not df.empty else None
        except:
            price = None

        pe = f.get("PERatio") if f else None

        cols = st.columns([1, 2, 1])

        with cols[0]:
            st.markdown(f"### {c}")

        with cols[1]:
            st.write(f"- **Último precio:** {price}")
            st.write(f"- **P/E:** {pe}")

        with cols[2]:
            if st.button(f"Ver {c}", key=f"comp_view_{c}"):
                st.json(f)

        st.divider()
