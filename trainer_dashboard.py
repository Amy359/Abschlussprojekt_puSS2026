import os
import streamlit as st
import pandas as pd
from datetime import datetime, date
from streamlit_calendar import calendar
import plotly.express as px

from personenklasse import Person
from login import hash_password
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
    """Speichert das Wettkampf-DataFrame als Semikolon-getrennte CSV-Datei
    unter 'data/wettkaempfe.csv'."""
    df.to_csv("data/wettkaempfe.csv", sep=";", index=False, encoding="utf-8")


def athlet_hinzufuegen(trainer):
    """Zeigt ein Formular zum Anlegen eines neuen Athleten an."""

    st.header("Athlet hinzufügen")

    if "athlet_hinzufuegen_erfolg" in st.session_state:
        st.success(st.session_state.pop("athlet_hinzufuegen_erfolg"))

    trainer_name = trainer.get_vollname()
    formular_version = st.session_state.get("athlet_hinzufuegen_formular_version", 0)

    with st.form("athlet_hinzufuegen"):
        col1, col2 = st.columns(2)

        vorname = col1.text_input("Vorname", key=f"athlet_vorname_{formular_version}")
        nachname = col2.text_input("Nachname", key=f"athlet_nachname_{formular_version}")

        geburtsdatum = col1.date_input(
            "Geburtsdatum",
            value=date(1990, 1, 1),
            min_value=date(1920, 1, 1),
            max_value=date.today(),
            key=f"athlet_geburtsdatum_{formular_version}",
        )
        nationalitaet = col2.text_input("Nationalität", key=f"athlet_nationalitaet_{formular_version}")

        spezialisierung = col1.text_input("Spezialisierung", key=f"athlet_spezialisierung_{formular_version}")
        col2.text_input("Trainer", value=trainer_name, disabled=True, key=f"athlet_trainer_{formular_version}")

        verein = st.text_input("Verein", key=f"athlet_verein_{formular_version}")

        speichern = st.form_submit_button("💾 Athlet speichern")

    if speichern:
        vorname = vorname.strip().title()
        nachname = nachname.strip().title()
        nationalitaet = nationalitaet.strip().title()
        spezialisierung = spezialisierung.strip().title()
        verein = verein.strip().title()

        if not vorname or not nachname:
            st.error("Vorname und Nachname müssen ausgefüllt sein.")
            return

        personen_datei = "data/triathlon_personen.csv"
        users_datei = "data/users_secure.csv"
        geburtsdatum_text = geburtsdatum.strftime("%d.%m.%Y")
        username = f"{vorname.lower()}.{nachname.lower()}"

        df_personen = pd.read_csv(personen_datei, sep=";")
        df_users = pd.read_csv(users_datei, sep=";")

        df_users["user_login"] = (
            df_users["Vorname"].astype(str).str.lower() + "." + df_users["Nachname"].astype(str).str.lower()
        )

        if username in df_users["user_login"].values:
            st.error("Dieser Benutzername existiert bereits.")
            return

        gleicher_name = (df_personen["Vorname"].astype(str).str.lower() == vorname.lower()) & (
            df_personen["Nachname"].astype(str).str.lower() == nachname.lower()
        )

        if gleicher_name.any():
            st.error("Ein Athlet mit diesem Vor- und Nachnamen existiert bereits.")
            return

        neuer_athlet = {
            "Vorname": vorname,
            "Nachname": nachname,
            "Geburtsdatum": geburtsdatum_text,
            "Nationalitaet": nationalitaet,
            "Rolle": "Athlet",
            "Spezialisierung": spezialisierung,
            "Erfolge_Lizenzen": "",
            "Trainer": trainer_name,
            "Verein": verein,
        }

        for spalte in neuer_athlet:
            if spalte not in df_personen.columns:
                df_personen[spalte] = ""

        df_personen = pd.concat(
            [df_personen, pd.DataFrame([neuer_athlet])],
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

        athlet = f"{vorname} {nachname}"
        st.session_state.athlet_hinzufuegen_erfolg = f"{athlet} wurde erfolgreich angelegt."
        st.session_state.athlet_hinzufuegen_formular_version = formular_version + 1
        st.rerun()


def zeige_wettkaempfe(df):
    """Rendert die Wettkämpfe aus dem übergebenen DataFrame als Events in
    einem Monatskalender (streamlit_calendar). Zeigt einen Hinweis an,
    falls noch keine Wettkämpfe vorhanden sind."""
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
    """Zeigt ein Formular zum Erfassen eines neuen Wettkampfs (Datum, Athlet,
    Name, Ort, Distanz) an und hängt den Eintrag bei Absenden an das
    übergebene DataFrame an, bevor er in der CSV gespeichert wird."""
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
    """Zeigt die Gesamtübersicht aller Athleten."""

    st.header("📊 Gesamtübersicht aller Athleten")
    st.write("Kennzahlen und Trainingsdaten des gesamten Teams")

    # -------------------------------
    # Durchschnittswerte Regeneration
    # -------------------------------
    schlaf = df_regen["Schlaf_Stunden"].mean()
    ruhepuls = df_regen["Ruhepuls_bpm"].mean()
    hrv = df_regen["HRV_ms"].mean()
    kalorien = df_regen["Kalorien"].mean()

    h = int(schlaf)
    m = int((schlaf - h) * 60)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("😴 Ø Schlaf", f"{h}h {m}m")
    c2.metric("❤️ Ø Ruhepuls", f"{ruhepuls:.1f} bpm")
    c3.metric("📈 Ø HRV", f"{hrv:.0f} ms")
    c4.metric("🔥 Ø Kalorien", f"{kalorien:.0f} kcal")

    st.divider()

    # -------------------------------
    # Trainingsdistanzen nach Sportart
    # -------------------------------
    st.subheader("🏋️ Trainingsdistanzen des Teams")

    df_distanz = df_train[df_train["Aktivitaet"].str.lower() != "ruhetag"].copy()

    if "Datum" in df_distanz.columns:
        df_distanz["Monat"] = df_distanz["Datum"].dt.strftime("%B %Y")

        monat = st.selectbox(
            "Monat auswählen",
            sorted(df_distanz["Monat"].unique(), reverse=True),
        )

        df_distanz = df_distanz[df_distanz["Monat"] == monat]

    distanzen = df_distanz.groupby("Aktivitaet")["Distanz_km"].sum().reset_index()

    AKTIVITAET_FARBEN: dict[str, str] = {
        "Schwimmen": "#3B82F6",
        "Radfahren": "#FF33B1",
        "Laufen": "#0B7A55",
        "Kraft": "#8B5CF6",
        "Ruhetag": "#9CA3AF",
        "Sonstiges": "#FFEB38",
    }

    fig = px.bar(
        distanzen,
        x="Aktivitaet",
        y="Distanz_km",
        color="Aktivitaet",
        color_discrete_map=AKTIVITAET_FARBEN,
        title="Trainingsdistanzen nach Sportart",
        text="Distanz_km",
    )

    fig.update_traces(
        texttemplate="%{text:.1f} km",
        textposition="outside",
    )

    fig.update_layout(
        showlegend=False,
        yaxis_title="Distanz (km)",
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )

    fig.update_yaxes(rangemode="tozero")

    st.plotly_chart(fig, width="stretch")

    st.divider()

    # -------------------------------
    # Athletenvergleich
    # -------------------------------
    st.subheader("🏆 Athletenvergleich")

    vergleich = (
        df_train.groupby("Athlet")
        .agg(
            Distanz_km=("Distanz_km", "sum"),
            Trainings=("Datum", "count"),
            Max_Puls=("Max_Herzfrequenz", "max"),
        )
        .reset_index()
    )

    regen = (
        df_regen.groupby("Athlet")
        .agg(
            Schlaf=("Schlaf_Stunden", "mean"),
            Ruhepuls=("Ruhepuls_bpm", "mean"),
            HRV=("HRV_ms", "mean"),
        )
        .reset_index()
    )

    vergleich = vergleich.merge(regen, on="Athlet", how="left")

    # Sieger hervorheben
    beste_distanz = vergleich.loc[vergleich["Distanz_km"].idxmax(), "Athlet"]
    bester_schlaf = vergleich.loc[vergleich["Schlaf"].idxmax(), "Athlet"]
    beste_hrv = vergleich.loc[vergleich["HRV"].idxmax(), "Athlet"]

    c1, c2, c3 = st.columns(3)

    c1.success(f"🥇 Meiste Trainingskilometer\n\n{beste_distanz}")
    c2.success(f"😴 Längster Schlaf\n\n{bester_schlaf}")
    c3.success(f"❤️ Höchste HRV\n\n{beste_hrv}")

    st.dataframe(
        vergleich.style.format(
            {
                "Distanz_km": "{:.1f}",
                "Schlaf": "{:.1f}",
                "Ruhepuls": "{:.1f}",
                "HRV": "{:.0f}",
            }
        ),
        width="stretch",
    )


# HAUPTFUNKTION
def trainer_dashboard(person):
    """Hauptansicht für eingeloggte Trainer.

    Baut die Sidebar-Navigation auf (Wettkampfkalender, Gesamtübersicht,
    Athleten) und rendert je nach Auswahl die entsprechende Unterseite
    sowie die Feedback-Inbox der Athleten."""

    # Daten laden
    df_train, df_regen = lade_daten()

    # Navigation und sidebar
    athlet_name = person.get_vollname()
    st.sidebar.title(f"Hallo, {athlet_name}!")
    menu = st.sidebar.selectbox("Menü", ["📅 Wettkampfkalender", "📊 Gesamtübersicht", "👥 Athleten"])

    # Untermenü für "Athleten"
    eingabe_typ = None
    if menu == "👥 Athleten":
        eingabe_typ = st.sidebar.radio(
            "Optionen",
            ["Athleten anzeigen", "Athleten - Feedback anzeigen", "Neuen Athlet hinzufügen"],
        )
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
        if eingabe_typ == "Athleten anzeigen":
            st.header("Athleten")

            athleten = Person.get_athleten()

            for i, athlet in enumerate(athleten):
                athlet_name = athlet.get_vollname()

                if st.button(athlet_name, key=f"trainer_athlet_{i}"):
                    if st.session_state.get("ausgewaehlter_athlet") == athlet_name:
                        st.session_state.ausgewaehlter_athlet = None
                    else:
                        st.session_state.ausgewaehlter_athlet = athlet_name

                if st.session_state.get("ausgewaehlter_athlet") == athlet_name:
                    zeige_auswertung(athlet_name, df_train, df_regen)

        elif eingabe_typ == "Athleten - Feedback anzeigen":
            # Feedback von Athleten
            render_trainer_feedback_inbox()

        elif eingabe_typ == "Neuen Athlet hinzufügen":
            athlet_hinzufuegen(person)


# def show_trainer_dashboard():

# st.write("Trainer dashboard")


# Trainerprofil anzeigen
# Athletenübersicht anzeigen
# Athleten - dropdown menu
# kalender
