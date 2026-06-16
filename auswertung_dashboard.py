import streamlit as st
import pandas as pd
import plotly.express as px

# Seiteneinstellungen für Breitbild-Layout
st.set_page_config(page_title="Triathlon Dashboard", layout="wide")

# Titel-Styling
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🏆 Professional Triathlon Athlete Performance Center</h1>", unsafe_allow_html=True)
st.markdown("---")

# 1. DATEN LADEN & BEREINIGEN
try:
    df_train = pd.read_csv("data/triathlon_training.csv", sep=";", encoding="utf-8")
    df_regen = pd.read_csv("data/triathlon_regeneration.csv", sep=";", encoding="utf-8")
except (UnicodeDecodeError, FileNotFoundError):
    try:
        df_train = pd.read_csv("data/triathlon_training.csv", sep=";", encoding="cp1252")
        df_regen = pd.read_csv("data/triathlon_regeneration.csv", sep=";", encoding="cp1252")
    except FileNotFoundError:
        st.error("🚨 Fehler: Die CSV-Dateien wurden nicht im Ordner 'data' gefunden!")
        st.stop()

# Spaltennamen bereinigen
df_train.columns = df_train.columns.str.strip()
df_regen.columns = df_regen.columns.str.strip()

# Umbenennungen
df_train = df_train.rename(columns={"Aktivität": "Aktivitaet", "Schmerzen_Beschwerden": "Schmerzen"})
df_regen = df_regen.rename(columns={"Ernaehrung_Kalorien_kcal": "Kalorien"})

# Datumsformatierung
df_train["Datum"] = pd.to_datetime(df_train["Datum"], format="%Y-%m-%d", errors='coerce')
df_train["KW"] = df_train["Datum"].dt.isocalendar().week.fillna(0).astype(int)
df_regen["Datum"] = pd.to_datetime(df_regen["Datum"], format="%Y-%m-%d", errors='coerce')
df_regen["KW"] = df_regen["Datum"].dt.isocalendar().week.fillna(0).astype(int)

# Schlaf-Helper (Dezimalwert berechnen)
def extrahiere_schlaf_stunden(schlaf_str):
    try:
        if pd.isna(schlaf_str): return 0.0
        teile = str(schlaf_str).split()
        stunden = float(teile[0])
        minuten = float(teile[2]) if len(teile) > 2 else 0.0
        return stunden + (minuten / 60.0)
    except: return 0.0

df_regen["Schlaf_Stunden"] = df_regen["Schlaf_Dauer"].apply(extrahiere_schlaf_stunden)

# 2. SEITENLEISTE
st.sidebar.markdown("### 👤 Athleten-Profil")
alle_athleten = sorted(df_train["Athlet"].dropna().unique())
gewaehlter_athlet = st.sidebar.selectbox("Wähle den zu analysierenden Athleten:", alle_athleten)

df_t_ath = df_train[df_train["Athlet"] == gewaehlter_athlet]
df_r_ath = df_regen[df_regen["Athlet"] == gewaehlter_athlet]

# --- TABS ---
tab_training, tab_recovery = st.tabs(["🏋️‍♂️ Trainings-Performance", "🛌 Regeneration & Vitalwerte"])

# --- TAB 1: TRAINING ---
with tab_training:
    st.markdown(f"## 📊 Trainingsübersicht: {gewaehlter_athlet}")
    
    # Ruhetag aus Distanzberechnung entfernen
    df_distanz = df_t_ath[df_t_ath["Aktivitaet"].str.lower() != "ruhetag"]
    kw_aktivitaet = df_distanz.groupby(["KW", "Aktivitaet"])["Distanz_km"].sum().reset_index()
    
    fig_km = px.bar(kw_aktivitaet, x="KW", y="Distanz_km", color="Aktivitaet", barmode="group",
                    title="Wöchentliche Trainingsdistanzen (exkl. Ruhetage)")
    st.plotly_chart(fig_km, use_container_width=True)
    
    st.markdown("### 📋 Leistungsfaktoren & Schmerzprotokoll")
    col_left, col_right = st.columns(2)
    
    with col_left:
        max_puls = df_t_ath["Max_Herzfrequenz"].max()
        ruhepuls_schnitt = df_r_ath["Ruhepuls_bpm"].mean()
        st.subheader("🫁 Kardiovaskuläre Kapazität")
        if pd.notna(ruhepuls_schnitt) and ruhepuls_schnitt > 0:
            vo2max = 15.3 * (max_puls / ruhepuls_schnitt)
            st.write(f"**Geschätzte VO2max:** {vo2max:.1f} ml/min/kg")
        else: st.info("Nicht genügend Pulsdaten.")

    with col_right:
        st.subheader("⚠️ Schmerz- & Beschwerdeprotokoll")
        schmerzen = df_t_ath[df_t_ath["Schmerzen"].notna() & (df_t_ath["Schmerzen"].str.lower() != "keine")]
        if not schmerzen.empty:
            df_schmerz = schmerzen["Schmerzen"].value_counts().reset_index()
            df_schmerz.columns = ["Beschwerde", "Anzahl"]
            df_schmerz = df_schmerz.sort_values(by="Anzahl", ascending=False)
            
            # Farb-Tabelle
            def highlight_row(x):
                return ['background-color: #fca5a5'] * len(x)
            st.table(df_schmerz.style.apply(highlight_row, axis=1))
        else:
            st.write("🟢 Keine Schmerzen dokumentiert.")

# --- TAB 2: REGENERATION ---
with tab_recovery:
    st.markdown(f"## 🛌 Regenerations- & Vitalwerte: {gewaehlter_athlet}")
    
    # Schlaf-Berechnung (Std & Min)
    schlaf_avg = df_r_ath["Schlaf_Stunden"].mean()
    h = int(schlaf_avg)
    m = int((schlaf_avg - h) * 60)
    
    # Statistiken
    kal_s = df_r_ath["Kalorien"].mean()
    rp_s = df_r_ath["Ruhepuls_bpm"].mean()
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.metric("Ø Schlaf (pro Tag)", f"{h}h {m}m")
    with m2:
        st.metric("Ø Ruhepuls (pro Tag)", f"{rp_s:.1f} bpm")
    with m3:
        st.markdown("#### 🍏 Durchschnitt Ernährung (pro Tag)")
        st.write(f"**{kal_s:.0f} kcal**")
        st.caption(f"KH: {df_r_ath['Kohlenhydrate_g'].mean():.0f}g | P: {df_r_ath['Proteine_g'].mean():.0f}g | F: {df_r_ath['Fette_g'].mean():.0f}g")

    # Gesundheitstrends als separate Graphen
    if not df_r_ath.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_p = px.line(df_r_ath, x="Datum", y="Ruhepuls_bpm", title="Trend Ruhepuls (bpm)", color_discrete_sequence=['red'])
            st.plotly_chart(fig_p, use_container_width=True)
        with col_g2:
            fig_h = px.line(df_r_ath, x="Datum", y="HRV_ms", title="Trend HRV (ms)", color_discrete_sequence=['green'])
            st.plotly_chart(fig_h, use_container_width=True)