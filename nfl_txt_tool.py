import requests
import datetime as dt
from zoneinfo import ZoneInfo  # Python 3.9+, unter Windows ggf. `pip install tzdata`
from typing import List, Dict, Tuple

# ============================================================
# KONFIGURATION
# ============================================================

# !!! HIER DEIN API-KEY VON "The Odds API" EINTRAGEN !!!
API_KEY = "DEIN API-KEY"

# NFL Odds Endpoint (Moneyline / h2h)
ODDS_API_URL = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"

# NFL Scoreboard (ESPN)
NFL_SCOREBOARD_URL = "https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard"

TIMEZONE = "Europe/Berlin"
LOCAL_TZ = ZoneInfo(TIMEZONE)


# ============================================================
# HILFSFUNKTIONEN
# ============================================================

def parse_date_input(date_str: str) -> dt.date:
    """
    Erwartet Datum im Format TT.MM.JJJJ und gibt datetime.date zurück.
    """
    return dt.datetime.strptime(date_str.strip(), "%d.%m.%Y").date()


def to_local_datetime(iso_str: str) -> dt.datetime:
    """
    ISO-String (UTC) -> lokale Zeit (Europe/Berlin).
    Beispiel: "2025-11-25T18:00:00Z"
    """
    if iso_str.endswith("Z"):
        iso_str = iso_str.replace("Z", "+00:00")
    dt_utc = dt.datetime.fromisoformat(iso_str)
    return dt_utc.astimezone(LOCAL_TZ)


def fcomma(value: float) -> str:
    """
    Float -> String mit 2 Nachkommastellen und Komma als Dezimaltrenner.
    1.25 -> "1,25"
    """
    return f"{value:.2f}".replace(".", ",")


def get_nfl_week_range(target_date: dt.date) -> Tuple[dt.date, dt.date]:
    """
    Berechnet die NFL-Week (Donnerstag–Dienstag) zu einem Datum.

    Idee:
      - Datum Do–Di => Zugehörige Week: Do davor/bzw. derselbe + 5 Tage
      - Mittwoch => kommende Week (ab morgen Donnerstag)

    Rückgabe: (week_start (Do), week_end (Di))
    """
    weekday = target_date.weekday()  # Montag=0, Dienstag=1, Mittwoch=2, Donnerstag=3, ...

    if weekday == 2:
        # Mittwoch -> nächste Week (ab morgen Donnerstag)
        week_start = target_date + dt.timedelta(days=1)
    else:
        # Für alle anderen Tage: Donnerstag der laufenden Week
        # Donnerstag hat weekday == 3
        diff = (weekday - 3) % 7
        week_start = target_date - dt.timedelta(days=diff)

    week_end = week_start + dt.timedelta(days=5)  # Do–Di (6 Tage)
    return week_start, week_end


# ============================================================
# QUOTEN HOLEN (The Odds API) – NFL-WEEK
# ============================================================

def fetch_odds_week(api_key: str, week_start: dt.date, week_end: dt.date) -> List[Dict]:
    """
    Holt Quoten (moneyline / h2h) für alle NFL-Spiele innerhalb der NFL-Week.

    NFL-Week = Donnerstag–Dienstag (week_start–week_end).

    Rückgabe: Liste von Dicts mit:
      - datetime_str (lokal)
      - away_team
      - home_team
      - odds_away
      - odds_home
    """
    params = {
        "apiKey": api_key,
        "regions": "eu",       # europäische Bookies
        "markets": "h2h",      # moneyline
        "dateFormat": "iso",
        "oddsFormat": "decimal",
    }

    print("Hole Quoten von The Odds API für NFL-Week...")
    resp = requests.get(ODDS_API_URL, params=params, timeout=20)
    resp.raise_for_status()
    events = resp.json()

    games_out = []

    for ev in events:
        commence_iso = ev.get("commence_time")
        if not commence_iso:
            continue

        try:
            commence_local = to_local_datetime(commence_iso)
        except Exception:
            continue

        game_date = commence_local.date()

        # Nur Spiele innerhalb der NFL-Woche berücksichtigen
        if not (week_start <= game_date <= week_end):
            continue

        home = ev.get("home_team")
        away = ev.get("away_team")
        if not home or not away:
            continue

        odds_home = None
        odds_away = None

        for bm in ev.get("bookmakers", []):
            for market in bm.get("markets", []):
                if market.get("key") != "h2h":
                    continue
                for out in market.get("outcomes", []):
                    name = out.get("name")
                    price = out.get("price")
                    if name == away:
                        odds_away = float(price)
                    elif name == home:
                        odds_home = float(price)
                if odds_home is not None and odds_away is not None:
                    break
            if odds_home is not None and odds_away is not None:
                break

        if odds_home is None or odds_away is None:
            # Wenn bei diesem Event keine kompletten Quoten gefunden werden, überspringen
            continue

        games_out.append(
            {
                "datetime_str": commence_local.strftime("%d.%m.%Y %H:%M"),
                "away_team": away,
                "home_team": home,
                "odds_away": odds_away,
                "odds_home": odds_home,
            }
        )

    return games_out


def format_odds_line(game: Dict) -> str:
    """
    Format:
      "Datum Uhrzeit | Awayteam : Hometeam | Quote Away | Quote Home"

    Beispiel:
      "14.11.2025 01:10 | Miami Dolphins : Kansas City Chiefs | 3,48 | 1,36"
    """
    return (
        f"{game['datetime_str']} | "
        f"{game['away_team']} : {game['home_team']} | "
        f"{fcomma(game['odds_away'])} | {fcomma(game['odds_home'])}"
    )


def write_odds_file_week(games: List[Dict], week_start: dt.date, week_end: dt.date) -> str:
    """
    Schreibt die Quoten der NFL-Week in eine Textdatei.

    Dateiname: NFL_Quoten_Week_YYYY-MM-DD_bis_YYYY-MM-DD.txt
    """
    filename = (
        f"NFL_Quoten_Week_{week_start.isoformat()}_bis_{week_end.isoformat()}.txt"
    )
    with open(filename, "w", encoding="utf-8") as f:
        for g in games:
            line = format_odds_line(g)
            f.write(line + "\n")

    return filename


# ============================================================
# ERGEBNISSE HOLEN (ESPN NFL Scoreboard) – NFL-WEEK
# ============================================================

def fetch_results_week(week_start: dt.date, week_end: dt.date) -> List[Dict]:
    """
    Holt Ergebnisse für die gesamte NFL-Week (Donnerstag–Dienstag)
    über das ESPN NFL Scoreboard.

    Für jeden Tag im Bereich [week_start, week_end] wird
    https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates=YYYYMMDD
    abgefragt.

    Rückgabe: Liste von Dicts mit:
      - away_team
      - home_team
      - score_away
      - score_home
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (NFL-Results-Script)",
        "Accept": "application/json",
    }

    games_out: List[Dict] = []

    current = week_start
    while current <= week_end:
        dates_param = current.strftime("%Y%m%d")
        print(f"Hole Ergebnisse für {dates_param} vom NFL Scoreboard...")

        params = {"dates": dates_param}
        resp = requests.get(NFL_SCOREBOARD_URL, headers=headers, params=params, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        events = data.get("events", [])

        for ev in events:
            # Status filtern: nur "fertige" Spiele (state == "post")
            status = (
                ev.get("status", {})
                  .get("type", {})
                  .get("state")
            )
            if status != "post":
                continue

            competitions = ev.get("competitions", [])
            if not competitions:
                continue

            comp = competitions[0]
            competitors = comp.get("competitors", [])

            home_name = ""
            away_name = ""
            home_score = 0
            away_score = 0

            for c in competitors:
                team = c.get("team", {})
                name = f"{team.get('location', '').strip()} {team.get('name', '').strip()}".strip()
                try:
                    score = int(c.get("score", 0) or 0)
                except (TypeError, ValueError):
                    score = 0

                if c.get("homeAway") == "home":
                    home_name = name
                    home_score = score
                elif c.get("homeAway") == "away":
                    away_name = name
                    away_score = score

            if not home_name or not away_name:
                continue

            games_out.append(
                {
                    "away_team": away_name,
                    "home_team": home_name,
                    "score_away": away_score,
                    "score_home": home_score,
                }
            )

        current += dt.timedelta(days=1)

    return games_out


def format_result_line(game: Dict) -> str:
    """
    Format für Ergebnisse OHNE Datum/Uhrzeit:

      "Awayteam : Hometeam AwayScore:HomeScore"

    Beispiel:
      "Miami Dolphins : Kansas City Chiefs 24:31"
    """
    return (
        f"{game['away_team']} : {game['home_team']} "
        f"{game['score_away']}:{game['score_home']}"
    )


def write_results_file_week(games: List[Dict], week_start: dt.date, week_end: dt.date) -> str:
    """
    Schreibt die Ergebnisse der NFL-Week in eine Textdatei.

    Dateiname: NFL_Ergebnisse_Week_YYYY-MM-DD_bis_YYYY-MM-DD.txt

    Jede Zeile im Format (ohne Datum/Uhrzeit):
      Awayteam : Hometeam AwayScore:HomeScore
    """
    filename = (
        f"NFL_Ergebnisse_Week_{week_start.isoformat()}_bis_{week_end.isoformat()}.txt"
    )
    with open(filename, "w", encoding="utf-8") as f:
        for g in games:
            line = format_result_line(g)
            f.write(line + "\n")

    return filename


# ============================================================
# HAUPTMENÜ / CLI
# ============================================================

def menu():
    print("========================================")
    print(" NFL TXT TOOL (Week Donnerstag–Dienstag)")
    print("========================================")
    print("1) NFL-Quoten für eine Week holen und als TXT speichern")
    print("2) NFL-Ergebnisse für eine Week holen und als TXT speichern")
    print("3) Beenden")
    print("========================================")

    choice = input("Auswahl (1/2/3): ").strip()
    return choice


def main():
    while True:
        choice = menu()

        if choice == "3":
            print("Beende Programm.")
            break

        if choice not in ("1", "2"):
            print("Ungültige Auswahl.")
            continue

        date_str = input("Bitte Datum eingeben (TT.MM.JJJJ): ").strip()
        try:
            target_date = parse_date_input(date_str)
        except ValueError:
            print("Ungültiges Datum. Bitte Format TT.MM.JJJJ verwenden.")
            continue

        week_start, week_end = get_nfl_week_range(target_date)
        print(
            f"Berechnete NFL-Week: Donnerstag–Dienstag "
            f"{week_start.strftime('%d.%m.%Y')} bis {week_end.strftime('%d.%m.%Y')}"
        )

        if choice == "1":
            # QUOTEN FÜR NFL-WEEK
            if not API_KEY or API_KEY == "DEIN_API_KEY_HIER":
                print("FEHLER: Kein gültiger API_KEY eingetragen. Bitte im Skript API_KEY setzen.")
                continue

            try:
                games = fetch_odds_week(API_KEY, week_start, week_end)
            except Exception as e:
                print(f"Fehler beim Holen der Quoten: {e}")
                continue

            if not games:
                print("Keine Quoten für diese NFL-Week gefunden.")
                continue

            filename = write_odds_file_week(games, week_start, week_end)
            print(f"{len(games)} Quoten gespeichert in: {filename}")

        elif choice == "2":
            # ERGEBNISSE FÜR NFL-WEEK
            try:
                games = fetch_results_week(week_start, week_end)
            except Exception as e:
                print(f"Fehler beim Holen der Ergebnisse: {e}")
                continue

            if not games:
                print("Keine Ergebnisse für diese NFL-Week gefunden.")
                continue

            filename = write_results_file_week(games, week_start, week_end)
            print(f"{len(games)} Ergebnisse gespeichert in: {filename}")
            print("Format der Zeilen: Awayteam : Hometeam AwayScore:HomeScore")

        input("\nWeiter mit Enter...")


if __name__ == "__main__":
    main()
