import os
import streamlit as st
import pandas as pd
from datetime import datetime, date
from html import escape
from streamlit_calendar import calendar
import plotly.express as px

from personenklasse import Person
from login import hash_password
from auswertung import lade_daten, zeige_auswertung
from training_calendar import render_trainer_feedback_inbox, AKTIVITAET_FARBEN


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

    st.subheader("➕ Neuen Athlet anlegen")

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

        # Geburtsdatum dient als initiales Passwort (siehe check_login in login.py);
        # der Athlet kennt es und kann sich damit sofort anmelden
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

        # Personen-Registry (im Speicher gehalten seit main.py-Start) neu aufbauen,
        # sonst würde der neue Athlet erst nach einem vollständigen Neustart der
        # App in Person.get_athleten() auftauchen
        Person.load_data_from_csv("triathlon_personen.csv")

        athlet = f"{vorname} {nachname}"
        st.session_state.athlet_hinzufuegen_erfolg = f"{athlet} wurde erfolgreich angelegt."
        st.session_state.athlet_hinzufuegen_formular_version = formular_version + 1
        st.rerun()


def person_bearbeiten_formular(person):
    """Rendert ein mit den aktuellen Stammdaten vorausgefülltes Formular für
    eine Person (Athlet oder Trainer) und speichert Änderungen in
    'triathlon_personen.csv' sowie 'users_secure.csv'. Wird sowohl für die
    Athleten-Bearbeitung durch den Trainer als auch für die
    Trainer-Selbstbearbeitung verwendet."""

    # Vor-Namen der übergebenen Person merken, um beim Speichern die richtige
    # CSV-Zeile wiederzufinden, auch wenn Vor-/Nachname selbst geändert werden
    alter_vorname, alter_nachname = person.vorname, person.nachname
    ist_athlet = person.get_role() == "Athlet"

    with st.form(f"bearbeiten_form_{person.get_loginname()}"):
        col1, col2 = st.columns(2)

        vorname = col1.text_input("Vorname", value=person.vorname)
        nachname = col2.text_input("Nachname", value=person.nachname)

        geburtsdatum = col1.date_input(
            "Geburtsdatum",
            value=person.geburtsdatum,
            min_value=date(1920, 1, 1),
            max_value=date.today(),
        )
        nationalitaet = col2.text_input("Nationalität", value=person.nationalitaet)

        if ist_athlet:
            spezialisierung = col1.text_input("Spezialisierung", value=", ".join(person.spezialisierung))

        verein = st.text_input("Verein", value=person.verein)

        st.caption(
            "Hinweis: Das Geburtsdatum ist gleichzeitig das Passwort. Bei einer "
            "Änderung wird das Passwort automatisch mit aktualisiert."
        )

        speichern = st.form_submit_button("💾 Änderungen speichern")

    if not speichern:
        return

    vorname = vorname.strip().title()
    nachname = nachname.strip().title()
    nationalitaet = nationalitaet.strip().title()
    verein = verein.strip().title()

    if not vorname or not nachname:
        st.error("Vorname und Nachname müssen ausgefüllt sein.")
        return

    personen_datei = "data/triathlon_personen.csv"
    users_datei = "data/users_secure.csv"
    geburtsdatum_text = geburtsdatum.strftime("%d.%m.%Y")
    altes_geburtsdatum_text = person.geburtsdatum.strftime("%d.%m.%Y")

    df_personen = pd.read_csv(personen_datei, sep=";")
    df_users = pd.read_csv(users_datei, sep=";")

    zeile = (df_personen["Vorname"].astype(str).str.lower() == alter_vorname.lower()) & (
        df_personen["Nachname"].astype(str).str.lower() == alter_nachname.lower()
    )

    if not zeile.any():
        st.error("Person wurde nicht gefunden. Bitte die Seite neu laden und erneut versuchen.")
        return

    name_geaendert = (vorname.lower() != alter_vorname.lower()) or (nachname.lower() != alter_nachname.lower())

    if name_geaendert:
        gleicher_name = (
            (df_personen["Vorname"].astype(str).str.lower() == vorname.lower())
            & (df_personen["Nachname"].astype(str).str.lower() == nachname.lower())
            & ~zeile
        )
        if gleicher_name.any():
            st.error("Eine Person mit diesem Vor- und Nachnamen existiert bereits.")
            return

    df_personen.loc[zeile, "Vorname"] = vorname
    df_personen.loc[zeile, "Nachname"] = nachname
    df_personen.loc[zeile, "Geburtsdatum"] = geburtsdatum_text
    df_personen.loc[zeile, "Nationalitaet"] = nationalitaet
    df_personen.loc[zeile, "Verein"] = verein
    if ist_athlet:
        df_personen.loc[zeile, "Spezialisierung"] = spezialisierung.strip().title()

    df_personen.to_csv(personen_datei, sep=";", index=False, encoding="utf-8")

    users_zeile = (df_users["Vorname"].astype(str).str.lower() == alter_vorname.lower()) & (
        df_users["Nachname"].astype(str).str.lower() == alter_nachname.lower()
    )
    df_users.loc[users_zeile, "Vorname"] = vorname
    df_users.loc[users_zeile, "Nachname"] = nachname
    if geburtsdatum_text != altes_geburtsdatum_text:
        df_users.loc[users_zeile, "Password_Hash"] = hash_password(geburtsdatum_text)

    df_users.to_csv(users_datei, sep=";", index=False, encoding="utf-8")

    # Personen-Registry neu aufbauen, damit die Änderung sofort überall sichtbar ist
    Person.load_data_from_csv("triathlon_personen.csv")

    # Falls die bearbeitete Person die aktuell angemeldete ist (Trainer bearbeitet
    # sich selbst), die Session-Referenz auf die neu geladene Instanz umstellen -
    # sonst würde die Sidebar weiter den alten Namen zeigen
    if st.session_state.person.get_loginname() == person.get_loginname():
        for p in Person.get_athleten() + Person.get_trainer():
            if p.get_loginname() == f"{vorname.lower()}.{nachname.lower()}":
                st.session_state.person = p
                break

    st.success(f"{vorname} {nachname} wurde aktualisiert.")
    st.rerun()


def athlet_bearbeiten_liste():
    """Zeigt eine Liste aller Athleten; ein Klick auf einen Athleten öffnet
    darunter dessen vorausgefülltes Bearbeitungsformular (person_bearbeiten_formular)."""

    st.subheader("✏️ Athlet bearbeiten")

    athleten = Person.get_athleten()
    if not athleten:
        st.caption("Noch keine Athleten vorhanden.")
        return

    for i, athlet in enumerate(athleten):
        athlet_name = athlet.get_vollname()

        if st.button(athlet_name, key=f"bearbeiten_athlet_{i}"):
            if st.session_state.get("athlet_bearbeiten_ausgewaehlt") == athlet_name:
                st.session_state.athlet_bearbeiten_ausgewaehlt = None
            else:
                st.session_state.athlet_bearbeiten_ausgewaehlt = athlet_name

        if st.session_state.get("athlet_bearbeiten_ausgewaehlt") == athlet_name:
            person_bearbeiten_formular(athlet)


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

    trainer_name = person.get_vollname()

    # Trainer bearbeitet das eigene Profil (ausgelöst über den Button in der
    # Sidebar, siehe logout() in login.py) - ersetzt die normale Ansicht,
    # bis er zum Dashboard zurückkehrt
    if st.session_state.get("zeige_profil_bearbeitung"):
        st.sidebar.image("images/logo.png")
        st.sidebar.markdown(
            f"<h1 style='margin:0;line-height:1.2'>Hallo,<br>{escape(trainer_name)}!</h1>",
            unsafe_allow_html=True,
        )
        st.header("Profil bearbeiten")
        if st.button("← Zurück zum Dashboard"):
            st.session_state.zeige_profil_bearbeitung = False
            st.rerun()
        person_bearbeiten_formular(person)
        return

    # Daten laden
    df_train, df_regen = lade_daten()

    # Navigation und sidebar
    st.sidebar.image("images/logo.png")
    st.sidebar.markdown(
        f"<h1 style='margin:0;line-height:1.2'>Hallo,<br>{escape(trainer_name)}!</h1>",
        unsafe_allow_html=True,
    )
    menu = st.sidebar.selectbox("Menü", ["📅 Wettkampfkalender", "📊 Gesamtübersicht", "👥 Athleten"])

    # Untermenü für "Athleten"
    eingabe_typ = None
    if menu == "👥 Athleten":
        eingabe_typ = st.sidebar.radio(
            "Optionen",
            ["Athleten anzeigen", "Athleten - Feedback anzeigen", "Athleten hinzufügen oder bearbeiten"],
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

            # Zeigt alle Athleten, nicht gefiltert auf den angemeldeten Trainer:
            # Person.get_athleten_von_trainer() steht dafür bereit, sobald das
            # Trainer-Feld für jeden Athleten gepflegt ist
            athleten = Person.get_athleten()

            for i, athlet in enumerate(athleten):
                athlet_name = athlet.get_vollname()

                # Klick auf den bereits ausgewählten Athleten klappt die
                # Auswertung wieder zu (Toggle), Klick auf einen anderen
                # Athleten wechselt die Auswahl
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

        elif eingabe_typ == "Athleten hinzufügen oder bearbeiten":
            st.header("Athleten hinzufügen oder bearbeiten")
            athlet_hinzufuegen(person)
            st.divider()
            athlet_bearbeiten_liste()
