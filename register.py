import streamlit as st
import pandas as pd
import hashlib
import os


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def register():

    st.title("📝 Registrierung")

    vorname = st.text_input("Vorname", key="reg_vorname")
    nachname = st.text_input("Nachname", key="reg_nachname")

    rolle = st.selectbox(
        "Ich bin",
        ["Athlet", "Trainer"],
        key="reg_rolle"
    )

    password = st.text_input(
        "Passwort",
        type="password",
        key="reg_password"
    )

    password2 = st.text_input(
        "Passwort wiederholen",
        type="password",
        key="reg_password2"
    )

    if st.button("Registrieren"):

        if password != password2:
            st.error("Die Passwörter stimmen nicht überein.")
            return

        filename = "data/users_secure.csv"

        if os.path.exists(filename):
            df = pd.read_csv(filename, delimiter=";")
        else:
            df = pd.DataFrame(columns=[
                "Vorname",
                "Nachname",
                "Password_Hash",
                "Rolle"
            ])

        # Benutzername erzeugen
        username = f"{vorname.lower()}.{nachname.lower()}"

        df["user_login"] = (
            df["Vorname"].str.lower()
            + "."
            + df["Nachname"].str.lower()
        )

        if username in df["user_login"].values:
            st.error("Dieser Benutzer existiert bereits.")
            return

        neuer_user = pd.DataFrame([{
            "Vorname": vorname,
            "Nachname": nachname,
            "Password_Hash": hash_password(password),
            "Rolle": rolle
        }])

        df = pd.concat(
            [
                df.drop(columns=["user_login"], errors="ignore"),
                neuer_user
            ],
            ignore_index=True
        )

        df.to_csv(filename, sep=";", index=False)

        st.success("Registrierung erfolgreich! 🎉")