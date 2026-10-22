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
# Later Bulgarian additions request the Open-Meteo marine cell centre directly
# (the grid is 1/12 deg, ~9 km). Several resorts snap to the same current cell
# as a neighbour, so their live readings match (archived history can still
# differ where the upstream model grid changed over time):
#   golden-sands = sveti-konstantin      burgas = pomorie = sarafovo = chernomorets
#   sunny-beach  = sveti-vlas            tyulenovo = shabla     albena = kranevo
#   irakli = byala = obzor               primorsko = dyuni = kiten
#   lozenets = tsarevo                   sinemorets = ahtopol
# Own cells: durankulak, krapets, shkorpilovtsi, ravda, silistar, rezovo.
# Ukraine (all own cells): odesa 46.458N 30.875E, chornomorsk 46.292N 30.792E,
# zatoka 46.042N 30.542E, serhiivka 45.958N 30.458E, koblevo 46.625N 31.208E.
#
# International locations (Turkey/Romania/Georgia/Russia) are nudged toward the
# open sea away from their coastlines (north for the Turkish south coast, east
# for Romania, west for Georgia, south for the NE Russian coast). Ukrainian
# locations request their own marine cell centre, like the later Bulgarian ones.

# Display order for grouping the UI by country (hub grid, dropdown, checkboxes).
COUNTRY_ORDER = ["bulgaria", "turkey", "romania", "ukraine", "georgia", "russia"]

# IANA time zone per country, so the weather page shows sunrise/sunset and
# moonrise/moonset in the location's local time.
COUNTRY_TZ = {
    "bulgaria": "Europe/Sofia",
    "turkey": "Europe/Istanbul",
    "romania": "Europe/Bucharest",
    "ukraine": "Europe/Kyiv",
    "georgia": "Asia/Tbilisi",
    "russia": "Europe/Moscow",
}

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
    {"slug": "durankulak", "csv_file": "durankulak_water_temp.csv", "lat": 43.708, "lon": 28.708,
     "name_en": "Durankulak", "name_bg": "Дуранкулак", "flag": "🦢", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "krapets", "csv_file": "krapets_water_temp.csv", "lat": 43.625, "lon": 28.708,
     "name_en": "Krapets", "name_bg": "Крапец", "flag": "🏄", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "shabla", "csv_file": "shabla_water_temp.csv", "lat": 43.541, "lon": 28.708,
     "name_en": "Shabla", "name_bg": "Шабла", "flag": "🔦", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "kranevo", "csv_file": "kranevo_water_temp.csv", "lat": 43.291, "lon": 28.208,
     "name_en": "Kranevo", "name_bg": "Кранево", "flag": "🌲", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "shkorpilovtsi", "csv_file": "shkorpilovtsi_water_temp.csv", "lat": 43.042, "lon": 27.958,
     "name_en": "Shkorpilovtsi", "name_bg": "Шкорпиловци", "flag": "🏞️", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "byala", "csv_file": "byala_water_temp.csv", "lat": 42.792, "lon": 27.958,
     "name_en": "Byala", "name_bg": "Бяла", "flag": "🍷", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "obzor", "csv_file": "obzor_water_temp.csv", "lat": 42.792, "lon": 27.958,
     "name_en": "Obzor", "name_bg": "Обзор", "flag": "🌄", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "ravda", "csv_file": "ravda_water_temp.csv", "lat": 42.625, "lon": 27.708,
     "name_en": "Ravda", "name_bg": "Равда", "flag": "🐟", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "sarafovo", "csv_file": "sarafovo_water_temp.csv", "lat": 42.542, "lon": 27.708,
     "name_en": "Sarafovo", "name_bg": "Сарафово", "flag": "✈️", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "chernomorets", "csv_file": "chernomorets_water_temp.csv", "lat": 42.542, "lon": 27.708,
     "name_en": "Chernomorets", "name_bg": "Черноморец", "flag": "🐬", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "dyuni", "csv_file": "dyuni_water_temp.csv", "lat": 42.375, "lon": 27.875,
     "name_en": "Dyuni", "name_bg": "Дюни", "flag": "🏜️", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "kiten", "csv_file": "kiten_water_temp.csv", "lat": 42.375, "lon": 27.875,
     "name_en": "Kiten", "name_bg": "Китен", "flag": "⛺", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "tsarevo", "csv_file": "tsarevo_water_temp.csv", "lat": 42.292, "lon": 27.958,
     "name_en": "Tsarevo", "name_bg": "Царево", "flag": "👑", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "ahtopol", "csv_file": "ahtopol_water_temp.csv", "lat": 42.208, "lon": 28.125,
     "name_en": "Ahtopol", "name_bg": "Ахтопол", "flag": "🌊", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "silistar", "csv_file": "silistar_water_temp.csv", "lat": 42.042, "lon": 28.208,
     "name_en": "Silistar", "name_bg": "Силистар", "flag": "🏝️", "start_date": "2023-01-01",
     "country": "bulgaria", "country_en": "Bulgaria", "country_bg": "България"},
    {"slug": "rezovo", "csv_file": "rezovo_water_temp.csv", "lat": 41.958, "lon": 28.208,
     "name_en": "Rezovo", "name_bg": "Резово", "flag": "🛂", "start_date": "2023-01-01",
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

    # --- Ukraine (Odesa coast; each requests its own marine cell centre) ---
    {"slug": "odesa", "csv_file": "odesa_water_temp.csv", "lat": 46.458, "lon": 30.875,
     "name_en": "Odesa", "name_bg": "Одеса", "flag": "🎭", "start_date": "2023-01-01",
     "country": "ukraine", "country_en": "Ukraine", "country_bg": "Украйна"},
    {"slug": "chornomorsk", "csv_file": "chornomorsk_water_temp.csv", "lat": 46.292, "lon": 30.792,
     "name_en": "Chornomorsk", "name_bg": "Чорноморск", "flag": "🏗️", "start_date": "2023-01-01",
     "country": "ukraine", "country_en": "Ukraine", "country_bg": "Украйна"},
    {"slug": "zatoka", "csv_file": "zatoka_water_temp.csv", "lat": 46.042, "lon": 30.542,
     "name_en": "Zatoka", "name_bg": "Затока", "flag": "🌉", "start_date": "2023-01-01",
     "country": "ukraine", "country_en": "Ukraine", "country_bg": "Украйна"},
    {"slug": "serhiivka", "csv_file": "serhiivka_water_temp.csv", "lat": 45.958, "lon": 30.458,
     "name_en": "Serhiivka", "name_bg": "Сергиевка", "flag": "💆", "start_date": "2023-01-01",
     "country": "ukraine", "country_en": "Ukraine", "country_bg": "Украйна"},
    {"slug": "koblevo", "csv_file": "koblevo_water_temp.csv", "lat": 46.625, "lon": 31.208,
     "name_en": "Koblevo", "name_bg": "Коблево", "flag": "🎡", "start_date": "2023-01-01",
     "country": "ukraine", "country_en": "Ukraine", "country_bg": "Украйна"},

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


# Real on-land position of each place (town centre / named beach, from
# OpenStreetMap), used wherever the location is *shown*: map pins, JSON-LD geo
# and "nearby" distances. The lat/lon above are the offshore Open-Meteo sea
# cells the data is fetched from, which can sit several km out to sea and are
# shared by neighbours, so they're unsuitable for plotting.
PLACE_COORDS = {
    "burgas":           (42.4937, 27.4721),
    "sinemorets":       (42.0611, 27.9762),
    "varna":            (43.2074, 27.9167),
    "kamen-bryag":      (43.4549, 28.5508),
    "tyulenovo":        (43.4941, 28.5793),
    "nessebar":         (42.6608, 27.7167),
    "sozopol":          (42.4182, 27.6943),
    "sunny-beach":      (42.6876, 27.7126),
    "golden-sands":     (43.2855, 28.044),
    "balchik":          (43.4049, 28.1681),
    "cape-kaliakra":    (43.3604, 28.4652),
    "albena":           (43.3678, 28.0772),
    "sveti-konstantin": (43.2297, 28.0064),
    "irakli":           (42.739, 27.8921),
    "pomorie":          (42.5684, 27.6168),
    "primorsko":        (42.2699, 27.7506),
    "lozenets":         (42.2089, 27.8068),
    "sveti-vlas":       (42.7138, 27.7588),
    "durankulak":       (43.693, 28.5267),
    "krapets":          (43.625, 28.5664),
    "shabla":           (43.5402, 28.607),
    "kranevo":          (43.344, 28.0612),
    "shkorpilovtsi":    (42.9638, 27.8771),
    "byala":            (42.8766, 27.8845),
    "obzor":            (42.8206, 27.8794),
    "ravda":            (42.6445, 27.6784),
    "sarafovo":         (42.5675, 27.4927),
    "chernomorets":     (42.4439, 27.6382),
    "dyuni":            (42.3729, 27.7094),
    "kiten":            (42.2358, 27.7742),
    "tsarevo":          (42.1703, 27.8483),
    "ahtopol":          (42.0996, 27.9434),
    "silistar":         (42.0225, 28.0096),
    "rezovo":           (41.9856, 28.0296),
    "trabzon":          (41.0055, 39.7301),
    "sinop":            (42.0266, 35.1512),
    "amasra":           (41.7489, 32.3867),
    "rize":             (41.0248, 40.5199),
    "sile":             (41.1744, 29.6125),
    "constanta":        (44.1767, 28.6508),
    "mamaia":           (44.2338, 28.6256),
    "vama-veche":       (43.7525, 28.5722),
    "olimp":            (43.8856, 28.6065),
    "vadu":             (44.4515, 28.7352),
    "odesa":            (46.4843, 30.7323),
    "chornomorsk":      (46.3013, 30.6549),
    "zatoka":           (46.064, 30.4503),
    "serhiivka":        (46.0276, 30.3727),
    "koblevo":          (46.6668, 31.204),
    "batumi":           (41.651, 41.636),
    "kvariati":         (41.5476, 41.5638),
    "shekvetili":       (41.9289, 41.7693),
    "kobuleti":         (41.8114, 41.7793),
    "green-cape":       (41.6932, 41.7058),
    "sochi":            (43.5855, 39.7231),
    "anapa":            (44.8943, 37.3169),
    "gelendzhik":       (44.5609, 38.0767),
    "novorossiysk":     (44.724, 37.7691),
    "abrau-durso":      (44.7018, 37.6019),
}

for _loc in LOCATIONS:
    _loc["place_lat"], _loc["place_lon"] = PLACE_COORDS[_loc["slug"]]
