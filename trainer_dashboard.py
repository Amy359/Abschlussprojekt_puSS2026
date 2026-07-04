import os
import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_calendar import calendar
import plotly.express as px

from personenklasse import Person
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
    df.to_csv("data/wettkaempfe.csv", sep=";", index=False, encoding="utf-8")


def zeige_wettkaempfe(df):
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

    # Daten laden
    df_train, df_regen = lade_daten()

    # Navigation und sidebar
    athlet_name = person.get_vollname()
    st.sidebar.title(f"Hallo, {athlet_name}!")
    menu = st.sidebar.radio("Menü", ["📅 Wettkampfkalender", "📊 Gesamtübersicht", "👥 Athleten"])

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
        st.header("Athleten")

        athleten = Person.get_athleten()

        for i, athlet in enumerate(athleten):
            if st.button(athlet.get_vollname(), key=f"trainer_athlet_{i}"):
                zeige_auswertung(athlet.get_vollname(), df_train, df_regen)

        # Feedback von Athleten
        render_trainer_feedback_inbox()


# def show_trainer_dashboard():

# st.write("Trainer dashboard")


# Trainerprofil anzeigen
# Athletenübersicht anzeigen
# Athleten - dropdown menu
# kalender
