import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os
from streamlit_calendar import calendar

# --- HILFSFUNKTIONEN ---
def extrahiere_schlaf_stunden(schlaf_str):
    try:
        if pd.isna(schlaf_str): return 0.0
        teile = str(schlaf_str).split()
        stunden = float(teile[0])
        minuten = float(teile[2]) if len(teile) > 2 else 0.0
        return stunden + (minuten / 60.0)
    except: 
        return 0.0

def load_data():
    """Lädt CSV-Daten oder erstellt leere Dataframes."""
    if os.path.exists("data/triathlon_training.csv"):
        df_t = pd.read_csv("data/triathlon_training.csv", sep=";", encoding="utf-8")
    else:
        df_t = pd.DataFrame(columns=["Datum", "Athlet", "Aktivitaet", "Dauer_min", "Distanz_km", "Max_Herzfrequenz", "Schmerzen"])
        
    if os.path.exists("data/triathlon_regeneration.csv"):
        df_r = pd.read_csv("data/triathlon_regeneration.csv", sep=";", encoding="utf-8")
    else:
        df_r = pd.DataFrame(columns=["Datum", "Athlet", "Schlaf_Dauer", "Ruhepuls_bpm", "Kalorien", "Kohlenhydrate_g", "Proteine_g", "Fette_g", "HRV_ms"])
    
    df_t.columns = df_t.columns.str.strip()
    df_r.columns = df_r.columns.str.strip()
    return df_t, df_r

def save_to_csv(df, filename):
    df.to_csv(filename, sep=";", index=False, encoding="utf-8")

def show_calendar(df_user_t):
    """Zeigt den Kalender mit Trainingsterminen an."""
    calendar_events = []
    for _, row in df_user_t.iterrows():
        color = "#10b981" if row["Aktivitaet"] != "Ruhetag" else "#fca5a5"
        calendar_events.append({
            "title": f"{row['Aktivitaet']} ({row['Distanz_km']}km)",
            "start": row["Datum"].strftime("%Y-%m-%d"),
            "end": row["Datum"].strftime("%Y-%m-%d"),
            "backgroundColor": color,
            "borderColor": color
        })
    calendar(events=calendar_events, options={"headerToolbar": {"left": "prev,next today", "center": "title", "right": "dayGridMonth"}})

# --- HAUPTFUNKTION ---
def show_athlete_dashboard():
    if "username" not in st.session_state:
        st.warning("Bitte logge dich zuerst ein.")
        return

    aktiver_athlet = st.session_state["username"]
    df_train, df_regen = load_data()
    
    # Datum konvertieren
    df_train["Datum"] = pd.to_datetime(df_train["Datum"], errors='coerce')
    df_regen["Datum"] = pd.to_datetime(df_regen["Datum"], errors='coerce')

    # Sidebar Navigation
    st.sidebar.title(f"👋 Hallo, {aktiver_athlet}!")
    menu = st.sidebar.radio("Navigation", ["📅 Mein Kalender", "🏋️ Training eingeben", "🛌 Regeneration eingeben", "📊 Meine Auswertung"])

    # 1. KALENDER
    if menu == "📅 Mein Kalender":
        st.header("📅 Dein Trainings-Kalender")
        df_user_t = df_train[df_train["Athlet"] == aktiver_athlet].dropna(subset=["Datum"]).copy()
        if not df_user_t.empty:
            show_calendar(df_user_t)
        else:
            st.info("Noch keine Trainingstermine gefunden.")

    # 2. TRAINING EINGEBEN
    elif menu == "🏋️ Training eingeben":
        st.header("🏋️ Neues Training protokollieren")
        with st.form("training_form"):
            col1, col2 = st.columns(2)
            datum = col1.date_input("Datum", datetime.now())
            aktivitaet = col2.selectbox("Aktivität", ["Schwimmen", "Radfahren", "Laufen", "Krafttraining", "Ruhetag"])
            col3, col4 = st.columns(2)
            dauer = col3.number_input("Dauer (min)", min_value=0)
            distanz = col4.number_input("Distanz (km)", min_value=0.0, step=0.1)
            col5, col6 = st.columns(2)
            puls = col5.number_input("Max. Herzfrequenz", min_value=0)
            schmerzen = col6.selectbox("Schmerzen", ["Keine", "Leicht", "Mittel", "Stark"])
            
            if st.form_submit_button("Training speichern"):
                new_data = pd.DataFrame([{
                    "Datum": datum.strftime("%Y-%m-%d"), "Athlet": aktiver_athlet, "Aktivitaet": aktivitaet,
                    "Dauer_min": dauer, "Distanz_km": distanz, "Max_Herzfrequenz": puls, "Schmerzen": schmerzen
                }])
                df_train = pd.concat([df_train, new_data], ignore_index=True)
                save_to_csv(df_train, "data/triathlon_training.csv")
                st.success("Training gespeichert!")

    # 3. REGENERATION EINGEBEN
    elif menu == "🛌 Regeneration eingeben":
        st.header("🛌 Regenerationsdaten erfassen")
        with st.form("regen_form"):
            datum_r = st.date_input("Datum", datetime.now())
            schlaf = st.text_input("Schlafdauer (z.B. '8 h 0 min')", "8 h 0 min")
            c1, c2, c3 = st.columns(3)
            ruhepuls = c1.number_input("Ruhepuls (bpm)", min_value=0)
            hrv = c2.number_input("HRV (ms)", min_value=0)
            kalorien = c3.number_input("Kalorien (kcal)", min_value=0)
            
            if st.form_submit_button("Daten speichern"):
                new_regen = pd.DataFrame([{
                    "Datum": datum_r.strftime("%Y-%m-%d"), "Athlet": aktiver_athlet, "Schlaf_Dauer": schlaf,
                    "Ruhepuls_bpm": ruhepuls, "HRV_ms": hrv, "Kalorien": kalorien
                }])
                df_regen = pd.concat([df_regen, new_regen], ignore_index=True)
                save_to_csv(df_regen, "data/triathlon_regeneration.csv")
                st.success("Regenerationsdaten gespeichert!")

    # 4. AUSWERTUNG
    elif menu == "📊 Meine Auswertung":
        st.title("📊 Dein persönliches Performance Center")
        df_t_ath = df_train[df_train["Athlet"] == aktiver_athlet]
        df_r_ath = df_regen[df_regen["Athlet"] == aktiver_athlet]
        
        if df_t_ath.empty:
            st.warning("Keine Daten vorhanden.")
        else:
            df_r_ath["Schlaf_Stunden"] = df_r_ath["Schlaf_Dauer"].apply(extrahiere_schlaf_stunden)
            df_t_ath["KW"] = df_t_ath["Datum"].dt.isocalendar().week
            
            t1, t2 = st.tabs(["🏋️‍♂️ Training", "🛌 Regeneration"])
            with t1:
                kw_data = df_t_ath.groupby(["KW", "Aktivitaet"])["Distanz_km"].sum().reset_index()
                st.plotly_chart(px.bar(kw_data, x="KW", y="Distanz_km", color="Aktivitaet"), use_container_width=True)
            with t2:
                st.line_chart(df_r_ath.set_index("Datum")[["Ruhepuls_bpm", "HRV_ms"]])


if __name__ == "__main__":
    # Test-Modus: Setze den Session-State manuell, damit der Login übersprungen wird
 if "username" not in st.session_state:
    st.session_state["username"] = "Test-Athlet"
    
    # Jetzt wird die Dashboard-Funktion direkt ausgeführt
show_athlete_dashboard()