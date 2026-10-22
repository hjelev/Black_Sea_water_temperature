# Static site generator for the Black Sea water temperature site.
#
# Reads the page templates in templates/*.html, the location list in
# locations.py and the translation dictionary in translations.json, and writes
# one SEO-distinct set of pages per location *per language* into docs/<slug>/
# (Bulgarian, the default) and docs/<lang>/<slug>/ (English, Russian, Turkish,
# Romanian), plus the generated docs/i18n.<lang>.js, docs/locations.js, the hub
# pages, the country pages (docs/<country>/), the month pages
# (docs/months/<month>/), sitemap.xml, robots.txt and 404.html.
#
# Social preview cards (docs/og/*.png) are drawn with Pillow only when missing;
# `python3 build_site.py --og` redraws them all. Without Pillow (as in CI) the
# pages just reference the cards already committed.
#
# All static text is baked into the HTML at build time (the data-i18n
# placeholders in the templates are filled per language), so search engines see
# fully translated pages. docs/i18n.<lang>.js still ships that language's
# dictionary for dynamic content rendered client-side (charts, dropdowns, map
# popups); the page's language is fixed via window.LANG injected in <head>.
#
# Each page gets its own URL, <title>, meta description, canonical link,
# hreflang alternates and JSON-LD so search engines index every town separately
# in every language. The latest reading, monthly averages, records and an FAQ
# are computed from the csv files and baked into the dashboard pages, so the
# numbers are in the HTML itself, not only in the client-side charts.
#
#   python3 build_site.py
#
# CI (update-temp.yml) runs it after every data update so the baked numbers
# stay current; run it locally too whenever templates/, locations.py,
# translations.json or the page metadata change, then commit docs/.
#
# Python 3.7+ , standard library only.
import colorsys
import datetime
import hashlib
import json
import math
import os
import re
import sys

import moon
from locations import LOCATIONS, COUNTRY_ORDER, COUNTRY_TZ

BASE_URL = "https://more.masoko.net"
ROOT_DIR = os.path.dirname(__file__)
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")

# Every site language. The default lives at the site root, the others under
# /<code>/. Emitted into docs/i18n.<lang>.js for the runtime language switcher.
LANG_INFO = [
    {"code": "bg", "flag": "🇧🇬", "label": "Български", "locale": "bg-BG", "og": "bg_BG"},
    {"code": "en", "flag": "🇬🇧", "label": "English", "locale": "en-US", "og": "en_US"},
    {"code": "ru", "flag": "🇷🇺", "label": "Русский", "locale": "ru-RU", "og": "ru_RU"},
    {"code": "tr", "flag": "🇹🇷", "label": "Türkçe", "locale": "tr-TR", "og": "tr_TR"},
    {"code": "ro", "flag": "🇷🇴", "label": "Română", "locale": "ro-RO", "og": "ro_RO"},
]
LANGS = tuple(info["code"] for info in LANG_INFO)
DEFAULT_LANG = "bg"
OG_LOCALE = {info["code"]: info["og"] for info in LANG_INFO}

CSV_BASE = ("https://raw.githubusercontent.com/hjelev/Black_Sea_water_temperature/"
            "refs/heads/main/")

# Russian needs the prepositional case after "в"/"на", which can't be derived
# from the nominative names in translations.json. Used for {loc_in} in the ru
# page metadata and {location_in} in ru strings.
RU_LOCATIVE = {
    "burgas": "в Бургасе", "sinemorets": "в Синеморце", "varna": "в Варне",
    "kamen-bryag": "в Камен-Бряге", "tyulenovo": "в Тюленово",
    "nessebar": "в Несебре", "sozopol": "в Созополе",
    "sunny-beach": "на Солнечном Берегу", "golden-sands": "на Золотых Песках",
    "balchik": "в Балчике", "cape-kaliakra": "на мысе Калиакра",
    "albena": "в Албене", "sveti-konstantin": "в Святых Константине и Елене",
    "irakli": "на пляже Иракли", "pomorie": "в Поморие",
    "primorsko": "в Приморско", "lozenets": "в Лозенце",
    "sveti-vlas": "в Святом Власе", "durankulak": "в Дуранкулаке",
    "krapets": "в Крапеце", "shabla": "в Шабле", "kranevo": "в Кранево",
    "shkorpilovtsi": "в Шкорпиловцах", "byala": "в Бяле", "obzor": "в Обзоре",
    "ravda": "в Равде", "sarafovo": "в Сарафово",
    "chernomorets": "в Черноморце", "dyuni": "в Дюнах", "kiten": "в Китене",
    "tsarevo": "в Царево", "ahtopol": "в Ахтополе", "silistar": "на Силистаре",
    "rezovo": "в Резово",
    "trabzon": "в Трабзоне", "sinop": "в Синопе", "amasra": "в Амасре",
    "rize": "в Ризе", "sile": "в Шиле", "constanta": "в Констанце",
    "mamaia": "в Мамае", "vama-veche": "в Вама-Веке", "olimp": "в Олимпе",
    "vadu": "в Ваду и Корбу", "batumi": "в Батуми", "kvariati": "в Квариати",
    "shekvetili": "в Шекветили", "kobuleti": "в Кобулети",
    "green-cape": "в Зелёном Мысе", "sochi": "в Сочи", "anapa": "в Анапе",
    "gelendzhik": "в Геленджике", "novorossiysk": "в Новороссийске",
    "abrau-durso": "в Абрау-Дюрсо",
    "odesa": "в Одессе", "chornomorsk": "в Черноморске", "zatoka": "в Затоке",
    "serhiivka": "в Сергеевке", "koblevo": "в Коблево",
}

# "in <country>" per language, for the country pages ({country_in}). Russian
# declines the name and Turkish uses a suffix; the rest prefix a preposition.
COUNTRY_IN = {
    "ru": {"bulgaria": "в Болгарии", "turkey": "в Турции", "romania": "в Румынии",
           "ukraine": "в Украине", "georgia": "в Грузии", "russia": "в России"},
    "tr": {"bulgaria": "Bulgaristan'da", "turkey": "Türkiye'de",
           "romania": "Romanya'da", "ukraine": "Ukrayna'da",
           "georgia": "Gürcistan'da", "russia": "Rusya'da"},
}
COUNTRY_IN_PREFIX = {"en": "in", "bg": "в", "ro": "în"}

# English month slugs for the /months/<month>/ pages (same in every language).
MONTH_SLUGS = ("january", "february", "march", "april", "may", "june", "july",
               "august", "september", "october", "november", "december")
# Russian months in the prepositional case ("в июне").
RU_MONTH_PREP = ("январе", "феврале", "марте", "апреле", "мае", "июне", "июле",
                 "августе", "сентябре", "октябре", "ноябре", "декабре")

# Bulgarian "в" becomes "във" before a word starting with в/ф ("във Варна").
# Applied to every baked Bulgarian page; i18n_runtime.js has the JS twin.
BG_V_RE = re.compile(r"(?<!\w)([вВ]) (?=[вВфФ])")

# Plotly partial bundle with the scatter and heatmap traces the pages use
# (~1.3 MB instead of the ~3.6 MB full build). Loaded at the end of <body>,
# right before data.js, so it doesn't block rendering the page text.
PLOTLY_TAG = '<script src="https://cdn.plot.ly/plotly-cartesian-2.27.0.min.js"></script>\n'

# Social preview cards (1200x630 PNG) generated by write_og_images().
OG_DIR = os.path.join(DOCS_DIR, "og")

with open(os.path.join(ROOT_DIR, "translations.json"), encoding="utf-8") as fh:
    TR = json.load(fh)

# EU bathing water classifications near each BG/RO town, written by
# fetch_bathing_water.py (run by hand once a year). Optional.
try:
    with open(os.path.join(ROOT_DIR, "bathing_water.json"), encoding="utf-8") as fh:
        BATHING = json.load(fh)
except (FileNotFoundError, ValueError):
    BATHING = {"year": None, "locations": {}}

# Per-page SEO metadata, per language. {loc} = town name, {loc_in} = "in
# <town>" as the language needs it (only Russian declines: "в Бургасе"),
# {country} = country name, all in the page language; {year} = first data year.
# Turkish puts the town first ("Trabzon deniz suyu sıcaklığı"), matching how
# the query is typed.
PAGES = {
    "index.html": {
        "title": {
            "en": "{loc} Sea Water Temperature — Live Black Sea Data",
            "bg": "Температура на морската вода в {loc} — Черно море на живо",
            "ru": "Температура воды {loc_in} — Черное море онлайн",
            "tr": "{loc} Deniz Suyu Sıcaklığı — Karadeniz Canlı Veri",
            "ro": "Temperatura apei mării la {loc} — Marea Neagră live",
        },
        "desc": {
            "en": ("Live and historical Black Sea water temperature at {loc}, "
                   "{country}. Daily sea surface temperature since {year}, with a "
                   "30-day trend and full history charts."),
            "bg": ("Актуална и историческа температура на морската вода в Черно "
                   "море при {loc}, {country}. Дневна температура на морската "
                   "повърхност от {year} г., с 30-дневна тенденция и графики с "
                   "пълната история."),
            "ru": ("Текущая и историческая температура воды в Черном море {loc_in} "
                   "({country}). Ежедневная температура поверхности моря с {year} г., "
                   "тренд за 30 дней и графики за всю историю."),
            "tr": ("{loc} ({country}) için güncel ve geçmiş Karadeniz deniz suyu "
                   "sıcaklığı. {year} yılından bu yana günlük deniz yüzeyi sıcaklığı, "
                   "30 günlük eğilim ve tüm geçmiş grafikleri."),
            "ro": ("Temperatura actuală și istorică a apei Mării Negre la {loc}, "
                   "{country}. Temperatura zilnică a suprafeței mării din {year}, cu "
                   "tendința pe 30 de zile și grafice cu tot istoricul."),
        },
        # With the latest reading baked in (the build runs in CI after every
        # data update); {temp} = °C, {date} = date of the reading.
        "title_live": {
            "en": "{loc} Sea Water Temperature Today: {temp}°C — Black Sea",
            "bg": "Температура на морската вода в {loc} днес: {temp}°C",
            "ru": "Температура воды {loc_in} сегодня: {temp}°C — Черное море",
            "tr": "{loc} Deniz Suyu Sıcaklığı Bugün: {temp}°C — Karadeniz",
            "ro": "Temperatura apei mării la {loc} azi: {temp}°C — Marea Neagră",
        },
        "desc_live": {
            "en": ("Sea water temperature in {loc}, {country} today: {temp}°C "
                   "({date}). Live and historical Black Sea data since {year} — "
                   "30-day trend, monthly averages and records."),
            "bg": ("Температурата на морската вода в {loc}, {country} днес е "
                   "{temp}°C ({date}). Актуални и исторически данни за Черно "
                   "море от {year} г. — 30-дневна тенденция, средни стойности по "
                   "месеци и рекорди."),
            "ru": ("Температура морской воды {loc_in} ({country}) сегодня — "
                   "{temp}°C ({date}). Текущие и исторические данные по Черному морю "
                   "с {year} г.: тренд за 30 дней, средние по месяцам и рекорды."),
            "tr": ("{loc} ({country}) deniz suyu sıcaklığı bugün {temp}°C ({date}). "
                   "{year} yılından bu yana güncel ve geçmiş Karadeniz verileri — "
                   "30 günlük eğilim, aylık ortalamalar ve rekorlar."),
            "ro": ("Temperatura apei mării la {loc}, {country} azi: {temp}°C "
                   "({date}). Date actuale și istorice pentru Marea Neagră din "
                   "{year} — tendința pe 30 de zile, medii lunare și recorduri."),
        },
    },
    "compare.html": {
        "title": {
            "en": "Compare Years — {loc} Black Sea Water Temperature",
            "bg": "Сравнение по години — температура на водата в {loc}",
            "ru": "Сравнение по годам — температура воды {loc_in}",
            "tr": "Yılları Karşılaştır — {loc} Deniz Suyu Sıcaklığı",
            "ro": "Comparație pe ani — temperatura apei la {loc}",
        },
        "desc": {
            "en": ("Compare Black Sea water temperature at {loc}, {country} across "
                   "years on a Jan–Dec axis to spot seasonal patterns and warming "
                   "trends."),
            "bg": ("Сравнете температурата на морската вода в Черно море при "
                   "{loc}, {country} по години върху ос януари–декември, за да "
                   "откриете сезонни модели и тенденции на затопляне."),
            "ru": ("Сравните температуру воды в Черном море {loc_in} ({country}) по "
                   "годам на оси январь–декабрь, чтобы увидеть сезонные закономерности "
                   "и тенденции потепления."),
            "tr": ("{loc} ({country}) Karadeniz su sıcaklığını yıllar arasında "
                   "Ocak–Aralık ekseninde karşılaştırın; mevsimsel örüntüleri ve "
                   "ısınma eğilimlerini görün."),
            "ro": ("Comparați temperatura apei Mării Negre la {loc}, {country} de la "
                   "an la an, pe o axă ianuarie–decembrie, pentru a observa tiparele "
                   "sezoniere și tendințele de încălzire."),
        },
    },
    "heatmap.html": {
        "title": {
            "en": "Monthly Heatmap — {loc} Black Sea Water Temperature",
            "bg": "Месечна топлинна карта — температура на водата в {loc}",
            "ru": "Тепловая карта по месяцам — температура воды {loc_in}",
            "tr": "Aylık Isı Haritası — {loc} Deniz Suyu Sıcaklığı",
            "ro": "Hartă termică lunară — temperatura apei la {loc}",
        },
        "desc": {
            "en": ("Monthly Black Sea water temperature heatmap for {loc}, "
                   "{country} — average sea surface temperature per month across "
                   "every recorded year."),
            "bg": ("Месечна топлинна карта на температурата на морската вода при "
                   "{loc}, {country} — средна температура на морската повърхност "
                   "по месеци за всяка записана година."),
            "ru": ("Тепловая карта температуры воды в Черном море {loc_in} "
                   "({country}) — средняя температура поверхности моря по месяцам за "
                   "каждый год наблюдений."),
            "tr": ("{loc} ({country}) için aylık Karadeniz su sıcaklığı ısı haritası — "
                   "kayıtlı her yıl için aylık ortalama deniz yüzeyi sıcaklığı."),
            "ro": ("Hartă termică lunară a temperaturii apei Mării Negre la {loc}, "
                   "{country} — temperatura medie a suprafeței mării pe luni, pentru "
                   "fiecare an înregistrat."),
        },
    },
    "stats.html": {
        "title": {
            "en": "Statistics & Records — {loc} Black Sea Water Temperature",
            "bg": "Статистика и рекорди — температура на водата в {loc}",
            "ru": "Статистика и рекорды — температура воды {loc_in}",
            "tr": "İstatistikler ve Rekorlar — {loc} Deniz Suyu Sıcaklığı",
            "ro": "Statistici și recorduri — temperatura apei la {loc}",
        },
        "desc": {
            "en": ("All-time records and annual statistics for Black Sea water "
                   "temperature at {loc}, {country} — hottest and coldest readings, "
                   "yearly min/avg/max and the long-term trend."),
            "bg": ("Рекорди и годишна статистика за температурата на морската "
                   "вода в Черно море при {loc}, {country} — най-високи и "
                   "най-ниски стойности, годишни мин/ср/макс и дългосрочната "
                   "тенденция."),
            "ru": ("Рекорды и годовая статистика температуры воды в Черном море "
                   "{loc_in} ({country}) — самые высокие и низкие значения, годовые "
                   "мин./сред./макс. и долгосрочный тренд."),
            "tr": ("{loc} ({country}) Karadeniz su sıcaklığı için tüm zamanların "
                   "rekorları ve yıllık istatistikler — en sıcak ve en soğuk ölçümler, "
                   "yıllık min./ort./maks. ve uzun vadeli eğilim."),
            "ro": ("Recorduri absolute și statistici anuale pentru temperatura apei "
                   "Mării Negre la {loc}, {country} — cele mai mari și mai mici "
                   "valori, min./medie/max. anuale și tendința pe termen lung."),
        },
    },
    "gallery.html": {
        "title": {
            "en": "Photos — {loc} Black Sea Coast",
            "bg": "Снимки — {loc} на Черноморието",
            "ru": "Фото — {loc}, побережье Черного моря",
            "tr": "Fotoğraflar — {loc} Karadeniz Kıyısı",
            "ro": "Fotografii — {loc}, litoralul Mării Negre",
        },
        "desc": {
            "en": ("Photos of {loc}, {country} on the Black Sea coast, sourced from "
                   "Wikimedia Commons — beaches, harbour and seaside views."),
            "bg": ("Снимки на {loc}, {country} по Черноморското крайбрежие от "
                   "Wikimedia Commons — плажове, пристанище и морски гледки."),
            "ru": ("Фотографии: {loc} ({country}) на побережье Черного моря, с "
                   "Wikimedia Commons — пляжи, гавань и морские виды."),
            "tr": ("Karadeniz kıyısındaki {loc} ({country}) fotoğrafları, Wikimedia "
                   "Commons'tan — plajlar, liman ve deniz manzaraları."),
            "ro": ("Fotografii din {loc}, {country}, pe litoralul Mării Negre, de pe "
                   "Wikimedia Commons — plaje, port și priveliști la mare."),
        },
        "plotly": False,  # photo page has no charts; skip the ~1 MB Plotly bundle
        # Hotlinked Commons thumbnails repeated in 5 languages: thin for search,
        # so kept out of the index (links still followed) and the sitemap.
        "noindex": True,
    },
    "weather.html": {
        "title": {
            "en": "Weather Forecast — {loc} Black Sea Coast",
            "bg": "Прогноза за времето — {loc}",
            "ru": "Прогноза погоды — {loc}",
            "tr": "{loc} Hava Durumu Tahmini",
            "ro": "Prognoza meteo — {loc}",
        },
        "desc": {
            "en": ("Air temperature, UV index and wind speed for {loc}, {country} — "
                   "last 5 days and a 5-day forecast, updated hourly."),
            "bg": ("Температура на въздуха, UV индекс и скорост на вятъра за {loc}, "
                   "{country} — последните 5 дни и прогноза за 5 дни, обновявани "
                   "всеки час."),
            "ru": ("Температура воздуха, УФ-индекс и скорость ветра {loc_in} "
                   "({country}) — последние 5 дней и прогноз на 5 дней, обновляется "
                   "каждый час."),
            "tr": ("{loc} ({country}) için hava sıcaklığı, UV indeksi ve rüzgâr hızı — "
                   "son 5 gün ve 5 günlük tahmin, saatlik güncellenir."),
            "ro": ("Temperatura aerului, indicele UV și viteza vântului la {loc}, "
                   "{country} — ultimele 5 zile și prognoza pe 5 zile, actualizate "
                   "din oră în oră."),
        },
        "plotly": True,   # air-vs-sea + hourly charts
    },
}

HUB_META = {
    "title": {
        "en": "Black Sea Water Temperature — Bulgaria, Turkey, Romania, Ukraine, Georgia, Russia",
        "bg": "Температура на водата в Черно море — България, Турция, Румъния, Украйна, Грузия, Русия",
        "ru": "Температура воды в Черном море — Болгария, Турция, Румыния, Украина, Грузия, Россия",
        "tr": "Karadeniz Deniz Suyu Sıcaklığı — Bulgaristan, Türkiye, Romanya, Ukrayna, Gürcistan, Rusya",
        "ro": "Temperatura apei Mării Negre — Bulgaria, Turcia, România, Ucraina, Georgia, Rusia",
    },
    "desc": {
        "en": ("Live and historical Black Sea water temperature for coastal towns across "
               "Bulgaria, Turkey, Romania, Ukraine, Georgia and Russia. Daily sea surface "
               "temperature, yearly comparisons, heatmaps and records."),
        "bg": ("Актуална и историческа температура на морската вода в Черно море за "
               "крайбрежни градове в България, Турция, Румъния, Украйна, Грузия и Русия. Дневна "
               "температура, годишни сравнения, топлинни карти и рекорди."),
        "ru": ("Текущая и историческая температура воды в Черном море для прибрежных "
               "городов Болгарии, Турции, Румынии, Украины, Грузии и России. Ежедневная "
               "температура моря, сравнение по годам, тепловые карты и рекорды."),
        "tr": ("Bulgaristan, Türkiye, Romanya, Ukrayna, Gürcistan ve Rusya'daki kıyı kasabaları "
               "için güncel ve geçmiş Karadeniz deniz suyu sıcaklığı. Günlük deniz "
               "sıcaklığı, yıllık karşılaştırmalar, ısı haritaları ve rekorlar."),
        "ro": ("Temperatura actuală și istorică a apei Mării Negre pentru localitățile "
               "de pe coastă din Bulgaria, Turcia, România, Ucraina, Georgia și Rusia. "
               "Temperatura zilnică, comparații anuale, hărți termice și recorduri."),
    },
}

COMPARE_LOCATIONS_META = {
    "title": {
        "en": "Compare Locations — Black Sea Water Temperature",
        "bg": "Сравнение на локации — температура на водата в Черно море",
        "ru": "Сравнение мест — температура воды в Черном море",
        "tr": "Konumları Karşılaştır — Karadeniz Deniz Suyu Sıcaklığı",
        "ro": "Comparație între localități — temperatura apei Mării Negre",
    },
    "desc": {
        "en": ("Compare Black Sea water temperature across coastal towns in Bulgaria, "
               "Turkey, Romania, Ukraine, Georgia and Russia on a single chart — overlay any "
               "locations across the years and on a Jan–Dec seasonal axis."),
        "bg": ("Сравнете температурата на морската вода в Черно море между крайбрежни "
               "градове в България, Турция, Румъния, Украйна, Грузия и Русия на една графика — "
               "наложете локации през годините и на сезонна ос януари–декември."),
        "ru": ("Сравните температуру воды в Черном море в прибрежных городах Болгарии, "
               "Турции, Румынии, Украины, Грузии и России на одном графике — за все годы и на "
               "сезонной оси январь–декабрь."),
        "tr": ("Bulgaristan, Türkiye, Romanya, Ukrayna, Gürcistan ve Rusya'daki kıyı "
               "kasabalarının Karadeniz su sıcaklığını tek grafikte karşılaştırın — "
               "yıllar boyunca ve Ocak–Aralık mevsim ekseninde."),
        "ro": ("Comparați temperatura apei Mării Negre în localitățile de pe coastă din "
               "Bulgaria, Turcia, România, Ucraina, Georgia și Rusia pe un singur grafic — de-a "
               "lungul anilor și pe o axă sezonieră ianuarie–decembrie."),
    },
}

# Country pages (/<country>/): every location of one country in a table.
# {country} = name, {country_in} = "in <country>" (COUNTRY_IN), {min}/{max} =
# today's range across its locations, {warm}/{warm_t} = the warmest one.
COUNTRY_META = {
    "title": {
        "en": "{country} Sea Water Temperature Today: {min}–{max}°C — Black Sea",
        "bg": "Температура на морската вода {country_in} днес: {min}–{max}°C",
        "ru": "Температура воды в Черном море {country_in} сегодня: {min}–{max}°C",
        "tr": "{country} Deniz Suyu Sıcaklığı Bugün: {min}–{max}°C — Karadeniz",
        "ro": "Temperatura apei mării {country_in} azi: {min}–{max}°C — Marea Neagră",
    },
    "desc": {
        "en": ("Black Sea water temperature today at every beach and resort "
               "{country_in}: {min}–{max}°C ({date}). Warmest: {warm} {warm_t}°C. "
               "Monthly averages and swimming season for each location."),
        "bg": ("Температура на морската вода днес на всеки плаж и курорт "
               "{country_in}: {min}–{max}°C ({date}). Най-топло: {warm} {warm_t}°C. "
               "Средни стойности по месеци и сезон за къпане за всяка локация."),
        "ru": ("Температура воды в Черном море сегодня на всех пляжах и курортах "
               "{country_in}: {min}–{max}°C ({date}). Теплее всего: {warm} "
               "{warm_t}°C. Средние по месяцам и купальный сезон для каждого места."),
        "tr": ("{country} Karadeniz kıyısındaki tüm plaj ve tatil yerlerinde bugünkü "
               "deniz suyu sıcaklığı: {min}–{max}°C ({date}). En sıcak: {warm} "
               "{warm_t}°C. Her konum için aylık ortalamalar ve yüzme sezonu."),
        "ro": ("Temperatura apei Mării Negre azi la toate plajele și stațiunile "
               "{country_in}: {min}–{max}°C ({date}). Cea mai caldă: {warm} "
               "{warm_t}°C. Medii lunare și sezonul de baie pentru fiecare localitate."),
    },
    "h1": {
        "en": "Sea Water Temperature {country_in} Today",
        "bg": "Температура на морската вода {country_in} днес",
        "ru": "Температура воды в Черном море {country_in} сегодня",
        "tr": "{country} Deniz Suyu Sıcaklığı Bugün",
        "ro": "Temperatura apei mării {country_in} azi",
    },
}

# Month pages (/months/<month>/): every location's average for one month.
# {month} = month name, {month_in} = "in <month>" (month_in()), {n} = number
# of locations, {warm}/{warm_t} = the warmest one.
MONTH_META = {
    "title": {
        "en": "Black Sea Water Temperature {month_in} — Average by Resort",
        "bg": "Температура на морската вода {month_in} — Черно море по курорти",
        "ru": "Температура воды в Черном море {month_in} — по курортам",
        "tr": "{month} Ayında Karadeniz Deniz Suyu Sıcaklığı — Tatil Yerlerine Göre",
        "ro": "Temperatura apei Mării Negre {month_in} — pe stațiuni",
    },
    "desc": {
        "en": ("How warm is the Black Sea {month_in}? Average sea water temperature "
               "for {n} beaches and resorts in Bulgaria, Romania, Turkey, Georgia, "
               "Ukraine and Russia — warmest: {warm} ({warm_t}°C)."),
        "bg": ("Колко топло е Черно море {month_in}? Средна температура на морската "
               "вода за {n} плажа и курорта в България, Румъния, Турция, Грузия, "
               "Украйна и Русия — най-топло: {warm} ({warm_t}°C)."),
        "ru": ("Насколько теплое Черное море {month_in}? Средняя температура воды на "
               "{n} пляжах и курортах Болгарии, Румынии, Турции, Грузии, Украины и "
               "России — теплее всего: {warm} ({warm_t}°C)."),
        "tr": ("Karadeniz {month_in} ne kadar sıcak? Bulgaristan, Romanya, Türkiye, "
               "Gürcistan, Ukrayna ve Rusya'daki {n} plaj ve tatil yeri için ortalama "
               "deniz suyu sıcaklığı — en sıcak: {warm} ({warm_t}°C)."),
        "ro": ("Cât de caldă este Marea Neagră {month_in}? Temperatura medie a apei la "
               "{n} plaje și stațiuni din Bulgaria, România, Turcia, Georgia, Ucraina "
               "și Rusia — cea mai caldă: {warm} ({warm_t}°C)."),
    },
    "h1": {
        "en": "Black Sea Water Temperature {month_in}",
        "bg": "Температура на морската вода в Черно море {month_in}",
        "ru": "Температура воды в Черном море {month_in}",
        "tr": "{month} Ayında Karadeniz Deniz Suyu Sıcaklığı",
        "ro": "Temperatura apei Mării Negre {month_in}",
    },
}


# Moon phase pages: /moon-phases/ for the current year, /moon-phases/<year>/
# for the others. {year} = the page's year.
MOON_META = {
    "title": {
        "en": "Moon Phase Today & Lunar Calendar {year} — Full Moon, New Moon Dates",
        "bg": "Фаза на луната днес и лунен календар {year} — пълнолуние, новолуние",
        "ru": "Фаза Луны сегодня и лунный календарь {year} — полнолуние, новолуние",
        "tr": "Bugün Ay Evresi ve {year} Ay Takvimi — Dolunay, Yeni Ay Tarihleri",
        "ro": "Faza Lunii azi și calendarul lunar {year} — lună plină, lună nouă",
    },
    "title_year": {
        "en": "Lunar Calendar {year} — Moon Phases, Full Moon and New Moon Dates",
        "bg": "Лунен календар {year} — фази на луната, пълнолуние и новолуние",
        "ru": "Лунный календарь {year} — фазы Луны, даты полнолуний и новолуний",
        "tr": "{year} Ay Takvimi — Ay Evreleri, Dolunay ve Yeni Ay Tarihleri",
        "ro": "Calendarul lunar {year} — fazele Lunii, date de lună plină și lună nouă",
    },
    "desc": {
        "en": ("Moon phases in {year}: today's phase, illumination and zodiac sign, a "
               "day-by-day moon calendar and the exact date and time of every new moon, "
               "first quarter, full moon and last quarter."),
        "bg": ("Фазите на луната през {year} г.: фазата днес, осветеност и зодиакален "
               "знак, лунен календар по дни и точната дата и час на всяко новолуние, "
               "първа четвърт, пълнолуние и последна четвърт."),
        "ru": ("Фазы Луны в {year} году: фаза сегодня, освещённость и знак зодиака, "
               "лунный календарь по дням и точные дата и время каждого новолуния, первой "
               "четверти, полнолуния и последней четверти."),
        "tr": ("{year} yılında Ay evreleri: bugünkü evre, aydınlanma ve burç, günlük Ay "
               "takvimi ve her yeni ay, ilk dördün, dolunay ve son dördünün kesin tarih "
               "ve saati."),
        "ro": ("Fazele Lunii în {year}: faza de azi, iluminarea și zodia, calendarul "
               "lunar pe zile și data și ora exactă a fiecărei luni noi, primului pătrar, "
               "lunii pline și ultimului pătrar."),
    },
    "h1": {
        "en": "Moon Phases {year}",
        "bg": "Фази на луната {year}",
        "ru": "Фазы Луны {year}",
        "tr": "{year} Ay Evreleri",
        "ro": "Fazele Lunii {year}",
    },
}


def i18n_key(slug):
    return "loc_" + slug.replace("-", "")


def loc_full(loc, lang):
    """'Burgas, Bulgaria' in the given language."""
    return TR[lang][i18n_key(loc["slug"])]


def loc_name(loc, lang):
    """Short town name ('Burgas'), taken from the translated 'Town, Country'."""
    return loc_full(loc, lang).rsplit(", ", 1)[0]


def country_name(loc, lang):
    return TR[lang]["country_" + loc["country"]]


def loc_in(loc, lang):
    """'in <town>' phrase for metadata; only Russian declines the name."""
    return RU_LOCATIVE[loc["slug"]] if lang == "ru" else loc_name(loc, lang)


def loc_in_full(loc, lang):
    """{location_in} in strings: the declined town plus the country (ru)."""
    if lang != "ru":
        return loc_full(loc, lang)
    return "{}, {}".format(RU_LOCATIVE[loc["slug"]], country_name(loc, lang))


def country_in(country, lang):
    """'in Bulgaria' as the language needs it, for the country pages."""
    if lang in COUNTRY_IN:
        return COUNTRY_IN[lang][country]
    return "{} {}".format(COUNTRY_IN_PREFIX[lang], TR[lang]["country_" + country])


def month_in(index, lang):
    """'in June' / 'през юни' / 'в июне' / 'Haziran ayında' / 'în iunie'."""
    name = TR[lang]["months_full"][index]
    if lang == "ru":
        return "в " + RU_MONTH_PREP[index]
    if lang == "tr":
        return name + " ayında"
    return {"en": "in", "bg": "през", "ro": "în"}[lang] + " " + name


def capitalize(text):
    return text[:1].upper() + text[1:]


def month_path(index):
    return "months/{}/".format(MONTH_SLUGS[index])


def locations_by_country():
    """Yield (country_slug, [locations]) in COUNTRY_ORDER, skipping empty groups."""
    for country in COUNTRY_ORDER:
        group = [loc for loc in LOCATIONS if loc["country"] == country]
        if group:
            yield country, group


def escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def lang_prefix(lang):
    """URL prefix of a language: '' for the default (site root), else '/<code>'."""
    return "" if lang == DEFAULT_LANG else "/" + lang


def url_for(path, lang):
    """Absolute URL for a site path ('', 'burgas/', 'burgas/compare.html', ...)."""
    return "{}{}/{}".format(BASE_URL, lang_prefix(lang), path)


def hreflang_links(path):
    """hreflang alternates for one page: every language + x-default (bg)."""
    lines = ['    <link rel="alternate" hreflang="{}" href="{}">\n'.format(
        lang, escape(url_for(path, lang))) for lang in LANGS]
    lines.append('    <link rel="alternate" hreflang="x-default" href="{}">\n'.format(
        escape(url_for(path, DEFAULT_LANG))))
    return "".join(lines)


def tr_fmt(lang, key, **fields):
    """Translated string with {name} placeholders filled (text, not escaped)."""
    val = TR[lang][key]
    for name, value in fields.items():
        val = val.replace("{" + name + "}", str(value))
    return val


def json_ld(obj):
    """One <script type="application/ld+json"> line for the <head>."""
    data = json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
    return '    <script type="application/ld+json">{}</script>\n'.format(
        data.replace("</", "<\\/"))


def og_image_url(name):
    """Absolute URL of docs/og/<name>.png, or None if it hasn't been generated
    (write_og_images() needs Pillow, which CI doesn't install)."""
    if os.path.isfile(os.path.join(OG_DIR, name + ".png")):
        return "{}/og/{}.png".format(BASE_URL, name)
    return None


def build_head(title, description, path, lang, structured=(), noindex=False,
               robots=None, image=None):
    """Generated <head> shared by every page; the SEO fields and language vary.

    path is the language-neutral site path ('' for the hub, 'burgas/', ...);
    structured is a list of JSON-LD objects; noindex=True (the 404 page) drops
    canonical/hreflang/og tags, while robots adds a robots meta to an otherwise
    normal page; image is the absolute og:image URL (1200x630) or None.
    Plotly is not loaded here: with_plotly() adds it at the end of <body>."""
    t = escape(title)
    d = escape(description)
    canonical = escape(url_for(path, lang))
    if noindex:
        seo = '    <meta name="robots" content="noindex">\n'
    else:
        if image:
            card = ('    <meta property="og:image" content="{img}">\n'
                    '    <meta property="og:image:width" content="1200">\n'
                    '    <meta property="og:image:height" content="630">\n'
                    '    <meta name="twitter:card" content="summary_large_image">\n'
                    .format(img=escape(image)))
        else:
            card = '    <meta name="twitter:card" content="summary">\n'
        seo = ('{robots}'
               '    <link rel="canonical" href="{canonical}">\n'
               '{alternates}'
               '    <meta property="og:type" content="website">\n'
               '    <meta property="og:site_name" content="{site}">\n'
               '    <meta property="og:title" content="{title}">\n'
               '    <meta property="og:description" content="{desc}">\n'
               '    <meta property="og:url" content="{canonical}">\n'
               '    <meta property="og:locale" content="{og_locale}">\n'
               '{og_alternates}'
               '{card}'
               '{ld}').format(
                   robots=('    <meta name="robots" content="{}">\n'.format(robots)
                           if robots else ""),
                   canonical=canonical, alternates=hreflang_links(path),
                   site=escape(TR[lang]["hub_h1"]),
                   title=t, desc=d, og_locale=OG_LOCALE[lang],
                   og_alternates="".join(
                       '    <meta property="og:locale:alternate" content="{}">\n'
                       .format(OG_LOCALE[other]) for other in LANGS if other != lang),
                   card=card,
                   ld="".join(json_ld(obj) for obj in structured))
    return """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">
{seo}    <link rel="icon" href="/favicon.svg">
    <link rel="stylesheet" href="/style.css">
    <script src="/i18n.{lang}.js"></script>
    <script src="/locations.js"></script>
    <script>window.LOCATION_ID = '{slug}'; window.LANG = '{lang}'; window.LANG_PREFIX = '{prefix}';</script>
    <script defer src="https://m.masoko.net/core-util" data-website-id="a6c69550-2eed-4ba4-8568-57dc4c66e466"></script>
</head>
""".format(lang=lang, title=t, desc=d, seo=seo, slug="{slug}",
           prefix=lang_prefix(lang))


def with_plotly(body):
    """Load Plotly right before data.js at the end of <body>: the page scripts
    that draw the charts run after it, and the text above renders first."""
    return body.replace('<script src="/data.js"></script>',
                        PLOTLY_TAG + '<script src="/data.js"></script>', 1)


# Matches a leaf element carrying data-i18n="key" or data-i18n-html="key".
# Every translatable element in the templates holds plain text only (no child
# tags), so [^<]* is safe for the current content.
TRANSLATABLE_RE = re.compile(
    r'(<(\w+)[^>]*\bdata-i18n(-html)?="([^"]+)"[^>]*>)([^<]*)(</\2>)')


def bake(html, lang, loc=None):
    """Fill every data-i18n placeholder with the translated text for lang.

    {location}, {location_in} and {year} (first data year) are filled for
    per-location pages. The data-i18n attributes are kept in the output as provenance; the runtime
    no longer translates static text. Elements flagged data-i18n-loc get the
    ' for <Town, Country>' suffix appended (translated), mirroring the old
    client-side locSuffix()."""
    tr = TR[lang]

    def repl(m):
        open_tag, _tag, is_html, key, _old, close_tag = m.groups()
        val = tr.get(key, TR["en"].get(key, key))
        if not is_html:
            val = escape(val)
        if loc is not None:
            val = (val.replace("{location_in}", escape(loc_in_full(loc, lang)))
                      .replace("{location}", escape(loc_full(loc, lang)))
                      .replace("{year}", loc["start_date"][:4]))
        if "data-i18n-loc" in open_tag and loc is not None:
            val += escape(" {} {}".format(tr["loc_connector"],
                                          tr[i18n_key(loc["slug"])]))
        return open_tag + val + close_tag

    html = TRANSLATABLE_RE.sub(repl, html)
    if lang == "bg":
        html = BG_V_RE.sub(r"\1ъв ", html)
    return html


def prefix_links(body, lang):
    """Rewrite root-absolute page links for a non-default language (/x → /ru/x).

    Applied to page bodies only: relative links (./, compare.html, ...) already
    stay inside /<lang>/<slug>/, script/css assets use src= or absolute URLs,
    and the <head> is built with the right URLs directly."""
    if lang == DEFAULT_LANG:
        return body
    return body.replace('href="/', 'href="{}/'.format(lang_prefix(lang)))


def template_body(page_file):
    """Return everything after </head> from a template, with asset paths fixed."""
    with open(os.path.join(TEMPLATES_DIR, page_file), encoding="utf-8") as fh:
        html = fh.read()
    body = html[html.index("</head>") + len("</head>"):]
    # data.js lives at the site root, not in the per-location folder.
    body = body.replace('src="data.js"', 'src="/data.js"')
    return body


# Root-level local assets (/data.js, /style.css, ...) referenced from pages.
ASSET_RE = re.compile(r'((?:src|href)="/)([\w.-]+\.(?:js|css))"')


def version_assets(html):
    """Append ?v=<content hash> to root-level js/css references.

    The assets are served with a multi-hour max-age while pages expire after
    minutes, so without this a browser can pair a fresh page with a stale
    data.js and crash on helpers it doesn't have yet. Run after
    write_i18n_js()/write_locations_js() so their hashes are current."""
    def repl(m):
        path = os.path.join(DOCS_DIR, m.group(2))
        if not os.path.isfile(path):
            return m.group(0)
        with open(path, "rb") as fh:
            digest = hashlib.sha1(fh.read()).hexdigest()[:8]
        return '{}{}?v={}"'.format(m.group(1), m.group(2), digest)

    return ASSET_RE.sub(repl, html)


def load_galleries():
    """Per-location Commons photos cached by fetch_galleries.py. Optional: if the
    file is missing the gallery pages just render an empty-state message."""
    path = os.path.join(DOCS_DIR, "galleries.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError):
        return {}


def photo_alt(title, town):
    """Readable alt text from a Commons file title: 'File:Burgas_beach.jpg' →
    'Burgas beach — Burgas, Bulgaria'."""
    text = re.sub(r"^File:", "", title)
    text = re.sub(r"\.(jpe?g|png|gif|tiff?|webp)$", "", text, flags=re.I)
    text = re.sub(r"[_\s]+", " ", text).strip()
    return "{} — {}".format(text, town) if text else town


def gallery_markup(images, town):
    """Build the static grid of thumbnails + attribution for one location."""
    if not images:
        return ('<p class="gallery-empty" data-i18n="gal_none">'
                'No photos found for this location yet.</p>')
    items = []
    for im in images:
        artist = escape(im.get("artist") or "Wikimedia Commons")
        license_name = escape(im.get("license") or "")
        license_url = escape(im.get("licenseUrl") or im.get("page") or "")
        thumb = escape(im["thumb"])
        full = escape(im.get("full") or im["thumb"])
        page = escape(im.get("page") or "")
        title = escape(photo_alt(im.get("title") or "", town))
        w, h = im.get("w"), im.get("h")
        dims = ' width="{}" height="{}"'.format(w, h) if w and h else ""
        # Commons serves fixed thumbnail widths; offer the 960px one to
        # high-density screens (originals are >= 1000px, see fetch_galleries).
        hires = re.sub(r"/\d+px-", "/960px-", im["thumb"], count=1)
        srcset = (' srcset="{} 1x, {} 2x"'.format(thumb, escape(hires))
                  if hires != im["thumb"] else "")
        lic = ('<a href="{url}" target="_blank" rel="noopener nofollow">{name}</a>'
               .format(url=license_url, name=license_name)) if license_name else ""
        items.append(
            '<figure class="gallery-item">'
            '<a class="gallery-link" href="{full}" data-full="{full}" '
            'data-page="{page}" data-artist="{artist}">'
            '<img src="{thumb}"{srcset} alt="{title}" loading="lazy"{dims}></a>'
            '<figcaption class="gallery-caption">© {artist}{sep}{lic}</figcaption>'
            '</figure>'.format(
                full=full, page=page, artist=artist, thumb=thumb, srcset=srcset,
                title=title, dims=dims, sep=" · " if lic else "", lic=lic))
    return "\n".join(items)


# --- Data baked into the pages ---------------------------------------------

def load_readings(loc):
    """[(datetime 'YYYY-MM-DD HH:MM:SS', temp)] from the location's csv."""
    rows = []
    with open(os.path.join(ROOT_DIR, loc["csv_file"]), encoding="utf-8") as fh:
        next(fh, None)  # header
        for line in fh:
            date, _, temp = line.strip().partition(",")
            try:
                rows.append((date, float(temp)))
            except ValueError:
                continue
    return rows


# Daily-mean water temperature that opens the swimming season, and the
# "properly warm" threshold behind the month table's share-of-days column.
SWIM_TEMP = 20
WARM_TEMP = 22


def swim_seasons(daily):
    """[{year, first, last, days, complete}] per year, newest first: the first
    and last day with a daily mean >= SWIM_TEMP and how many such days there
    were. A year is complete when its data spans May to mid-October, so a
    partial first year or the season still under way don't skew the typical
    dates."""
    years = {}
    for date in sorted(daily):
        y = years.setdefault(date[:4], {"year": date[:4], "first": None, "last": None,
                                        "days": 0, "start": date, "end": date})
        y["end"] = date
        if daily[date] >= SWIM_TEMP:
            y["first"] = y["first"] or date
            y["last"] = date
            y["days"] += 1
    seasons = []
    for y in sorted(years.values(), key=lambda y: y["year"], reverse=True):
        y["complete"] = y["start"][5:] <= "05-01" and y["end"][5:] >= "10-15"
        del y["start"], y["end"]
        seasons.append(y)
    return seasons


def typical_season(seasons):
    """Median first day, last day and length over the complete seasons, as
    ('MM-DD', 'MM-DD', days, n_years), or None if the water never got there."""
    done = [s for s in seasons if s["complete"] and s["first"]]
    if not done:
        return None

    def median(values):
        values = sorted(values)
        return values[len(values) // 2]

    def day_of_year(date):
        return datetime.date(2001, int(date[5:7]), int(date[8:10])).timetuple().tm_yday

    def from_day_of_year(n):
        return (datetime.date(2001, 1, 1) + datetime.timedelta(n - 1)).strftime("%m-%d")

    return (from_day_of_year(median(day_of_year(s["first"]) for s in done)),
            from_day_of_year(median(day_of_year(s["last"]) for s in done)),
            median(s["days"] for s in done), len(done))


def location_stats(loc):
    """Latest reading, anomaly vs previous years and per-month climatology.

    Monthly averages use daily means (some years have one reading a day,
    others two); records and monthly extremes use the raw readings. Returns
    None when the csv has no data."""
    rows = load_readings(loc)
    if not rows:
        return None
    last_dt, last_temp = rows[-1]
    daily = {}
    for dt, temp in rows:
        daily.setdefault(dt[:10], []).append(temp)
    daily = {d: sum(v) / len(v) for d, v in daily.items()}

    # Same calendar day in earlier years, exactly as dayAverages() in data.js
    # computes it for the hero card: raw readings, years = all earlier years.
    last_year, md = last_dt[:4], last_dt[5:10]
    prior_years = {dt[:4] for dt, _ in rows if dt[:4] < last_year}
    prior = [t for dt, t in rows if dt[5:10] == md and dt[:4] < last_year]
    norm = (sum(prior) / len(prior)
            if prior and len(prior_years) >= 2 else None)

    months = []
    for m in range(1, 13):
        key = "{:02d}".format(m)
        means = [v for d, v in daily.items() if d[5:7] == key]
        raw = [(t, dt) for dt, t in rows if dt[5:7] == key]
        if not means:
            months.append(None)
            continue
        months.append({"avg": sum(means) / len(means),
                       "min": min(raw), "max": max(raw),
                       "warm_share": sum(v >= WARM_TEMP for v in means) / len(means)})
    return {
        "temp": last_temp, "date": last_dt,
        "first": rows[0][0], "norm": norm, "norm_years": len(prior_years),
        "months": months, "rows": rows, "daily": daily,
        "seasons": swim_seasons(daily),
        "max": max((t, dt) for dt, t in rows),
        "min": min((t, dt) for dt, t in rows),
    }


def load_all_stats():
    return {loc["slug"]: location_stats(loc) for loc in LOCATIONS}


def fmt_temp(value):
    return "{:.1f}".format(value + 0.0).replace("-0.0", "0.0")


def fmt_date(dt, lang):
    """'2026-10-20 06:00:00' → 'Oct 20, 2026' (en) / '20.10.2026' (others)."""
    y, m, d = int(dt[:4]), int(dt[5:7]), int(dt[8:10])
    if lang == "en":
        return "{} {}, {}".format(TR["en"]["months"][m - 1], d, y)
    return "{:02d}.{:02d}.{}".format(d, m, y)


def month_name(lang, index):
    return TR[lang]["months_full"][index]


def day_month(md, lang):
    """'06-12' → 'June 12' / '12 юни' / '12 июня' ..."""
    return tr_fmt(lang, "seo_day_month", day=int(md[3:5]),
                  month=TR[lang]["seo_months_gen"][int(md[:2]) - 1])


def bathing_sites(loc):
    return BATHING["locations"].get(loc["slug"], [])


def bathing_summary(loc, lang):
    """('Excellent', 5, 7): the most common latest class and its count among
    the town's EU bathing sites, or None outside the EU."""
    sites = [s for s in bathing_sites(loc) if s["status"] != "none"]
    if not sites:
        return None
    order = ("excellent", "good", "sufficient", "poor")
    top = max(order, key=lambda k: (sum(s["status"] == k for s in sites), -order.index(k)))
    return (TR[lang]["seo_bw_" + top], sum(s["status"] == top for s in sites), len(sites))


def today_sentences(loc, lang, st):
    """Plain-text 'water is X°C today' summary (+ anomaly), shared by the
    static hero fallback and the FAQ answer."""
    text = tr_fmt(lang, "today_summary", location=loc_full(loc, lang),
                  location_in=loc_in_full(loc, lang), temp=fmt_temp(st["temp"]),
                  date=fmt_date(st["date"], lang))
    if st["norm"] is not None:
        diff = round(st["temp"] - st["norm"], 1)
        key = ("anomaly_above" if diff > 0 else
               "anomaly_below" if diff < 0 else "anomaly_same")
        text += " " + tr_fmt(lang, key, n=fmt_temp(abs(diff)),
                             years=st["norm_years"], avg=fmt_temp(st["norm"]))
    return text


def today_html(loc, lang, st):
    """Static content of #water-hero: renderWaterHero() replaces it on load,
    but crawlers and no-JS visitors get the reading as text."""
    if not st:
        return ""
    return '<p class="water-hero-static">{}</p>'.format(
        escape(today_sentences(loc, lang, st)))


def faq_items(loc, lang, st):
    """[(question, answer)] computed from the data; shown on the dashboard and
    mirrored in its FAQPage JSON-LD."""
    if not st:
        return []
    names = dict(location=loc_full(loc, lang), location_in=loc_in_full(loc, lang))
    months = [(i, m) for i, m in enumerate(st["months"]) if m]
    warm_i, warm = max(months, key=lambda im: im[1]["avg"])
    cold_i, cold = min(months, key=lambda im: im[1]["avg"])
    items = [(tr_fmt(lang, "faq_today_q", **names), today_sentences(loc, lang, st))]
    items.append((tr_fmt(lang, "faq_warm_q", **names), tr_fmt(
        lang, "faq_warm_a", month=month_name(lang, warm_i), avg=fmt_temp(warm["avg"]),
        max=fmt_temp(st["max"][0]), date=fmt_date(st["max"][1], lang))))
    swim = [i for i, m in months if m["avg"] >= 20]
    if swim:
        answer = tr_fmt(lang, "faq_swim_a", **{
            "from": month_name(lang, swim[0]), "to": month_name(lang, swim[-1]),
            "month": month_name(lang, warm_i), "avg": fmt_temp(warm["avg"])})
    else:
        answer = tr_fmt(lang, "faq_swim_none", month=month_name(lang, warm_i),
                        avg=fmt_temp(warm["avg"]))
    items.append((tr_fmt(lang, "faq_swim_q", **names), answer))
    items.append((tr_fmt(lang, "faq_cold_q", **names), tr_fmt(
        lang, "faq_cold_a", month=month_name(lang, cold_i), avg=fmt_temp(cold["avg"]),
        min=fmt_temp(st["min"][0]), date=fmt_date(st["min"][1], lang))))
    season = typical_season(st["seasons"])
    if season:
        items.append((tr_fmt(lang, "faq_season_q", **names), tr_fmt(
            lang, "faq_season_a", **{"from": day_month(season[0], lang),
                                     "to": day_month(season[1], lang),
                                     "days": season[2], "years": season[3]})))
    items.append((tr_fmt(lang, "faq_beach_q", **names),
                  tr_fmt(lang, "faq_beach_" + loc["beach"], **names)))
    quality = bathing_summary(loc, lang)
    if quality:
        items.append((tr_fmt(lang, "faq_quality_q", **names), tr_fmt(
            lang, "faq_quality_a", year=BATHING["year"], status=quality[0],
            n=quality[1], total=quality[2], **names)))
    for key in ("upwelling", "jelly", "tides"):
        items.append((tr_fmt(lang, "faq_{}_q".format(key), **names),
                      tr_fmt(lang, "faq_{}_a".format(key), **names)))
    return items


def glance_html(loc, lang, st):
    """'At a glance' facts under the water hero: beach type, typical swimming
    season, best month and EU water quality."""
    if not st:
        return ""
    facts = [("🏖️", TR[lang]["seo_glance_beach"], TR[lang]["seo_beach_" + loc["beach"]])]
    season = typical_season(st["seasons"])
    if season:
        facts.append(("🏊", TR[lang]["seo_glance_season"], tr_fmt(
            lang, "seo_glance_season_v", **{"from": day_month(season[0], lang),
                                           "to": day_month(season[1], lang),
                                           "days": season[2]})))
    best_i, best = best_month(st)
    facts.append(("☀️", TR[lang]["seo_glance_best"], tr_fmt(
        lang, "seo_glance_best_v", month=capitalize(month_name(lang, best_i)),
        avg=fmt_temp(best["avg"]))))
    quality = bathing_summary(loc, lang)
    if quality:
        facts.append(("🔬", tr_fmt(lang, "seo_glance_quality", year=BATHING["year"]),
                      tr_fmt(lang, "seo_glance_quality_v", status=quality[0],
                             n=quality[1], total=quality[2])))
    return '    <dl class="glance">\n{}\n    </dl>\n'.format("\n".join(
        '        <div class="glance-item"><dt>{icon} {label}</dt><dd>{value}</dd></div>'.format(
            icon=icon, label=escape(label), value=escape(value))
        for icon, label, value in facts))


def best_month(st):
    """(index, month) with the highest share of days >= WARM_TEMP, ties broken
    by the warmer average."""
    return max(((i, m) for i, m in enumerate(st["months"]) if m),
               key=lambda im: (round(im[1]["warm_share"], 2), im[1]["avg"]))


def seo_content_html(loc, lang, st):
    """Monthly climatology table, swimming seasons, EU bathing water quality
    and the FAQ appended to the dashboard."""
    if not st:
        return ""
    best_i, best = best_month(st)
    rows = []
    for i, m in enumerate(st["months"]):
        if not m:
            continue
        share = int(round(m["warm_share"] * 100))
        rows.append(
            '            <tr><th scope="row"><a href="/{path}">{month}</a></th><td>{avg}°C</td>'
            '<td>{min}°C</td><td>{max}°C</td>'
            '<td class="share-cell"><span class="share-bar" style="--p:{share}%"></span>'
            '{share}%</td></tr>'.format(
                path=month_path(i), month=escape(month_name(lang, i)),
                avg=fmt_temp(m["avg"]), min=fmt_temp(m["min"][0]),
                max=fmt_temp(m["max"][0]), share=share))
    faq = "\n".join(
        '        <div class="faq-item">\n'
        '            <h3>{q}</h3>\n'
        '            <p>{a}</p>\n'
        '        </div>'.format(q=escape(q), a=escape(a))
        for q, a in faq_items(loc, lang, st))
    return """    <section class="month-climate">
    <h2>{h2}</h2>
    <p class="best-month">{best}</p>
    <p class="tip">{note}</p>
    <div class="table-scroll">
    <table class="month-table">
        <thead><tr><th scope="col">{c_month}</th><th scope="col">{c_avg}</th><th scope="col">{c_min}</th><th scope="col">{c_max}</th><th scope="col">{c_warm}</th></tr></thead>
        <tbody>
{rows}
        </tbody>
    </table>
    </div>
    </section>
{season}{bathing}
    <section class="faq">
    <h2>{faq_h2}</h2>
{faq}
    </section>""".format(
        h2=escape(tr_fmt(lang, "seo_month_h2", location=loc_full(loc, lang),
                         location_in=loc_in_full(loc, lang))),
        note=escape(tr_fmt(lang, "seo_month_note", **{
            "from": fmt_date(st["first"], lang), "to": fmt_date(st["date"], lang)})),
        c_month=escape(TR[lang]["seo_col_month"]), c_avg=escape(TR[lang]["seo_col_avg"]),
        c_min=escape(TR[lang]["seo_col_min"]), c_max=escape(TR[lang]["seo_col_max"]),
        c_warm=escape(tr_fmt(lang, "seo_col_warm", temp=WARM_TEMP)),
        best=escape(tr_fmt(lang, "seo_best_month", month=capitalize(month_name(lang, best_i)),
                           avg=fmt_temp(best["avg"]),
                           share=int(round(best["warm_share"] * 100)), temp=WARM_TEMP)),
        rows="\n".join(rows), season=season_html(loc, lang, st),
        bathing=bathing_html(loc, lang),
        faq_h2=escape(TR[lang]["faq_h2"]), faq=faq)


SEASON_ROWS = 12


def season_html(loc, lang, st):
    """Typical swimming season + first/last swimmable day per year."""
    season = typical_season(st["seasons"])
    if not season:
        return ""
    rows = []
    for s in st["seasons"][:SEASON_ROWS]:
        if s["first"]:
            first, last = day_month(s["first"][5:], lang), day_month(s["last"][5:], lang)
        else:
            first = last = "—"
        rows.append('            <tr><th scope="row">{year}{mark}</th><td>{first}</td>'
                    '<td>{last}</td><td>{days}</td></tr>'.format(
                        year=s["year"], mark="" if s["complete"] else "*",
                        first=escape(first), last=escape(last), days=s["days"]))
    names = dict(location=loc_full(loc, lang), location_in=loc_in_full(loc, lang))
    return "\n" + table_section(
        "swim-season", tr_fmt(lang, "seo_season_h2", **names),
        tr_fmt(lang, "seo_season_note", temp=SWIM_TEMP, **{
            "from": day_month(season[0], lang), "to": day_month(season[1], lang),
            "days": season[2], "years": season[3]}),
        [escape(TR[lang]["seo_col_year"]), escape(TR[lang]["seo_col_first"]),
         escape(TR[lang]["seo_col_last"]),
         escape(tr_fmt(lang, "seo_col_days", temp=SWIM_TEMP))],
        rows) + "\n"


BW_LINK = "https://www.eea.europa.eu/en/topics/in-depth/bathing-water"


def bathing_html(loc, lang):
    """EU Bathing Water Directive classification of the town's bathing sites."""
    sites = bathing_sites(loc)
    if not sites:
        return ""
    badge = '<span class="bw-badge bw-{0}">{1}</span>'
    rows = ['            <tr><th scope="row">{name}</th><td>{km} km</td><td>{now}</td>'
            '<td>{prev}</td></tr>'.format(
                name=escape(s["name"]), km=s["km"],
                now=badge.format(s["status"], escape(TR[lang]["seo_bw_" + s["status"]])),
                prev=badge.format(s["prev"], escape(TR[lang]["seo_bw_" + s["prev"]])))
            for s in sites]
    year = BATHING["year"]
    section = table_section(
        "bathing-quality",
        tr_fmt(lang, "seo_bw_h2", location=loc_full(loc, lang),
               location_in=loc_in_full(loc, lang)),
        tr_fmt(lang, "seo_bw_note", year=year),
        [escape(TR[lang]["seo_col_site"]), escape(TR[lang]["seo_col_distance"]),
         str(year), str(year - 1)],
        rows)
    source = '    <p class="tip"><a href="{}" target="_blank" rel="noopener">{}</a></p>\n'.format(
        BW_LINK, escape(TR[lang]["seo_bw_source"]))
    return "\n" + section.replace("    </section>", source + "    </section>") + "\n"


# --- Static content for the chart pages --------------------------------------
# The charts are drawn client-side; these tables put the same numbers in the
# HTML so the stats/heatmap/compare pages aren't empty boxes to a crawler.

def mean(values):
    return sum(values) / len(values)


def year_month_matrix(st):
    """{year: [12 x avg or None]} from the raw readings, as heatmap.html
    computes it."""
    acc = {}
    for dt, temp in st["rows"]:
        acc.setdefault(int(dt[:4]), [[] for _ in range(12)])[int(dt[5:7]) - 1].append(temp)
    return {y: [mean(v) if v else None for v in months] for y, months in acc.items()}


def short_date(dt, lang):
    """'Jul 24, 2024' with the abbreviated month names, as stats.html shows it."""
    return "{} {}, {}".format(TR[lang]["months"][int(dt[5:7]) - 1],
                              int(dt[8:10]), dt[:4])


def records_html(lang, st):
    """Static content of #records-grid (stats.html replaces it on load)."""
    if not st:
        return ""
    yearly = {}
    for dt, temp in st["rows"]:
        yearly.setdefault(dt[:4], []).append(temp)
    avgs = {y: mean(v) for y, v in yearly.items()}
    warm_y = max(avgs, key=avgs.get)
    cold_y = min(avgs, key=avgs.get)
    cards = [("hot", "st_hottest", fmt_temp(st["max"][0]), short_date(st["max"][1], lang)),
             ("cold", "st_coldest", fmt_temp(st["min"][0]), short_date(st["min"][1], lang)),
             ("hot", "st_warmest_yr", fmt_temp(avgs[warm_y]), warm_y),
             ("cold", "st_coldest_yr", fmt_temp(avgs[cold_y]), cold_y)]
    return "".join(
        '<div class="record-card {cls}"><span class="label">{label}</span>'
        '<span class="record-value">{value}°C</span>'
        '<span class="record-date">{date}</span></div>'.format(
            cls=cls, label=escape(TR[lang][key]), value=value, date=escape(date))
        for cls, key, value, date in cards)


def table_section(cls, h2, note, head_cells, rows):
    """A <section> with an h2, a note and a scrollable .month-table."""
    return """    <section class="{cls}">
    <h2>{h2}</h2>
    <p class="tip">{note}</p>
    <div class="table-scroll">
    <table class="month-table">
        <thead><tr>{head}</tr></thead>
        <tbody>
{rows}
        </tbody>
    </table>
    </div>
    </section>""".format(cls=cls, h2=escape(h2), note=escape(note),
                         head="".join('<th scope="col">{}</th>'.format(c) for c in head_cells),
                         rows="\n".join(rows))


def stats_content_html(loc, lang, st):
    """Yearly min/avg/max table for stats.html."""
    if not st:
        return ""
    yearly = {}
    for dt, temp in st["rows"]:
        yearly.setdefault(dt[:4], []).append(temp)
    rows = ['            <tr><th scope="row">{}</th><td>{}°C</td><td>{}°C</td>'
            '<td>{}°C</td></tr>'.format(y, fmt_temp(min(v)), fmt_temp(mean(v)),
                                        fmt_temp(max(v)))
            for y, v in sorted(yearly.items(), reverse=True)]
    names = dict(location=loc_full(loc, lang), location_in=loc_in_full(loc, lang))
    return table_section(
        "year-table", tr_fmt(lang, "seo_year_h2", **names), TR[lang]["seo_year_note"],
        [escape(TR[lang][k]) for k in ("seo_col_year", "seo_col_min", "seo_col_avg",
                                       "seo_col_max")], rows)


def heatmap_content_html(loc, lang, st):
    """Year x month table of averages for heatmap.html, cells tinted like the
    hub badges so it reads as a static heatmap."""
    if not st:
        return ""
    rows = []
    for year, months in sorted(year_month_matrix(st).items(), reverse=True):
        cells = "".join(
            '<td style="background:{}">{}</td>'.format(temp_color(v), fmt_temp(v))
            if v is not None else "<td></td>" for v in months)
        rows.append('            <tr><th scope="row">{}</th>{}</tr>'.format(year, cells))
    names = dict(location=loc_full(loc, lang), location_in=loc_in_full(loc, lang))
    return table_section(
        "heat-table", tr_fmt(lang, "seo_hm_h2", **names), TR[lang]["seo_hm_note"],
        [escape(TR[lang]["seo_col_year"])] + [escape(m) for m in TR[lang]["months"]],
        rows)


def compare_content_html(loc, lang, st):
    """The latest reading's calendar day in every year, with the 30 days up to
    it, for compare.html."""
    if not st:
        return ""
    last = datetime.date.fromisoformat(st["date"][:10])
    daily = st["daily"]
    rows = []
    for year in sorted({int(d[:4]) for d in daily}, reverse=True):
        try:
            day = last.replace(year=year)
        except ValueError:  # 29 Feb in a non-leap year
            continue
        window = [daily[d.isoformat()] for d in
                  (day - datetime.timedelta(days=i) for i in range(30))
                  if d.isoformat() in daily]
        if not window:
            continue
        on_day = daily.get(day.isoformat())
        rows.append('            <tr><th scope="row">{}</th><td>{}</td><td>{}°C</td></tr>'
                    .format(year, fmt_temp(on_day) + "°C" if on_day is not None else "–",
                            fmt_temp(mean(window))))
    date = ("{} {}".format(TR["en"]["months"][last.month - 1], last.day) if lang == "en"
            else "{:02d}.{:02d}".format(last.day, last.month))
    names = dict(location=loc_full(loc, lang), location_in=loc_in_full(loc, lang),
                 date=date)
    return table_section(
        "cmp-table", tr_fmt(lang, "seo_cmp_h2", **names),
        tr_fmt(lang, "seo_cmp_note", date=date),
        [escape(TR[lang]["seo_col_year"]), escape(date), escape(TR[lang]["seo_col_30d"])],
        rows)


def distance_km(a, b):
    """Great-circle distance between two locations (haversine)."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a["place_lat"], a["place_lon"],
                                                 b["place_lat"], b["place_lon"]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(h))


NEARBY_COUNT = 6
# The main container's closing tag, right before the footer, in every template.
CONTAINER_END_RE = re.compile(r'</div>\s*<footer class="footer">')


def nearby_temp_html(st, other_st):
    """Neighbour's latest water temperature and how it compares to this town's
    ('21.3°C · +1.2°'), baked at build time like the hero fallback."""
    if not other_st:
        return ""
    diff = round(other_st["temp"] - st["temp"], 1) if st else 0.0
    cls = "up" if diff > 0 else "down" if diff < 0 else "flat"
    sign = "+" if diff > 0 else "−" if diff < 0 else "±"
    return (' <span class="nearby-temp" style="--wh-color:{color}">{temp}°C</span>'
            '<span class="nearby-diff {cls}">{sign}{diff}°</span>').format(
                color=temp_color(other_st["temp"]), temp=fmt_temp(other_st["temp"]),
                cls=cls, sign=sign, diff=fmt_temp(abs(diff)))


def nearby_html(loc, lang, page_file, stats):
    """Static links to the closest towns' page of the same kind, so every town
    page is reachable by crawlers from its neighbours, not only from the hub
    (the location dropdown is built client-side). Each link shows the
    neighbour's water temperature and the difference to this town."""
    others = sorted(((distance_km(loc, o), o) for o in LOCATIONS if o is not loc),
                    key=lambda pair: pair[0])
    page = "" if page_file == "index.html" else page_file
    st = stats.get(loc["slug"])
    links = "\n".join(
        '        <a class="nearby-link" href="/{slug}/{page}">{flag} {name} '
        '<span class="nearby-km">{km} km</span>{temp}</a>'.format(
            slug=o["slug"], page=page, flag=o["flag"], name=escape(loc_name(o, lang)),
            km=int(round(km)), temp=nearby_temp_html(st, stats.get(o["slug"])))
        for km, o in others[:NEARBY_COUNT])
    return ('\n    <section class="nearby">\n'
            '    <h2>{}</h2>\n'
            '    <div class="nearby-links">\n{}\n    </div>\n'
            '    </section>\n'.format(escape(TR[lang]["nearby_h2"]), links))


# Breadcrumb label of each per-location page (the dashboard is the town itself).
PAGE_NAV_KEY = {
    "compare.html": "nav_compare", "heatmap.html": "nav_heatmap",
    "stats.html": "nav_stats", "gallery.html": "nav_gallery",
    "weather.html": "nav_weather",
}


def breadcrumb_items(loc, lang, page_file):
    """[(name, absolute url)]: hub › country › town › page."""
    items = [(TR[lang]["crumb_home"], url_for("", lang)),
             (country_name(loc, lang), url_for(loc["country"] + "/", lang)),
             (loc_name(loc, lang), url_for(site_path(loc["slug"], "index.html"), lang))]
    if page_file in PAGE_NAV_KEY:
        items.append((TR[lang][PAGE_NAV_KEY[page_file]],
                      url_for(site_path(loc["slug"], page_file), lang)))
    return items


def breadcrumb_html(items, lang):
    """Visible breadcrumb matching the BreadcrumbList JSON-LD."""
    parts = []
    for i, (name, url) in enumerate(items):
        if i == len(items) - 1:
            parts.append('<span aria-current="page">{}</span>'.format(escape(name)))
        else:
            path = url[len(BASE_URL + lang_prefix(lang)):]
            parts.append('<a href="{}">{}</a>'.format(escape(path), escape(name)))
    return '    <nav class="breadcrumb" aria-label="{}">{}</nav>\n'.format(
        escape(TR[lang]["crumb_label"]), ' <span class="crumb-sep">›</span> '.join(parts))


def breadcrumb_ld(items):
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": name, "item": url}
                for i, (name, url) in enumerate(items)]}


def dataset_ld(loc, lang, st, name, description, url):
    """schema.org Dataset for a town's sea temperature series (Dataset Search)."""
    ld = {
        "@context": "https://schema.org", "@type": "Dataset",
        "name": name, "description": description, "url": url,
        "inLanguage": lang, "isAccessibleForFree": True,
        "license": "https://creativecommons.org/licenses/by/4.0/",
        "isBasedOn": "https://open-meteo.com/",
        "creator": {"@type": "Organization", "name": "more.masoko.net",
                    "url": BASE_URL + "/"},
        "keywords": [TR[lang]["hub_h1"], loc_name(loc, lang), country_name(loc, lang)],
        "spatialCoverage": {
            "@type": "Place", "name": loc_full(loc, lang),
            "geo": {"@type": "GeoCoordinates", "latitude": loc["place_lat"],
                    "longitude": loc["place_lon"]}},
        "variableMeasured": {"@type": "PropertyValue",
                             "name": "Sea surface temperature", "unitText": "°C"},
        "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv",
                          "contentUrl": CSV_BASE + loc["csv_file"]}],
    }
    if st:
        ld["temporalCoverage"] = "{}/{}".format(st["first"][:10], st["date"][:10])
    return ld


def place_ld(loc, lang, url):
    """schema.org Place for the town/beach a dashboard is about."""
    return {"@context": "https://schema.org", "@type": "Place",
            "name": loc_name(loc, lang), "url": url,
            "geo": {"@type": "GeoCoordinates", "latitude": loc["place_lat"],
                    "longitude": loc["place_lon"]},
            "containedInPlace": {"@type": "Country", "name": country_name(loc, lang)}}


def faq_ld(items):
    return {"@context": "https://schema.org", "@type": "FAQPage",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in items]}


def site_path(slug, page_file):
    """Language-neutral path of a per-location page, as used in URLs."""
    if page_file == "index.html":
        return "{}/".format(slug)
    return "{}/{}".format(slug, page_file)


def out_dir_for(lang, *parts):
    base = DOCS_DIR if lang == DEFAULT_LANG else os.path.join(DOCS_DIR, lang)
    return os.path.join(base, *parts)


def page_meta(meta, loc, lang, st):
    """(title, description) for one per-location page. The dashboard uses the
    *_live variants carrying the latest reading when there is data."""
    fields = dict(loc=loc_name(loc, lang), loc_in=loc_in(loc, lang),
                  country=country_name(loc, lang), year=loc["start_date"][:4])
    title_t, desc_t = meta["title"][lang], meta["desc"][lang]
    if st and "title_live" in meta:
        fields.update(temp=fmt_temp(st["temp"]), date=fmt_date(st["date"], lang))
        title_t, desc_t = meta["title_live"][lang], meta["desc_live"][lang]
    return title_t.format(**fields), desc_t.format(**fields)


def write_location_pages(stats):
    bodies = {page: template_body(page) for page in PAGES}
    galleries = load_galleries()
    for loc in LOCATIONS:
        slug = loc["slug"]
        st = stats.get(slug)
        for lang in LANGS:
            out_dir = out_dir_for(lang, slug)
            os.makedirs(out_dir, exist_ok=True)
            for page_file, meta in PAGES.items():
                path = site_path(slug, page_file)
                title, desc = page_meta(meta, loc, lang, st)
                crumbs = breadcrumb_items(loc, lang, page_file)
                structured = [breadcrumb_ld(crumbs)]
                body = bodies[page_file].replace("{lockey}", i18n_key(slug)[4:])
                if page_file == "index.html":
                    static_desc = meta["desc"][lang].format(
                        loc=loc_name(loc, lang), loc_in=loc_in(loc, lang),
                        country=country_name(loc, lang), year=loc["start_date"][:4])
                    structured.append(dataset_ld(
                        loc, lang, st, tr_fmt(lang, "dash_h1",
                                              location=loc_full(loc, lang),
                                              location_in=loc_in_full(loc, lang)),
                        static_desc, url_for(path, lang)))
                    structured.append(place_ld(loc, lang, url_for(path, lang)))
                    faq = faq_items(loc, lang, st)
                    if faq:
                        structured.append(faq_ld(faq))
                    body = (body.replace("{today}", today_html(loc, lang, st))
                                .replace("{glance}", glance_html(loc, lang, st))
                                .replace("{seo_content}", seo_content_html(loc, lang, st)))
                if page_file == "stats.html":
                    body = (body.replace("{records}", records_html(lang, st))
                                .replace("{seo_content}", stats_content_html(loc, lang, st)))
                if page_file == "heatmap.html":
                    body = body.replace("{seo_content}", heatmap_content_html(loc, lang, st))
                if page_file == "compare.html":
                    body = body.replace("{seo_content}", compare_content_html(loc, lang, st))
                if page_file == "gallery.html":
                    body = body.replace("{gallery}", gallery_markup(
                        galleries.get(slug, []), loc_full(loc, lang)))
                    body = (body.replace("{lat}", str(loc["lat"]))
                                .replace("{lon}", str(loc["lon"])))
                body = body.replace('<div class="container">',
                                    '<div class="container">\n'
                                    + breadcrumb_html(crumbs, lang), 1)
                # Nearby links go at the end of the main container.
                body = CONTAINER_END_RE.sub(
                    lambda m: nearby_html(loc, lang, page_file, stats) + m.group(0), body, 1)
                body = prefix_links(body, lang)
                if meta.get("plotly", True):
                    body = with_plotly(body)
                head = build_head(title, desc, path, lang, structured=structured,
                                  robots="noindex, follow" if meta.get("noindex") else None,
                                  image=og_image_url(slug) or og_image_url("site"))
                page = version_assets(
                    bake(head.replace("{slug}", slug) + body, lang, loc))
                with open(os.path.join(out_dir, page_file), "w", encoding="utf-8") as fh:
                    fh.write(page)
        print("{}: wrote {} pages x {} languages".format(
            loc["name_en"], len(PAGES), len(LANGS)))


def write_locations_js():
    lines = [
        "// Generated by build_site.py from locations.py — do not edit by hand.",
        "window.LOCATIONS = {",
    ]
    for loc in LOCATIONS:
        lines.append(
            '    "{slug}": {{ csv: "{csv}", nameKey: "{key}", flag: "{flag}", '
            'lat: {lat}, lon: {lon}, country: "{country}", tz: "{tz}", '
            'facing: {facing} }},'.format(
                slug=loc["slug"], csv=loc["csv_file"],
                key=i18n_key(loc["slug"]), flag=loc["flag"],
                lat=loc["place_lat"], lon=loc["place_lon"], country=loc["country"],
                tz=COUNTRY_TZ[loc["country"]], facing=loc["facing"]))
    lines.append("};")
    lines.append("window.COUNTRY_ORDER = {};".format(
        "[" + ", ".join('"{}"'.format(c) for c in COUNTRY_ORDER) + "]"))
    path = os.path.join(DOCS_DIR, "locations.js")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote docs/locations.js ({} locations)".format(len(LOCATIONS)))


# Strings only build_site.py uses (baked into the HTML); left out of the
# runtime bundles to keep docs/i18n.<lang>.js small.
BUILD_ONLY_KEY_RE = re.compile(
    r"^(desc_|seo_|faq_|anomaly_|notfound_|crumb_|title_)|"
    r"^(today_summary|nearby_h2|months_full)$")


def write_i18n_js():
    """Regenerate docs/i18n.<lang>.js from translations.json + the runtime
    template, one bundle per language.

    translations.json is the single source of truth for every UI string; each
    page gets its own language embedded as const I18N for the dynamic
    (chart/dropdown/map) strings, and build_site.py bakes the static page text
    from the same data."""
    en_keys = set(TR["en"])
    for lang in LANGS:
        if set(TR[lang]) != en_keys:
            print("WARNING: translations.json en/{} key mismatch: {}".format(
                lang, sorted(en_keys ^ set(TR[lang]))))
    with open(os.path.join(TEMPLATES_DIR, "i18n_runtime.js"), encoding="utf-8") as fh:
        runtime = fh.read()
    header = ("// Generated by build_site.py from translations.json + "
              "templates/i18n_runtime.js — do not edit by hand.\n")
    info = [{k: v for k, v in i.items() if k != "og"} for i in LANG_INFO]
    for lang in LANGS:
        strings = {k: v for k, v in TR[lang].items() if not BUILD_ONLY_KEY_RE.match(k)}
        body = ("const I18N = {};\nconst LANG_INFO = {};\nconst DEFAULT_LANG = {};\n\n"
                .format(json.dumps({lang: strings}, ensure_ascii=False, indent=2),
                        json.dumps(info, ensure_ascii=False),
                        json.dumps(DEFAULT_LANG)))
        with open(os.path.join(DOCS_DIR, "i18n.{}.js".format(lang)), "w",
                  encoding="utf-8") as fh:
            fh.write(header + body + runtime)
        print("wrote docs/i18n.{}.js ({} runtime keys)".format(lang, len(strings)))


def temp_color(temp):
    """Python twin of tempColor() in data.js, for the statically baked badges."""
    f = max(0.0, min(1.0, (temp - 4) / 24))
    return "hsl({}, 75%, 47%)".format(int(round(220 - f * 220)))


def hub_temp(st):
    """Format fields for a hub card's temperature badge."""
    if not st:
        return {"temp": "", "temp_style": ""}
    return {"temp": fmt_temp(st["temp"]) + "°",
            "temp_style": ' style="background:{};color:#fff"'.format(temp_color(st["temp"]))}


# Nav and footer of the generated (non-template) pages: hub, country, month.
SITE_NAV = """<nav class="nav">
    <div class="nav-inner">
        <a class="nav-brand" href="/" data-i18n="nav_brand">🌊 Black Sea Temp</a>
        <ul class="nav-links">
            <li><a href="/burgas/" data-i18n="nav_dashboard">Dashboard</a></li>
            <li><a href="/burgas/compare.html" data-i18n="nav_compare">Compare Years</a></li>
            <li><a href="/burgas/heatmap.html" data-i18n="nav_heatmap">Heatmap</a></li>
            <li><a href="/burgas/stats.html" data-i18n="nav_stats">Statistics</a></li>
            <li><a href="/burgas/gallery.html" data-i18n="nav_gallery">Photos</a></li>
            <li><a href="/compare-locations.html" data-i18n="nav_comparelocations">Compare Locations</a></li>
            <li><a href="/moon-phases/" data-i18n="nav_moon">Moon Phases</a></li>
        </ul>
        <div class="lang-switch"></div>
    </div>
</nav>
"""

SITE_FOOTER = """<footer class="footer">
    <span data-i18n="footer_title">Black Sea Water Temperature</span>
    <a href="https://github.com/hjelev/Black_Sea_water_temperature" target="_blank" rel="noopener">GitHub</a>
    <a href="https://masoko.net" target="_blank" rel="noopener">masoko.net</a>
</footer>
"""


def browse_links_html(lang, current=None):
    """Links to every country page and month page (hub, country and month
    pages); current is the site path of the page showing it."""
    def link(path, label):
        here = ' aria-current="page"' if path == current else ""
        return '        <a class="nearby-link" href="/{}"{}>{}</a>'.format(
            path, here, escape(label))
    countries = [link(country + "/", "{} {}".format(group[0]["flag"],
                                                   country_name(group[0], lang)))
                 for country, group in locations_by_country()]
    months = [link(month_path(i), capitalize(month_name(lang, i))) for i in range(12)]
    return ('    <section class="browse">\n'
            '    <h2>{}</h2>\n    <div class="nearby-links">\n{}\n    </div>\n'
            '    <h2>{}</h2>\n    <div class="nearby-links">\n{}\n    </div>\n'
            '    </section>'.format(escape(TR[lang]["seo_countries_h2"]), "\n".join(countries),
                                    escape(TR[lang]["seo_months_h2"]), "\n".join(months)))


def write_simple_page(lang, path, title, desc, crumbs, inner, structured=()):
    """Write a generated page (country/month) at the site path: shared nav,
    breadcrumb, the given container HTML and footer."""
    head = build_head(title, desc, path, lang,
                      structured=[breadcrumb_ld(crumbs)] + list(structured),
                      image=og_image_url("site")).replace("{slug}", "burgas")
    body = "<body>\n{nav}\n<div class=\"container\">\n{crumbs}{inner}\n</div>\n\n{footer}</body>\n</html>\n".format(
        nav=SITE_NAV, crumbs=breadcrumb_html(crumbs, lang), inner=inner, footer=SITE_FOOTER)
    page = version_assets(bake(head + prefix_links(body, lang), lang))
    out_dir = out_dir_for(lang, *path.strip("/").split("/"))
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(page)


def warm_cold_text(lang, pairs, name):
    """'The warmest sea is at X (t°C) and the coldest at Y (t°C).' from
    [(temp, loc)]."""
    warm = max(pairs, key=lambda p: p[0])
    cold = min(pairs, key=lambda p: p[0])
    return tr_fmt(lang, "seo_warm_cold", warm=name(warm[1]), warm_t=fmt_temp(warm[0]),
                  cold=name(cold[1]), cold_t=fmt_temp(cold[0]))


# Summer months shown as columns on the country pages (0-based).
COUNTRY_MONTH_COLS = (5, 6, 7, 8)


def swim_season(lang, st):
    """'June–September': the months averaging 20°C or more, as in the FAQ."""
    swim = [i for i, m in enumerate(st["months"]) if m and m["avg"] >= 20]
    if not swim:
        return "–"
    return "{}–{}".format(month_name(lang, swim[0]), month_name(lang, swim[-1]))


def write_country_pages(stats):
    """/<country>/: every location of one country with today's reading, the
    summer monthly averages and the swimming season."""
    for country, group in locations_by_country():
        data = [(stats[loc["slug"]], loc) for loc in group if stats.get(loc["slug"])]
        if not data:
            continue
        data.sort(key=lambda p: -p[0]["temp"])
        temps = [st["temp"] for st, _ in data]
        latest = max(st["date"] for st, _ in data)
        first = min(st["first"] for st, _ in data)
        warm_st, warm_loc = data[0]
        for lang in LANGS:
            fields = dict(country=country_name(group[0], lang),
                          country_in=country_in(country, lang),
                          min=fmt_temp(min(temps)), max=fmt_temp(max(temps)),
                          date=fmt_date(latest, lang), warm=loc_name(warm_loc, lang),
                          warm_t=fmt_temp(warm_st["temp"]))
            title = COUNTRY_META["title"][lang].format(**fields)
            desc = COUNTRY_META["desc"][lang].format(**fields)
            intro = "{} {}".format(
                tr_fmt(lang, "seo_country_intro", n=len(data), avg=fmt_temp(mean(temps)),
                       **fields),
                warm_cold_text(lang, [(st["temp"], loc) for st, loc in data],
                               lambda loc: loc_name(loc, lang)))
            rows = []
            for st, loc in data:
                months = "".join(
                    "<td>{}°C</td>".format(fmt_temp(st["months"][i]["avg"]))
                    if st["months"][i] else "<td></td>" for i in COUNTRY_MONTH_COLS)
                rows.append(
                    '            <tr><th scope="row"><a href="/{slug}/">{flag} {name}</a></th>'
                    '<td><span class="hub-temp" style="background:{color};color:#fff">'
                    '{temp}°</span></td>{months}<td>{swim}</td></tr>'.format(
                        slug=loc["slug"], flag=loc["flag"], name=escape(loc_name(loc, lang)),
                        color=temp_color(st["temp"]), temp=fmt_temp(st["temp"]),
                        months=months, swim=escape(swim_season(lang, st))))
            head_cells = ([escape(TR[lang]["seo_col_location"]), escape(TR[lang]["seo_col_today"])]
                          + ['<a href="/{}">{}</a>'.format(month_path(i),
                                                          escape(TR[lang]["months"][i]))
                             for i in COUNTRY_MONTH_COLS]
                          + [escape(TR[lang]["seo_col_swim"])])
            table = table_section(
                "country-table", TR[lang]["seo_country_table_h2"],
                tr_fmt(lang, "seo_month_note", **{"from": fmt_date(first, lang),
                                                  "to": fmt_date(latest, lang)}),
                head_cells, rows)
            inner = ('    <h1>{h1}</h1>\n    <p class="subtitle">{intro}</p>\n'
                     '{table}\n{browse}').format(
                h1=escape(COUNTRY_META["h1"][lang].format(**fields)), intro=escape(intro),
                table=table, browse=browse_links_html(lang, country + "/"))
            crumbs = [(TR[lang]["crumb_home"], url_for("", lang)),
                      (fields["country"], url_for(country + "/", lang))]
            item_list = {"@context": "https://schema.org", "@type": "ItemList",
                         "name": title, "itemListElement": [
                             {"@type": "ListItem", "position": i + 1,
                              "name": loc_full(loc, lang),
                              "url": url_for(site_path(loc["slug"], "index.html"), lang)}
                             for i, (_, loc) in enumerate(data)]}
            write_simple_page(lang, country + "/", title, desc, crumbs, inner, [item_list])
        print("wrote country page {} x {} languages".format(country, len(LANGS)))


def write_month_pages(stats):
    """/months/<month>/: every location's average for one calendar month,
    warmest first."""
    for i in range(12):
        data = [(stats[loc["slug"]]["months"][i], loc) for loc in LOCATIONS
                if stats.get(loc["slug"]) and stats[loc["slug"]]["months"][i]]
        if not data:
            continue
        data.sort(key=lambda p: -p[0]["avg"])
        sts = [stats[loc["slug"]] for _, loc in data]
        first = min(st["first"] for st in sts)
        latest = max(st["date"] for st in sts)
        avgs = [m["avg"] for m, _ in data]
        path = month_path(i)
        for lang in LANGS:
            fields = dict(month=month_name(lang, i), month_in=month_in(i, lang),
                          n=len(data), warm=loc_full(data[0][1], lang),
                          warm_t=fmt_temp(data[0][0]["avg"]))
            title = MONTH_META["title"][lang].format(**fields)
            desc = MONTH_META["desc"][lang].format(**fields)
            intro = "{} {}".format(
                tr_fmt(lang, "seo_month_intro", avg=fmt_temp(mean(avgs)), **fields),
                warm_cold_text(lang, [(m["avg"], loc) for m, loc in data],
                               lambda loc: loc_full(loc, lang)))
            rows = ['            <tr><td>{n}</td><th scope="row"><a href="/{slug}/">{flag} {name}</a></th>'
                    '<td><a href="/{country}/">{cname}</a></td>'
                    '<td style="background:{color};color:#fff">{avg}°C</td>'
                    '<td>{min}°C</td><td>{max}°C</td></tr>'.format(
                        n=rank + 1, slug=loc["slug"], flag=loc["flag"],
                        name=escape(loc_name(loc, lang)), country=loc["country"],
                        cname=escape(country_name(loc, lang)), color=temp_color(m["avg"]),
                        avg=fmt_temp(m["avg"]), min=fmt_temp(m["min"][0]),
                        max=fmt_temp(m["max"][0]))
                    for rank, (m, loc) in enumerate(data)]
            table = table_section(
                "month-rank", TR[lang]["seo_country_table_h2"],
                tr_fmt(lang, "seo_month_note", **{"from": fmt_date(first, lang),
                                                  "to": fmt_date(latest, lang)}),
                ["#"] + [escape(TR[lang][k]) for k in (
                    "seo_col_location", "seo_col_country", "seo_col_avg", "seo_col_min",
                    "seo_col_max")],
                rows)
            inner = ('    <h1>{h1}</h1>\n    <p class="subtitle">{intro}</p>\n'
                     '{table}\n{browse}').format(
                h1=escape(capitalize(MONTH_META["h1"][lang].format(**fields))),
                intro=escape(intro), table=table, browse=browse_links_html(lang, path))
            crumbs = [(TR[lang]["crumb_home"], url_for("", lang)),
                      (capitalize(month_name(lang, i)), url_for(path, lang))]
            write_simple_page(lang, path, title, desc, crumbs, inner)
        print("wrote month page {} x {} languages".format(MONTH_SLUGS[i], len(LANGS)))


# Years with a /moon-phases/ page around the build year; moon-data.js carries
# one more year on each side so the cycle around 1 January is complete.
MOON_YEARS_BEFORE, MOON_YEARS_AFTER = 2, 5
# Time zone of the baked year table per page language (the browser re-renders
# it in the viewer's zone): (name, UTC offset, EU summer time).
MOON_TZ = {"bg": ("Europe/Sofia", 2, True), "en": ("Europe/Sofia", 2, True),
           "ro": ("Europe/Bucharest", 2, True), "ru": ("Europe/Moscow", 3, False),
           "tr": ("Europe/Istanbul", 3, False)}
ZODIAC_SIGNS = "♈♉♊♋♌♍♎♏♐♑♒♓"


def moon_years():
    year = datetime.date.today().year
    return year, range(year - MOON_YEARS_BEFORE, year + MOON_YEARS_AFTER + 1)


def moon_path(year):
    return "moon-phases/" if year == datetime.date.today().year \
        else "moon-phases/{}/".format(year)


def moon_svg(pos, size):
    """The Moon at cycle position pos (0 new, 0.5 full). Twin of moonSvg() in
    docs/moon.js."""
    k = (1 - math.cos(2 * math.pi * pos)) / 2
    rx = abs(1 - 2 * k) * 10
    waxing = pos < 0.5
    term = 0 if waxing == (k < 0.5) else 1
    if k < 0.005:
        lit = ""
    elif k > 0.995:
        lit = '<circle class="moon-lit" cx="12" cy="12" r="10"/>'
    else:
        lit = ('<path class="moon-lit" d="M12 2A10 10 0 0 {} 12 22A{:.2f} 10 0 0 {} 12 2Z"/>'
               .format(1 if waxing else 0, rx, term))
    return ('<svg class="moon-svg" width="{0}" height="{0}" viewBox="0 0 24 24" aria-hidden="true">'
            '<circle class="moon-dark" cx="12" cy="12" r="10"/>{1}</svg>'.format(size, lit))


def moon_local(unix, lang):
    """datetime of unix in the page language's MOON_TZ zone."""
    _name, offset, eu = MOON_TZ[lang]
    if eu:
        offset = moon.eu_offset_hours(unix, offset)
    return datetime.datetime.fromtimestamp(unix + offset * 3600, datetime.timezone.utc)


def moon_day_time(unix, lang):
    """('26 October', '06:11') in the page language and zone."""
    dt = moon_local(unix, lang)
    return day_month(dt.strftime("%m-%d"), lang), dt.strftime("%H:%M")


def write_moon_data(phases, page_years):
    """docs/moon-data.js: the principal phase instants for docs/moon.js."""
    path = os.path.join(DOCS_DIR, "moon-data.js")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("// Generated by build_site.py (moon.py) — do not edit by hand.\n"
                 "window.MOON_YEARS = [{}, {}];\nwindow.MOON_PHASES = {};\n".format(
                     page_years[0], page_years[-1],
                     json.dumps([list(p) for p in phases], separators=(",", ":"))))
    print("wrote docs/moon-data.js ({} phases)".format(len(phases)))


def moon_year_rows(phases, year, lang):
    """Baked rows of the yearly table: one per lunation, from its new moon."""
    rows, row, last = [], None, -1
    for unix, q in phases:
        if moon_local(unix, lang).year != year:
            continue
        if row is None or q <= last:
            row = ["", "", "", ""]
            rows.append(row)
        day, time = moon_day_time(unix, lang)
        z = moon.zodiac_index(unix, q)
        row[q] = ('<span class="moon-year-date">{} {}</span> {}<span class="moon-zodiac">'
                  '<span class="moon-zodiac-sign">{}︎</span> {}</span>').format(
                      moon_svg(q / 4, 16), escape(day), time, ZODIAC_SIGNS[z],
                      escape(TR[lang]["zodiac"][z]))
        last = q
    return "\n".join("            <tr>{}</tr>".format(
        "".join("<td>{}</td>".format(c) for c in r)) for r in rows)


def moon_now_text(phases, lang):
    """'The Moon is now: Waxing gibbous. Next: Full moon on 26 October.' at
    build time, for the current year's page (moon.js replaces it)."""
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    past = [p for p in phases if p[0] <= now]
    upcoming = [p for p in phases if p[0] > now]
    if not past or not upcoming:
        return ""
    names = TR[lang]["moon_phases"]
    day, _time = moon_day_time(upcoming[0][0], lang)
    return tr_fmt(lang, "seo_moon_now", phase=names[past[-1][1] * 2 + 1],
                  next=names[upcoming[0][1] * 2], date=day)


def write_moon_pages():
    current, years = moon_years()
    phases = moon.phases(years[0] - 1, years[-1] + 1)
    write_moon_data(phases, years)
    for year in years:
        path = moon_path(year)
        for lang in LANGS:
            fields = dict(year=year)
            title = MOON_META["title" if year == current else "title_year"][lang].format(**fields)
            desc = MOON_META["desc"][lang].format(**fields)
            names = TR[lang]["moon_phases"]
            now_text = moon_now_text(phases, lang) if year == current else ""
            year_links = "\n".join(
                '        <a class="nearby-link" href="/{}"{}>{}</a>'.format(
                    moon_path(y), ' aria-current="page"' if y == year else "", y)
                for y in years)
            inner = """    <h1>{h1}</h1>
    <p class="subtitle">{intro}</p>
    <div id="moon-app" class="moon-top" data-year="{year}">
        <section class="moon-panel">
            <h2 id="moon-now-h2" class="moon-panel-h2">{now_h2}</h2>
            <div id="moon-now" class="moon-now"><p>{now_text}</p></div>
        </section>
        <section class="moon-panel">
            <h2 class="moon-panel-h2" data-i18n="moon_cal_h2">Moon calendar by day</h2>
            <div id="moon-cal"></div>
            <p class="tip" data-i18n="moon_cal_tip">Tap a day to see the Moon at noon that day.</p>
        </section>
    </div>
    <h2 data-i18n="moon_cycle_h2">Phases of the current lunar cycle</h2>
    <div id="moon-cycle" class="moon-cards"></div>
    <h2 data-i18n="moon_days_h2">The next 5 days</h2>
    <div id="moon-days" class="moon-cards"></div>
    <section id="moon-year">
    <h2>{year_h2}</h2>
    <div class="nearby-links moon-year-links">
{year_links}
    </div>
    <p class="tip" id="moon-year-note">{tz_note}</p>
    <div class="table-scroll">
    <table class="month-table moon-table">
        <thead><tr>{head}</tr></thead>
        <tbody>
{rows}
        </tbody>
    </table>
    </div>
    </section>
    <section class="moon-about">
    <h2>{about_h2}</h2>
    <p class="location-description">{about}</p>
    </section>
{browse}
    <script src="/moon-data.js"></script>
    <script src="/moon.js"></script>""".format(
                h1=escape(MOON_META["h1"][lang].format(**fields)),
                intro=escape(tr_fmt(lang, "seo_moon_intro", year=year)),
                year=year, now_h2=escape(TR[lang]["moon_now"]), now_text=escape(now_text),
                year_h2=escape(tr_fmt(lang, "moon_year_h2", year=year)),
                year_links=year_links,
                tz_note=escape(tr_fmt(lang, "moon_tz_note", tz=MOON_TZ[lang][0])),
                head="".join("<th>{} {}</th>".format(moon_svg(q / 4, 16), escape(names[q * 2]))
                             for q in range(4)),
                rows=moon_year_rows(phases, year, lang),
                about_h2=escape(TR[lang]["seo_moon_about_h2"]),
                about=escape(TR[lang]["seo_moon_about"]),
                browse=browse_links_html(lang))
            crumbs = [(TR[lang]["crumb_home"], url_for("", lang)),
                      (TR[lang]["nav_moon"], url_for(moon_path(current), lang))]
            if year != current:
                crumbs.append((str(year), url_for(path, lang)))
            write_simple_page(lang, path, title, desc, crumbs, inner)
        print("wrote moon phase page {} x {} languages".format(year, len(LANGS)))


def write_hub(stats):
    for lang in LANGS:
        sections = []
        for country, group in locations_by_country():
            cards = []
            for loc in group:
                cards.append(
                    # Short town name only — the country is the section heading.
                    # data-search holds every language so search works either way.
                    # The temperature badge is baked in; map.js refreshes it.
                    '            <a class="hub-card" href="/{slug}/" data-loc="{slug}" data-search="{search}">\n'
                    '                <span class="hub-flag">{flag}</span>\n'
                    '                <span class="hub-name">{name}</span>\n'
                    '                <span class="hub-temp"{temp_style}>{temp}</span>\n'
                    '            </a>'.format(
                        slug=loc["slug"], flag=loc["flag"],
                        search=escape(" ".join(
                            [loc_name(loc, l) for l in LANGS] + [loc["slug"]]).lower()),
                        name=escape(loc_name(loc, lang)), **hub_temp(stats.get(loc["slug"]))))
            sections.append(
                '        <section class="hub-section">\n'
                '        <h3 class="hub-country"><a href="/{country}/" data-i18n="country_{country}">{label}</a></h3>\n'
                '        <div class="hub-grid">\n{cards}\n        </div>\n'
                '        </section>'.format(
                    country=country, label=escape(country_name(group[0], lang)),
                    cards="\n".join(cards)))
        website = {"@context": "https://schema.org", "@type": "WebSite",
                   "name": TR[lang]["hub_h1"], "url": url_for("", lang),
                   "inLanguage": lang, "description": HUB_META["desc"][lang]}
        item_list = {"@context": "https://schema.org", "@type": "ItemList",
                     "name": TR[lang]["hub_pick"],
                     "itemListElement": [
                         {"@type": "ListItem", "position": i + 1,
                          "name": loc_full(loc, lang),
                          "url": url_for(site_path(loc["slug"], "index.html"), lang)}
                         for i, loc in enumerate(
                             l for _, group in locations_by_country() for l in group)]}
        head = build_head(HUB_META["title"][lang], HUB_META["desc"][lang],
                          "", lang, structured=[website, item_list],
                          image=og_image_url("site")).replace("{slug}", "burgas")
        body = """<body>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
      integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"
      integrity="sha256-YU3qCpj/P06tdPBJGPax0bm6Q1wltfwjsho5TR4+TYc=" crossorigin="" />
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"
      integrity="sha256-Hk4dIpcqOSb0hZjgyvFOP+cEmDXUKKNE/tT542ZbNQg=" crossorigin=""></script>

{nav}
<div class="container">
    <h1 data-i18n="hub_h1">Black Sea Water Temperature</h1>
    <p class="subtitle" data-i18n="hub_subtitle">Live and historical sea surface temperature for Bulgaria's Black Sea coast</p>

    <h2 data-i18n="hub_map">Current water temperature</h2>
    <div id="hub-summary" class="hub-summary"></div>
    <div id="map"></div>

    <h2 data-i18n="hub_pick">Choose a location</h2>
    <div class="hub-tools">
        <input type="search" id="hub-search" class="hub-search" placeholder="{search_ph}" autocomplete="off">
        <label class="hub-sort"><input type="checkbox" id="hub-sort"> <span data-i18n="hub_sort_temp">Sort by temperature</span></label>
    </div>
    <div id="hub-locations">
{sections}
    </div>
    <p id="hub-no-match" class="gallery-empty" data-i18n="hub_no_match" hidden>No locations match your search.</p>
{browse}
</div>

{footer}
<script src="/map.js"></script>
</body>
</html>
""".format(nav=SITE_NAV, footer=SITE_FOOTER, sections="\n".join(sections),
           search_ph=escape(TR[lang]["hub_search"]), browse=browse_links_html(lang))
        body = prefix_links(body, lang)
        page = version_assets(bake(head + body, lang))
        out_dir = out_dir_for(lang)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page)
        print("wrote docs/{}index.html (hub)".format(
            lang + "/" if lang != DEFAULT_LANG else ""))


def write_compare_locations():
    """Global (non per-location) page that overlays multiple towns on one chart."""
    for lang in LANGS:
        head = build_head(COMPARE_LOCATIONS_META["title"][lang],
                          COMPARE_LOCATIONS_META["desc"][lang],
                          "compare-locations.html", lang,
                          image=og_image_url("site")).replace("{slug}", "burgas")
        body = template_body("compare-locations.html")
        body = with_plotly(prefix_links(body, lang))
        page = version_assets(bake(head + body, lang))
        out_dir = out_dir_for(lang)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "compare-locations.html"), "w",
                  encoding="utf-8") as fh:
            fh.write(page)
        print("wrote docs/{}compare-locations.html".format(
            lang + "/" if lang != DEFAULT_LANG else ""))


# Per-location pages whose rendered content follows the data (lastmod = date of
# the latest reading). Gallery and weather pages are left without a lastmod:
# their HTML doesn't change with the sea temperature data.
DATA_PAGES = ("index.html", "compare.html", "heatmap.html", "stats.html")


def write_sitemap(stats):
    """Generate docs/sitemap.xml from LOCATIONS so it stays in sync with the
    actual pages. Every page is listed once per language, and each entry carries
    the bidirectional hreflang alternates Google recommends. URLs are produced
    by url_for(), the same helper used for each page's <link rel="canonical">,
    so the sitemap can never drift from the pages it lists. Google ignores
    changefreq/priority, so only <lastmod> is emitted."""
    dates = [st["date"][:10] for st in stats.values() if st]
    latest = max(dates) if dates else None
    paths = [("", latest)]
    for loc in LOCATIONS:
        st = stats.get(loc["slug"])
        for page_file, meta in PAGES.items():
            if meta.get("noindex"):
                continue
            lastmod = st["date"][:10] if st and page_file in DATA_PAGES else None
            paths.append((site_path(loc["slug"], page_file), lastmod))
    paths.append(("compare-locations.html", latest))
    # Country pages carry today's readings; month pages change with the data.
    paths.extend((country + "/", latest) for country, _ in locations_by_country())
    paths.extend((month_path(i), latest) for i in range(12))
    # The current year's moon page shows today's phase; other years are fixed.
    current, years = moon_years()
    paths.extend((moon_path(y), latest if y == current else None) for y in years)

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    count = 0
    for path, lastmod in paths:
        alternates = ['    <xhtml:link rel="alternate" hreflang="{}" href="{}"/>'.format(
            lang, escape(url_for(path, lang))) for lang in LANGS]
        alternates.append('    <xhtml:link rel="alternate" hreflang="x-default" href="{}"/>'
                          .format(escape(url_for(path, DEFAULT_LANG))))
        for lang in LANGS:
            count += 1
            lines.append("  <url>")
            lines.append("    <loc>{}</loc>".format(escape(url_for(path, lang))))
            lines.extend(alternates)
            if lastmod:
                lines.append("    <lastmod>{}</lastmod>".format(lastmod))
            lines.append("  </url>")
    lines.append("</urlset>")
    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote docs/sitemap.xml ({} urls)".format(count))


def write_404():
    """docs/404.html, served by GitHub Pages for any unknown path (so every
    link is root-absolute). One page for all languages: a heading per language
    and links to each language's hub."""
    head = build_head("404 — " + TR[DEFAULT_LANG]["notfound_h1"],
                      TR[DEFAULT_LANG]["notfound_text"], "404.html", DEFAULT_LANG,
                      noindex=True).replace("{slug}", "burgas")
    blocks = []
    for lang in LANGS:
        blocks.append(
            '    <section class="notfound" lang="{lang}">\n'
            '        <h2>{h}</h2>\n'
            '        <p>{text} <a href="{href}">{hub}</a></p>\n'
            '    </section>'.format(
                lang=lang, h=escape(TR[lang]["notfound_h1"]),
                text=escape(TR[lang]["notfound_text"]),
                href=lang_prefix(lang) + "/", hub=escape(TR[lang]["hub_h1"])))
    body = """<body>
<nav class="nav">
    <div class="nav-inner">
        <a class="nav-brand" href="/">{brand}</a>
        <div class="lang-switch"></div>
    </div>
</nav>

<div class="container">
    <h1>404</h1>
{blocks}
</div>
</body>
</html>
""".format(brand=escape(TR[DEFAULT_LANG]["nav_brand"]), blocks="\n".join(blocks))
    with open(os.path.join(DOCS_DIR, "404.html"), "w", encoding="utf-8") as fh:
        fh.write(version_assets(head + body))
    print("wrote docs/404.html")


def write_robots():
    """Generate docs/robots.txt; the Sitemap line stays tied to BASE_URL."""
    content = ("User-agent: *\n"
               "Allow: /\n\n"
               "Sitemap: {}/sitemap.xml\n".format(BASE_URL))
    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote docs/robots.txt")


def write_og_images(stats, force=False):
    """docs/og/<slug>.png + site.png: 1200x630 social preview cards with the
    town name and its monthly average water temperature as bars.

    Generated only when missing (or with --og): they change slowly, and
    regenerating them on every CI data update would bloat the repo. Needs
    Pillow, which CI doesn't install; without it this is a no-op and the pages
    reference whatever cards already exist."""
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Pillow not installed: skipping og images")
        return
    font_dir = "/usr/share/fonts/truetype/dejavu"
    try:
        def font(size, bold=True):
            return ImageFont.truetype(os.path.join(
                font_dir, "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"), size)
        font(10)
    except OSError:
        print("DejaVu fonts not found: skipping og images")
        return
    os.makedirs(OG_DIR, exist_ok=True)

    def rgb(temp):
        f = max(0.0, min(1.0, (temp - 4) / 24))
        return tuple(int(c * 255) for c in colorsys.hls_to_rgb((220 - f * 220) / 360, 0.47, 0.75))

    def card(name, title, subtitle, monthly):
        path = os.path.join(OG_DIR, name + ".png")
        if os.path.isfile(path) and not force:
            return
        img = Image.new("RGB", (1200, 630))
        draw = ImageDraw.Draw(img)
        top, bottom = (11, 79, 108), (2, 30, 44)
        for y in range(630):
            k = y / 629
            draw.line([(0, y), (1200, y)],
                      fill=tuple(int(a + (b - a) * k) for a, b in zip(top, bottom)))
        draw.text((70, 60), "BLACK SEA WATER TEMPERATURE", font=font(28), fill=(170, 211, 223))
        size = 92
        while font(size).getlength(title) > 1060 and size > 40:
            size -= 4
        draw.text((70, 105), title, font=font(size), fill=(255, 255, 255))
        draw.text((72, 115 + size + 10), subtitle, font=font(34, bold=False),
                  fill=(200, 225, 235))
        # Monthly averages: 12 bars on a 0-30 °C scale.
        base, scale, bar_w, gap, x0 = 560, 7, 64, 20, 70
        for i, value in enumerate(monthly):
            x = x0 + i * (bar_w + gap)
            if value is not None:
                h = max(4, int(value * scale))
                draw.rounded_rectangle([x, base - h, x + bar_w, base], radius=8, fill=rgb(value))
                label = "{:.0f}°".format(value)
                draw.text((x + bar_w / 2, base - h - 8), label, font=font(24),
                          fill=(255, 255, 255), anchor="ms")
            draw.text((x + bar_w / 2, base + 36), "JFMAMJJASOND"[i], font=font(24, bold=False),
                      fill=(170, 211, 223), anchor="ms")
        draw.text((1130, 60), "more.masoko.net", font=font(26, bold=False),
                  fill=(170, 211, 223), anchor="ra")
        img.save(path, optimize=True)
        print("wrote docs/og/{}.png".format(name))

    def monthly_of(sts):
        out = []
        for i in range(12):
            vals = [st["months"][i]["avg"] for st in sts if st and st["months"][i]]
            out.append(mean(vals) if vals else None)
        return out

    for loc in LOCATIONS:
        st = stats.get(loc["slug"])
        if st:
            card(loc["slug"], loc["name_en"], "{} · average by month, °C".format(
                TR["en"]["country_" + loc["country"]]), monthly_of([st]))
    card("site", "Black Sea", "{} beaches in {} countries · average by month, °C".format(
        len(LOCATIONS), len(list(locations_by_country()))), monthly_of(stats.values()))


def main():
    stats = load_all_stats()
    write_og_images(stats, force="--og" in sys.argv)
    write_i18n_js()
    write_locations_js()
    write_location_pages(stats)
    write_hub(stats)
    write_compare_locations()
    write_country_pages(stats)
    write_month_pages(stats)
    write_moon_pages()
    write_sitemap(stats)
    write_robots()
    write_404()


if __name__ == "__main__":
    main()
