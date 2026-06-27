import pandas as pd
import hashlib


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def check_login(username, password):
    try:
        df = pd.read_csv("data/users_secure.csv", delimiter=";")
        df["user_login"] = df["Vorname"].str.lower() + "." + df["Nachname"].str.lower()
        input_hash = hash_password(password)
        user = df[(df["user_login"] == username.lower()) & (df["Password_Hash"] == input_hash)]
        if not user.empty:
            return user.iloc[0]["Rolle"]
    except Exception as e:
        st.error(f"Fehler: {e}")
    return None
