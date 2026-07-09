import streamlit as st
import pandas as pd
from datetime import datetime, date

from login import check_login, hash_password
from personenklasse import Person


def _lade_csv(dateiname: str, spalten: list[str]) -> pd.DataFrame:
    """Laedt eine CSV-Datei oder erzeugt ein leeres DataFrame mit Spalten."""
    try:
        return pd.read_csv(dateiname, delimiter=";")
    except FileNotFoundError:
        return pd.DataFrame(columns=spalten)


def register():
    """Zeigt die Trainer-Registrierung an und loggt neue Trainer direkt ein."""

    st.markdown(
        """
        <style>
        .st-key-register-box {
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
    dunkelblau = "#0A0A26"

    with center:
        with st.container(key="register-box"):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image("images/logo.png")

            st.markdown(
                f"<p style='text-align: center; color: {dunkelblau}; font-size: 20px; font-weight: bold;'>📝 Registrierung</p>",
                unsafe_allow_html=True,
            )

            vorname = st.text_input("Vorname", key="reg_vorname").strip().title()
            nachname = st.text_input("Nachname", key="reg_nachname").strip().title()
            geburtsdatum = st.date_input(
                "Geburtsdatum",
                value=date(1990, 1, 1),
                min_value=date(1920, 1, 1),
                max_value=date.today(),
                key="reg_geburtsdatum",
            )
            nationalitaet = st.text_input("Nationalität", key="reg_nationalitaet").strip()
            verein = st.text_input("Verein", key="reg_verein").strip()
            ist_trainer = st.checkbox("Ich bin Trainer.", key="reg_ist_trainer")

            if st.button("Registrieren", width="stretch"):
                if not ist_trainer:
                    st.warning("Nur Trainer können sich selbst registrieren.")
                    return

                if not vorname or not nachname:
                    st.error("Vorname und Nachname müssen ausgefüllt sein.")
                    return

                personen_datei = "data/triathlon_personen.csv"
                users_datei = "data/users_secure.csv"
                geburtsdatum_text = geburtsdatum.strftime("%d.%m.%Y")
                username = f"{vorname.lower()}.{nachname.lower()}"

                df_personen = _lade_csv(
                    personen_datei,
                    [
                        "Vorname",
                        "Nachname",
                        "Geburtsdatum",
                        "Nationalitaet",
                        "Rolle",
                        "Spezialisierung",
                        "Erfolge_Lizenzen",
                        "Trainer",
                        "Verein",
                    ],
                )
                df_users = _lade_csv(
                    users_datei,
                    [
                        "Vorname",
                        "Nachname",
                        "Password_Hash",
                    ],
                )

                df_users["user_login"] = (
                    df_users["Vorname"].astype(str).str.lower() + "." + df_users["Nachname"].astype(str).str.lower()
                )

                if username in df_users["user_login"].values:
                    st.error("Dieser Benutzer existiert bereits.")
                    return

                gleicher_name = (df_personen["Vorname"].astype(str).str.lower() == vorname.lower()) & (
                    df_personen["Nachname"].astype(str).str.lower() == nachname.lower()
                )

                if gleicher_name.any():
                    st.error("Diese Person existiert bereits.")
                    return

                neuer_trainer = {
                    "Vorname": vorname,
                    "Nachname": nachname,
                    "Geburtsdatum": geburtsdatum_text,
                    "Nationalitaet": nationalitaet,
                    "Rolle": "Trainer",
                    "Spezialisierung": "",
                    "Erfolge_Lizenzen": "",
                    "Trainer": "",
                    "Verein": verein,
                }

                for spalte in neuer_trainer:
                    if spalte not in df_personen.columns:
                        df_personen[spalte] = ""

                df_personen = pd.concat(
                    [df_personen, pd.DataFrame([neuer_trainer])],
                    ignore_index=True,
                )

                df_personen.to_csv(
                    personen_datei,
                    sep=";",
                    index=False,
                    encoding="utf-8",
                )

                neuer_user = {
                    "Vorname": vorname,
                    "Nachname": nachname,
                    "Password_Hash": hash_password(geburtsdatum_text),
                }

                for spalte in neuer_user:
                    if spalte not in df_users.columns:
                        df_users[spalte] = ""

                df_users = pd.concat(
                    [
                        df_users.drop(columns=["user_login"], errors="ignore"),
                        pd.DataFrame([neuer_user]),
                    ],
                    ignore_index=True,
                )

                df_users.to_csv(
                    users_datei,
                    sep=";",
                    index=False,
                    encoding="utf-8",
                )

                Person.load_data_from_csv("triathlon_personen.csv")
                person = check_login(username, geburtsdatum_text)

                if not person:
                    st.error("Registrierung gespeichert, aber der direkte Login ist fehlgeschlagen.")
                    return

                st.session_state.logged_in = True
                st.session_state.person = person
                st.rerun()

            if st.button("Zurück zum Log In", width="stretch"):
                st.session_state.page = "login"
                st.rerun()
