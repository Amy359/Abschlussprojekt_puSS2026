import os
from datetime import datetime

import pandas as pd
import streamlit as st

from personenklasse import Person
from training_calendar import render_calendar
from auswertung_dashboard import show_dashboard   # Diese Funktion bauen wir später um


# ----------------------------------------------------------
# Seiteneinstellungen
# ----------------------------------------------------------

st.set_page_config(
    page_title="Triathlon Athlete Dashboard",
    page_icon="🏊",
    layout="wide"
)


# ----------------------------------------------------------
# Dateipfade
# ----------------------------------------------------------

TRAINING_FILE = "data/triathlon_training.csv"
REGEN_FILE = "data/triathlon_regeneration.csv"


# ----------------------------------------------------------
# CSV laden
# ----------------------------------------------------------

def load_csv(datei, spalten):

    if os.path.exists(datei):
        df = pd.read_csv(
            datei,
            sep=";",
            encoding="utf-8"
        )

    else:
        df = pd.DataFrame(columns=spalten)

    df.columns = df.columns.str.strip()

    return df


def save_csv(df, datei):

    df.to_csv(
        datei,
        sep=";",
        index=False,
        encoding="utf-8"
    )


# ----------------------------------------------------------
# Login prüfen
# ----------------------------------------------------------

if "username" not in st.session_state:

    st.warning("Bitte zuerst anmelden.")

    st.stop()


# ----------------------------------------------------------
# Personen laden
# ----------------------------------------------------------

Person.load_data_from_csv("triathlon_personen.csv")

user = Person.finde_person(
    st.session_state["username"]
)

if user is None:

    st.error("Athlet wurde nicht gefunden.")

    st.stop()


# ----------------------------------------------------------
# Daten laden
# ----------------------------------------------------------

training_spalten = [

    "Datum",
    "Athlet",
    "Aktivität",
    "Einheit_Des_Tages",
    "Fokus",
    "Dauer_Minuten",
    "Distanz_km",
    "Ø_Herzfrequenz",
    "Max_Herzfrequenz",
    "Kalorienverbrauch",
    "Gefühl",
    "Schmerzen_Beschwerden",
    "Kommentar"

]

regen_spalten = [

    "Datum",
    "Athlet",
    "Schlaf_Dauer",
    "Ruhepuls_bpm",
    "HRV_ms",
    "Kalorien",
    "Proteine_g",
    "Kohlenhydrate_g",
    "Fette_g",
    "Wasser_Liter",
    "Frühstück",
    "Mittagessen",
    "Abendessen",
    "Snacks",
    "Supplemente",
    "Kommentar"

]


df_training = load_csv(
    TRAINING_FILE,
    training_spalten
)

df_regen = load_csv(
    REGEN_FILE,
    regen_spalten
)


# ----------------------------------------------------------
# Sidebar
# ----------------------------------------------------------

st.sidebar.title("🏊 Triathlon Dashboard")

st.sidebar.success(

    f"""
Willkommen

**{user.get_vollname()}**
"""
)

menu = st.sidebar.radio(

    "Navigation",

    [

        "🏠 Startseite",

        "📅 Trainingskalender",

        "🏋 Training",

        "🛌 Regeneration",

        "📊 Performance Center"

    ]

)


# ----------------------------------------------------------
# Startseite
# ----------------------------------------------------------

if menu == "🏠 Startseite":

    st.title("🏊 Triathlon Athlete Dashboard")

    st.markdown("---")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Trainings",
        len(df_training[df_training["Athlet"] == user.get_vollname()])
    )

    c2.metric(
        "Regeneration",
        len(df_regen[df_regen["Athlet"] == user.get_vollname()])
    )

    if not df_training.empty:

        km = df_training[
            df_training["Athlet"] == user.get_vollname()
        ]["Distanz_km"].sum()

    else:
        km = 0

    c3.metric(
        "Gesamtdistanz",
        f"{km:.1f} km"
    )

    st.info(
        "Willkommen im persönlichen Athleten-Dashboard."
    )