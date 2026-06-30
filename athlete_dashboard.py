import streamlit as st
import pandas as pd
import io
from datetime import datetime
from pathlib import Path

# --- IMPORTS AUS DEN ANDEREN MODULEN ---
# training_calendar.py muss im selben Ordner liegen
from training_calendar import render_calendar

# ---------------------------------------------------------------------------
# AUSWERTUNG WIRD AUS auswertung.py IMPORTIERT
# ---------------------------------------------------------------------------

from auswertung import lade_daten, zeige_auswertung
def save_to_csv(df, filename):
    df.to_csv(filename, sep=";", index=False, encoding="utf-8")

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

def athlete_dashboard(person):
    """
    Hauptfunktion des Athleten-Dashboards.

    Parameters
    ----------
    person : Objekt mit Methode get_vollname() → str
    """
    athlet_name = person.get_vollname()
    df_train, df_regen = lade_daten()

    # Sidebar
    st.sidebar.title(f"Hallo, {athlet_name}!")
    menu = st.sidebar.selectbox(
        "Menü",
        [
            "📅 Mein Kalender",
            "✏️ Eingaben",
            "📊 Meine Auswertung",
            "📥 Daten exportieren",
        ],
    )

    # Untermenü für "Eingaben"
    eingabe_typ = None
    if menu == "✏️ Eingaben":
        eingabe_typ = st.sidebar.selectbox(
            "Was möchtest du eingeben?",
            ["🏋️ Training", "🛌 Regeneration"],
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

    elif menu == "✏️ Eingaben":
        if eingabe_typ == "🏋️ Training":
            zeige_training_eingabe(athlet_name)
        elif eingabe_typ == "🛌 Regeneration":
            zeige_regen_eingabe(athlet_name)

    elif menu == "📊 Meine Auswertung":
        zeige_auswertung(athlet_name, df_train, df_regen)
    
    elif menu == "📥 Daten exportieren":

        st.header("📥 Daten exportieren")

        df_train, df_regen = lade_daten()

        # Nur Daten des angemeldeten Athleten
        train_export = df_train[df_train["Athlet"] == athlet_name]
        regen_export = df_regen[df_regen["Athlet"] == athlet_name]

        # Excel-Datei im Speicher erzeugen
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            train_export.to_excel(
                writer,
                sheet_name="Training",
                index=False
            )

            regen_export.to_excel(
                writer,
                sheet_name="Regeneration",
                index=False
            )

        output.seek(0)

        st.success("✅ Deine Daten sind bereit.")

        st.download_button(
            label="📥 Excel-Datei herunterladen",
            data=output,
            file_name=f"{athlet_name}_Triathlon_Daten.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

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