*Dies ist das Abschlussprojekt zur Vorlesung Programmierübung II (SS 2026) von Amelie Tücking und Leonie Schwerin.*

# 🏊🚴🏃 Triathlon Performance Dashboard

Ein Streamlit-Dashboard zur Trainings- und Regenerationsanalyse für Trainer:innen und Athlet:innen im Triathlon. Athlet:innen tragen Trainings- und Regenerationsdaten ein und sehen ihre Auswertung, Trainer:innen behalten den Überblick über das ganze Team, verwalten Athlet:innen und Wettkämpfe.

## Inhaltsverzeichnis

- [Funktionen](#funktionen)
- [Projektstruktur](#projektstruktur)
- [Installation](#installation-lokal)
- [Nutzung](#nutzung)
- [Dashboards testen](#dashboards-testen)
- [Datenhaltung](#datenhaltung)
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
- **Registrierung:** Nur Trainer:innen können sich über den Button "Registrieren" auf der Login-Seite selbst registrieren.
- **Athlet:innen anlegen/bearbeiten:** Als Trainer über "👥 Athleten → Athleten hinzufügen oder bearbeiten". Beim Anlegen wird das Geburtsdatum automatisch zum Passwort; wird es später bearbeitet, wird das Passwort mit aktualisiert.

## Dashboards testen

Die App wird mit einem vollständigen Beispieldatensatz ausgeliefert (7 Athlet:innen, 2 Trainer, ein Jahr Trainings- und Regenerationsverlauf) – ein Durchklicken ist ohne eigene Registrierung möglich.

**Als Athletin einloggen:** `anne.haug` / `20.01.1983`

- 📅 **Mein Kalender** – Trainingstage anklicken (z. B. im Januar 2026), um Details wie Aktivität, Herzfrequenz, Beschwerden und Kommentar zu sehen
- 📊 **Meine Auswertung** – Trainingsdistanzen, Leistungskennzahlen und Regenerationswerte für einen ausgewählten Monat
- ⌨ **Eingaben** – einen neuen Trainings- oder Regenerationseintrag erfassen
- 💾 **Daten exportieren** – die eigenen Daten als Excel-Datei herunterladen

**Als Trainer einloggen:** `dan.lorang` / `17.08.1979`

- 📅 **Wettkampfkalender** – Team-Wettkämpfe im Kalender, neue Wettkämpfe eintragen
- 📊 **Gesamtübersicht** – Team-Kennzahlen und Athletenvergleich
- 👥 **Athleten → Athleten anzeigen** – z. B. Anne Haug anklicken, um ihre Auswertung einzusehen
- 👥 **Athleten → Athleten hinzufügen oder bearbeiten** – neue Athlet:innen anlegen oder bestehende bearbeiten
- 👥 **Athleten → Athleten - Feedback anzeigen** – Feedback-Nachrichten der Athlet:innen
- ⚙️ **Profil bearbeiten** (Button über "Logout" in der Sidebar) – eigene Stammdaten anpassen

## Datenhaltung

Alle Daten liegen als Semikolon-getrennte CSV-Dateien in `data/` – keine Datenbank nötig, um das Projekt lokal auszuprobieren:

| Datei | Inhalt |
|---|---|
| `triathlon_personen.csv` | Stammdaten aller Athlet:innen und Trainer |
| `users_secure.csv` | Login-Daten (Benutzername, gehashtes Passwort) |
| `triathlon_training.csv` | Trainingseinträge |
| `triathlon_regeneration.csv` | Regenerationseinträge (Schlaf, Ruhepuls, Ernährung, ...) |
| `wettkaempfe.csv` | Wettkampftermine |
| `feedback.csv` | Feedback-Nachrichten der Athlet:innen an den Trainer |

Der Zugriff auf diese Dateien ist in eigenen Klassen/Funktionen gekapselt (`Person` in `personenklasse.py`; `TrainingData`, `CompetitionData`, `FeedbackData` in `training_calendar.py`; `lade_daten()` in `auswertung.py`). Für eine produktive Nutzung mit vielen gleichzeitigen Nutzer:innen wäre der naheliegende nächste Ausbauschritt, diese Datenzugriffe intern durch eine echte Datenbank zu ersetzen (z. B. SQLite für einen leichten Umstieg oder PostgreSQL für einen gehosteten Mehrbenutzerbetrieb) – die restliche App (Dashboards, Kalender, Auswertung) müsste dafür nicht verändert werden.

## Webversion

Deployment über [Streamlit Community Cloud](https://share.streamlit.io) (kostenlos, direkt an dieses GitHub-Repo angebunden):

1. Repository zu GitHub pushen (inkl. `requirements.txt`)
2. Auf [share.streamlit.io](https://share.streamlit.io) mit dem GitHub-Account einloggen
3. "New app" → Repository und Branch wählen, als **Main file path** `main.py` angeben, "Deploy" klicken

🔗 **Live-Demo:** *(Link zu website)*

> **Hinweis:** Da alle Daten in `data/*.csv` gespeichert werden (siehe [Datenhaltung](#datenhaltung)), setzt Streamlit Community Cloud den Dateistand bei jedem Neustart der App (z. B. nach einem Code-Push oder nach längerer Inaktivität) auf den zuletzt committeten Stand zurück. Über die Web-Oberfläche neu angelegte Athlet:innen oder Einträge bleiben also nur bis zum nächsten Neustart erhalten.

## Tech-Stack

- [Streamlit](https://streamlit.io/) – UI-/App-Framework
- [pandas](https://pandas.pydata.org/) – Datenverarbeitung
- [Plotly](https://plotly.com/python/) & [Altair](https://altair-viz.github.io/) – Diagramme
- [streamlit-calendar](https://github.com/im-perativa/streamlit-calendar) – Kalenderkomponente
- CSV-Dateien als einfache Datenhaltung, kein Datenbankserver nötig
