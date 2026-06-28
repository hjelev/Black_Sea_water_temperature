# Single source of truth for every tracked Black Sea location.
#
# Imported by:
#   - get_daily_temp.py  (appends new readings to each csv every 2h in CI)
#   - backfill.py        (one-time historical backfill from the Open-Meteo archive)
#   - build_site.py      (generates the per-location SEO pages + docs/locations.js)
#
# Coordinates are nudged offshore so they snap to a valid Open-Meteo *sea* cell.
# The exact town coords often land on a land-masked cell that returns all-null
# (the original Sinemorets gotcha). The cell each request snaps to is noted below.
#
#   slug         request lat/lon   snapped cell
#   burgas       42.47, 27.55      Burgas Bay
#   sinemorets   42.06, 28.00      42.21N, 28.13E
#   varna        43.19, 28.00      43.125N, 27.958E (Varna Bay)
#   kamen-bryag  43.45, 28.58      43.375N, 28.542E
#   tyulenovo    43.52, 28.60      43.541N, 28.708E

LOCATIONS = [
    {"slug": "burgas",      "csv_file": "sea_water_temp.csv",        "lat": 42.47, "lon": 27.55,
     "name_en": "Burgas",      "name_bg": "Бургас",     "flag": "🏖️", "start_date": "2000-01-01"},
    {"slug": "sinemorets",  "csv_file": "sinemorets_water_temp.csv", "lat": 42.06, "lon": 28.0,
     "name_en": "Sinemorets",  "name_bg": "Синеморец",  "flag": "⛵", "start_date": "2023-01-01"},
    {"slug": "varna",       "csv_file": "varna_water_temp.csv",      "lat": 43.19, "lon": 28.0,
     "name_en": "Varna",       "name_bg": "Варна",      "flag": "🏛️", "start_date": "2023-01-01"},
    {"slug": "kamen-bryag", "csv_file": "kamen_bryag_water_temp.csv", "lat": 43.45, "lon": 28.58,
     "name_en": "Kamen Bryag", "name_bg": "Камен бряг", "flag": "🪨", "start_date": "2023-01-01"},
    {"slug": "tyulenovo",   "csv_file": "tyulenovo_water_temp.csv",   "lat": 43.52, "lon": 28.6,
     "name_en": "Tyulenovo",   "name_bg": "Тюленово",   "flag": "🦭", "start_date": "2023-01-01"},
]
