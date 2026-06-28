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
#   nessebar          42.66, 27.78
#   sozopol           42.41, 27.73
#   sunny-beach       42.69, 27.76
#   golden-sands      43.28, 28.10
#   balchik           43.42, 28.25
#   cape-kaliakra     43.36, 28.50
#   albena            43.37, 28.15
#   sveti-konstantin  43.23, 28.08
#   irakli            42.80, 27.93
#   pomorie           42.56, 27.70
#   primorsko         42.27, 27.82
#   lozenets          42.22, 27.85
#   sveti-vlas        42.71, 27.80

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
    {"slug": "nessebar",    "csv_file": "nessebar_water_temp.csv",    "lat": 42.66, "lon": 27.78,
     "name_en": "Nessebar",    "name_bg": "Несебър",    "flag": "🏘️", "start_date": "2023-01-01"},
    {"slug": "sozopol",     "csv_file": "sozopol_water_temp.csv",     "lat": 42.41, "lon": 27.73,
     "name_en": "Sozopol",     "name_bg": "Созопол",    "flag": "⚓", "start_date": "2023-01-01"},
    {"slug": "sunny-beach", "csv_file": "sunny_beach_water_temp.csv", "lat": 42.69, "lon": 27.76,
     "name_en": "Sunny Beach", "name_bg": "Слънчев бряг", "flag": "☀️", "start_date": "2023-01-01"},
    {"slug": "golden-sands", "csv_file": "golden_sands_water_temp.csv", "lat": 43.28, "lon": 28.1,
     "name_en": "Golden Sands", "name_bg": "Златни пясъци", "flag": "🌅", "start_date": "2023-01-01"},
    {"slug": "balchik",     "csv_file": "balchik_water_temp.csv",     "lat": 43.42, "lon": 28.25,
     "name_en": "Balchik",     "name_bg": "Балчик",     "flag": "🌷", "start_date": "2023-01-01"},
    {"slug": "cape-kaliakra", "csv_file": "cape_kaliakra_water_temp.csv", "lat": 43.36, "lon": 28.5,
     "name_en": "Cape Kaliakra", "name_bg": "Нос Калиакра", "flag": "🦅", "start_date": "2023-01-01"},
    {"slug": "albena",      "csv_file": "albena_water_temp.csv",      "lat": 43.37, "lon": 28.15,
     "name_en": "Albena",      "name_bg": "Албена",     "flag": "🌴", "start_date": "2023-01-01"},
    {"slug": "sveti-konstantin", "csv_file": "sveti_konstantin_water_temp.csv", "lat": 43.23, "lon": 28.08,
     "name_en": "St. Konstantin and Elena", "name_bg": "Св. св. Константин и Елена", "flag": "🧖", "start_date": "2023-01-01"},
    {"slug": "irakli",      "csv_file": "irakli_water_temp.csv",      "lat": 42.8, "lon": 27.93,
     "name_en": "Irakli Beach", "name_bg": "Иракли",    "flag": "🌿", "start_date": "2023-01-01"},
    {"slug": "pomorie",     "csv_file": "pomorie_water_temp.csv",     "lat": 42.56, "lon": 27.7,
     "name_en": "Pomorie",     "name_bg": "Поморие",    "flag": "🧂", "start_date": "2023-01-01"},
    {"slug": "primorsko",   "csv_file": "primorsko_water_temp.csv",   "lat": 42.27, "lon": 27.82,
     "name_en": "Primorsko",   "name_bg": "Приморско",  "flag": "🏕️", "start_date": "2023-01-01"},
    {"slug": "lozenets",    "csv_file": "lozenets_water_temp.csv",    "lat": 42.22, "lon": 27.85,
     "name_en": "Lozenets",    "name_bg": "Лозенец",    "flag": "🍇", "start_date": "2023-01-01"},
    {"slug": "sveti-vlas",  "csv_file": "sveti_vlas_water_temp.csv",  "lat": 42.71, "lon": 27.8,
     "name_en": "Sveti Vlas",  "name_bg": "Свети Влас", "flag": "🛥️", "start_date": "2023-01-01"},
]
