import streamlit as st
import pandas as pd
import plotly.express as px

def show_auswertungs_dashboard():
    # --- Hier beginnt das eingerückte Dashboard ---
    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏆 Professional Triathlon Athlete Performance Center</h1>", unsafe_allow_html=True)
    st.markdown("---")

    # 1. DATEN LADEN & BEREINIGEN
    try:
        df_train = pd.read_csv("data/triathlon_training.csv", sep=";", encoding="utf-8")
        df_regen = pd.read_csv("data/triathlon_regeneration.csv", sep=";", encoding="utf-8")
    except:
        st.error("🚨 Fehler: CSV-Dateien nicht gefunden!")
        return

    df_train.columns = df_train.columns.str.strip()
    df_regen.columns = df_regen.columns.str.strip()

    # 2. SEITENLEISTE
    st.sidebar.markdown("### 👤 Athleten-Profil")
    alle_athleten = sorted(df_train["Athlet"].dropna().unique())
    gewaehlter_athlet = st.sidebar.selectbox("Wähle den zu analysierenden Athleten:", alle_athleten)

    df_t_ath = df_train[df_train["Athlet"] == gewaehlter_athlet]
    df_r_ath = df_regen[df_regen["Athlet"] == gewaehlter_athlet]

    # --- TABS ---
    tab_training, tab_recovery = st.tabs(["🏋️‍♂️ Trainings-Performance", "🛌 Regeneration & Vitalwerte"])

    with tab_training:
        st.markdown(f"## 📊 Trainingsübersicht: {gewaehlter_athlet}")
        df_distanz = df_t_ath[df_t_ath["Aktivitaet"].str.lower() != "ruhetag"]
        kw_aktivitaet = df_distanz.groupby(["KW", "Aktivitaet"])["Distanz_km"].sum().reset_index()
        fig_km = px.bar(kw_aktivitaet, x="KW", y="Distanz_km", color="Aktivitaet", barmode="group")
        st.plotly_chart(fig_km, use_container_width=True)

    with tab_recovery:
        st.markdown(f"## 🛌 Regenerations- & Vitalwerte: {gewaehlter_athlet}")
        st.write("Hier stehen deine Regenerationsdaten...")