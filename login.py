import streamlit as st
import pandas as pd
import hashlib

from personenklasse import Person


def hash_password(password):
    """Erstellt einen SHA-256 Hash des Passworts."""
    return hashlib.sha256(password.encode()).hexdigest()


def check_login(username, password):
    """Überprüft die Login-Daten und gibt das passende Person-Objekt zurück."""

    try:
        df = pd.read_csv("data/users_secure.csv", delimiter=";")

        df["user_login"] = df["Vorname"].str.lower() + "." + df["Nachname"].str.lower()

        input_hash = hash_password(password)

        user = df[(df["user_login"] == username.lower()) & (df["Password_Hash"] == input_hash)]

        if user.empty:
            return None

        vorname = user.iloc[0]["Vorname"]
        nachname = user.iloc[0]["Nachname"]

        vollname = f"{vorname} {nachname}"

        alle_personen = Person.get_athleten() + Person.get_trainer()

        for person in alle_personen:
            if person.get_vollname() == vollname:
                return person

    except Exception as e:
        st.error(f"Fehler beim Login: {e}")

    return None


def login():
    """Zeigt die Login-Oberfläche an."""

    st.title("🔐 Login - Triathlon Dashboard")

    username = st.text_input("Benutzername (Vorname.Nachname)")

    password = st.text_input("Passwort (TT.MM.JJJJ)", type="password")

    if st.button("Anmelden"):
        person = check_login(username, password)

        if person:
            st.session_state.logged_in = True
            st.session_state.person = person

            st.rerun()

        else:
            st.error("Benutzername oder Passwort falsch!")


def logout():
    """Zeigt den Logout-Button an."""

    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.person = None

        st.rerun()
