# Maine Black Bears Sports

A Bangor Daily News hub for University of Maine athletics: schedules and scores, conference standings, box scores, rosters, and news. A Python scraper collects the data into JSON files twice a day, and a static React page served from GitHub Pages displays it.

**Live site:** https://dsmacleod.github.io/bdn-umaine-sports/

## How it works

1. **Scraper** (`scraper/`, started with `python -m scraper.main`) fetches each data type and writes it to `data/`. Each step is wrapped in its own error handling, so one failed source does not stop the others.
2. **Front end** (`index.html` + `app.js`) is a single page that uses React 18, Babel standalone, and Tailwind, all loaded from CDNs, so there is no build step. It loads the five JSON files and shows a featured-games strip, a news strip, and tabs for Scores, Standings, Box Scores, and Rosters, with a sport filter.

## Data sources and outputs

| Output | Module | Source |
|---|---|---|
| `data/schedules.json` | `scraper/schedules.py` | GoBlackBears.com `schedule_txt.ashx` plaintext schedules (records and game list) |
| `data/standings.json` | `scraper/standings.py` | America East JSON API (`americaeast.com/services/standings.ashx`) and Hockey East HTML standings (`hockeyeastonline.com`) |
| `data/box_scores.json` | `scraper/box_scores.py` | GoBlackBears.com `responsive-schedule.ashx` JSON, up to 5 games per sport, using the game IDs from the schedules |
| `data/rosters.json` | `scraper/rosters.py` | GoBlackBears.com (Sidearm) roster pages |
| `data/news.json` | `scraper/news.py` | GoBlackBears.com RSS, plus BDN sports category RSS feeds filtered by keyword to UMaine coverage |

Each file contains a `last_updated` UTC timestamp. Sports, URLs, the four featured "priority" sports (men's hockey, women's and men's basketball, football), and the scraper's User-Agent are set in `scraper/config.py`.

## Automation (GitHub Actions)

- **`scrape.yml`** runs at 12:00 UTC (7 a.m. Eastern) and 02:00 UTC (9 p.m. Eastern) and can also be started by hand. It installs `requirements.txt` on Python 3.12, runs the scraper, and commits `data/` as `github-actions[bot]` when anything has changed.
- **`pages.yml`** deploys the repo root to GitHub Pages on every push to `main` and can also be started by hand.

No secrets or environment variables are required. Both workflows use only the default `GITHUB_TOKEN`.

## Running locally

```sh
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

python -m scraper.main      # refresh data/*.json
pytest                      # parser tests against fixtures in tests/fixtures/

python3 -m http.server 8000 # then open http://localhost:8000/
```

Serve the site over HTTP, not `file://`, because `app.js` uses `fetch` to load `data/*.json`.
