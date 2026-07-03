import calendar
import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import date
from pathlib import Path
from typing import Optional

CSV_PATH = Path(__file__).parent / "data" / "triathlon_training.csv"

WETTKAMPF_CSV_PATH = Path(__file__).parent / "data" / "wettkaempfe.csv"
WETTKAMPF_FARBE = "#DC2626"

FEEDBACK_CSV_PATH = Path(__file__).parent / "data" / "feedback.csv"
FEEDBACK_COLUMNS = ["Zeitstempel", "Athlet", "Jahr", "Monat", "Nachricht", "Gelesen"]

AKTIVITAET_FARBEN: dict[str, str] = {
    "Schwimmen": "#3B82F6",
    "Radfahren": "#FF33B1",
    "Laufen": "#0B7A55",
    "Kraft": "#8B5CF6",
    "Ruhetag": "#9CA3AF",
    "Sonstiges": "#FFEB38",
}

GEFUEHL_EMOJI: dict[str, str] = {
    "Sehr gut": "😄",
    "Gut": "🙂",
    "Normal": "😐",
    "Müde": "😓",
}

SCHMERZEN_FARBE: dict[str, str] = {
    "Keine": "#10B981",
    "Leicht": "#F59E0B",
    "Mittel": "#EF4444",
    "Stark": "#7F1D1D",
}

WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
MONATE_DE = [
    "Januar",
    "Februar",
    "März",
    "April",
    "Mai",
    "Juni",
    "Juli",
    "August",
    "September",
    "Oktober",
    "November",
    "Dezember",
]


def _schmerzen_kategorie(wert: str) -> str:
    """Gibt 'Keine', 'Leicht', 'Mittel' oder 'Stark' zurück."""
    w = str(wert).strip()
    if w.lower() in ("keine", "nan", ""):
        return "Keine"
    if w.lower().startswith("leicht"):
        return "Leicht"
    if w.lower().startswith("mittel"):
        return "Mittel"
    if w.lower().startswith("stark"):
        return "Stark"
    return "Leicht"


class TrainingData:
    """Lädt und verwaltet die Trainingsdaten aus der CSV."""

    def __init__(self, csv_path: Path = CSV_PATH):
        self.csv_path = csv_path
        self._df: Optional[pd.DataFrame] = None

    def load(self) -> pd.DataFrame:
        """Liest CSV (Semikolon), normalisiert Typen, cacht das Ergebnis."""
        if self._df is not None:
            return self._df

        if not self.csv_path.exists():
            st.error(
                f"❌ CSV nicht gefunden!\n\n"
                f"Gesuchter Pfad: `{self.csv_path.resolve()}`\n\n"
                f"**Lösung:** Lege `triathlon_training.csv` in denselben Ordner "
                f"wie `training_calendar.py` und starte Streamlit neu."
            )
            st.stop()

        df = pd.read_csv(self.csv_path, sep=";", encoding="utf-8")
        df = self._normalize(df)
        self._df = df
        return self._df

    def _normalize(self, df: pd.DataFrame) -> pd.DataFrame:

        df.columns = [c.strip() for c in df.columns]

        # Datum
        df["Datum"] = pd.to_datetime(df["Datum"], format="%Y-%m-%d", errors="coerce")
        df = df.dropna(subset=["Datum"])

        for col in ["Dauer_Minuten", "Distanz_km", "Ø_Herzfrequenz", "Max_Herzfrequenz", "Kalorienverbrauch"]:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

        for col in [
            "Athlet",
            "Wochentag",
            "Einheit_Des_Tages",
            "Aktivität",
            "Fokus",
            "Gefühl",
            "Schmerzen_Beschwerden",
            "Kommentar",
        ]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        df["_ist_ruhetag"] = df["Aktivität"].str.lower() == "ruhetag"

        return df.reset_index(drop=True)

    def get_athletes(self) -> list[str]:
        df = self.load()
        return sorted(df["Athlet"].dropna().unique().tolist())

    def get_for_athlete(self, athlete: str) -> pd.DataFrame:
        return self.load()[self.load()["Athlet"] == athlete].copy()

    def get_for_month(self, df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
        mask = (df["Datum"].dt.year == year) & (df["Datum"].dt.month == month)
        return df[mask]

    def get_for_date(self, df: pd.DataFrame, target: date) -> pd.DataFrame:
        return df[df["Datum"].dt.date == target]


class CompetitionData:
    """Lädt und verwaltet die Wettkampfdaten aus wettkaempfe.csv."""

    def __init__(self, csv_path: Path = WETTKAMPF_CSV_PATH):
        self.csv_path = csv_path
        self._df: Optional[pd.DataFrame] = None

    def load(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df

        if not self.csv_path.exists():
            # Wettkämpfe sind optional – ohne CSV einfach leeres DataFrame
            self._df = pd.DataFrame(
                columns=["ID", "Datum", "Athlet", "Wettkampf", "Ort", "Distanz", "Status", "Ergebnis"]
            )
            return self._df

        df = pd.read_csv(self.csv_path, sep=";", encoding="utf-8")
        df.columns = [c.strip() for c in df.columns]

        df["Datum"] = pd.to_datetime(df["Datum"], format="%Y-%m-%d", errors="coerce")
        df = df.dropna(subset=["Datum"])

        for col in ["Athlet", "Wettkampf", "Ort", "Distanz", "Status", "Ergebnis"]:
            if col in df.columns:
                df[col] = df[col].fillna("").astype(str).str.strip()

        self._df = df.reset_index(drop=True)
        return self._df

    def get_for_athlete(self, athlete: str) -> pd.DataFrame:
        df = self.load()
        return df[df["Athlet"] == athlete].copy()

    def get_for_month(self, df: pd.DataFrame, year: int, month: int) -> pd.DataFrame:
        mask = (df["Datum"].dt.year == year) & (df["Datum"].dt.month == month)
        return df[mask]

    def get_for_date(self, df: pd.DataFrame, target: date) -> pd.DataFrame:
        return df[df["Datum"].dt.date == target]


class FeedbackData:
    """Speichert und lädt Feedback-Nachrichten von Athlet:innen an den Trainer."""

    def __init__(self, csv_path: Path = FEEDBACK_CSV_PATH):
        self.csv_path = csv_path

    def _ensure_file(self):
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.csv_path.exists():
            pd.DataFrame(columns=FEEDBACK_COLUMNS).to_csv(self.csv_path, sep=";", index=False)

    def load(self) -> pd.DataFrame:
        self._ensure_file()
        try:
            df = pd.read_csv(self.csv_path, sep=";", encoding="utf-8")
        except pd.errors.EmptyDataError:
            df = pd.DataFrame(columns=FEEDBACK_COLUMNS)

        df.columns = [c.strip() for c in df.columns]
        for col in FEEDBACK_COLUMNS:
            if col not in df.columns:
                df[col] = False if col == "Gelesen" else ""

        df["Gelesen"] = df["Gelesen"].apply(lambda x: str(x).strip().lower() in ("true", "1", "wahr")).astype(bool)
        return df

    def add(self, athlet: str, jahr: int, monat: int, nachricht: str):
        df = self.load()
        neu = pd.DataFrame(
            [
                {
                    "Zeitstempel": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Athlet": athlet,
                    "Jahr": jahr,
                    "Monat": monat,
                    "Nachricht": nachricht,
                    "Gelesen": False,
                }
            ]
        )
        df = pd.concat([df, neu], ignore_index=True)
        df.to_csv(self.csv_path, sep=";", index=False)

    def get_for_athlete(self, athlet: str) -> pd.DataFrame:
        df = self.load()
        return df[df["Athlet"] == athlet].sort_values("Zeitstempel", ascending=False)

    def get_unread(self) -> pd.DataFrame:
        df = self.load()
        return df[~df["Gelesen"]].sort_values("Zeitstempel", ascending=False)

    def mark_as_read(self, index):
        df = self.load()
        if index in df.index:
            df.loc[index, "Gelesen"] = True
            df.to_csv(self.csv_path, sep=";", index=False)


def render_trainer_feedback_inbox(csv_path: Path = FEEDBACK_CSV_PATH, only_unread: bool = True):
    """
    Zeigt das Athleten-Feedback für den Trainer an.

    Für die Einbindung in trainer_dashboard.py:

        from training_calendar import render_trainer_feedback_inbox
        render_trainer_feedback_inbox()
    """
    fb = FeedbackData(csv_path)
    df = fb.get_unread() if only_unread else fb.load().sort_values("Zeitstempel", ascending=False)

    st.markdown("### 📬 Athleten-Feedback")
    if df.empty:
        st.caption("Kein neues Feedback." if only_unread else "Noch kein Feedback vorhanden.")
        return

    for idx, r in df.iterrows():
        with st.container(border=True):
            c1, c2 = st.columns([4, 1])
            with c1:
                st.markdown(f"**{r['Athlet']}** · {r['Zeitstempel']}")
                st.write(r["Nachricht"])
            with c2:
                if not r["Gelesen"]:
                    if st.button("✅ Gelesen", key=f"inbox_read_{idx}"):
                        fb.mark_as_read(idx)
                        st.rerun()


class TrainingCalendar:
    """Rendert den interaktiven Trainings-Kalender in Streamlit."""

    def __init__(
        self,
        data: TrainingData,
        competitions: Optional[CompetitionData] = None,
        feedback: Optional[FeedbackData] = None,
    ):
        self.data = data
        self.competitions = competitions or CompetitionData()
        self.feedback = feedback or FeedbackData()

    # -- Öffentliche Methode -------------------------------------------------

    def render(self, role: str = "trainer", current_user: Optional[str] = None):
        self._init_session_state()

        selected_athlete = self._render_athlete_selector(role, current_user)
        if not selected_athlete:
            st.info("Bitte einen Athleten auswählen.")
            return

        df_athlete = self.data.get_for_athlete(selected_athlete)
        df_comp_athlete = self.competitions.get_for_athlete(selected_athlete)

        st.markdown("---")
        self._render_month_navigation()

        year = st.session_state["cal_year"]
        month = st.session_state["cal_month"]

        st.markdown(f"### {MONATE_DE[month - 1]} {year} · {selected_athlete}")
        self._render_legend()

        df_month = self.data.get_for_month(df_athlete, year, month)
        df_comp_month = self.competitions.get_for_month(df_comp_athlete, year, month)
        self._render_calendar_grid(df_month, df_comp_month, year, month)

        if st.session_state.get("cal_selected_date"):
            self._render_day_detail(df_athlete, df_comp_athlete, st.session_state["cal_selected_date"])

        self._render_feedback_section(selected_athlete, role, year, month)

        self._render_monthly_stats(df_month, selected_athlete)

    @staticmethod
    def _init_session_state():
        today = date.today()
        for k, v in {
            "cal_year": today.year,
            "cal_month": today.month,
            "cal_selected_date": None,
        }.items():
            if k not in st.session_state:
                st.session_state[k] = v

    def _render_athlete_selector(self, role: str, current_user: Optional[str]) -> Optional[str]:
        athletes = self.data.get_athletes()

        if role == "athlete":
            if not current_user:
                st.error("Kein Athlet angemeldet.")
                return None
            if current_user not in athletes:
                st.warning(f"Keine Daten für **{current_user}** gefunden.")
                return None
            st.success(f"👤 Angemeldet als: **{current_user}**")
            return current_user

        # Trainer
        st.markdown("#### 🏋️ Athlet auswählen")
        if not athletes:
            st.error("Keine Athleten gefunden.")
            return None
        return st.selectbox(
            "Athlet", athletes, key="cal_athlete_select", help="Als Trainer kannst du jeden Athleten einsehen."
        )

    @staticmethod
    def _render_month_navigation():
        col_prev, col_mid, col_next = st.columns([1, 4, 1])

        with col_prev:
            if st.button("◀", use_container_width=True, help="Vormonat"):
                m = st.session_state["cal_month"]
                y = st.session_state["cal_year"]
                if m == 1:
                    st.session_state["cal_month"] = 12
                    st.session_state["cal_year"] = y - 1
                else:
                    st.session_state["cal_month"] = m - 1
                st.session_state["cal_selected_date"] = None

        with col_mid:
            ca, cb = st.columns(2)
            with ca:
                new_month = st.selectbox(
                    "Monat",
                    range(1, 13),
                    index=st.session_state["cal_month"] - 1,
                    format_func=lambda m: MONATE_DE[m - 1],
                    key="cal_month_sel",
                    label_visibility="collapsed",
                )
                st.session_state["cal_month"] = new_month
            with cb:
                new_year = st.number_input(
                    "Jahr",
                    min_value=2020,
                    max_value=2030,
                    value=st.session_state["cal_year"],
                    step=1,
                    key="cal_year_inp",
                    label_visibility="collapsed",
                )
                st.session_state["cal_year"] = int(new_year)

        with col_next:
            if st.button("▶", use_container_width=True, help="Nächster Monat"):
                m = st.session_state["cal_month"]
                y = st.session_state["cal_year"]
                if m == 12:
                    st.session_state["cal_month"] = 1
                    st.session_state["cal_year"] = y + 1
                else:
                    st.session_state["cal_month"] = m + 1
                st.session_state["cal_selected_date"] = None

    # -- Legende -------------------------------------------------------------

    @staticmethod
    def _render_legend():
        parts = []
        for aktivitaet, color in AKTIVITAET_FARBEN.items():
            parts.append(
                f"<span style='background:{color};color:white;padding:2px 8px;"
                f"border-radius:10px;font-size:0.75rem;margin-right:4px'>"
                f"{aktivitaet}</span>"
            )
        st.markdown(" ".join(parts), unsafe_allow_html=True)
        st.markdown(
            f"<span style='border-left:5px solid {WETTKAMPF_FARBE};padding-left:6px;"
            f"font-size:0.78rem;color:{WETTKAMPF_FARBE};font-weight:600'>"
            f"Wettkampftag</span>",
            unsafe_allow_html=True,
        )
        st.markdown("")

    def _render_calendar_grid(self, df_month: pd.DataFrame, df_comp_month: pd.DataFrame, year: int, month: int):
        today = date.today()
        selected = st.session_state.get("cal_selected_date")

        html = """
        <style>
        .cal-table { width:100%; border-collapse:separate; border-spacing:4px; }
        .cal-th { text-align:center; font-weight:700; color:#6B7280;
                  font-size:0.82rem; padding:4px 0 8px 0; }
        .cal-td { vertical-align:top; width:14.28%; }
        .cal-cell {
            border-radius:8px; padding:7px; min-height:100px;
            cursor:pointer; transition:box-shadow .15s;
        }
        .cal-cell:hover { box-shadow:0 2px 8px rgba(0,0,0,.15); }
        .cal-num { font-weight:700; font-size:0.9rem; }
        .cal-dots { margin-top:5px; line-height:1.6; }
        .cal-dot { display:inline-block; width:10px; height:10px;
                   border-radius:50%; margin:1px; }
        .cal-info { font-size:0.65rem; color:#6B7280; margin-top:3px; }
        .cal-ruhe { font-size:0.7rem; color:#9CA3AF; margin-top:3px; }
        .cal-wettkampf {
            font-size:0.65rem; font-weight:700; color:#7F1D1D;
            background:#FEE2E2; border-radius:6px; padding:2px 5px;
            margin-top:4px; line-height:1.3;
        }
        </style>
        <table class="cal-table"><thead><tr>
        """
        for wd in WOCHENTAGE:
            html += f'<th class="cal-th">{wd}</th>'
        html += "</tr></thead><tbody>"

        cal_weeks = calendar.monthcalendar(year, month)
        for week in cal_weeks:
            html += "<tr>"
            for day_num in week:
                if day_num == 0:
                    html += '<td class="cal-td"></td>'
                    continue

                current_date = date(year, month, day_num)
                df_day = self.data.get_for_date(df_month, current_date)
                aktiv_df = df_day[~df_day["_ist_ruhetag"]]
                df_comp_day = self.competitions.get_for_date(df_comp_month, current_date)
                is_wettkampf = not df_comp_day.empty

                is_today = current_date == today
                is_selected = current_date == selected

                border = (
                    "2px solid #3B82F6" if is_today else ("2px solid #F59E0B" if is_selected else "1px solid #E5E7EB")
                )
                bg = "#EFF6FF" if is_today else ("#FFFBEB" if is_selected else "#FAFAFA")
                num_color = "#1D4ED8" if is_today else "#374151"

                # Wettkampftag überschreibt Rahmen/Hintergrund (außer heute/ausgewählt bleibt sichtbar als Akzent)
                wettkampf_border_accent = ""
                if is_wettkampf:
                    wettkampf_border_accent = f"border-left:5px solid {WETTKAMPF_FARBE};"
                    if not is_today and not is_selected:
                        bg = "#FEF2F2"

                # Punkte
                dots = ""
                for _, row in aktiv_df.iterrows():
                    akt = row.get("Aktivität", "Sonstiges")
                    color = AKTIVITAET_FARBEN.get(akt, "#6B7280")
                    dots += f'<span class="cal-dot" style="background:{color}"></span>'

                # Ruhetag
                ruhe_html = ""
                if not df_day[df_day["_ist_ruhetag"]].empty:
                    ruhe_html = '<div class="cal-ruhe">😴 Ruhe</div>'

                # Dauer
                total_min = int(aktiv_df["Dauer_Minuten"].sum())
                dauer_html = f'<div class="cal-info">{total_min} min</div>' if total_min else ""

                # Schmerzen
                hat_schmerzen = (
                    aktiv_df["Schmerzen_Beschwerden"].apply(lambda x: _schmerzen_kategorie(x) != "Keine").any()
                    if not aktiv_df.empty
                    else False
                )
                schmerz = '<span style="color:#EF4444;font-size:0.7rem">⚠️</span>' if hat_schmerzen else ""

                # Wettkampf-Badge
                wettkampf_html = ""
                if is_wettkampf:
                    namen = ", ".join(df_comp_day["Wettkampf"].unique())
                    wettkampf_html = f'<div class="cal-wettkampf">🏆 {namen}</div>'

                html += f"""
                <td class="cal-td">
                  <div class="cal-cell" style="border:{border};background:{bg};{wettkampf_border_accent}">
                    <div style="display:flex;justify-content:space-between;align-items:center">
                      <span class="cal-num" style="color:{num_color}">{day_num}</span>
                      {schmerz}
                    </div>
                    <div class="cal-dots">{dots}</div>
                    {ruhe_html}
                    {dauer_html}
                    {wettkampf_html}
                  </div>
                </td>"""
            html += "</tr>"
        html += "</tbody></table>"

        # Anzahl Wochen bestimmt die Höhe
        num_weeks = len(calendar.monthcalendar(year, month))
        height = 60 + num_weeks * 115
        components.html(html, height=height, scrolling=False)

        # Klick-Auswahl per Selectbox (kompakt, kein Button-Chaos)
        cal_weeks_flat = calendar.monthcalendar(year, month)
        alle_tage = [date(year, month, d) for week in cal_weeks_flat for d in week if d != 0]
        tage_labels = {d: d.strftime("%d. %b (%A)") for d in alle_tage}

        selected_day = st.selectbox(
            "Tag auswählen für Details",
            options=[None] + alle_tage,
            format_func=lambda d: "– kein Tag ausgewählt –" if d is None else tage_labels[d],
            key="cal_day_select",
        )
        st.session_state["cal_selected_date"] = selected_day

    # -- Tag-Detail ----------------------------------------------------------

    def _render_day_detail(self, df_athlete: pd.DataFrame, df_comp_athlete: pd.DataFrame, selected_date: date):
        df_day = self.data.get_for_date(df_athlete, selected_date)
        df_comp_day = self.competitions.get_for_date(df_comp_athlete, selected_date)

        wochentag = df_day["Wochentag"].iloc[0] if not df_day.empty else ""
        st.markdown("---")
        st.markdown(f"### 📋 {wochentag}, {selected_date.strftime('%d. %B %Y')}")

        # Wettkampf-Hinweis
        if not df_comp_day.empty:
            for _, wk in df_comp_day.iterrows():
                st.markdown(
                    f"<div style='border:2px solid {WETTKAMPF_FARBE};border-radius:10px;"
                    f"padding:12px 16px;background:#FEF2F2;margin-bottom:10px'>"
                    f"<span style='font-size:1.1rem;font-weight:700;color:{WETTKAMPF_FARBE}'>"
                    f"🏆 {wk.get('Wettkampf', '')}</span><br>"
                    f"<span style='font-size:0.85rem;color:#374151'>"
                    f"📍 {wk.get('Ort', '')} &nbsp;·&nbsp; "
                    f"📏 {wk.get('Distanz', '')} &nbsp;·&nbsp; "
                    f"📌 {wk.get('Status', '')}"
                    f"{' &nbsp;·&nbsp; 🥇 ' + str(wk.get('Ergebnis')) if str(wk.get('Ergebnis', '')).strip() else ''}"
                    f"</span></div>",
                    unsafe_allow_html=True,
                )

        # Ruhetag
        ruhe = df_day[df_day["_ist_ruhetag"]]
        if not ruhe.empty:
            st.info(" **Geplante Regeneration** – Kein aktives Training.")

        aktiv_df = df_day[~df_day["_ist_ruhetag"]]
        if aktiv_df.empty and ruhe.empty:
            st.info("Kein Training eingetragen.")
            return

        for _, row in aktiv_df.iterrows():
            akt = row.get("Aktivität", "Sonstiges")
            color = AKTIVITAET_FARBEN.get(akt, "#6B7280")
            fokus = row.get("Fokus", "")
            gefuehl = row.get("Gefühl", "")
            g_emoji = GEFUEHL_EMOJI.get(gefuehl, "❓")
            schmerzen = row.get("Schmerzen_Beschwerden", "Keine")
            s_kat = _schmerzen_kategorie(schmerzen)
            s_color = SCHMERZEN_FARBE.get(s_kat, "#6B7280")
            kommentar = row.get("Kommentar", "")
            einheit = row.get("Einheit_Des_Tages", "")
            dauer = int(row.get("Dauer_Minuten", 0))
            distanz = float(row.get("Distanz_km", 0))
            hf_avg = int(row.get("Ø_Herzfrequenz", 0))
            hf_max = int(row.get("Max_Herzfrequenz", 0))
            kalorien = int(row.get("Kalorienverbrauch", 0))

            with st.container(border=True):
                # Titel-Zeile
                c_left, c_right = st.columns([3, 1])
                with c_left:
                    st.markdown(
                        f"<span style='background:{color};color:white;padding:3px 12px;"
                        f"border-radius:12px;font-size:0.8rem;font-weight:600'>"
                        f"{akt}</span> "
                        f"<span style='color:#6B7280;font-size:0.8rem'>{fokus}</span>",
                        unsafe_allow_html=True,
                    )
                    st.markdown(f"**{einheit}**")
                with c_right:
                    st.markdown(
                        f"<div style='text-align:right;font-size:0.85rem'>{g_emoji} {gefuehl}</div>",
                        unsafe_allow_html=True,
                    )

                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Dauer", f"{dauer} min")
                m2.metric("Distanz", f"{distanz:.1f} km" if distanz else "–")
                m3.metric("Ø HF", f"{hf_avg} bpm" if hf_avg else "–")
                m4.metric("Max HF", f"{hf_max} bpm" if hf_max else "–")
                m5.metric("Kalorien", f"{kalorien} kcal" if kalorien else "–")

                st.markdown(
                    f"<span style='background:{s_color};color:white;padding:2px 8px;"
                    f"border-radius:8px;font-size:0.75rem'> {schmerzen}</span>",
                    unsafe_allow_html=True,
                )

                if kommentar:
                    st.caption(f"💬 {kommentar}")

    # -- Feedback --------------------------------------------------------

    def _render_feedback_section(self, athlete: str, role: str, year: int, month: int):
        st.markdown("---")
        st.markdown("### 💬 Feedback an den Trainer")

        if role == "athlete":
            with st.form(key="feedback_form", clear_on_submit=True):
                nachricht = st.text_area(
                    "Wie lief dein Training? Anmerkungen, Beschwerden oder Fragen gehen direkt an deinen Trainer.",
                    height=100,
                    placeholder="z. B. Rechtes Knie zwickt seit dem Lauf am Dienstag …",
                )
                submitted = st.form_submit_button("Feedback senden")
                if submitted:
                    if nachricht.strip():
                        self.feedback.add(athlete, year, month, nachricht.strip())
                        st.success("✅ Dein Feedback wurde an den Trainer gesendet.")
                    else:
                        st.warning("Bitte gib eine Nachricht ein, bevor du sie sendest.")

            eigene = self.feedback.get_for_athlete(athlete)
            if not eigene.empty:
                with st.expander("Bisher gesendetes Feedback anzeigen"):
                    for _, r in eigene.iterrows():
                        status = "✅ gelesen" if r["Gelesen"] else "🕓 noch ungelesen"
                        st.markdown(f"**{r['Zeitstempel']}** ({status}) – {r['Nachricht']}")

        else:
            # Trainer-Ansicht: Verlauf des ausgewählten Athleten, direkt quittierbar
            verlauf = self.feedback.get_for_athlete(athlete)
            if verlauf.empty:
                st.caption("Noch kein Feedback von diesem Athleten erhalten.")
            else:
                for idx, r in verlauf.iterrows():
                    icon = "✅" if r["Gelesen"] else "🆕"
                    with st.container(border=True):
                        st.markdown(
                            f"{icon} **{r['Zeitstempel']}** — {MONATE_DE[int(r['Monat']) - 1]} {int(r['Jahr'])}"
                        )
                        st.write(r["Nachricht"])
                        if not r["Gelesen"]:
                            if st.button("Als gelesen markieren", key=f"cal_read_{idx}"):
                                self.feedback.mark_as_read(idx)
                                st.rerun()

    @staticmethod
    def _aktivitaet_bar_chart(df: pd.DataFrame, value_col: str, y_title: str):
        """Balkendiagramm, dessen Balkenfarben zu AKTIVITAET_FARBEN passen
        (also identisch zu den Farben im Kalender/der Legende)."""
        vorhandene = [a for a in AKTIVITAET_FARBEN if a in df["Aktivität"].unique()]
        chart = (
            alt.Chart(df)
            .mark_bar()
            .encode(
                x=alt.X("Aktivität:N", sort=vorhandene, title=None),
                y=alt.Y(f"{value_col}:Q", title=y_title),
                color=alt.Color(
                    "Aktivität:N",
                    scale=alt.Scale(
                        domain=vorhandene,
                        range=[AKTIVITAET_FARBEN[a] for a in vorhandene],
                    ),
                    legend=None,
                ),
                tooltip=["Aktivität", alt.Tooltip(f"{value_col}:Q", title=y_title)],
            )
            .properties(height=280)
        )
        st.altair_chart(chart, use_container_width=True)

    def _render_monthly_stats(self, df_month: pd.DataFrame, athlet: str):
        aktiv = df_month[~df_month["_ist_ruhetag"]]
        if aktiv.empty:
            return

        st.markdown("---")
        st.markdown(f"### Monatsübersicht – {athlet}")

        total_einheiten = len(aktiv)
        total_min = int(aktiv["Dauer_Minuten"].sum())
        total_km = aktiv["Distanz_km"].sum()
        total_kcal = int(aktiv["Kalorienverbrauch"].sum())
        avg_hf = (
            int(aktiv["Ø_Herzfrequenz"][aktiv["Ø_Herzfrequenz"] > 0].mean())
            if (aktiv["Ø_Herzfrequenz"] > 0).any()
            else 0
        )
        ruhetage = len(df_month[df_month["_ist_ruhetag"]]["Datum"].dt.date.unique())
        schmerzen_count = aktiv["Schmerzen_Beschwerden"].apply(lambda x: _schmerzen_kategorie(x) != "Keine").sum()

        # KPI-Zeile 1
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Einheiten", total_einheiten)
        c2.metric("Gesamtdauer", f"{total_min // 60}h {total_min % 60}min")
        c3.metric("Distanz", f"{total_km:.1f} km")
        c4.metric("Kalorien", f"{total_kcal:,} kcal")

        # KPI-Zeile 2
        c5, c6, c7, _ = st.columns(4)
        c5.metric("Ø Herzfrequenz", f"{avg_hf} bpm" if avg_hf else "–")
        c6.metric("Ruhetage", ruhetage)
        c7.metric("Schmerz-Einh.", schmerzen_count)

        # Größerer Abstand zwischen den Kennzahlen und den Diagrammen
        st.markdown("<div style='margin-top:2.5rem'></div>", unsafe_allow_html=True)

        # Disziplin-Verteilung
        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            st.markdown("**Dauer nach Aktivität (Minuten)**")
            dist_dauer = (
                aktiv.groupby("Aktivität")["Dauer_Minuten"]
                .sum()
                .reset_index()
                .sort_values("Dauer_Minuten", ascending=False)
            )
            self._aktivitaet_bar_chart(dist_dauer, "Dauer_Minuten", "Minuten")

        with col_chart2:
            st.markdown("**Distanz nach Aktivität (km)**")
            dist_km = (
                aktiv.groupby("Aktivität")["Distanz_km"].sum().reset_index().sort_values("Distanz_km", ascending=False)
            )
            self._aktivitaet_bar_chart(dist_km, "Distanz_km", "km")

        # Gefühls-Verteilung
        st.markdown("**Tagesgefühl-Verteilung**")
        gefuehl_counts = aktiv["Gefühl"].value_counts().reset_index().rename(columns={"count": "Anzahl"})
        gefuehl_counts["Gefühl"] = gefuehl_counts["Gefühl"].apply(lambda g: f"{GEFUEHL_EMOJI.get(g, '')} {g}")
        gefuehl_chart = (
            alt.Chart(gefuehl_counts)
            .mark_bar(color="#9CA3AF")
            .encode(
                x=alt.X("Gefühl:N", sort=None, title=None),
                y=alt.Y("Anzahl:Q"),
                tooltip=["Gefühl", "Anzahl"],
            )
            .properties(height=280)
        )
        st.altair_chart(gefuehl_chart, use_container_width=True)

        # Schmerzen-Übersicht
        with st.expander("Schmerzen & Beschwerden im Monat"):
            schmerz_df = aktiv[aktiv["Schmerzen_Beschwerden"].apply(lambda x: _schmerzen_kategorie(x) != "Keine")][
                ["Datum", "Aktivität", "Schmerzen_Beschwerden", "Gefühl", "Kommentar"]
            ]

            if schmerz_df.empty:
                st.success("Keine Beschwerden im gewählten Monat")
            else:
                schmerz_df = schmerz_df.copy()
                schmerz_df["Datum"] = schmerz_df["Datum"].dt.strftime("%d.%m.%Y")
                st.dataframe(schmerz_df, use_container_width=True, hide_index=True)


def render_calendar(
    role: str = "trainer",
    current_user: Optional[str] = None,
    csv_path: Path = CSV_PATH,
    wettkaempfe_csv: Path = WETTKAMPF_CSV_PATH,
    feedback_csv: Path = FEEDBACK_CSV_PATH,
):
    """
    Haupt-Einstiegspunkt für den Import in ein anderes Dashboard.

    Parameters
    ----------
    role            : "trainer"  → Athleten per Dropdown auswählbar
                      "athlete"  → nur current_user sichtbar, keine Auswahl
    current_user    : Athlet-Name (Pflicht bei role="athlete")
    csv_path        : Pfad zur Trainings-CSV (Standard: triathlon_training.csv)
    wettkaempfe_csv : Pfad zur Wettkampf-CSV (Standard: wettkaempfe.csv)
    feedback_csv    : Pfad zur Feedback-CSV (Standard: feedback.csv)

    Beispiel
    --------
    # dashboard.py
    from training_calendar import render_calendar

    if st.session_state["role"] == "trainer":
        render_calendar(role="trainer", csv_path="data/triathlon_training.csv")
    else:
        render_calendar(role="athlete", current_user=st.session_state["username"])

    Um das Athleten-Feedback im Trainer-Dashboard (trainer_dashboard.py)
    zusätzlich als eigene Inbox anzuzeigen (z. B. auf der Startseite):

        from training_calendar import render_trainer_feedback_inbox
        render_trainer_feedback_inbox()
    """
    data = TrainingData(csv_path=csv_path)
    competitions = CompetitionData(csv_path=wettkaempfe_csv)
    feedback = FeedbackData(csv_path=feedback_csv)
    cal = TrainingCalendar(data, competitions, feedback)
    cal.render(role=role, current_user=current_user)


if __name__ == "__main__":
    st.set_page_config(
        page_title="Triathlon Trainingskalender",
        layout="wide",
        page_icon="🏊",
    )

    st.title("🏊🚴🏃 Triathlon Trainingskalender")

    with st.sidebar:
        st.header("⚙️ Einstellungen")
        demo_role = st.radio("Rolle", ["trainer", "athlete"], index=0)
        demo_user = None
        if demo_role == "athlete":
            demo_user = st.selectbox(
                "Athlet-Name (Simulation)",
                [
                    "Anne Haug",
                    "Jan Frodeno",
                    "Daniela Ryf",
                    "Chrissie Wellington",
                    "Gustav Iden",
                    "Kristian Blummenfelt",
                    "Lucy Charles-Barclay",
                    "Patrick Lange",
                ],
            )

    render_calendar(role=demo_role, current_user=demo_user)
