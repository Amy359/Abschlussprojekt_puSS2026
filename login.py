import streamlit as st
import pandas as pd
import hashlib

import base64

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
    # 1. Definiere das CSS mit deinem eigenen Key
    st.markdown(
        """
        <style>
        /* .st-key-login-box entspricht dem key="login-box" im Container */
        .st-key-login-box {
            background-color: rgba(255, 255, 255, 0.6) !important;
            padding: 40px !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
            border: 1px solid rgba(255,255,255,0.3) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    left, center, right = st.columns([1, 2, 1])
    # Farbe Dunkelblau (Hex: #00008B)
    dunkelblau = "#0A0A26"

    with center:
        # 2. Nutze den key-Parameter, um den Container direkt adressierbar zu machen
        with st.container(key="login-box"):
            # Logo zentriert
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("images/logo.png")

            st.markdown(
                f"<p style='text-align: center; color: {dunkelblau}; font-size: 20px; font-weight: bold;'>🔐 Log In</p>",
                unsafe_allow_html=True,
            )

            username = st.text_input("Benutzername")
            password = st.text_input("Passwort", type="password")

            if st.button("Anmelden", width="stretch"):
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


def set_background(image_file):
    with open(image_file, "rb") as f:
        img = base64.b64encode(f.read()).decode()

    page_bg = f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{img}");
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        background-attachment: fixed;
    }}
    </style>
    """

    st.markdown(page_bg, unsafe_allow_html=True)
