# ui/dashboard_ui.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime, timedelta, time, date

from core.favorites import (
    load_favorites,
    add_favorite as persist_add_favorite,
    remove_favorite as persist_remove_favorite,
    clear_favorites as persist_clear_favorites
)

# ======================================================
# DEMO DATA
# ======================================================
STOCK_TICKERS = {
    "Microsoft": "MSFT.US",
    "Apple": "AAPL.US",
    "Google": "GOOGL.US",
    "Amazon": "AMZN.US",
    "Galicia": "GGAL.BA"
}

CRYPTO_TICKERS = {
    "Bitcoin": "BTC.CRYPTO",
    "Ethereum": "ETH.CRYPTO",
    "Solana": "SOL.CRYPTO"
}

ETF_THEMES = [
    "Technology", "Energy", "Healthcare",
    "Artificial Intelligence", "Fintech", "Space"
]

PRICE_ALERTS = {
    "MSFT.US": ("Precio excesivamente alto", "#00ff99"),
    "GGAL.BA": ("Precio muy bajo", "#ff4d4d")
}

SMART_ALERTS = {
    "BTC.CRYPTO": {"pump": True, "volatility": 18, "rapid_move": True},
    "ETH.CRYPTO": {"volatility": 9},
}

ASSET_FLAGS = {
    "BTC.CRYPTO": ["Alta volatilidad", "Demo data"],
    "GGAL.BA": ["Mercado local", "Demo data"],
}

# ======================================================
# HELPERS
# ======================================================
def market_status(t):
    now = datetime.now().time()
    if t.endswith(".CRYPTO"):
        return "🟣 Cripto 24/7"
    if t.endswith(".BA"):
        return "🟢 BYMA abierto" if time(11, 0) <= now <= time(17, 0) else "🔴 BYMA cerrado"
    return "🟢 Wall Street abierto" if time(9, 30) <= now <= time(16, 0) else "🔴 Wall Street cerrado"


def demo_ohlc(start, end):
    days = max((end - start).days, 30)
    dates = pd.date_range(start=start, periods=days)
    price = 100 + np.cumsum(np.random.randn(days))
    df = pd.DataFrame({
        "date": dates,
        "open": price + np.random.randn(days),
        "close": price,
    })
    df["high"] = df[["open", "close"]].max(axis=1) + abs(np.random.randn(days))
    df["low"] = df[["open", "close"]].min(axis=1) - abs(np.random.randn(days))
    df["SMA20"] = df["close"].rolling(20).mean()
    df["EMA20"] = df["close"].ewm(span=20).mean()
    return df


def risk_score(t):
    score = 20 if t.endswith(".CRYPTO") else 10
    alerts = SMART_ALERTS.get(t, {})
    if alerts.get("pump"):
        score += 30
    if alerts.get("volatility", 0) > 15:
        score += 20
    return min(score, 100)


def demo_overview(t):
    return {
        "executive": {
            "Ticker": t,
            "Sector": "Technology",
            "Score Global": round(np.random.uniform(40, 90), 2)
        },
        "fundamentals": {
            "Revenue": "1200M",
            "Profit": "260M",
            "Debt": "Low",
            "ROE": "18%"
        },
        "competitors": ["AAPL", "GOOGL", "AMZN"],
        "news": [
            {"title": "Strong growth outlook", "sentiment": 0.7},
            {"title": "Analysts cautious short term", "sentiment": -0.3}
        ]
    }


# ======================================================
# STATE INIT
# ======================================================
def init_state():
    if "username" not in st.session_state:
        st.session_state.username = "demo_user"

    if "selected_ticker" not in st.session_state:
        st.session_state.selected_ticker = None

    if "favorites" not in st.session_state:
        st.session_state.favorites = load_favorites(st.session_state.username)

    if "scores" not in st.session_state:
        st.session_state.scores = {}

    if "preferences" not in st.session_state:
        st.session_state.preferences = {
            "time_range": "3M",
            "max_risk": 100,
            "order_by": "Score"
        }

    if "confirm_delete_one" not in st.session_state:
        st.session_state.confirm_delete_one = None

    if "confirm_delete_all" not in st.session_state:
        st.session_state.confirm_delete_all = False


# ======================================================
# DASHBOARD
# ======================================================
ENABLE_ETF_FINDER = True

def show_dashboard():
    init_state()
    st.title("📊 AppFinanzAr")

    # ================= SIDEBAR =================
    with st.sidebar:
        st.subheader("🕒 Estado del mercado")
        if st.session_state.selected_ticker:
            st.write(market_status(st.session_state.selected_ticker))
        else:
            st.caption("Seleccioná un activo")

        st.divider()

    
        # ---------- FAVORITOS ----------
        st.subheader("⭐ Favoritos")

        if st.session_state.favorites:
            for f in st.session_state.favorites:
                c1, c2 = st.columns([8, 1])

                if c1.button(f, key=f"fav_nav_{f}"):
                    st.session_state.selected_ticker = f
                    st.rerun()

                if c2.button("❌", key=f"fav_del_{f}"):
                    st.session_state.confirm_delete_one = f

            # --- confirmación eliminar uno ---
            if st.session_state.confirm_delete_one:
                st.warning(
                    f"¿Eliminar {st.session_state.confirm_delete_one}?"
                )
                y, n = st.columns(2)

                if y.button("Sí, eliminar"):
                    persist_remove_favorite(
                        st.session_state.username,
                        st.session_state.confirm_delete_one
                    )
                    st.session_state.favorites.remove(
                        st.session_state.confirm_delete_one
                    )
                    st.session_state.confirm_delete_one = None
                    st.rerun()

                if n.button("Cancelar"):
                    st.session_state.confirm_delete_one = None

            st.divider()

            # --- acciones globales ---
            if st.button("🧹 Eliminar todos"):
                persist_clear_favorites(st.session_state.username)
                st.session_state.favorites = []
                st.session_state.selected_ticker = None
                st.rerun()

            csv = pd.DataFrame(
                st.session_state.favorites,
                columns=["Ticker"]
            ).to_csv(index=False)

            st.download_button(
                "⬇ Exportar favoritos",
                csv,
                "favoritos.csv"
            )

        else:
            st.caption("No tenés favoritos todavía")

              # ---------- BUSCAR EMPRESA ----------
        st.subheader("🔍 Buscar empresa")
        company = st.selectbox("Empresa", [""] + list(STOCK_TICKERS.keys()))
        if company:
            if st.button("Ver"):
                st.session_state.selected_ticker = STOCK_TICKERS[company]

        st.divider()

        # ---------- BUSCAR CRIPTO ----------
        st.subheader("🟣 Buscar cripto")
        crypto = st.selectbox("Cripto", [""] + list(CRYPTO_TICKERS.keys()))
        if crypto:
            if st.button("Ver cripto"):
                st.session_state.selected_ticker = CRYPTO_TICKERS[crypto]

    # ================= MAIN =================
    if not st.session_state.selected_ticker:
        st.info("👈 Seleccioná un activo")
        return

    ticker = st.session_state.selected_ticker

    # ---------- FAVORITO (TOGGLE) ----------
    is_fav = ticker in st.session_state.favorites

    fav_label = (
        "⭐ Quitar de favoritos"
        if is_fav
        else "⭐ Agregar a favoritos"
    )

    if st.button(fav_label):
        if is_fav:
            persist_remove_favorite(
                st.session_state.username, ticker
            )
            st.session_state.favorites.remove(ticker)
        else:
            persist_add_favorite(
                st.session_state.username, ticker
            )
            st.session_state.favorites.append(ticker)

        st.rerun()


    # ---------- FLAGS ----------
    for f in ASSET_FLAGS.get(ticker, []):
        st.warning(f)

    # ---------- RANGO TEMPORAL ----------
    st.subheader("📅 Rango temporal")
    today = date.today()

    if "start_date" not in st.session_state:
        st.session_state.start_date = today - timedelta(days=90)
    if "end_date" not in st.session_state:
        st.session_state.end_date = today

    ranges = {
        "1M": 30, "3M": 90, "6M": 180, "1Y": 365
    }

    cols = st.columns(len(ranges) + 1)
    for i, (label, days) in enumerate(ranges.items()):
        if cols[i].button(label):
            st.session_state.start_date = today - timedelta(days=days)
            st.session_state.end_date = today

    if cols[-1].button("📅"):
        c1, c2 = st.columns(2)
        st.session_state.start_date = c1.date_input(
            "Desde", st.session_state.start_date
        )
        st.session_state.end_date = c2.date_input(
            "Hasta", st.session_state.end_date
        )

    df = demo_ohlc(st.session_state.start_date, st.session_state.end_date)

    fig = go.Figure()
    fig.add_candlestick(
        x=df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"]
    )
    fig.add_scatter(x=df["date"], y=df["SMA20"], name="SMA 20")
    fig.add_scatter(x=df["date"], y=df["EMA20"], name="EMA 20")
    st.plotly_chart(fig, use_container_width=True)

    # ---------- FAVORITO ----------
    if st.button("⭐ Agregar a favoritos"):
        if ticker not in st.session_state.favorites:
            persist_add_favorite(st.session_state.username, ticker)
            st.session_state.favorites.append(ticker)

        if ticker not in st.session_state.scores:
            st.session_state.scores[ticker] = round(
                np.random.uniform(40, 90), 2
            )

    # ---------- OVERVIEW ----------
    ov = demo_overview(ticker)
    st.subheader("📋 Resumen ejecutivo")
    st.json(ov["executive"])

    st.subheader("📰 Noticias & Sentimiento")
    for n in ov["news"]:
        s = n["sentiment"]
        if s > 0.2:
            st.success(n["title"])
        elif s < -0.2:
            st.error(n["title"])
        else:
            st.info(n["title"])

    # ================= RANKING =================
    st.subheader("🏆 Ranking personalizado")

    if st.session_state.favorites:
        rows = []
        for f in st.session_state.favorites:
            if f not in st.session_state.scores:
                st.session_state.scores[f] = round(
                    np.random.uniform(40, 90), 2
                )
            rows.append({
                "Ticker": f,
                "Riesgo": risk_score(f),
                "Score": st.session_state.scores[f]
            })

        df_rank = pd.DataFrame(rows)
        df_rank["Balance"] = df_rank["Score"] - df_rank["Riesgo"] * 0.5
        df_rank = df_rank.sort_values("Balance", ascending=False)

        edited = st.data_editor(
            df_rank,
            hide_index=True,
            disabled=True,
            key="ranking_editor"
        )

        sel = st.session_state.get("ranking_editor", {}).get("selected_rows")
        if sel:
            st.session_state.selected_ticker = df_rank.iloc[sel[0]]["Ticker"]
            st.rerun()

        # ---------- COMPARACIÓN RÁPIDA ----------
        st.subheader("🔀 Comparación rápida")

        tickers = df_rank["Ticker"].tolist()

        c1, c2 = st.columns(2)

        t1 = c1.selectbox("Activo A", tickers, key="cmp_a")
        t2 = c2.selectbox(
            "Activo B",
            tickers,
            index=1 if len(tickers) > 1 else 0,
            key="cmp_b"
        )

        if t1 and t2:
            score_a = st.session_state.scores.get(t1, 0)
            score_b = st.session_state.scores.get(t2, 0)

            risk_a = risk_score(t1)
            risk_b = risk_score(t2)

            balance_a = score_a - risk_a * 0.5
            balance_b = score_b - risk_b * 0.5

            # --- gráfico ---
            st.bar_chart(
                {
                    t1: score_a,
                    t2: score_b
                }
            )

            # --- métricas ---
            compare_df = pd.DataFrame({
                "Métrica": [
                    "Score",
                    "Riesgo",
                    "Balance",
                    "Estado mercado",
                    "Tipo de activo"
                ],
                t1: [
                    score_a,
                    risk_a,
                    round(balance_a, 2),
                    market_status(t1),
                    "Cripto" if t1.endswith(".CRYPTO") else "Acción / ETF"
                ],
                t2: [
                    score_b,
                    risk_b,
                    round(balance_b, 2),
                    market_status(t2),
                    "Cripto" if t2.endswith(".CRYPTO") else "Acción / ETF"
                ]
            })

            st.table(compare_df)
        # ================= RECOMENDADO PARA VOS =================
        st.subheader("🧠 Recomendado para vos")

        if st.session_state.favorites and not df_rank.empty:

            # excluir el activo actual
            candidates = df_rank[
                df_rank["Ticker"] != st.session_state.selected_ticker
            ]

            if not candidates.empty:
                rec = candidates.sort_values(
                    "Balance", ascending=False
                ).iloc[0]

                st.markdown(
                    f"""
        **👉 {rec['Ticker']}**

        Mejor balance riesgo / retorno según tus favoritos.

        - **Score:** {rec['Score']}
        - **Riesgo:** {rec['Riesgo']}
        - **Balance:** {round(rec['Balance'], 2)}
        """
                )

                if st.button("Ver activo recomendado"):
                    st.session_state.selected_ticker = rec["Ticker"]
                    st.rerun()

            else:
                st.caption(
                    "Ya estás viendo el activo con mejor balance de tu ranking."
                )

        else:
            st.caption(
                "Agregá activos a favoritos para recibir recomendaciones personalizadas."
            )

    if ENABLE_ETF_FINDER:
    
        # ================= ETF FINDER =================
        st.subheader("🧭 ETF Finder")

        ETF_TYPES = {
            "Indexados": ["Mercado amplio", "S&P 500", "Nasdaq"],
            "Temáticos": [
                "Technology", "Artificial Intelligence",
                "Fintech", "Energy", "Healthcare", "Space"
            ],
            "Sectoriales": [
                "Technology", "Energy", "Healthcare", "Financials"
            ],
            "Apalancados": [
                "Bull x2", "Bull x3", "Bear x2", "Bear x3"
            ],
            "Inversos": [
                "Mercado", "S&P 500", "Nasdaq"
            ]
        }

        ETF_CATALOG = {
            ("Indexados", "Mercado amplio"): ["VTI", "VT"],
            ("Indexados", "S&P 500"): ["SPY", "IVV"],
            ("Indexados", "Nasdaq"): ["QQQ"],

            ("Temáticos", "Technology"): ["XLK"],
            ("Temáticos", "Artificial Intelligence"): ["BOTZ", "AIQ"],
            ("Temáticos", "Fintech"): ["FINX"],
            ("Temáticos", "Energy"): ["ICLN", "XLE"],
            ("Temáticos", "Healthcare"): ["XLV"],
            ("Temáticos", "Space"): ["ARKX"],

            ("Sectoriales", "Technology"): ["XLK"],
            ("Sectoriales", "Energy"): ["XLE"],
            ("Sectoriales", "Healthcare"): ["XLV"],

            ("Apalancados", "Bull x2"): ["SSO"],
            ("Apalancados", "Bull x3"): ["UPRO"],
            ("Apalancados", "Bear x2"): ["SDS"],
            ("Apalancados", "Bear x3"): ["SPXU"],

            ("Inversos", "Mercado"): ["SH"],
            ("Inversos", "S&P 500"): ["SH"],
            ("Inversos", "Nasdaq"): ["PSQ"],
        }

        c1, c2 = st.columns(2)

        etf_type = c1.selectbox(
            "Tipo de ETF",
            [""] + list(ETF_TYPES.keys())
        )

        theme = None
        if etf_type:
            theme = c2.selectbox(
                "Tema / Industria",
                [""] + ETF_TYPES[etf_type]
            )

        if etf_type and theme:
            etfs = ETF_CATALOG.get((etf_type, theme), [])

            if etfs:
                st.markdown("**ETFs disponibles:**")

                for etf in etfs:
                    col1, col2 = st.columns([6, 2])
                    col1.write(f"📈 {etf}")

                    if col2.button(
                        "Ver ETF",
                        key=f"etf_{etf}"
                    ):
                        st.session_state.selected_ticker = etf
                        st.rerun()
            else:
                st.caption("No hay ETFs para esta combinación")

    st.caption("Modo DEMO — arquitectura lista para datos reales")


    
