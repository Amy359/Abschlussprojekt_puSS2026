import streamlit as st
import pandas as pd
import io
from datetime import datetime
from html import escape
from pathlib import Path
from training_calendar import render_calendar
from auswertung import lade_daten, zeige_auswertung


def save_to_csv(df, filename):
    """Speichert ein DataFrame als Semikolon-getrennte CSV-Datei (UTF-8)."""
    df.to_csv(filename, sep=";", index=False, encoding="utf-8")


def zeige_training_eingabe(athlet_name):
    """Zeigt das Formular zur Eingabe eines Trainingseintrags (Wohlbefinden,
    Sportart, Dauer, Distanz, Puls usw.) und hängt den Eintrag bei Absenden
    an 'data/triathlon_training.csv' an."""
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

        energie = st.slider("Energie vor dem Training", 1, 10, 7)

        trainingsgefuehl = st.slider("Wie zufrieden bist du mit deinem Training?", 1, 10, 8)

        tagebuch = st.text_area(
            "Erzähl kurz von deinem Training",
            height=120,
            placeholder="Wie hast du dich gefühlt? Was ist gut oder schlecht gelaufen?",
        )

        auffaelligkeiten = st.text_area("Was ist dir besonders aufgefallen?", height=80)

        beschwerden = st.text_area("Beschwerden oder Schmerzen", height=80, placeholder="Falls vorhanden...")

        st.divider()

        st.subheader("Trainingsdaten")

        aktivitaet = st.selectbox(
            "Aktivität",
            ["Schwimmen", "Radfahren", "Laufen", "Krafttraining", "Koppeltraining", "Mobilität", "Sonstiges"],
        )

        col_dauer1, col_dauer2 = st.columns(2)
        dauer_stunden = col_dauer1.number_input("Dauer (Stunden)", min_value=0, step=1)
        dauer_minuten = col_dauer2.number_input("Dauer (Minuten)", min_value=0, max_value=55, step=5)
        dauer = dauer_stunden * 60 + dauer_minuten

        col_distanz1, col_distanz2 = st.columns(2)
        distanz_km = col_distanz1.number_input("Distanz (km)", min_value=0, step=1)
        distanz_m = col_distanz2.number_input("Distanz (m)", min_value=0, max_value=950, step=50)
        distanz = distanz_km + (distanz_m / 1000)

        intensitaet = st.select_slider(
            "Intensität", options=["Regeneration", "Locker", "Mittel", "Hart", "Wettkampfnah"]
        )

        durchschnittspuls = st.number_input("Durchschnittspuls (optional)", min_value=0, value=30)

        max_puls = st.number_input("Maximalpuls (optional)", min_value=0, value=100)

        if st.form_submit_button("Training speichern"):
            # Tagebuch und Auffälligkeiten werden in der Kategoriespalte
            # 'Kommentar' gespeichert - derselben Spalte, in der auch die
            # Trainer im Kalender ihre Kommentare sehen
            kommentar = " | ".join(text for text in [tagebuch.strip(), auffaelligkeiten.strip()] if text)

            new_row = pd.DataFrame(
                [
                    {
                        "Datum": datum.strftime("%Y-%m-%d"),
                        "Athlet": athlet_name,
                        "Aktivitaet": aktivitaet,
                        "Dauer_Minuten": dauer,
                        "Distanz_km": distanz,
                        "Intensitaet": intensitaet,
                        "Ø_Herzfrequenz": durchschnittspuls,
                        "Max_Herzfrequenz": max_puls,
                        "Gefühl": wohlbefinden,
                        "Energielevel": energie,
                        "Trainingszufriedenheit": trainingsgefuehl,
                        "Kommentar": kommentar,
                        "Schmerzen": beschwerden,
                    }
                ]
            )

            # new_row auf genau die Spalten der bestehenden CSV zurechtstutzen:
            # pd.concat() würde sonst für jeden Dict-Key, der (z. B. durch einen
            # Tippfehler) nicht exakt einem bestehenden Spaltennamen entspricht,
            # stillschweigend eine neue Spalte anlegen statt einen Fehler zu werfen
            for col in df_train.columns:
                if col not in new_row.columns:
                    new_row[col] = pd.NA
            new_row = new_row[df_train.columns]

            df_train = pd.concat([df_train, new_row], ignore_index=True)

            save_to_csv(df_train, "data/triathlon_training.csv")

            st.cache_data.clear()

            st.success("Training erfolgreich gespeichert!")


def zeige_regen_eingabe(athlet_name):
    """Zeigt das Formular zur Eingabe eines Regenerationseintrags (Schlaf,
    Erholung, Maßnahmen, Körpergefühl usw.) und hängt den Eintrag bei
    Absenden an 'data/triathlon_regeneration.csv' an."""

    st.header("Regenerationstagebuch")

    _, df_regen = lade_daten()

    with st.form("regen_form"):
        datum = st.date_input("Datum", datetime.now())

        schlafdauer = st.text_input("Schlafdauer", "8 h")

        schlafqualitaet = st.slider("⭐ Schlafqualität", 1, 5, 4)

        erholung = st.slider("Wie erholt fühlst du dich heute?", 1, 10, 7)

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
                "Sonstiges",
            ],
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
                "Sonstiges",
            ],
        )

        ernaehrung = st.text_area("Ernährung & Flüssigkeit")

        notizen = st.text_area("Sonstige Gedanken", height=120)

        if st.form_submit_button("Regeneration speichern"):
            # Die Kategoriespalte 'Schlaf_Gefuehl' speichert Text, der Slider
            # liefert aber eine Zahl (1-5) - hier in die passende Textstufe
            # übersetzen, bevor der Datensatz gespeichert wird
            schlafqualitaet_text = {5: "Sehr gut", 4: "Gut", 3: "Mittelmäßig", 2: "Schlecht", 1: "Sehr schlecht"}

            new_row = pd.DataFrame(
                [
                    {
                        "Datum": datum.strftime("%Y-%m-%d"),
                        "Athlet": athlet_name,
                        "Schlaf_Dauer": schlafdauer,
                        "Schlaf_Gefuehl": schlafqualitaet_text[schlafqualitaet],
                        "Erholung": erholung,
                        "Regenerations_Massnahme": ", ".join(massnahmen),
                        "Koerpergefuehl": ", ".join(koerpergefuehl),
                        "Ernaehrung": ernaehrung,
                        "Notizen": notizen,
                    }
                ]
            )

            # new_row auf genau die Spalten der bestehenden CSV zurechtstutzen
            # (siehe Kommentar in zeige_training_eingabe weiter oben)
            for col in df_regen.columns:
                if col not in new_row.columns:
                    new_row[col] = pd.NA

            new_row = new_row[df_regen.columns]

            df_regen = pd.concat([df_regen, new_row], ignore_index=True)

            save_to_csv(df_regen, "data/triathlon_regeneration.csv")

            st.cache_data.clear()

            st.success("Regeneration erfolgreich gespeichert!")


def athlete_dashboard(person):
    """Hauptansicht für eingeloggte Athleten.

    Baut die Sidebar-Navigation auf (Kalender, Eingaben, Auswertung,
    Datenexport) und rendert je nach Auswahl die entsprechende Unterseite
    für die übergebene Person (ein Person-Objekt mit Rolle 'Athlet')."""

    athlet_name = person.get_vollname()
    df_train, df_regen = lade_daten()

    # Sidebar
    st.sidebar.image("images/logo.png")
    # Manueller Zeilenumbruch statt einem einzeiligen Titel, damit lange Namen
    # nicht mitten im Wort umbrechen, sondern 'Hallo,' und der Name je eine
    # eigene Zeile bekommen
    st.sidebar.markdown(
        f"<h1 style='margin:0;line-height:1.2'>Hallo,<br>{escape(athlet_name)}!</h1>",
        unsafe_allow_html=True,
    )

    menu = st.sidebar.selectbox(
        "Menü", ["📅 Mein Kalender", "⌨ Eingaben", "📊 Meine Auswertung", "💾 Daten exportieren"]
    )

    # Untermenü für "Eingaben"
    eingabe_typ = None
    if menu == "⌨ Eingaben":
        eingabe_typ = st.sidebar.selectbox(
            "Was möchtest du eingeben?",
            ["Training", "Regeneration"],
        )

    # --- Seiten ---

    if menu == "📅 Mein Kalender":
        st.header("Dein Trainings-Kalender")
        # render_calendar aus training_calendar.py mit role="athlete"
        render_calendar(
            role="athlete",
            current_user=athlet_name,
            csv_path=Path("data/triathlon_training.csv"),
        )

    elif menu == "⌨ Eingaben":
        if eingabe_typ == "Training":
            zeige_training_eingabe(athlet_name)
        elif eingabe_typ == "Regeneration":
            zeige_regen_eingabe(athlet_name)

    elif menu == "📊 Meine Auswertung":
        zeige_auswertung(athlet_name, df_train, df_regen)

    elif menu == "💾 Daten exportieren":
        st.header("Daten exportieren")

        df_train, df_regen = lade_daten()

        # Nur Daten des angemeldeten Athleten
        train_export = df_train[df_train["Athlet"] == athlet_name]
        regen_export = df_regen[df_regen["Athlet"] == athlet_name]

        # Excel-Datei im Speicher erzeugen
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            train_export.to_excel(writer, sheet_name="Training", index=False)

            regen_export.to_excel(writer, sheet_name="Regeneration", index=False)

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
