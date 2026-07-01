import streamlit as st
import pandas as pd
import io
from datetime import datetime
from pathlib import Path
from training_calendar import render_calendar
from auswertung import lade_daten, zeige_auswertung

def save_to_csv(df, filename):
    df.to_csv(filename, sep=";", index=False, encoding="utf-8")


def zeige_training_eingabe(athlet_name):
    st.header("Trainingstagebuch")

    df_train, _ = lade_daten()

    with st.form("training_form"):

        datum = st.date_input("Datum", datetime.now())

        st.subheader(" Wie ging es dir heute?")

        wohlbefinden = st.select_slider(
            "Wie hast du dich insgesamt gefühlt?",
            options=[
                "Erschöpft",
                "Müde",
                "Neutral",
                "Gut",
                "Sehr gut",
            ],
            value="Gut",
        )

        energie = st.slider(
            "Energie vor dem Training",
            1, 10, 7
        )

        trainingsgefuehl = st.slider(
            "Wie zufrieden bist du mit deinem Training?",
            1, 10, 8
        )

        tagebuch = st.text_area(
            "Erzähl kurz von deinem Training",
            height=120,
            placeholder="Wie hast du dich gefühlt? Was ist gut oder schlecht gelaufen?"
        )

        auffaelligkeiten = st.text_area(
            "Was ist dir besonders aufgefallen?",
            height=80
        )

        beschwerden = st.text_area(
            "Beschwerden oder Schmerzen",
            height=80,
            placeholder="Falls vorhanden..."
        )

        st.divider()

        st.subheader("Trainingsdaten")

        sportart = st.selectbox(
            "Sportart",
            [
                "Schwimmen",
                "Radfahren",
                "Laufen",
                "Krafttraining",
                "Koppeltraining",
                "Mobilität",
                "Sonstiges"
            ]
        )

        dauer = st.number_input(
            "Dauer (Minuten)",
            min_value=0
        )

        distanz = st.number_input(
            "Distanz (km)",
            min_value=0.0,
            step=0.1
        )

        intensitaet = st.select_slider(
            "Intensität",
            options=[
                "Regeneration",
                "Locker",
                "Mittel",
                "Hart",
                "Wettkampfnah"
            ]
        )

        durchschnittspuls = st.number_input(
            "Durchschnittspuls (optional)",
            min_value=0
        )

        max_puls = st.number_input(
            "Maximalpuls (optional)",
            min_value=0
        )

        if st.form_submit_button("Training speichern"):

            new_row = pd.DataFrame([{

                "Datum": datum.strftime("%Y-%m-%d"),
                "Athlet": athlet_name,

                "Wohlbefinden": wohlbefinden,
                "Energielevel": energie,
                "Trainingszufriedenheit": trainingsgefuehl,
                "Trainingstagebuch": tagebuch,
                "Auffaelligkeiten": auffaelligkeiten,
                "Beschwerden": beschwerden,

                "Sportart": sportart,
                "Dauer_Minuten": dauer,
                "Distanz_km": distanz,
                "Intensitaet": intensitaet,
                "Durchschnittspuls": durchschnittspuls,
                "Maximalpuls": max_puls

            }])

            df_train = pd.concat([df_train, new_row], ignore_index=True)

            save_to_csv(df_train, "data/triathlon_training.csv")

            st.cache_data.clear()

            st.success("Training erfolgreich gespeichert!")


def zeige_regen_eingabe(athlet_name):

    st.header("Regenerationstagebuch")

    _, df_regen = lade_daten()

    with st.form("regen_form"):

        datum = st.date_input("Datum", datetime.now())

        schlafdauer = st.text_input(
            "Schlafdauer",
            "8 h"
        )

        schlafqualitaet = st.slider(
            "⭐ Schlafqualität",
            1,
            5,
            4
        )

        erholung = st.slider(
            "Wie erholt fühlst du dich heute?",
            1,
            10,
            7
        )

        massnahmen = st.multiselect(

            "Welche Regenerationsmaßnahmen hast du durchgeführt?",

            [

                "Physiotherapie",
                "Massage",
                "Blackroll",
                "Dehnen",
                "Mobility",
                "Sauna",
                "Eistonne",
                "Kompressionsstiefel",
                "Yoga",
                "Meditation",
                "Atemübungen",
                "Spaziergang",
                "Ruhetag",
                "Sonstiges"

            ]

        )

        koerpergefuehl = st.multiselect(

            "Wie fühlt sich dein Körper an?",

            [

                "Beine frisch",
                "Beine schwer",
                "Muskelkater",
                "Rücken verspannt",
                "Schultern verspannt",
                "Kniebeschwerden",
                "Keine Beschwerden",
                "Sonstiges"

            ]

        )

        ernaehrung = st.text_area(
            "Ernährung & Flüssigkeit"
        )

        notizen = st.text_area(
            "Sonstige Gedanken",
            height=120
        )

        if st.form_submit_button("Regeneration speichern"):

            new_row = pd.DataFrame([{

                "Datum": datum.strftime("%Y-%m-%d"),
                "Athlet": athlet_name,

                "Schlafdauer": schlafdauer,
                "Schlafqualitaet": schlafqualitaet,
                "Erholung": erholung,

                "Regenerationsmassnahmen": ", ".join(massnahmen),

                "Koerpergefuehl": ", ".join(koerpergefuehl),

                "Ernaehrung": ernaehrung,

                "Notizen": notizen

            }])

            df_regen = pd.concat([df_regen, new_row], ignore_index=True)

            save_to_csv(df_regen, "data/triathlon_regeneration.csv")

            st.cache_data.clear()

            st.success("Regeneration erfolgreich gespeichert!")



def athlete_dashboard(person):
    
    athlet_name = person.get_vollname()
    df_train, df_regen = lade_daten()

    # Sidebar
    st.sidebar.title(f"Hallo, {athlet_name}!")
    menu = st.sidebar.selectbox(
        "Menü",
        [
            "Mein Kalender",
            "Eingaben",
            "Meine Auswertung",
            "Daten exportieren",
        ],
    )

    # Untermenü für "Eingaben"
    eingabe_typ = None
    if menu == "Eingaben":
        eingabe_typ = st.sidebar.selectbox(
            "Was möchtest du eingeben?",
            ["Training", "Regeneration"],
        )

    # --- Seiten ---

    if menu == "Mein Kalender":
        st.header("Dein Trainings-Kalender")
        # render_calendar aus training_calendar.py mit role="athlete"
        render_calendar(
            role="athlete",
            current_user=athlet_name,
            csv_path=Path("data/triathlon_training.csv"),
        )

    elif menu == "Eingaben":
        if eingabe_typ == "Training":
            zeige_training_eingabe(athlet_name)
        elif eingabe_typ == "Regeneration":
            zeige_regen_eingabe(athlet_name)

    elif menu == "Meine Auswertung":
        zeige_auswertung(athlet_name, df_train, df_regen)
    
    elif menu == "Daten exportieren":

        st.header("Daten exportieren")

        df_train, df_regen = lade_daten()

        # Nur Daten des angemeldeten Athleten
        train_export = df_train[df_train["Athlet"] == athlet_name]
        regen_export = df_regen[df_regen["Athlet"] == athlet_name]

        # Excel-Datei im Speicher erzeugen
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            train_export.to_excel(
                writer,
                sheet_name="Training",
                index=False
            )

            regen_export.to_excel(
                writer,
                sheet_name="Regeneration",
                index=False
            )

        output.seek(0)

        st.success("Deine Daten sind bereit.")

        st.download_button(
            label="Excel-Datei herunterladen",
            data=output,
            file_name=f"{athlet_name}_Triathlon_Daten.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

if __name__ == "__main__":
    st.set_page_config(
        page_title="Athleten Dashboard",
        layout="wide",
        page_icon="🏊",
    )
    st.error("⚠️ Bitte das Dashboard über die Haupt-App starten (mit Login).")
    st.stop()