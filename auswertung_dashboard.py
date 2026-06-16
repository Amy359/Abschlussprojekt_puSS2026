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
        st.error("🚨 Fehler: Die CSV-Dateien wurden nicht im Ordner 'data' gefunden! Bitte überprüfe die Pfade.")
        st.stop()

# Unsichtbare Leerzeichen aus Spaltennamen entfernen
df_train.columns = df_train.columns.str.strip()
df_regen.columns = df_regen.columns.str.strip()

# Kritische Spalten für den Code umbenennen
df_train = df_train.rename(columns={"Aktivität": "Aktivitaet", "Schmerzen_Beschwerden": "Schmerzen"})
df_regen = df_regen.rename(columns={"Ernaehrung_Kalorien_kcal": "Kalorien"})

# HIER WAR DER FEHLER: Das Datumsformat muss exakt auf JJJJ-MM-TT (z.B. 2026-06-01) angepasst sein!
df_train["Datum"] = pd.to_datetime(df_train["Datum"], format="%Y-%m-%d", errors='coerce')
df_train["KW"] = df_train["Datum"].dt.isocalendar().week.fillna(0).astype(int)

df_regen["Datum"] = pd.to_datetime(df_regen["Datum"], format="%Y-%m-%d", errors='coerce')
df_regen["KW"] = df_regen["Datum"].dt.isocalendar().week.fillna(0).astype(int)

# Schlafstunden extrahieren ("8 Std. 12 Min.")
def extrahiere_schlaf_stunden(schlaf_str):
    try:
        if pd.isna(schlaf_str): return 0.0
        teile = str(schlaf_str).split()
        stunden = float(teile[0])
        minuten = float(teile[2]) if len(teile) > 2 else 0.0
        return stunden + (minuten / 60.0)
    except:
        return 0.0

df_regen["Schlaf_Stunden"] = df_regen["Schlaf_Dauer"].apply(extrahiere_schlaf_stunden)

# 2. SEITENLEISTE (ATHLETEN-AUSWAHL)
st.sidebar.markdown("### 👤 Athleten-Profil")
alle_athleten = sorted(df_train["Athlet"].dropna().unique())
gewaehlter_athlet = st.sidebar.selectbox("Wähle den zu analysierenden Athleten:", alle_athleten)

df_t_ath = df_train[df_train["Athlet"] == gewaehlter_athlet]
df_r_ath = df_regen[df_regen["Athlet"] == gewaehlter_athlet]

# --- HAUPTBEREICH: TABS FÜR BESSERE STRUKTUR ---
tab_training, tab_recovery = st.tabs(["🏋️‍♂️ Trainings-Performance", "🛌 Regeneration & Vitalwerte"])

# ==========================================
# TAB 1: TRAININGSDATEN
# ==========================================
with tab_training:
    st.markdown(f"## 📊 Trainingsübersicht: {gewaehlter_athlet}")
    
    if not df_t_ath.empty:
        # Kilometer-Berechnung pro Woche
        kw_aktivitaet = df_t_ath.groupby(["KW", "Aktivitaet"])["Distanz_km"].sum().reset_index()
        
        # Balkendiagramm über die volle Breite
        fig_km = px.bar(
            kw_aktivitaet, x="KW", y="Distanz_km", color="Aktivitaet", barmode="group",
            title="Wöchentliche Trainingsdistanzen nach Disziplin",
            labels={"Distanz_km": "Distanz (km)", "KW": "Kalenderwoche", "Aktivitaet": "Disziplin"},
            color_discrete_sequence=px.colors.qualitative.Safe
        )
        fig_km.update_layout(xaxis_type='category', margin=dict(l=20, r=20, t=40, b=20))
        st.plotly_chart(fig_km, use_container_width=True)
    else:
        st.info("Keine Trainingsdaten für diesen Athleten vorhanden.")
    
    st.markdown("### 📋 Leistungsfaktoren & Medizinischer Status")
    col_left, col_right = st.columns(2)
    
    with col_left:
        # VO2max Sektion
        max_puls = df_t_ath["Max_Herzfrequenz"].max()
        ruhepuls_schnitt = df_r_ath["Ruhepuls_bpm"].mean()
        
        st.markdown("<div style='background-color:#F0F4F8; padding:15px; border-radius:10px; border-left: 5px solid #1E3A8A; min-height: 150px;'>", unsafe_allow_html=True)
        st.markdown("#### 🫁 Kardiovaskuläre Kapazität (VO2max)")
        if pd.notna(ruhepuls_schnitt) and ruhepuls_schnitt > 0 and pd.notna(max_puls):
            vo2max = 15.3 * (max_puls / ruhepuls_schnitt)
            st.write(f"**Geschätzte VO2max:** {vo2max:.1f} ml/min/kg")
            st.caption("Berechnet basierend auf maximalem Trainingspuls und Ruhepuls-Wochenschnitt.")
        else:
            st.info("Pulsdaten unvollständig für VO2max-Berechnung.")
        st.markdown("</div>", unsafe_allow_html=True)
            
    with col_right:
        # Schmerz-Tracking Sektion
        st.markdown("<div style='background-color:#FEF2F2; padding:15px; border-radius:10px; border-left: 5px solid #DC2626; min-height: 150px;'>", unsafe_allow_html=True)
        st.markdown("#### ⚠️ Schmerz- & Beschwerdeprotokoll")
        
        if "Schmerzen" in df_t_ath.columns and not df_t_ath.empty:
            schmerzen = df_t_ath[df_t_ath["Schmerzen"].astype(str).str.strip().str.lower() != "keine"]
            schmerzen = schmerzen.dropna(subset=["Schmerzen"])
            
            if not schmerzen.empty:
                counts = schmerzen["Schmerzen"].value_counts()
                for beschwerde, count in counts.items():
                    st.write(f"• **{beschwerde}**: {count}x gemeldet")
            else:
                st.write("🟢 Keine Schmerzen oder orthopädischen Probleme im System dokumentiert.")
        else:
            st.write("🟢 Keine Schmerzen dokumentiert.")
        st.markdown("</div>", unsafe_allow_html=True)

# ==========================================
# TAB 2: REGENERATIONSDATEN
# ==========================================
with tab_recovery:
    st.markdown(f"## 🛌 Regenerations- & Gesundheitsstatus: {gewaehlter_athlet}")
    
    # Berechnungen der Durchschnitte
    schlaf_schnitt = df_r_ath["Schlaf_Stunden"].mean()
    kalorien_schnitt = df_r_ath["Kalorien"].mean()
    kh_schnitt = df_r_ath["Kohlenhydrate_g"].mean()
    protein_schnitt = df_r_ath["Proteine_g"].mean()
    fett_schnitt = df_r_ath["Fette_g"].mean()
    ruhepuls_woche = df_r_ath["Ruhepuls_bpm"].mean()
    hrv_schnitt = df_r_ath["HRV_ms"].mean()
    
    # HRV Zustand
    if pd.notna(hrv_schnitt):
        hrv_bewertung = "🟢 Gut / Ausgeruht" if hrv_schnitt >= 75 else "🔴 Erholungsbedarf"
    else:
        hrv_bewertung = "Keine Daten"
    
    # Bevorzugte Methode
    liebste_massnahme = df_r_ath["Regenerations_Massnahme"].value_counts().index[0] if not df_r_ath.empty and df_r_ath["Regenerations_Massnahme"].dropna().size > 0 else "N/A"

    # Kacheln-Layout für Metriken
    m1, m2, m3, m4 = st.columns(4)
    
    with m1:
        st.markdown("<div style='background-color:#F3F4F6; padding:15px; border-radius:8px; text-align:center;'>", unsafe_allow_html=True)
        st.subheader("💤 Schlaf")
        if pd.notna(schlaf_schnitt) and schlaf_schnitt > 0:
            st.markdown(f"<h2>{int(schlaf_schnitt)}h {int((schlaf_schnitt%1)*60)}m</h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2>N/A</h2>", unsafe_allow_html=True)
        st.caption("Durchschnitt pro Tag")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with m2:
        st.markdown("<div style='background-color:#F3F4F6; padding:15px; border-radius:8px; text-align:center;'>", unsafe_allow_html=True)
        st.subheader("❤️ Vitalwerte")
        if pd.notna(ruhepuls_woche):
            st.markdown(f"<h2>{ruhepuls_woche:.1f} <span style='font-size:16px;'>bpm</span></h2>", unsafe_allow_html=True)
        else:
            st.markdown("<h2>N/A</h2>", unsafe_allow_html=True)
        st.caption(f"Ø Ruhepuls | HRV: {hrv_schnitt:.0f}ms" if pd.notna(hrv_schnitt) else "Ø Ruhepuls")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with m3:
        st.markdown("<div style='background-color:#F3F4F6; padding:15px; border-radius:8px; text-align:center;'>", unsafe_allow_html=True)
        st.subheader("🍏 Ernährung")
        if pd.notna(kalorien_schnitt):
            st.markdown(f"<h2>{kalorien_schnitt:.0f} <span style='font-size:16px;'>kcal</span></h2>", unsafe_allow_html=True)
            st.caption(f"KH: {kh_schnitt:.0f}g | P: {protein_schnitt:.0f}g | F: {fett_schnitt:.0f}g")
        else:
            st.markdown("<h2>N/A</h2>", unsafe_allow_html=True)
            st.caption("Keine Ernährungsdaten")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with m4:
        st.markdown("<div style='background-color:#F3F4F6; padding:15px; border-radius:8px; text-align:center;'>", unsafe_allow_html=True)
        st.subheader("🧘 Erholung")
        st.markdown(f"<h4>{liebste_massnahme}</h4>", unsafe_allow_html=True)
        st.caption(f"Status: {hrv_bewertung}")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Gesundheitstrend-Linie über die volle Breite
    if not df_r_ath.empty:
        df_trend = df_r_ath.groupby("KW")[["Ruhepuls_bpm", "HRV_ms"]].mean().reset_index()
        fig_health = px.line(
            df_trend, x="KW", y=["Ruhepuls_bpm", "HRV_ms"],
            title="Wöchentlicher Gesundheitstrend (Ruhepuls vs. HRV)",
            markers=True,
            labels={"value": "Messwert", "KW": "Kalenderwoche", "variable": "Metrik"},
            color_discrete_map={"Ruhepuls_bpm": "#EF4444", "HRV_ms": "#10B981"}
        )
        fig_health.update_layout(xaxis_type='category')
        st.plotly_chart(fig_health, use_container_width=True)