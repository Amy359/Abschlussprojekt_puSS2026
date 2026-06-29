import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from pathlib import Path

# --- IMPORTS AUS DEN ANDEREN MODULEN ---
# training_calendar.py muss im selben Ordner liegen
from training_calendar import render_calendar

# ---------------------------------------------------------------------------
# HILFSFUNKTIONEN (aus auswertung.py)
# ---------------------------------------------------------------------------

def extrahiere_schlaf_stunden(schlaf_str):
    try:
        if pd.isna(schlaf_str):
            return 0.0
        teile = str(schlaf_str).split()
        stunden = float(teile[0])
        minuten = float(teile[2]) if len(teile) > 2 else 0.0
        return stunden + (minuten / 60.0)
    except Exception:
        return 0.0


def get_color(beschwerde):
    b = str(beschwerde).lower()
    if "leicht" in b:
        return "background-color: #86efac"
    if "mittel" in b:
        return "background-color: #fdba74"
    if "stark" in b:
        return "background-color: #fca5a5"
    return "background-color: #e5e7eb"


@st.cache_data
def lade_daten():
    """Lädt und bereinigt Daten aus den CSV-Dateien."""
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

    df_train.columns = df_train.columns.str.strip()
    df_regen.columns = df_regen.columns.str.strip()
    df_train = df_train.rename(columns={"Aktivität": "Aktivitaet", "Schmerzen_Beschwerden": "Schmerzen"})
    df_regen = df_regen.rename(columns={"Ernaehrung_Kalorien_kcal": "Kalorien"})

    for df in [df_train, df_regen]:
        df["Datum"] = pd.to_datetime(df["Datum"], format="%Y-%m-%d", errors="coerce")
        df["KW"] = df["Datum"].dt.isocalendar().week.fillna(0).astype(int)

    df_regen["Schlaf_Stunden"] = df_regen["Schlaf_Dauer"].apply(extrahiere_schlaf_stunden)

    return df_train, df_regen


def save_to_csv(df, filename):
    df.to_csv(filename, sep=";", index=False, encoding="utf-8")


# ---------------------------------------------------------------------------
# AUSWERTUNGS-TAB (aus auswertung.py)
# ---------------------------------------------------------------------------

def zeige_auswertung(athlet_name, df_train, df_regen):
    st.markdown(
        "<h1 style='text-align: center; color: #1E3A8A;'>🏆 Professional Triathlon Athlete Performance Center</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    df_t_ath = df_train[df_train["Athlet"] == athlet_name]
    df_r_ath = df_regen[df_regen["Athlet"] == athlet_name]

    tab_training, tab_recovery = st.tabs(["🏋️‍♂️ Trainings-Performance", "🛌 Regeneration & Vitalwerte"])

    # --- TAB 1: TRAINING ---
    with tab_training:
        st.markdown(f"## 📊 Trainingsübersicht: {athlet_name}")

        df_distanz = df_t_ath[df_t_ath["Aktivitaet"].str.lower() != "ruhetag"]
        kw_aktivitaet = df_distanz.groupby(["KW", "Aktivitaet"])["Distanz_km"].sum().reset_index()

        fig_km = px.bar(
            kw_aktivitaet,
            x="KW",
            y="Distanz_km",
            color="Aktivitaet",
            barmode="group",
            title="Wöchentliche Trainingsdistanzen (exkl. Ruhetage)",
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
            schmerzen_df = df_t_ath[
                df_t_ath["Schmerzen"].notna() & (df_t_ath["Schmerzen"].str.lower() != "keine")
            ]
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
            f"KH: {df_r_ath['Kohlenhydrate_g'].mean():.0f}g | "
            f"P: {df_r_ath['Proteine_g'].mean():.0f}g | "
            f"F: {df_r_ath['Fette_g'].mean():.0f}g"
        )

        if not df_r_ath.empty:
            col_g1, col_g2 = st.columns(2)
            col_g1.plotly_chart(
                px.line(df_r_ath, x="Datum", y="Ruhepuls_bpm",
                        title="Trend Ruhepuls (bpm)", color_discrete_sequence=["red"]),
                use_container_width=True,
            )
            col_g2.plotly_chart(
                px.line(df_r_ath, x="Datum", y="HRV_ms",
                        title="Trend HRV (ms)", color_discrete_sequence=["green"]),
                use_container_width=True,
            )


# ---------------------------------------------------------------------------
# TRAINING EINGEBEN
# ---------------------------------------------------------------------------

def zeige_training_eingabe(athlet_name):
    st.header("🏋️ Neues Training protokollieren")
    df_train, _ = lade_daten()

    with st.form("training_form"):
        col1, col2 = st.columns(2)
        datum = col1.date_input("Datum", datetime.now())
        aktivitaet = col2.selectbox(
            "Aktivität", ["Schwimmen", "Radfahren", "Laufen", "Kraft", "Ruhetag", "Sonstiges"]
        )
        col3, col4 = st.columns(2)
        dauer = col3.number_input("Dauer (min)", min_value=0)
        distanz = col4.number_input("Distanz (km)", min_value=0.0, step=0.1)
        col5, col6 = st.columns(2)
        puls_max = col5.number_input("Max. Herzfrequenz", min_value=0)
        schmerzen = col6.selectbox("Schmerzen", ["Keine", "Leicht", "Mittel", "Stark"])

        if st.form_submit_button("💾 Training speichern"):
            new_row = pd.DataFrame([{
                "Datum":             datum.strftime("%Y-%m-%d"),
                "Athlet":            athlet_name,
                "Aktivität":         aktivitaet,
                "Dauer_Minuten":     dauer,
                "Distanz_km":        distanz,
                "Max_Herzfrequenz":  puls_max,
                "Schmerzen_Beschwerden": schmerzen,
            }])
            df_train = pd.concat([df_train, new_row], ignore_index=True)
            save_to_csv(df_train, "data/triathlon_training.csv")
            st.cache_data.clear()   # Cache leeren, damit neue Daten sichtbar sind
            st.success("✅ Training gespeichert!")


# ---------------------------------------------------------------------------
# REGENERATION EINGEBEN
# ---------------------------------------------------------------------------

def zeige_regen_eingabe(athlet_name):
    st.header("🛌 Regenerationsdaten erfassen")
    _, df_regen = lade_daten()

    with st.form("regen_form"):
        datum_r = st.date_input("Datum", datetime.now())
        schlaf = st.text_input("Schlafdauer (z.B. '8 h 0 min')", "8 h 0 min")
        c1, c2, c3 = st.columns(3)
        ruhepuls = c1.number_input("Ruhepuls (bpm)", min_value=0)
        hrv = c2.number_input("HRV (ms)", min_value=0)
        kalorien = c3.number_input("Kalorien (kcal)", min_value=0)

        if st.form_submit_button("💾 Daten speichern"):
            new_row = pd.DataFrame([{
                "Datum":        datum_r.strftime("%Y-%m-%d"),
                "Athlet":       athlet_name,
                "Schlaf_Dauer": schlaf,
                "Ruhepuls_bpm": ruhepuls,
                "HRV_ms":       hrv,
                "Kalorien":     kalorien,
            }])
            df_regen = pd.concat([df_regen, new_row], ignore_index=True)
            save_to_csv(df_regen, "data/triathlon_regeneration.csv")
            st.cache_data.clear()
            st.success("✅ Regenerationsdaten gespeichert!")


# ---------------------------------------------------------------------------
# HAUPT-DASHBOARD
# ---------------------------------------------------------------------------

def athlet_dashboard(person):
    """
    Hauptfunktion des Athleten-Dashboards.

    Parameters
    ----------
    person : Objekt mit Methode get_vollname() → str
    """
    athlet_name = person.get_vollname()
    df_train, df_regen = lade_daten()

    # Sidebar
    st.sidebar.title(f"👋 Hallo, {athlet_name}!")
    menu = st.sidebar.radio(
        "Navigation",
        [
            "📅 Mein Kalender",
            "🏋️ Training eingeben",
            "🛌 Regeneration eingeben",
            "📊 Meine Auswertung",
        ],
    )

    # --- Seiten ---

    if menu == "📅 Mein Kalender":
        st.header("📅 Dein Trainings-Kalender")
        # render_calendar aus training_calendar.py mit role="athlete"
        render_calendar(
            role="athlete",
            current_user=athlet_name,
            csv_path=Path("data/triathlon_training.csv"),
        )

    elif menu == "🏋️ Training eingeben":
        zeige_training_eingabe(athlet_name)

    elif menu == "🛌 Regeneration eingeben":
        zeige_regen_eingabe(athlet_name)

    elif menu == "📊 Meine Auswertung":
        zeige_auswertung(athlet_name, df_train, df_regen)


# ---------------------------------------------------------------------------
# Standalone-Test  →  streamlit run athlete_dashboard.py
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    st.set_page_config(
        page_title="Athleten Dashboard",
        layout="wide",
        page_icon="🏊",
    )
    st.error("⚠️ Bitte das Dashboard über die Haupt-App starten (mit Login).")
    st.stop()