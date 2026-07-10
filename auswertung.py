import streamlit as st
import pandas as pd
import plotly.express as px

# Trainingsdaten werden über TrainingData eingelesen (siehe training_calendar.py),
# damit es für 'triathlon_training.csv' nur eine Stelle im Code gibt, die
# Spalten umbenennt, doppelte Kategoriespalten zusammenführt und Typen
# umwandelt - Kalender und Auswertung sehen so garantiert dieselben Daten.
from training_calendar import TrainingData, spalten_zusammenfuehren, MONATE_DE, AKTIVITAET_FARBEN


# --- HILFSFUNKTIONEN ---
def extrahiere_schlaf_stunden(schlaf_str):
    """Wandelt einen Schlafdauer-String (z. B. '7 h 30 min') in eine Dezimalzahl
    an Stunden um (z. B. 7.5). Gibt 0.0 zurück, wenn der Wert fehlt oder sich
    nicht parsen lässt."""
    try:
        if pd.isna(schlaf_str):
            return 0.0
        teile = str(schlaf_str).split()
        stunden = float(teile[0])
        minuten = float(teile[2]) if len(teile) > 2 else 0.0
        return stunden + (minuten / 60.0)
    except (ValueError, IndexError):
        return 0.0


def get_color(beschwerde):
    """Ordnet einer Beschwerde-Bezeichnung ('leicht', 'mittel', 'stark') eine
    Hintergrundfarbe (CSS-Style-String) für die Tabellendarstellung zu."""
    b = str(beschwerde).lower()
    if "leicht" in b:
        return "background-color: #86efac"  # Grün
    if "mittel" in b:
        return "background-color: #fdba74"  # Orange
    if "stark" in b:
        return "background-color: #fca5a5"  # Rot
    return "background-color: #e5e7eb"  # Default Grau


@st.cache_data
def lade_daten():
    """Lädt und bereinigt Trainings- und Regenerationsdaten.

    Die Trainingsdaten kommen über TrainingData (siehe training_calendar.py),
    das Spaltennamen und doppelte Kategoriespalten bereits normalisiert -
    dieselbe Normalisierung, die auch der Kalender verwendet. Nur die
    Regenerationsdaten werden hier eingelesen, da es dafür (noch) keine
    eigene Datenklasse gibt."""

    df_train = TrainingData().load()

    try:
        df_regen = pd.read_csv("data/triathlon_regeneration.csv", sep=";", encoding="utf-8")
    except UnicodeDecodeError:
        df_regen = pd.read_csv("data/triathlon_regeneration.csv", sep=";", encoding="cp1252")
    except FileNotFoundError:
        st.error("🚨 Fehler: Die Regenerations-CSV wurde nicht gefunden.")
        st.stop()

    df_regen.columns = df_regen.columns.str.strip()

    rename_regen = {
        "Ernaehrung_Kalorien_kcal": "Kalorien",
    }
    rename_regen = {k: v for k, v in rename_regen.items() if k in df_regen.columns}
    df_regen = df_regen.rename(columns=rename_regen)
    df_regen = df_regen.loc[:, ~df_regen.columns.duplicated()]

    # --------------------------------------------------
    # Doppelte Kategoriespalten der Regenerationsdaten zusammenführen (z. B.
    # wenn ein Eingabeformular versehentlich in eine neue statt in die
    # bestehende Spalte schreibt) - für Trainingsdaten übernimmt das bereits
    # TrainingData.load() weiter oben
    # --------------------------------------------------

    if "Schlafqualitaet" in df_regen.columns:
        schlafqualitaet_text = {
            5: "Sehr gut",
            4: "Gut",
            3: "Mittelmäßig",
            2: "Schlecht",
            1: "Sehr schlecht",
        }
        schlafqualitaet_zahl = pd.to_numeric(df_regen["Schlafqualitaet"], errors="coerce").round()
        df_regen["Schlafqualitaet"] = schlafqualitaet_zahl.map(schlafqualitaet_text)
    df_regen = spalten_zusammenfuehren(df_regen, "Schlaf_Dauer", ["Schlafdauer"])
    df_regen = spalten_zusammenfuehren(df_regen, "Schlaf_Gefuehl", ["Schlafqualitaet"])
    df_regen = spalten_zusammenfuehren(df_regen, "Regenerations_Massnahme", ["Regenerationsmassnahmen"])

    # --------------------------------------------------
    # Fehlende Spalten ergänzen
    # --------------------------------------------------

    # Spalten ergänzen, die für die Auswertung gebraucht werden, aber nicht
    # zum Kern-Schema von TrainingData gehören (z. B. weil sie erst mit den
    # neueren Eingabeformularen dazugekommen sind)
    train_spalten = {
        "Datum": pd.NaT,
        "Athlet": "",
        "Aktivitaet": "",
        "Dauer_Minuten": 0,
        "Distanz_km": 0.0,
        "Intensitaet": "",
        "Ø_Herzfrequenz": 0,
        "Max_Herzfrequenz": 0,
        "Gefühl": "",
        "Energielevel": 0,
        "Trainingszufriedenheit": 0,
        "Kommentar": "",
        "Schmerzen": "",
    }

    for spalte, standard in train_spalten.items():
        if spalte not in df_train.columns:
            df_train[spalte] = standard

    # --------------------------------------------------
    # Monats-/Jahres-Hilfsspalten für die Monatsauswahl in der Auswertung
    # (Dauer_Minuten/Distanz_km/Ø_Herzfrequenz/Max_Herzfrequenz sind für
    # df_train bereits durch TrainingData numerisch, nur df_regen braucht das
    # Datum hier noch neu)
    # --------------------------------------------------

    for df in [df_train, df_regen]:
        df["Datum"] = pd.to_datetime(
            df["Datum"],
            errors="coerce",
        )

        df["Jahr"] = df["Datum"].dt.year.fillna(0).astype(int)
        df["Monat"] = df["Datum"].dt.month.fillna(0).astype(int)

        # Zahl wie 202601 für Januar 2026: lässt sich rein numerisch sortieren,
        # ohne dass Januar 2027 vor Dezember 2026 einsortiert wird (was bei
        # alphabetischer Sortierung von 'Monat_Label' passieren würde)
        df["Monat_Sortierschluessel"] = df["Jahr"] * 100 + df["Monat"]

        df["Monat_Label"] = [
            f"{MONATE_DE[m - 1]} {j}" if 1 <= m <= 12 else "Unbekannt" for m, j in zip(df["Monat"], df["Jahr"])
        ]

        df["Wochentag"] = df["Datum"].dt.day_name(locale="de_DE")

    # --------------------------------------------------
    # Schlafstunden berechnen
    # --------------------------------------------------

    if "Schlaf_Dauer" in df_regen.columns:
        df_regen["Schlaf_Stunden"] = df_regen["Schlaf_Dauer"].apply(extrahiere_schlaf_stunden)
    else:
        df_regen["Schlaf_Stunden"] = 0

    return df_train, df_regen


def zeige_auswertung(athlet_name, df_train, df_regen):
    """Diese Funktion stellt die Auswertung grafisch und schriftlich auf einem streamlit dashboard dar."""

    # Überschrift
    st.markdown(
        "<h1 style='text-align: center; color: #1E3A8A;'> Triathlon Performance Lab</h1>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    # Daten filtern
    df_t_ath = df_train[df_train["Athlet"] == athlet_name]
    df_r_ath = df_regen[df_regen["Athlet"] == athlet_name]

    # --- Monatsauswahl (gilt für die gesamte Auswertung) ---
    monats_optionen = (
        pd.concat(
            [df_t_ath[["Monat_Sortierschluessel", "Monat_Label"]], df_r_ath[["Monat_Sortierschluessel", "Monat_Label"]]]
        )
        .drop_duplicates("Monat_Label")
        .sort_values("Monat_Sortierschluessel")["Monat_Label"]
        .tolist()
    )

    if not monats_optionen:
        st.info("Keine Daten für diesen Athleten vorhanden.")
        return

    # Standardmäßig den aktuellen Monat vorauswählen, falls Daten dafür
    # existieren - sonst zeigt die Selectbox sinnvollerweise den letzten
    # Monat, für den tatsächlich Einträge vorhanden sind (s. else-Zweig unten)
    heute = pd.Timestamp.now()
    aktueller_schluessel = heute.year * 100 + heute.month
    monats_schluessel_liste = (
        pd.concat(
            [df_t_ath[["Monat_Sortierschluessel", "Monat_Label"]], df_r_ath[["Monat_Sortierschluessel", "Monat_Label"]]]
        )
        .drop_duplicates("Monat_Label")
        .sort_values("Monat_Sortierschluessel")["Monat_Sortierschluessel"]
        .tolist()
    )
    if aktueller_schluessel in monats_schluessel_liste:
        default_index = monats_schluessel_liste.index(aktueller_schluessel)
    else:
        default_index = len(monats_optionen) - 1  # letzter verfügbarer Monat

    st.markdown("### Monat auswählen")
    selected_monat = st.selectbox("Monat", monats_optionen, index=default_index, key="auswertung_monat_select")

    # Daten auf den gewählten Monat einschränken
    df_t_ath = df_t_ath[df_t_ath["Monat_Label"] == selected_monat].copy()
    df_r_ath = df_r_ath[df_r_ath["Monat_Label"] == selected_monat].copy()

    # Woche innerhalb des Monats bestimmen (Woche 1 = Tag 1-7, Woche 2 = Tag 8-14, ...)
    for df in [df_t_ath, df_r_ath]:
        df["Woche_Nr"] = ((df["Datum"].dt.day - 1) // 7) + 1
        df["Woche_Label"] = "Woche " + df["Woche_Nr"].astype(str)

    # Tabs
    tab_training, tab_recovery = st.tabs(["🏋️‍♂️ Trainings-Performance", "🛌 Regeneration & Vitalwerte"])

    # --- TAB 1: TRAINING ---
    with tab_training:
        st.markdown(f"## Trainingsübersicht: {athlet_name}")
        st.markdown(f"### {selected_monat}")

        df_distanz = df_t_ath[df_t_ath["Aktivitaet"].str.lower() != "ruhetag"].copy()
        woche_aktivitaet = (
            df_distanz.groupby(["Woche_Nr", "Woche_Label", "Aktivitaet"])["Distanz_km"]
            .sum()
            .reset_index()
            .sort_values("Woche_Nr")
        )

        # Chronologische Reihenfolge der Wochen auf der x-Achse sicherstellen
        wochen_reihenfolge = (
            woche_aktivitaet.drop_duplicates("Woche_Label").sort_values("Woche_Nr")["Woche_Label"].tolist()
        )

        if woche_aktivitaet.empty:
            st.info("Keine Trainingsdaten für diesen Monat vorhanden.")
        else:
            fig_km = px.bar(
                woche_aktivitaet,
                x="Woche_Label",
                y="Distanz_km",
                color="Aktivitaet",
                barmode="group",
                title=f"Trainingsdistanzen pro Woche – {selected_monat} (exkl. Ruhetage)",
                color_discrete_map=AKTIVITAET_FARBEN,
                category_orders={"Woche_Label": wochen_reihenfolge},
            )
            fig_km.update_xaxes(title="Woche")
            fig_km.update_yaxes(title="Distanz (km)")
            st.plotly_chart(fig_km, width="stretch")

        st.markdown("### Leistungsfaktoren & Schmerzprotokoll:")
        col_left, col_right = st.columns(2)

        with col_left:
            max_puls = df_t_ath["Max_Herzfrequenz"].max()
            ruhepuls_schnitt = df_r_ath["Ruhepuls_bpm"].mean()
            st.subheader("📈 Leistungskennzahlen")

            # 1. VO2max
            if pd.notna(ruhepuls_schnitt) and ruhepuls_schnitt > 0 and pd.notna(max_puls):
                vo2max = 15.3 * (max_puls / ruhepuls_schnitt)
                st.write(f"**Geschätzte VO2max:** {vo2max:.1f} ml/min/kg")

                # 2. Geschätzte FTP (hrFTP)
                # Als Faustformel für Radsportler wird oft 75-80% der HFmax als Schwellenbereich angenommen.
                # Dies ist eine Schätzung, da kein Leistungsmesser vorliegt.
                hr_ftp_schätzung = max_puls * 0.82  # Klassischer Richtwert für Schwellen-HF
                st.write(f"**Geschätzte Schwellen-HF (hrFTP):** {int(hr_ftp_schätzung)} bpm")
            else:
                st.info("Nicht genügend Pulsdaten für Berechnungen.")

            if pd.notna(max_puls):
                st.write(f"**Max. Herzfrequenz (Monat):** {int(max_puls)} bpm")

            # 3. TSS Berechnung
            df_aktiv = df_t_ath[df_t_ath["Aktivitaet"].str.lower() != "ruhetag"].copy()
            if not df_aktiv.empty and pd.notna(max_puls) and max_puls > 0:
                schwellen_hf = 0.82 * max_puls  # Verwendung des gleichen Wertes wie oben
                df_aktiv["TSS"] = (
                    (df_aktiv["Dauer_Minuten"] / 60) * (df_aktiv["Ø_Herzfrequenz"] / schwellen_hf) ** 2 * 100
                )
                tss_gesamt = df_aktiv["TSS"].sum()
                st.write(f"**TSS (geschätzt, Monat gesamt):** {tss_gesamt:.0f}")
                st.caption("Berechnung basiert auf hrTSS (HF-basierter Stress Score).")

        with col_right:
            st.subheader("⚠️ Schmerz- & Beschwerdeprotokoll")
            schmerzen_df = df_t_ath[df_t_ath["Schmerzen"].notna() & (df_t_ath["Schmerzen"].str.lower() != "keine")]

            if not schmerzen_df.empty:
                df_schmerz = schmerzen_df["Schmerzen"].value_counts().reset_index()
                df_schmerz.columns = ["Beschwerde", "Anzahl"]
                st.table(df_schmerz.style.apply(lambda row: [get_color(row["Beschwerde"])] * len(row), axis=1))
            else:
                st.write("🟢 Keine Schmerzen dokumentiert.")

    # --- TAB 2: REGENERATION ---
    with tab_recovery:
        st.markdown(f"## Regenerations- & Vitalwerte: {athlet_name}")
        st.markdown(f"### {selected_monat}")

        schlaf_avg = df_r_ath["Schlaf_Stunden"].mean()
        h, m = (int(schlaf_avg), int((schlaf_avg - int(schlaf_avg)) * 60)) if pd.notna(schlaf_avg) else (0, 0)

        m1, m2, m3 = st.columns(3)
        m1.metric("Ø Schlaf (pro Tag)", f"{h}h {m}m")
        m2.metric("Ø Ruhepuls (pro Tag)", f"{df_r_ath['Ruhepuls_bpm'].mean():.1f} bpm")
        m3.write(f"**Ø Kalorien:** {df_r_ath['Kalorien'].mean():.0f} kcal")
        m3.caption(
            f"KH: {df_r_ath['Kohlenhydrate_g'].mean():.0f}g | P: {df_r_ath['Proteine_g'].mean():.0f}g | F: {df_r_ath['Fette_g'].mean():.0f}g"
        )

        if not df_r_ath.empty:
            # Wöchentliche Mittelwerte für Ruhepuls & HRV innerhalb des gewählten Monats
            woche_vitalwerte = (
                df_r_ath.groupby(["Woche_Nr", "Woche_Label"])[["Ruhepuls_bpm", "HRV_ms"]]
                .mean()
                .reset_index()
                .sort_values("Woche_Nr")
            )
            wochen_reihenfolge_regen = woche_vitalwerte["Woche_Label"].tolist()

            col_g1, col_g2 = st.columns(2)
            col_g1.plotly_chart(
                px.line(
                    woche_vitalwerte,
                    x="Woche_Label",
                    y="Ruhepuls_bpm",
                    title=f"Trend Ruhepuls (bpm) – {selected_monat}",
                    color_discrete_sequence=["red"],
                    category_orders={"Woche_Label": wochen_reihenfolge_regen},
                    markers=True,
                ).update_xaxes(title="Woche"),
                width="stretch",
            )
            col_g2.plotly_chart(
                px.line(
                    woche_vitalwerte,
                    x="Woche_Label",
                    y="HRV_ms",
                    title=f"Trend HRV (ms) – {selected_monat}",
                    color_discrete_sequence=["green"],
                    category_orders={"Woche_Label": wochen_reihenfolge_regen},
                    markers=True,
                ).update_xaxes(title="Woche"),
                width="stretch",
            )
        else:
            st.info("Keine Regenerationsdaten für diesen Monat vorhanden.")
