"""Haupteinstiegspunkt der Triathlon-Dashboard-App.

Lädt beim Start die Personendaten aus der CSV, verwaltet den Login-Status
im Session-State und leitet je nach Login-Status und Rolle (Athlet/Trainer)
zur passenden Ansicht (Login, Registrierung, Athleten- oder Trainer-Dashboard)
weiter."""

import streamlit as st

from personenklasse import Person
from login import login, logout, set_background
from register import register
import athlete_dashboard
import trainer_dashboard

st.set_page_config(page_title="Triathlon Dashboard", layout="wide")

if not Person.daten_geladen():
    Person.load_data_from_csv("triathlon_personen.csv")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "person" not in st.session_state:
    st.session_state.person = None

if "page" not in st.session_state:
    st.session_state.page = "login"


# ----------------------------
# Nicht eingeloggt
# ----------------------------
if not st.session_state.logged_in:

    set_background("images/background.jpg")

    if st.session_state.page == "login":
        login()

    elif st.session_state.page == "register":
        register()

# ----------------------------
# Eingeloggt
# ----------------------------
else:

    person = st.session_state.person

    logout(person)

    if person.get_role() == "Trainer":
        trainer_dashboard.trainer_dashboard(person)
    else:
        athlete_dashboard.athlete_dashboard(person)
