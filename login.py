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
    """Rendert die Login-Maske (Logo, Benutzername/Passwort-Felder, Buttons).

    Bei erfolgreichem Login werden 'logged_in' und 'person' im Session-State
    gesetzt und die Seite neu geladen. Über den Button "Registrieren" wechselt
    die App in die Registrierungsansicht."""
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

            if st.button("Registrieren"):
                st.session_state.page = "register"
                st.rerun()


def logout(person=None):
    """Zeigt in der Sidebar einen Logout-Button an und setzt bei Klick
    den Login-Status sowie die gespeicherte Person zurück.

    Trainer erhalten zusätzlich einen 'Profil bearbeiten'-Button direkt über
    dem Logout-Button, der in trainer_dashboard.py das eigene
    Bearbeitungsformular öffnet."""

    ist_trainer = person is not None and person.get_role() == "Trainer"
    # Genug Platz am unteren Sidebar-Rand freihalten, damit der fix positionierte
    # Logout- (und ggf. Profil-bearbeiten-)Button keinen Inhalt überdeckt
    sidebar_padding_bottom = "134px" if ist_trainer else "90px"

    st.sidebar.markdown(
        f"""
        <style>
        section[data-testid="stSidebar"] .st-key-logout-button {{
            position: fixed;
            bottom: 24px;
            width: 16rem;
        }}
        section[data-testid="stSidebar"] .st-key-profil-bearbeiten-button {{
            position: fixed;
            bottom: 68px;
            width: 16rem;
        }}
        section[data-testid="stSidebar"] .st-key-logout-button button,
        section[data-testid="stSidebar"] .st-key-profil-bearbeiten-button button {{
            width: 100%;
        }}
        section[data-testid="stSidebar"] > div {{
            padding-top: 0;
            padding-bottom: {sidebar_padding_bottom};
        }}
        section[data-testid="stSidebarHeader"] {{
            min-height: 0;
            height: auto;
            padding: 0;
        }}
        section[data-testid="stSidebarUserContent"] {{
            padding-top: 0 !important;
        }}
        section[data-testid="stSidebarUserContent"] > div:first-child {{
            margin-top: 0 !important;
        }}
        section[data-testid="stSidebarUserContent"] [data-testid="stElementContainer"]:first-child {{
            margin-top: -1rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    if ist_trainer and st.sidebar.button("Profil bearbeiten", key="profil-bearbeiten-button"):
        st.session_state.zeige_profil_bearbeitung = True
        st.rerun()

    if st.sidebar.button("Logout", key="logout-button"):
        st.session_state.logged_in = False
        st.session_state.person = None

        st.rerun()


def set_background(image_file):
    """Setzt ein lokales Bild als Vollbild-Hintergrund der Streamlit-App.

    Das Bild wird base64-kodiert und per CSS (background-image) in
    den .stApp-Container eingebunden."""
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
