import streamlit as st

from personenklasse import Person
from auswertung import lade_daten, zeige_auswertung


def trainer_dashboard():

    # Daten laden
    df_train, df_regen = lade_daten()

    # Überschrift
    st.title("🏋️ Trainer Dashboard")

    # Navigation
    seite = st.sidebar.radio("Navigation", ["📅 Kalender", "📊 Gesamtübersicht", "👥 Athleten"])

    # ------------------------
    # Kalender
    # ------------------------
    if seite == "📅 Kalender":
        st.header("Kalender")
        st.write("Hier kommt später der Kalender hin.")

    # ------------------------
    # Gesamtübersicht
    # ------------------------
    elif seite == "📊 Gesamtübersicht":
        st.header("Gesamtübersicht")

        st.write("Hier kommen später Diagramme aller Athleten hin.")

    # ------------------------
    # Athleten
    # ------------------------
    elif seite == "👥 Athleten":
        st.header("Athleten")

        athleten = Person.get_athleten()

        for athlet in athleten:
            if st.button(athlet.get_vollname()):
                zeige_auswertung(athlet.get_vollname(), df_train, df_regen)


# def show_trainer_dashboard():

# st.write("Trainer dashboard")


# Trainerprofil anzeigen
# Athletenübersicht anzeigen
# Athleten - dropdown menu
# kalender
