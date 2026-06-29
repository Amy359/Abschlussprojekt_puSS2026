import streamlit as st
import pandas as pd
import plotly.express as px


# --- HILFSFUNKTIONEN ---
def extrahiere_schlaf_stunden(schlaf_str):
    try:
        if pd.isna(schlaf_str):
            return 0.0
        teile = str(schlaf_str).split()
        stunden = float(teile[0])
        minuten = float(teile[2]) if len(teile) > 2 else 0.0
        return stunden + (minuten / 60.0)
    except (ValueError, IndexError):
        return 0.0


def get_color(beschwerde):
    b = str(beschwerde).lower()
    if "leicht" in b:
        return "background-color: #86efac"  # Grün
    if "mittel" in b:
        return "background-color: #fdba74"  # Orange
    if "stark" in b:
        return "background-color: #fca5a5"  # Rot
    return "background-color: #e5e7eb"  # Default Grau


@st.cache_data  # wenn nichts neues eingelesen wird, arbeitet streamlit immer mit den letzten daten
def lade_daten():
    """Diese Funktion lädt und bereinigt Daten aus einer csv Datei."""
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

    # Spaltennamen bereinigen & umbenennen
    df_train.columns = df_train.columns.str.strip()
    df_regen.columns = df_regen.columns.str.strip()
    df_train = df_train.rename(columns={"Aktivität": "Aktivitaet", "Schmerzen_Beschwerden": "Schmerzen"})
    df_regen = df_regen.rename(columns={"Ernaehrung_Kalorien_kcal": "Kalorien"})

    # Datumsformatierung & Berechnungen
    for df in [df_train, df_regen]:
        df["Datum"] = pd.to_datetime(df["Datum"], format="%Y-%m-%d", errors="coerce")
        df["KW"] = df["Datum"].dt.isocalendar().week.fillna(0).astype(int)

    df_regen["Schlaf_Stunden"] = df_regen["Schlaf_Dauer"].apply(extrahiere_schlaf_stunden)

    return df_train, df_regen


def zeige_auswertung(athlet_name, df_train, df_regen):
    """Diese Funktion stellt die Auswertung grafisch und schriftlich auf einem streamlit dashboard dar."""

    # Überschrift
    st.markdown(
        "<h1 style='text-align: center; color: #1E3A8A;'>🏆 Professional Triathlon Athlete Performance Center</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Daten filtern
    df_t_ath = df_train[df_train["Athlet"] == athlet_name]
    df_r_ath = df_regen[df_regen["Athlet"] == athlet_name]

    # Tabs
    tab_training, tab_recovery = st.tabs(["🏋️‍♂️ Trainings-Performance", "🛌 Regeneration & Vitalwerte"])

    # --- TAB 1: TRAINING ---
    with tab_training:
        st.markdown(f"## 📊 Trainingsübersicht: {athlet_name}")

        df_distanz = df_t_ath[df_t_ath["Aktivitaet"].str.lower() != "ruhetag"]
        kw_aktivitaet = df_distanz.groupby(["KW", "Aktivitaet"])["Distanz_km"].sum().reset_index()

        AKTIVITAET_FARBEN = {
            "Schwimmen": "#3B82F6",
            "Radfahren": "#F59E0B",
            "Laufen":    "#10B981",
            "Kraft":     "#8B5CF6",
            "Ruhetag":   "#9CA3AF",
            "Sonstiges": "#EC4899",
        }

        fig_km = px.bar(
            kw_aktivitaet,
            x="KW",
            y="Distanz_km",
            color="Aktivitaet",
            barmode="group",
            title="Wöchentliche Trainingsdistanzen (exkl. Ruhetage)",
            color_discrete_map=AKTIVITAET_FARBEN,
        )
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
            else:
                st.info("Nicht genügend Pulsdaten.")

        with col_right:
            st.subheader("⚠️ Schmerz- & Beschwerdeprotokoll")
            schmerzen_df = df_t_ath[df_t_ath["Schmerzen"].notna() & (df_t_ath["Schmerzen"].str.lower() != "keine")]

            if not schmerzen_df.empty:
                df_schmerz = schmerzen_df["Schmerzen"].value_counts().reset_index()
                df_schmerz.columns = ["Beschwerde", "Anzahl"]
                st.table(df_schmerz.style.apply(lambda row: [get_color(row["Beschwerde"])] * len(row), axis=1))
            else:
                st.write("🟢 Keine Schmerzen dokumentiert.")

    # --- TAB 2: REGENERATION ---
    with tab_recovery:
        st.markdown(f"## 🛌 Regenerations- & Vitalwerte: {athlet_name}")

        schlaf_avg = df_r_ath["Schlaf_Stunden"].mean()
        h, m = int(schlaf_avg), int((schlaf_avg - int(schlaf_avg)) * 60)

        m1, m2, m3 = st.columns(3)
        m1.metric("Ø Schlaf (pro Tag)", f"{h}h {m}m")
        m2.metric("Ø Ruhepuls (pro Tag)", f"{df_r_ath['Ruhepuls_bpm'].mean():.1f} bpm")
        m3.write(f"**Ø Kalorien:** {df_r_ath['Kalorien'].mean():.0f} kcal")
        m3.caption(
            f"KH: {df_r_ath['Kohlenhydrate_g'].mean():.0f}g | P: {df_r_ath['Proteine_g'].mean():.0f}g | F: {df_r_ath['Fette_g'].mean():.0f}g"
        )

        if not df_r_ath.empty:
            col_g1, col_g2 = st.columns(2)
            col_g1.plotly_chart(
                px.line(
                    df_r_ath, x="Datum", y="Ruhepuls_bpm", title="Trend Ruhepuls (bpm)", color_discrete_sequence=["red"]
                ),
                use_container_width=True,
            )
            col_g2.plotly_chart(
                px.line(df_r_ath, x="Datum", y="HRV_ms", title="Trend HRV (ms)", color_discrete_sequence=["green"]),
                use_container_width=True,
            )