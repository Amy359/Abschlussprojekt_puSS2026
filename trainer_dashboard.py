import os
import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar

from personenklasse import Person
from auswertung import lade_daten, zeige_auswertung
from training_calendar import render_trainer_feedback_inbox


# HILFSFUNKTIONEN
# KALENDER
def lade_wettkaempfe():
    """Lädt die Wettkampfdaten."""

    if os.path.exists("data/wettkaempfe.csv"):
        df = pd.read_csv("data/wettkaempfe.csv", sep=";")
        df["Datum"] = pd.to_datetime(df["Datum"])
        return df

    return pd.DataFrame(columns=["ID", "Datum", "Athlet", "Wettkampf", "Ort", "Distanz", "Status", "Ergebnis"])


def speichere_wettkaempfe(df):
    df.to_csv("data/wettkaempfe.csv", sep=";", index=False, encoding="utf-8")


def zeige_wettkaempfe(df):
    if df.empty:
        st.info("Noch keine Wettkämpfe eingetragen.")
        return

    events = []

    for _, row in df.iterrows():
        events.append(
            {
                "title": f"{row['Athlet']} - {row['Wettkampf']}",
                "start": row["Datum"].strftime("%Y-%m-%d"),
                "end": row["Datum"].strftime("%Y-%m-%d"),
                "backgroundColor": "#2563eb",
                "borderColor": "#2563eb",
            }
        )

    calendar(
        events=events,
        options={
            "initialView": "dayGridMonth",
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,listMonth",
            },
        },
    )

    st.divider()


def wettkampf_hinzufuegen(df):
    st.subheader("➕ Neuen Wettkampf eintragen")

    with st.form("neuer_wettkampf"):
        col1, col2 = st.columns(2)

        datum = col1.date_input("Datum", datetime.today())

        athlet = col2.selectbox(
            "Athlet",
            [a.get_vollname() for a in Person.get_athleten()],
        )

        wettkampf = st.text_input("Wettkampf")

        col3, col4 = st.columns(2)

        ort = col3.text_input("Ort")

        distanz = col4.selectbox(
            "Distanz",
            [
                "Sprint",
                "Olympisch",
                "Mitteldistanz",
                "Langdistanz",
            ],
        )

        speichern = st.form_submit_button("💾 Wettkampf speichern")

    if speichern:
        neue_id = int(df["ID"].max()) + 1 if not df.empty else 1

        neuer_eintrag = pd.DataFrame(
            [
                {
                    "ID": neue_id,
                    "Datum": datum.strftime("%Y-%m-%d"),
                    "Athlet": athlet,
                    "Wettkampf": wettkampf,
                    "Ort": ort,
                    "Distanz": distanz,
                    "Status": "Geplant",
                    "Ergebnis": "",
                }
            ]
        )

        df = pd.concat(
            [df, neuer_eintrag],
            ignore_index=True,
        )

        speichere_wettkaempfe(df)

        st.success("✅ Wettkampf gespeichert!")

        st.rerun()


# GESAMTÜBERSICHT
def zeige_gesamtuebersicht(df_train, df_regen):
    pass


# HAUPTFUNKTION
def trainer_dashboard(person):

    # Daten laden
    df_train, df_regen = lade_daten()

    # Navigation und sidebar
    athlet_name = person.get_vollname()
    st.sidebar.title(f"Hallo, {athlet_name}!")
    menu = st.sidebar.radio("Menü", ["📅 Wettkampfkalender", "📊 Gesamtübersicht", "👥 Athleten"])

    # ------------------------
    # Kalender
    # ------------------------
    if menu == "📅 Wettkampfkalender":
        st.header("Wettkampfkalender")

        df_wettkaempfe = lade_wettkaempfe()

        zeige_wettkaempfe(df_wettkaempfe)

        wettkampf_hinzufuegen(df_wettkaempfe)

    # ------------------------
    # Gesamtübersicht
    # ------------------------
    elif menu == "📊 Gesamtübersicht":
        st.header("Gesamtübersicht")
        zeige_gesamtuebersicht(df_train, df_regen)
    # ------------------------
    # Athleten
    # ------------------------
    elif menu == "👥 Athleten":
        st.header("Athleten")

        athleten = Person.get_athleten()

        for i, athlet in enumerate(athleten):
            if st.button(athlet.get_vollname(), key=f"trainer_athlet_{i}"):
                zeige_auswertung(athlet.get_vollname(), df_train, df_regen)

        # Feedback von Athleten
        render_trainer_feedback_inbox()


# def show_trainer_dashboard():

# st.write("Trainer dashboard")


# Trainerprofil anzeigen
# Athletenübersicht anzeigen
# Athleten - dropdown menu
# kalender
