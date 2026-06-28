# Black Sea Water Temperature

Live and historical **sea surface temperature** for the Black Sea coast,
tracking **38 locations** across 5 countries (Bulgaria, Turkey, Romania, Georgia
and Russia). Data comes from the free, key-less
[Open-Meteo Marine API](https://open-meteo.com/en/docs/marine-weather-api) and is
updated automatically every 2 hours by GitHub Actions.

Live site: **https://more.masoko.net**

Each location has its own dashboard with a live reading, a 30-day trend, a
full-history chart, a year-over-year comparison, a monthly heatmap and all-time
records — plus a hub map and a cross-location comparison page.

## How it works

The whole project is driven by a single source of truth, `locations.py`, which
lists every tracked location and its coordinates. Everything else reads from it:

```
                         locations.py  (single source of truth)
                                 │
            ┌────────────────────┼─────────────────────┐
            │                    │                      │
      backfill.py          get_daily_temp.py        build_site.py
   (one-time history)   (every 2h, in CI: appends    (generates the
            │            new readings + latest.json)   static site)
            └────────────┬───────┘                      │
                         ▼                               ▼
              *_water_temp.csv  ─────────────────►   docs/  (HTML, JS,
              (one CSV per location)                  locations.js, sitemap…)
                         │                               │
                         ▼                               ▼
        frontend fetches each CSV from        GitHub Pages serves docs/
        raw.githubusercontent.com at runtime  at more.masoko.net
        and renders charts with Plotly
```

- **Collection** — `get_daily_temp.py` runs every 2 hours via GitHub Actions
  (`.github/workflows/update-temp.yml`). For each location it fetches the latest
  sea surface temperature, appends any new readings to that location's CSV, and
  rewrites `docs/latest_temps.json` (the current reading per location, used by the
  hub map). The workflow then commits the changed CSVs and JSON.
- **History** — `backfill.py` is a one-time script that pulls the full history
  from the Open-Meteo archive (back to each location's `start_date`).
- **Site** — `build_site.py` turns the templates in `templates/` plus
  `locations.py` into the static site under `docs/`. The frontend is fully static:
  it loads each location's CSV directly from `raw.githubusercontent.com` and draws
  the charts client-side with [Plotly](https://plotly.com/javascript/). GitHub
  Pages serves `docs/`.

The active pipeline (`locations.py`, `get_daily_temp.py`, `backfill.py`,
`build_site.py`) uses **only the Python standard library** (Python 3.7+) — no
`pip install` needed.

> **Note:** an earlier version scraped `stringmeteo.com`. That source is now
> behind a JavaScript anti-bot wall that blocks CI IP addresses, so the project
> switched to the Open-Meteo Marine API. The old scrapers are kept for reference
> (see *Legacy scripts* below) but are not used.

## Project structure

```
.
├── locations.py                 # SINGLE SOURCE OF TRUTH — every location + coords
├── get_daily_temp.py            # CI script: append new readings, write latest_temps.json
├── backfill.py                  # one-time historical backfill from Open-Meteo archive
├── build_site.py                # static site generator (templates + locations.py → docs/)
│
├── *_water_temp.csv             # one CSV per location (e.g. varna_water_temp.csv)
├── sea_water_temp.csv           # Burgas history (the original series)
│
├── templates/                   # page templates used by build_site.py
│   ├── index.html               #   per-location dashboard
│   ├── compare.html             #   year-over-year comparison
│   ├── heatmap.html             #   monthly heatmap
│   ├── stats.html               #   records & statistics
│   └── compare-locations.html   #   cross-location overlay (global page)
│
├── docs/                        # generated static site, served by GitHub Pages
│   ├── index.html               #   hub page with the map (generated)
│   ├── <slug>/                  #   per-location pages (generated)
│   ├── compare-locations.html   #   (generated)
│   ├── locations.js             #   location data for the frontend (generated)
│   ├── latest_temps.json        #   current reading per location (written by CI)
│   ├── data.js                  #   loads CSVs from raw GitHub + renders charts
│   ├── map.js                   #   Leaflet hub map
│   ├── i18n.js                  #   EN/BG translations (hand-maintained)
│   ├── style.css, favicon.svg
│   ├── sitemap.xml, robots.txt  #   (generated)
│   └── CNAME                     #   more.masoko.net
│
├── .github/workflows/
│   └── update-temp.yml          # runs get_daily_temp.py every 2 hours
│
└── (legacy) main.py, get_all.py, daily_air_temp.py, get_daily_temp.sh
```

### Legacy scripts

These are kept for history and are **not** part of the active pipeline:

- `main.py` / `get_all.py` — original one-time scrapers for `stringmeteo.com`
  (require `pandas`).
- `daily_air_temp.py` — air-temperature scraper for `sinoptik.bg` (requires
  `beautifulsoup4`).
- `get_daily_temp.sh` — old cron wrapper from when this ran on a Raspberry Pi.

## Data format

Each `*_water_temp.csv` has a header and rows of timestamp + temperature in °C:

```
date,temp
2023-01-01 06:00:00,11.4
2023-01-01 12:00:00,11.5
2023-01-01 18:00:00,11.6
```

Readings are recorded three times a day — at **06:00, 12:00 and 18:00 UTC** — to
match the cadence of the original historical series.

> **The offshore-coordinate gotcha:** Open-Meteo's marine grid has *land-masked*
> cells that return all-`null`. The exact town coordinates often land on such a
> cell, so the `lat`/`lon` in `locations.py` are deliberately nudged **offshore**
> until they snap to a valid sea cell. Always confirm the API returns non-null
> temperatures for a new coordinate before committing it.

## Adding a new location

1. **Add the location to `locations.py`.** Append a dict to `LOCATIONS`. Choose
   `lat`/`lon` nudged **offshore** (see the gotcha above) — not the exact town —
   and verify Open-Meteo returns non-null data for them. Example:

   ```python
   {"slug": "obzor", "csv_file": "obzor_water_temp.csv", "lat": 42.82, "lon": 27.92,
    "name_en": "Obzor", "name_bg": "Обзор", "flag": "🏖️", "start_date": "2023-01-01",
    "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
   ```

   Conventions: `csv_file` is `<slug-with-underscores>_water_temp.csv`; `slug`
   uses dashes (e.g. `cape-kaliakra`). If this is a **new country**, also add its
   slug to `COUNTRY_ORDER` at the top of the file.

   You can sanity-check a coordinate first:

   ```bash
   curl "https://marine-api.open-meteo.com/v1/marine?latitude=42.82&longitude=27.92&hourly=sea_surface_temperature&past_days=1&forecast_days=1"
   ```

2. **Add translations to `docs/i18n.js`.** In **both** the `en` and `bg` blocks
   add a `loc_<slug-without-dashes>` key (dashes are stripped — `cape-kaliakra`
   becomes `loc_capekaliakra`):

   ```js
   loc_obzor: 'Obzor, Bulgaria',   // in the en block
   loc_obzor: 'Обзор, България',   // in the bg block
   ```

   For a **new country**, also add `country_<slug>` to both blocks.

3. **Backfill the history:**

   ```bash
   python3 backfill.py obzor
   ```

   This creates `obzor_water_temp.csv` filled from `start_date` to today. (Run
   `python3 backfill.py` with no argument to rebuild every location.)

4. **Regenerate the site:**

   ```bash
   python3 build_site.py
   ```

   This writes the new `docs/obzor/` pages and refreshes `docs/locations.js`,
   `docs/index.html`, `docs/compare-locations.html`, `docs/sitemap.xml` and
   `docs/robots.txt`.

5. **Commit** the new CSV and the regenerated `docs/`. The next scheduled CI run
   will start appending fresh readings and add the location to
   `docs/latest_temps.json`.

## Local development

No third-party dependencies are needed for the active scripts (Python 3.7+,
standard library only):

```bash
python3 build_site.py            # regenerate the static site after a change
python3 backfill.py [slug]       # (re)build CSV history for one or all locations
python3 get_daily_temp.py        # fetch + append the latest readings locally
```

The legacy scrapers need `pandas` (`main.py`, `get_all.py`) or `beautifulsoup4`
(`daily_air_temp.py`).

## Deployment

The site is deployed via **GitHub Pages from the `docs/` directory**. `docs/CNAME`
points the custom domain `more.masoko.net` at it. Because the frontend reads the
CSV files directly from `raw.githubusercontent.com`, new data shows up on the live
site as soon as the 2-hourly GitHub Actions job commits it — no rebuild required.
