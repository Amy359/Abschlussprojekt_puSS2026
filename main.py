import streamlit as st

from personenklasse import Person
from login import login, logout
import athlet_dashboard
import trainer_dashboard


# --------------------------------
# Seiteneinstellungen
# --------------------------------
st.set_page_config(page_title="Triathlon Dashboard", layout="wide")
# --------------------------------
# Personen laden (nur einmal)
# --------------------------------
if not Person.daten_geladen():
    Person.load_data_from_csv("triathlon_personen.csv")

# --------------------------------
# Session State
# --------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "person" not in st.session_state:
    st.session_state.person = None

# --------------------------------
# Login oder Dashboard
# --------------------------------
if not st.session_state.logged_in:
    login()

else:
    logout()

    person = st.session_state.person

    if person.get_role() == "Trainer":
        trainer_dashboard.trainer_dashboard(person)

    else:
        athlet_dashboard.athlet_dashboard(person)
