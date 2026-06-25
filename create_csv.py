import pandas as pd
import hashlib

# Pfad zu deiner vorhandenen CSV
input_file = 'data/triathlon_personen.csv'
output_file = 'data/users_secure.csv'

# Daten einlesen (wichtig: delimiter=';' prüfen, ob das bei dir passt!)
df = pd.read_csv(input_file, delimiter=';')

# Hash-Funktion
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Passwort-Spalte erzeugen (basierend auf Geburtsdatum)
df['Password_Hash'] = df['Geburtsdatum'].apply(hash_password)

# Geburtsdatum entfernen (Sicherheit!)
df = df.drop(columns=['Geburtsdatum'])

# Speichern
df.to_csv(output_file, sep=';', index=False)

print(f"Erfolg! '{output_file}' wurde erstellt.")