import csv
from datetime import datetime, date


class Person:
    # 1. Klassenvariablen
    ERLAUBTE_ROLLEN = ["Athlet", "Trainer"]
    _alle_personen = []  # Hier werden alle erstellten Personen-Objekte gesammelt

    def __init__(self, vorname: str, nachname: str, geburtsdatum: str, nationalitaet: str, rolle: str):
        self.vorname = vorname
        self.nachname = nachname
        self.geburtsdatum = datetime.strptime(geburtsdatum, "%d.%m.%Y").date()
        self.nationalitaet = nationalitaet

        self.spezialisierung = []
        self.erfolge = []

        self.set_role(rolle)

        # Jedes Mal, wenn ein Objekt erstellt wird, registriert es sich in der Gesamtliste
        Person._alle_personen.append(self)

    # --- BESTEHENDE GETTER / SETTER ---
    def get_role(self) -> str:
        return self._rolle

    def set_role(self, neue_rolle: str):
        formatierte_rolle = neue_rolle.strip().title()
        if formatierte_rolle not in Person.ERLAUBTE_ROLLEN:
            raise ValueError(f"Ungültige Rolle '{neue_rolle}'. Erlaubt sind: {', '.join(Person.ERLAUBTE_ROLLEN)}")
        self._rolle = formatierte_rolle

    def get_vollname(self) -> str:
        return f"{self.vorname} {self.nachname}"

    def get_alter(self) -> int:
        heute = date.today()
        return (
            heute.year
            - self.geburtsdatum.year
            - ((heute.month, heute.day) < (self.geburtsdatum.month, self.geburtsdatum.day))
        )

    def spezialisierung_hinzufuegen(self, disziplin: str):
        self.spezialisierung.append(disziplin)

    def erfolg_eintragen(self, erfolg: str):
        self.erfolge.append(erfolg)

    # --- NEU: GET-LISTEN FÜR ATHLETEN & TRAINER (Klassenmethoden) ---
    @classmethod
    def get_athleten(cls):
        """Gibt eine Liste aller Objekte zurück, die die Rolle 'Athlet' haben."""
        return [p for p in cls._alle_personen if p.get_role() == "Athlet"]

    @classmethod
    def get_trainer(cls):
        """Gibt eine Liste aller Objekte zurück, die die Rolle 'Trainer' haben."""
        return [p for p in cls._alle_personen if p.get_role() == "Trainer"]

    # --- NEU: STATISCHE METHODE ZUM EINLESEN DER CSV ---
    @staticmethod
    def load_data_from_csv(dateiname: str):
        """Liest eine CSV-Datei ein und erstellt automatisch die Personen-Objekte."""
        dateipfad = f"data/{dateiname}"  # csv dateien sind immer im data ordner abgelegt
        try:
            with open(dateipfad, mode="r", encoding="utf-8") as file:
                # DictReader nutzt die erste Zeile der CSV automatisch als Key-Namen
                reader = csv.DictReader(file, delimiter=";")
                for row in reader:
                    # Objekt instanziieren
                    person = Person(
                        vorname=row["Vorname"],
                        nachname=row["Nachname"],
                        geburtsdatum=row["Geburtsdatum"],
                        nationalitaet=row["Nationalitaet"],
                        rolle=row["Rolle"],
                    )
                    # Optionale Zusatzattribute befüllen
                    if row.get("Spezialisierung"):
                        person.spezialisierung_hinzufuegen(row["Spezialisierung"])
                    if row.get("Erfolge_Lizenzen"):
                        person.erfolg_eintragen(row["Erfolge_Lizenzen"])
            print(f"Erfolgreich: Daten aus '{dateipfad}' wurden geladen.")
        except FileNotFoundError:
            print(f"Fehler: Die Datei '{dateipfad}' wurde nicht gefunden.")

    # --- STECKBRIEF ---
    def steckbrief_anzeigen(self):
        trenner = "-" * 30
        print(f"\n{trenner}\nPROFIL: {self.get_vollname().upper()}\n{trenner}")
        print(f"Rolle:          {self.get_role()}")
        print(f"Alter:          {self.get_alter()} Jahre ({self.geburtsdatum.strftime('%d.%m.%Y')})")
        print(f"Nationalität:   {self.nationalitaet}")
        print(f"Fokus:          {', '.join(self.spezialisierung) if self.spezialisierung else 'Keine Angabe'}")
        print(trenner)


# --- Anwendungsbeispiel ---
if __name__ == "__main__":
    Person.load_data_from_csv("triathlon_personen.csv")

    alle_athleten = Person.get_athleten()
    alle_trainer = Person.get_trainer()

    # Test-Ausgabe: Wie viele wurden geladen?
    print(f"\nGeladene Athleten: {len(alle_athleten)}")
    print(f"Geladene Trainer:  {len(alle_trainer)}")

    # Kurzsteckbriefe aller Athleten anzeigen
    print("\n--- ZEIGE ALLE ATHLETEN ---")
    for athlet in alle_athleten:
        print(
            f"- {athlet.get_vollname()} ({athlet.get_alter()} Jahre, {athlet.nationalitaet if hasattr(athlet, 'nationalitaet') else 'K.A.'})"
        )

    # Steckbrief von Trainer Dan Lorang anzeigen
    print("\n--- TRAINER PROFILE ---")
    for trainer in alle_trainer:
        trainer.steckbrief_anzeigen()
