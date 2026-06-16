from datetime import datetime, date


class Person:
    # Liste der erlaubten Rollen zur Validierung
    ERLAUBTE_ROLLEN = ["Athlet", "Trainer"]

    def __init__(self, vorname: str, nachname: str, geburtsdatum: str, nationalitaet: str, rolle: str):
        self._vorname = vorname
        self._nachname = nachname
        self._geburtsdatum = datetime.strptime(geburtsdatum, "%d.%m.%Y").date()
        self._nationalitaet = nationalitaet

        # Zusatzattribute
        self._spezialisierung = []
        self._erfolge = []

        self.set_role(rolle)

    def get_role(self) -> str:
        """Gibt den aktuellen Wert der Rolle zurück."""
        return self._rolle

    # --- KLASSISCHER SETTER ---
    def set_role(self, neue_rolle: str):
        """Überprüft die neue Rolle und setzt sie, wenn sie gültig ist."""
        # .strip().title() entfernt Leerzeichen und sorgt für Großschreibung des ersten Buchstabens
        formatierte_rolle = neue_rolle.strip().title()

        if formatierte_rolle not in Person.ERLAUBTE_ROLLEN:
            raise ValueError(f"Ungültige Rolle '{neue_rolle}'. Erlaubt sind nur: {', '.join(Person.ERLAUBTE_ROLLEN)}")

        # Zuweisung an das geschützte Attribut
        self._rolle = formatierte_rolle

    # --- WEITERE HILFSMETHODEN ---
    def get_vollname(self) -> str:
        return f"{self._vorname} {self._nachname}"

    def get_alter(self) -> int:
        heute = date.today()
        return (
            heute.year
            - self._geburtsdatum.year
            - ((heute.month, heute.day) < (self._geburtsdatum.month, self._geburtsdatum.day))
        )

    def spezialisierung_hinzufuegen(self, disziplin: str):
        self._spezialisierung.append(disziplin)

    def erfolg_eintragen(self, erfolg: str):
        self._erfolge.append(erfolg)

    def steckbrief_anzeigen(self):
        trenner = "-" * 30  # trennt Zeilen
        print(f"\n{trenner}\nPROFIL: {self.get_vollname().upper()}\n{trenner}")  # Überschrift Großbuchstaben

        print(f"Rolle:          {self.get_role()}")
        print(f"Alter:          {self.get_alter()} Jahre ({self._geburtsdatum.strftime('%d.%m.%Y')})")
        print(f"Nationalität:   {self._nationalitaet}")
        print(f"Disziplin:      {', '.join(self._spezialisierung) if self._spezialisierung else 'Keine Angabe'}")
        print(trenner)


# --- Testlauf der get/set-Variante ---
if __name__ == "__main__":
    # 1. Person erstellen (Rolle wird klein übergeben, der Setter korrigiert es)
    triathlet = Person("Jan", "Frodeno", "18.08.1981", "Deutsch", "athlet")

    # Rolle ausgeben mit get_role()
    print(f"Erstellte Rolle für Jan: {triathlet.get_role()}")

    # 2. Rolle ändern mit set_role()
    print("\nJan Frodeno wird nun Trainer...")
    triathlet.set_role("Trainer")
    triathlet.steckbrief_anzeigen()

    # 3. Fehlerhafter Versuch einer Falscheingabe
    print("\nVersuch, eine ungültige Rolle zu setzen:")
    try:
        triathlet.set_role("Manager")
    except ValueError as e:
        print(f"Fehler erfolgreich abgefangen: {e}")
