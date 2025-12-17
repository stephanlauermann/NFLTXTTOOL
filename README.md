# NFL TXT TOOL

Ein simples Python-CLI-Tool zum Abrufen von **NFL-Quoten** und **NFL-Ergebnissen**
und zum Export als **TXT-Dateien**.  

---

## Funktionen

- Abruf von **NFL Moneyline-Quoten (h2h)** für eine NFL-Week (Do–Di)
- Abruf von **NFL-Endergebnissen** für eine NFL-Week (Do–Di)
- TXT-Export mit klaren, einheitlichen Zeilenformaten
- Zeitzonen-Umrechnung auf **Europe/Berlin**
- CLI-Menü mit Datums-Eingabe (`TT.MM.JJJJ`)

---

## Voraussetzungen

- Python **3.9 oder höher**
- Python-Paket `requests`
- Internetverbindung
- API-Key von **The Odds API**

### Installation

```bash
python -m pip install -U requests
```

**Windows-Hinweis:**  
Falls es Probleme mit der Zeitzone gibt, installiere zusätzlich:

```bash
python -m pip install -U tzdata
```

---

## Konfiguration (API-Key)

Für den Abruf der Quoten wird ein API-Key von **The Odds API** benötigt.

Der API-Key wird **nicht im Code gespeichert**, sondern über die
Umgebungsvariable `ODDS_API_KEY` geladen.

### API-Key setzen

#### Windows (PowerShell)

```powershell
setx ODDS_API_KEY "DEIN_API_KEY"
```

Danach ein neues Terminal öffnen.

#### Linux / macOS

```bash
export ODDS_API_KEY="DEIN_API_KEY"
```

> Das Script liest den Key automatisch mit  
> `os.getenv("ODDS_API_KEY")` ein.  
> Fehlt der Key, bricht das Programm mit einer Fehlermeldung ab.

⚠ **Sicherheit:**  
Lege deinen API-Key niemals direkt im Code oder in öffentlichen Repositories ab.

---

## Programmstart

```bash
python nfl_txt_tool.py
```

---

## CLI-Menü

```text
1) Quoten für eine NFL-Week holen und als TXT speichern
2) Ergebnisse für eine NFL-Week holen und als TXT speichern
3) Beenden
```

Anschließend wird ein Startdatum der NFL-Week im Format `TT.MM.JJJJ`
(Donnerstag) abgefragt.

---

## Ausgabe-Dateien

### NFL-Quoten

**Dateiname:**

```text
NFL_Quoten_Week_YYYY-MM-DD_bis_YYYY-MM-DD.txt
```

**Format pro Zeile:**

```text
DD.MM.YYYY HH:MM | Awayteam : Hometeam | QuoteAway | QuoteHome
```

**Beispiel:**

```text
14.11.2025 01:10 | New York Jets : Miami Dolphins | 3,48 | 1,36
```

> Die Quoten sind im **Dezimalformat**
> mit **Komma** als Dezimaltrenner.

---

### NFL-Ergebnisse

**Dateiname:**

```text
NFL_Ergebnisse_Week_YYYY-MM-DD_bis_YYYY-MM-DD.txt
```

**Format pro Zeile:**

```text
Awayteam : Hometeam AwayScore:HomeScore
```

**Beispiel:**

```text
Dallas Cowboys : Philadelphia Eagles 24:31
```

---

## Fehlerbehebung

- **Fehlender API-Key:** Prüfe, ob `ODDS_API_KEY` gesetzt ist
- **Keine Spiele gefunden:** Für die NFL-Week existieren evtl. keine Spiele
- **401 / 403 Fehler:** API-Key ungültig oder Kontingent verbraucht
- **Netzwerkfehler:** Internetverbindung prüfen

---

## Technische Quellen

- Quoten: The Odds API (`americanfootball_nfl`)
- Ergebnisse: Offizielles ESPN NFL Scoreboard JSON
- Zeitzone: `Europe/Berlin`

---

README.md für `nfl_txt_tool.py`  
API-Key-Verwaltung über Umgebungsvariablen

---

## Author

Created by Stephan Lauermann. AI assisted by ChatGPT.
