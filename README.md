# 🏊🚴🏃 Triathlon Performance Dashboard

Ein Streamlit-Dashboard zur Trainings- und Regenerationsanalyse für Trainer:innen und Athlet:innen im Triathlon. Athlet:innen tragen Trainings- und Regenerationsdaten ein und sehen ihre Auswertung, Trainer:innen behalten den Überblick über das ganze Team, verwalten Athlet:innen und Wettkämpfe.

## Inhaltsverzeichnis

- [Funktionen](#funktionen)
- [Projektstruktur](#projektstruktur)
- [Installation](#installation-lokal)
- [Nutzung](#nutzung)
- [Webversion](#webversion)
- [Tech-Stack](#tech-stack)

## Funktionen

**Für Athlet:innen**

- 📅 Persönlicher Trainingskalender mit Tagesdetails, Aktivitäten, Beschwerden und Wettkampfterminen
- ⌨ Eingabe neuer Trainings- und Regenerationsdaten
- 📊 Persönliche Auswertung (Trainingsdistanzen, Herzfrequenz-Kennzahlen, Schlaf, Ruhepuls, HRV)
- 💾 Datenexport als Excel-Datei
- 💬 Feedback direkt an den Trainer senden

**Für Trainer:innen**

- 📅 Wettkampfkalender für das gesamte Team
- 📊 Gesamtübersicht aller Athlet:innen (Team-Kennzahlen, Athletenvergleich)
- 👥 Athletenverwaltung: neue Athlet:innen anlegen, bestehende bearbeiten
- 📬 Feedback-Inbox der Athlet:innen
- ⚙️ Eigenes Profil bearbeiten

## Projektstruktur

```
Abschlussprojekt_puSS2026/
├── main.py                  # Einstiegspunkt: lädt Personendaten, steuert Login-/Rollen-Routing
├── login.py                 # Login-Maske, Logout, Passwort-Hashing
├── register.py              # Selbstregistrierung für Trainer:innen
├── personenklasse.py        # Person-Klasse (Athlet/Trainer) inkl. CSV-Laden
├── athlete_dashboard.py     # Athleten-Ansicht: Kalender, Eingaben, Auswertung, Export
├── trainer_dashboard.py     # Trainer-Ansicht: Kalender, Übersicht, Athletenverwaltung
├── training_calendar.py     # Wiederverwendbarer Trainingskalender (für Athlet UND Trainer)
├── auswertung.py            # Laden/Aufbereiten der Trainings-/Regenerationsdaten + Auswertungs-Charts
├── create_csv.py            # Einmaliges Hilfsskript zum Erzeugen der Passwort-Hashes
├── data/                    # CSV-"Datenbank" (Personen, Trainings-/Regenerationsdaten, Feedback, ...)
├── images/                  # Logo & Hintergrundbild
├── pyproject.toml / pdm.lock
└── README.md
```

**Wie es zusammenspielt:** `main.py` lädt beim Start alle Personen aus `data/triathlon_personen.csv` in die `Person`-Klasse und zeigt je nach Login-Status entweder `login.py`/`register.py` oder – abhängig von der Rolle – `athlete_dashboard.py` bzw. `trainer_dashboard.py` an. Beide Dashboards greifen für Trainingsdaten auf dieselbe Ladefunktion aus `training_calendar.py` zurück (eine gemeinsame Quelle, damit Kalender und Auswertung immer dieselben Daten sehen) und für Regenerationsdaten sowie die Auswertungs-Charts auf `auswertung.py`. Alle Daten liegen als Semikolon-getrennte CSV-Dateien in `data/` – es wird keine Datenbank benötigt.

## Installation (lokal)

**Voraussetzungen:** Python 3.13 und [PDM](https://pdm-project.org/)

1. Repository klonen und ins Projektverzeichnis wechseln

   ```bash
   git clone <repo-url>
   cd Abschlussprojekt_puSS2026
   ```

2. Virtuelle Umgebung erstellen und Abhängigkeiten installieren

   ```powershell
   pdm venv create
   pdm use -f .\.venv\Scripts\python.exe
   pdm install
   ```

   *(unter macOS/Linux: `pdm use -f .venv/bin/python`)*

3. App starten

   ```bash
   streamlit run main.py
   ```

   Die App öffnet sich automatisch im Browser unter `http://localhost:8501`.

Die Beispieldaten (Athlet:innen, Trainer, ein Jahr Trainingsverlauf) sind bereits im `data/`-Ordner enthalten – es ist kein weiterer Setup-Schritt nötig, um die App direkt auszuprobieren.

## Nutzung

- **Login:** Benutzername ist `vorname.nachname` (klein geschrieben), das Passwort ist das Geburtsdatum im Format `TT.MM.JJJJ`.
  Zum Ausprobieren z. B.: `dan.lorang` / `17.08.1979` (Trainer) oder `jan.frodeno` / `18.08.1981` (Athlet).
- **Registrierung:** Nur Trainer:innen können sich über den Button "Registrieren" auf der Login-Seite selbst registrieren.
- **Athlet:innen anlegen/bearbeiten:** Als Trainer über "👥 Athleten → Athleten hinzufügen oder bearbeiten". Beim Anlegen wird das Geburtsdatum automatisch zum Passwort; wird es später bearbeitet, wird das Passwort mit aktualisiert.

## Webversion

🚧 Folgt in Kürze – das Deployment ist der nächste Schritt.

## Tech-Stack

- [Streamlit](https://streamlit.io/) – UI-/App-Framework
- [pandas](https://pandas.pydata.org/) – Datenverarbeitung
- [Plotly](https://plotly.com/python/) & [Altair](https://altair-viz.github.io/) – Diagramme
- [streamlit-calendar](https://github.com/im-perativa/streamlit-calendar) – Kalenderkomponente
- CSV-Dateien als einfache Datenhaltung, kein Datenbankserver nötig
