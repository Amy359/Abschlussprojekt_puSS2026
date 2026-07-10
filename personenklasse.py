import csv
from datetime import datetime, date


class Person:
    """Repräsentiert einen Athleten oder Trainer im Triathlon-Dashboard.

    Verwaltet Stammdaten (Name, Geburtsdatum, Nationalität), Rolle sowie
    optionale Zusatzangaben (Spezialisierungen, Erfolge/Lizenzen) und hält
    über die Klassenliste '_alle_personen' eine Übersicht aller erzeugten
    Personen (z. B. zum Auslesen aller Athleten/Trainer)."""

    # 1. Klassenvariablen
    ERLAUBTE_ROLLEN = ["Athlet", "Trainer"]
    _alle_personen = []  # Hier werden alle erstellten Personen-Objekte gesammelt

    def __init__(
        self,
        vorname: str,
        nachname: str,
        geburtsdatum: str,
        nationalitaet: str,
        rolle: str,
        trainer: str = "",
        verein: str = "",
    ):
        """Erstellt eine neue Person und registriert sie automatisch in der
        Klassenliste '_alle_personen'.

        geburtsdatum wird als String im Format 'TT.MM.JJJJ' erwartet und
        in ein date-Objekt umgewandelt. rolle wird über set_role validiert
        (muss 'Athlet' oder 'Trainer' sein)."""
        self.vorname = vorname
        self.nachname = nachname
        self.geburtsdatum = datetime.strptime(geburtsdatum, "%d.%m.%Y").date()
        self.nationalitaet = nationalitaet
        self.trainer = trainer
        self.verein = verein

        self.spezialisierung = []
        self.erfolge = []

        self.set_role(rolle)

        # Jedes Mal, wenn ein Objekt erstellt wird, registriert es sich in der Gesamtliste
        Person._alle_personen.append(self)

    # --- BESTEHENDE GETTER / SETTER ---
    def get_role(self) -> str:
        """Gibt die Rolle der Person zurück ('Athlet' oder 'Trainer')."""
        return self._rolle

    def set_role(self, neue_rolle: str):
        """Setzt die Rolle der Person nach Formatierung (getrimmt, Title Case).

        Wirft einen ValueError, falls die Rolle nicht in ERLAUBTE_ROLLEN
        ('Athlet', 'Trainer') enthalten ist."""
        formatierte_rolle = neue_rolle.strip().title()
        if formatierte_rolle not in Person.ERLAUBTE_ROLLEN:
            raise ValueError(f"Ungültige Rolle '{neue_rolle}'. Erlaubt sind: {', '.join(Person.ERLAUBTE_ROLLEN)}")
        self._rolle = formatierte_rolle

    def get_vollname(self) -> str:
        """Gibt den vollständigen Namen der Person zurück (Vorname + Nachname)."""
        return f"{self.vorname} {self.nachname}"

    def get_alter(self) -> int:
        """Berechnet das aktuelle Alter der Person in Jahren anhand des
        Geburtsdatums und des heutigen Datums."""
        heute = date.today()
        # Differenz der Jahreszahlen, minus 1 falls der Geburtstag dieses Jahr
        # noch nicht war: (Monat, Tag)-Tupel lassen sich wie Datumswerte
        # vergleichen, und True/False verhält sich beim Subtrahieren wie 1/0
        return (
            heute.year
            - self.geburtsdatum.year
            - ((heute.month, heute.day) < (self.geburtsdatum.month, self.geburtsdatum.day))
        )

    def get_loginname(self):
        """Gibt den Login-/Benutzernamen zurück, gebildet aus kleingeschriebenem
        Vor- und Nachnamen, getrennt durch einen Punkt (z. B. 'anna.mustermann')."""
        return f"{self.vorname.lower()}.{self.nachname.lower()}"

    def get_verein(self) -> str:
        """Gibt den Verein der Person zurück."""
        return self.verein

    def spezialisierung_hinzufuegen(self, disziplin: str):
        """Fügt der Person eine weitere Spezialisierung/Disziplin hinzu."""
        self.spezialisierung.append(disziplin)

    def erfolg_eintragen(self, erfolg: str):
        """Trägt einen weiteren sportlichen Erfolg bzw. eine Lizenz der
        Person in die Erfolgsliste ein."""
        self.erfolge.append(erfolg)

    # --- NEU: GET-LISTEN FÜR ATHLETEN & TRAINER (Klassenmethoden) ---
    @classmethod  # Eingabeparameter ist ganze Klasse, nicht nur ein konkretes Objekt
    def get_athleten(cls):
        """Gibt eine Liste aller Objekte zurück, die die Rolle 'Athlet' haben."""
        return [p for p in cls._alle_personen if p.get_role() == "Athlet"]

    @classmethod
    def get_trainer(cls):
        """Gibt eine Liste aller Objekte zurück, die die Rolle 'Trainer' haben."""
        return [p for p in cls._alle_personen if p.get_role() == "Trainer"]

    @classmethod
    def get_athleten_von_trainer(cls, trainer_name: str):
        """Gibt alle Athleten zurück, die einem Trainer zugeordnet sind."""
        return [
            p
            for p in cls.get_athleten()
            if getattr(p, "trainer", "") == trainer_name
        ]

    @classmethod
    def daten_geladen(cls):
        """Gibt True zurück, sobald mindestens eine Person-Instanz existiert
        (d. h. ob die CSV bereits eingelesen wurde)."""
        return len(cls._alle_personen) > 0

    # --- STATISCHE METHODE ZUM EINLESEN DER CSV ---
    @staticmethod  # benötigt kein Objekt/ Klasse als Eingabeparameter
    def load_data_from_csv(dateiname: str):
        """Liest eine CSV-Datei ein und erstellt automatisch die Personen-Objekte."""
        # Registry vor dem Neu-Einlesen leeren, sonst würden bei einem erneuten
        # Aufruf (z. B. nach einer Neuregistrierung) alle Personen doppelt erscheinen
        Person._alle_personen = []
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
                        trainer=row.get("Trainer", ""),
                        verein=row.get("Verein", ""),
                    )
                    # Optionale Zusatzattribute befüllen
                    if row.get("Spezialisierung"):
                        person.spezialisierung_hinzufuegen(row["Spezialisierung"])
                    if row.get("Erfolge_Lizenzen"):
                        person.erfolg_eintragen(row["Erfolge_Lizenzen"])
            print(f"Erfolgreich: Daten aus '{dateipfad}' wurden geladen.")
        except FileNotFoundError:
            print(f"Fehler: Die Datei '{dateipfad}' wurde nicht gefunden.")
