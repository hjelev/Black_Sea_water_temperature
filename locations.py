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
#
# International locations (Turkey/Romania/Georgia/Russia) are nudged toward the
# open sea away from their coastlines (north for the Turkish south coast, east
# for Romania, west for Georgia, south for the NE Russian coast).

# Display order for grouping the UI by country (hub grid, dropdown, checkboxes).
COUNTRY_ORDER = ["bulgaria", "turkey", "romania", "georgia", "russia"]

LOCATIONS = [
    # --- Bulgaria ---
    {"slug": "burgas",      "csv_file": "sea_water_temp.csv",        "lat": 42.47, "lon": 27.55,
     "name_en": "Burgas",      "name_bg": "Бургас",     "flag": "🏖️", "start_date": "2000-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "sinemorets",  "csv_file": "sinemorets_water_temp.csv", "lat": 42.06, "lon": 28.0,
     "name_en": "Sinemorets",  "name_bg": "Синеморец",  "flag": "⛵", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "varna",       "csv_file": "varna_water_temp.csv",      "lat": 43.19, "lon": 28.0,
     "name_en": "Varna",       "name_bg": "Варна",      "flag": "🏛️", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "kamen-bryag", "csv_file": "kamen_bryag_water_temp.csv", "lat": 43.45, "lon": 28.58,
     "name_en": "Kamen Bryag", "name_bg": "Камен бряг", "flag": "🪨", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "tyulenovo",   "csv_file": "tyulenovo_water_temp.csv",   "lat": 43.52, "lon": 28.6,
     "name_en": "Tyulenovo",   "name_bg": "Тюленово",   "flag": "🦭", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "nessebar",    "csv_file": "nessebar_water_temp.csv",    "lat": 42.66, "lon": 27.78,
     "name_en": "Nessebar",    "name_bg": "Несебър",    "flag": "🏘️", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "sozopol",     "csv_file": "sozopol_water_temp.csv",     "lat": 42.41, "lon": 27.73,
     "name_en": "Sozopol",     "name_bg": "Созопол",    "flag": "⚓", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "sunny-beach", "csv_file": "sunny_beach_water_temp.csv", "lat": 42.69, "lon": 27.76,
     "name_en": "Sunny Beach", "name_bg": "Слънчев бряг", "flag": "☀️", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "golden-sands", "csv_file": "golden_sands_water_temp.csv", "lat": 43.28, "lon": 28.1,
     "name_en": "Golden Sands", "name_bg": "Златни пясъци", "flag": "🌅", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "balchik",     "csv_file": "balchik_water_temp.csv",     "lat": 43.42, "lon": 28.25,
     "name_en": "Balchik",     "name_bg": "Балчик",     "flag": "🌷", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "cape-kaliakra", "csv_file": "cape_kaliakra_water_temp.csv", "lat": 43.36, "lon": 28.5,
     "name_en": "Cape Kaliakra", "name_bg": "Нос Калиакра", "flag": "🦅", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "albena",      "csv_file": "albena_water_temp.csv",      "lat": 43.37, "lon": 28.15,
     "name_en": "Albena",      "name_bg": "Албена",     "flag": "🌴", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "sveti-konstantin", "csv_file": "sveti_konstantin_water_temp.csv", "lat": 43.23, "lon": 28.08,
     "name_en": "St. Konstantin and Elena", "name_bg": "Св. св. Константин и Елена", "flag": "🧖", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "irakli",      "csv_file": "irakli_water_temp.csv",      "lat": 42.8, "lon": 27.93,
     "name_en": "Irakli Beach", "name_bg": "Иракли",    "flag": "🌿", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "pomorie",     "csv_file": "pomorie_water_temp.csv",     "lat": 42.56, "lon": 27.7,
     "name_en": "Pomorie",     "name_bg": "Поморие",    "flag": "🧂", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "primorsko",   "csv_file": "primorsko_water_temp.csv",   "lat": 42.27, "lon": 27.82,
     "name_en": "Primorsko",   "name_bg": "Приморско",  "flag": "🏕️", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "lozenets",    "csv_file": "lozenets_water_temp.csv",    "lat": 42.22, "lon": 27.85,
     "name_en": "Lozenets",    "name_bg": "Лозенец",    "flag": "🍇", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "sveti-vlas",  "csv_file": "sveti_vlas_water_temp.csv",  "lat": 42.71, "lon": 27.8,
     "name_en": "Sveti Vlas",  "name_bg": "Свети Влас", "flag": "🛥️", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},

    # --- Turkey (sea lies north of the coast → nudge latitude north) ---
    {"slug": "trabzon",     "csv_file": "trabzon_water_temp.csv",     "lat": 41.05, "lon": 39.72,
     "name_en": "Trabzon",     "name_bg": "Трабзон",    "flag": "⛪", "start_date": "2023-01-01",
     "country": "turkey", "country_en": "Turkey", "country_bg": "Турция"},
    {"slug": "sinop",       "csv_file": "sinop_water_temp.csv",       "lat": 42.1, "lon": 35.15,
     "name_en": "Sinop",       "name_bg": "Синоп",      "flag": "🏰", "start_date": "2023-01-01",
     "country": "turkey", "country_en": "Turkey", "country_bg": "Турция"},
    {"slug": "amasra",      "csv_file": "amasra_water_temp.csv",      "lat": 41.78, "lon": 32.38,
     "name_en": "Amasra",      "name_bg": "Амасра",     "flag": "🎣", "start_date": "2023-01-01",
     "country": "turkey", "country_en": "Turkey", "country_bg": "Турция"},
    {"slug": "rize",        "csv_file": "rize_water_temp.csv",        "lat": 41.07, "lon": 40.52,
     "name_en": "Rize",        "name_bg": "Ризе",       "flag": "🍵", "start_date": "2023-01-01",
     "country": "turkey", "country_en": "Turkey", "country_bg": "Турция"},
    {"slug": "sile",        "csv_file": "sile_water_temp.csv",        "lat": 41.22, "lon": 29.61,
     "name_en": "Şile",        "name_bg": "Шиле",       "flag": "🗼", "start_date": "2023-01-01",
     "country": "turkey", "country_en": "Turkey", "country_bg": "Турция"},

    # --- Romania (sea lies east of the coast → nudge longitude east) ---
    {"slug": "constanta",   "csv_file": "constanta_water_temp.csv",   "lat": 44.17, "lon": 28.72,
     "name_en": "Constanța",   "name_bg": "Кюстенджа",  "flag": "🎰", "start_date": "2023-01-01",
     "country": "romania", "country_en": "Romania", "country_bg": "Румъния"},
    {"slug": "mamaia",      "csv_file": "mamaia_water_temp.csv",      "lat": 44.25, "lon": 28.72,
     "name_en": "Mamaia",      "name_bg": "Мамая",      "flag": "🎉", "start_date": "2023-01-01",
     "country": "romania", "country_en": "Romania", "country_bg": "Румъния"},
    {"slug": "vama-veche",  "csv_file": "vama_veche_water_temp.csv",  "lat": 43.75, "lon": 28.65,
     "name_en": "Vama Veche",  "name_bg": "Вама Веке",  "flag": "🎸", "start_date": "2023-01-01",
     "country": "romania", "country_en": "Romania", "country_bg": "Румъния"},
    {"slug": "olimp",       "csv_file": "olimp_water_temp.csv",       "lat": 43.95, "lon": 28.68,
     "name_en": "Olimp",       "name_bg": "Олимп",      "flag": "🌳", "start_date": "2023-01-01",
     "country": "romania", "country_en": "Romania", "country_bg": "Румъния"},
    {"slug": "vadu",        "csv_file": "vadu_water_temp.csv",        "lat": 44.55, "lon": 28.83,
     "name_en": "Vadu & Corbu", "name_bg": "Ваду и Корбу", "flag": "🦩", "start_date": "2023-01-01",
     "country": "romania", "country_en": "Romania", "country_bg": "Румъния"},

    # --- Georgia (sea lies west of the coast → nudge longitude west) ---
    {"slug": "batumi",      "csv_file": "batumi_water_temp.csv",      "lat": 41.65, "lon": 41.58,
     "name_en": "Batumi",      "name_bg": "Батуми",     "flag": "🌆", "start_date": "2023-01-01",
     "country": "georgia", "country_en": "Georgia", "country_bg": "Грузия"},
    {"slug": "kvariati",    "csv_file": "kvariati_water_temp.csv",    "lat": 41.55, "lon": 41.5,
     "name_en": "Kvariati",    "name_bg": "Кварияти",   "flag": "🤿", "start_date": "2023-01-01",
     "country": "georgia", "country_en": "Georgia", "country_bg": "Грузия"},
    {"slug": "shekvetili",  "csv_file": "shekvetili_water_temp.csv",  "lat": 41.96, "lon": 41.68,
     "name_en": "Shekvetili",  "name_bg": "Шекветили",  "flag": "🧲", "start_date": "2023-01-01",
     "country": "georgia", "country_en": "Georgia", "country_bg": "Грузия"},
    {"slug": "kobuleti",    "csv_file": "kobuleti_water_temp.csv",    "lat": 41.82, "lon": 41.7,
     "name_en": "Kobuleti",    "name_bg": "Кобулети",   "flag": "🐚", "start_date": "2023-01-01",
     "country": "georgia", "country_en": "Georgia", "country_bg": "Грузия"},
    {"slug": "green-cape",  "csv_file": "green_cape_water_temp.csv",  "lat": 41.7, "lon": 41.64,
     "name_en": "Green Cape",  "name_bg": "Зелени нос", "flag": "🪴", "start_date": "2023-01-01",
     "country": "georgia", "country_en": "Georgia", "country_bg": "Грузия"},

    # --- Russia (sea lies south-west of the NE coast → nudge offshore) ---
    {"slug": "sochi",       "csv_file": "sochi_water_temp.csv",       "lat": 43.55, "lon": 39.72,
     "name_en": "Sochi",       "name_bg": "Сочи",       "flag": "🏔️", "start_date": "2023-01-01",
     "country": "russia", "country_en": "Russia", "country_bg": "Русия"},
    {"slug": "anapa",       "csv_file": "anapa_water_temp.csv",       "lat": 44.85, "lon": 37.3,
     "name_en": "Anapa",       "name_bg": "Анапа",      "flag": "🏝️", "start_date": "2023-01-01",
     "country": "russia", "country_en": "Russia", "country_bg": "Русия"},
    {"slug": "gelendzhik",  "csv_file": "gelendzhik_water_temp.csv",  "lat": 44.52, "lon": 38.05,
     "name_en": "Gelendzhik",  "name_bg": "Геленджик",  "flag": "🎢", "start_date": "2023-01-01",
     "country": "russia", "country_en": "Russia", "country_bg": "Русия"},
    {"slug": "novorossiysk", "csv_file": "novorossiysk_water_temp.csv", "lat": 44.68, "lon": 37.72,
     "name_en": "Novorossiysk", "name_bg": "Новоросийск", "flag": "🚢", "start_date": "2023-01-01",
     "country": "russia", "country_en": "Russia", "country_bg": "Русия"},
    {"slug": "abrau-durso", "csv_file": "abrau_durso_water_temp.csv", "lat": 44.59, "lon": 37.55,
     "name_en": "Abrau-Durso", "name_bg": "Абрау-Дюрсо", "flag": "🍾", "start_date": "2023-01-01",
     "country": "russia", "country_en": "Russia", "country_bg": "Русия"},
]
