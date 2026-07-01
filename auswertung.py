import streamlit as st
import pandas as pd
import plotly.express as px


MONATE_DE = [
    "Januar", "Februar", "März", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Dezember",
]


# --- HILFSFUNKTIONEN ---
def extrahiere_schlaf_stunden(schlaf_str):
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
    b = str(beschwerde).lower()
    if "leicht" in b:
        return "background-color: #86efac"  # Grün
    if "mittel" in b:
        return "background-color: #fdba74"  # Orange
    if "stark" in b:
        return "background-color: #fca5a5"  # Rot
    return "background-color: #e5e7eb"  # Default Grau


@st.cache_data  # wenn nichts neues eingelesen wird, arbeitet streamlit immer mit den letzten daten
def lade_daten():
    """Diese Funktion lädt und bereinigt Daten aus einer csv Datei."""
    try:
        df_train = pd.read_csv("data/triathlon_training.csv", sep=";", encoding="utf-8")
        df_regen = pd.read_csv("data/triathlon_regeneration.csv", sep=";", encoding="utf-8")
    except (UnicodeDecodeError, FileNotFoundError):
        try:
            df_train = pd.read_csv("data/triathlon_training.csv", sep=";", encoding="cp1252")
            df_regen = pd.read_csv("data/triathlon_regeneration.csv", sep=";", encoding="cp1252")
        except FileNotFoundError:
            st.error("🚨 Fehler: Die CSV-Dateien wurden nicht im Ordner 'data' gefunden!")
            st.stop()

    # Spaltennamen bereinigen & umbenennen
    df_train.columns = df_train.columns.str.strip()
    df_regen.columns = df_regen.columns.str.strip()
    df_train = df_train.rename(columns={"Aktivität": "Aktivitaet", "Schmerzen_Beschwerden": "Schmerzen"})
    df_regen = df_regen.rename(columns={"Ernaehrung_Kalorien_kcal": "Kalorien"})

    # Datumsformatierung & Berechnungen
    for df in [df_train, df_regen]:
        df["Datum"] = pd.to_datetime(df["Datum"], format="%Y-%m-%d", errors="coerce")
        df["Jahr"] = df["Datum"].dt.year.fillna(0).astype(int)
        df["Monat"] = df["Datum"].dt.month.fillna(0).astype(int)
        # Sortierschlüssel (z.B. 202601 für Januar 2026) + lesbares Label (z.B. "Januar 2026")
        df["Monat_Sortierschluessel"] = df["Jahr"] * 100 + df["Monat"]
        df["Monat_Label"] = [
            f"{MONATE_DE[m - 1]} {j}" if 1 <= m <= 12 else "Unbekannt"
            for m, j in zip(df["Monat"], df["Jahr"])
        ]

    df_regen["Schlaf_Stunden"] = df_regen["Schlaf_Dauer"].apply(extrahiere_schlaf_stunden)

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
        pd.concat([df_t_ath[["Monat_Sortierschluessel", "Monat_Label"]],
                   df_r_ath[["Monat_Sortierschluessel", "Monat_Label"]]])
        .drop_duplicates("Monat_Label")
        .sort_values("Monat_Sortierschluessel")["Monat_Label"]
        .tolist()
    )

    if not monats_optionen:
        st.info("Keine Daten für diesen Athleten vorhanden.")
        return

    # Standardmäßig den aktuellen Monat vorauswählen, falls vorhanden
    heute = pd.Timestamp.now()
    aktueller_schluessel = heute.year * 100 + heute.month
    monats_schluessel_liste = (
        pd.concat([df_t_ath[["Monat_Sortierschluessel", "Monat_Label"]],
                   df_r_ath[["Monat_Sortierschluessel", "Monat_Label"]]])
        .drop_duplicates("Monat_Label")
        .sort_values("Monat_Sortierschluessel")["Monat_Sortierschluessel"]
        .tolist()
    )
    if aktueller_schluessel in monats_schluessel_liste:
        default_index = monats_schluessel_liste.index(aktueller_schluessel)
    else:
        default_index = len(monats_optionen) - 1  # letzter verfügbarer Monat

    st.markdown("### Monat auswählen")
    selected_monat = st.selectbox(
        "Monat", monats_optionen, index=default_index, key="auswertung_monat_select"
    )

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
            woche_aktivitaet.drop_duplicates("Woche_Label")
            .sort_values("Woche_Nr")["Woche_Label"]
            .tolist()
        )

        AKTIVITAET_FARBEN = {
            "Schwimmen": "#3B82F6",
            "Radfahren": "#F59E0B",
            "Laufen":    "#10B981",
            "Kraft":     "#8B5CF6",
            "Ruhetag":   "#9CA3AF",
            "Sonstiges": "#EC4899",
        }

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
            st.plotly_chart(fig_km, use_container_width=True)

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
                schwellen_hf = 0.82 * max_puls # Verwendung des gleichen Wertes wie oben
                df_aktiv["TSS"] = (
                    (df_aktiv["Dauer_Minuten"] / 60)
                    * (df_aktiv["Ø_Herzfrequenz"] / schwellen_hf) ** 2
                    * 100
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
                use_container_width=True,
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
                use_container_width=True,
            )
        else:
            st.info("Keine Regenerationsdaten für diesen Monat vorhanden.")