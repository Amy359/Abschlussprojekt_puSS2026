import streamlit as st
import pandas as pd
import hashlib
import athlet_dashboard
import trainer_dashboard

# Konfiguration
st.set_page_config(page_title="Triathlon Login", layout="centered")

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_login(username, password):
    try:
        df = pd.read_csv('data/users_secure.csv', delimiter=';')
        df['user_login'] = df['Vorname'].str.lower() + '.' + df['Nachname'].str.lower()
        input_hash = hash_password(password)
        user = df[(df['user_login'] == username.lower()) & (df['Password_Hash'] == input_hash)]
        if not user.empty:
            return user.iloc[0]['Rolle']
    except Exception as e:
        st.error(f"Fehler: {e}")
    return None

# --- Session State ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None

# --- LOGIN UI ---
if not st.session_state['logged_in']:
    st.title("🔐 Login - Triathlon Dashboard")
    username = st.text_input("Benutzername (Vorname.Nachname)")
    password = st.text_input("Passwort (DD.MM.YYYY)", type="password")
    
    if st.button("Anmelden"):
        rolle = check_login(username, password)
        if rolle:
            st.session_state['logged_in'] = True
            st.session_state['role'] = rolle
            st.rerun()
        else:
            st.error("Benutzername oder Passwort falsch!")
else:
    # --- DASHBOARD UI ---
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.rerun()
    
    if st.session_state['role'] == "Trainer":
        trainer_dashboard.show_trainer_dashboard()
    else:
        athlet_dashboard.show_athlete_dashboard()