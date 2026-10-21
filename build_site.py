# Static site generator for the Black Sea water temperature site.
#
# Reads the page templates in templates/*.html, the location list in
# locations.py and the translation dictionary in translations.json, and writes
# one SEO-distinct set of pages per location *per language* into docs/<slug>/
# (Bulgarian, the default) and docs/<lang>/<slug>/ (English, Russian, Turkish,
# Romanian), plus the generated docs/i18n.<lang>.js, docs/locations.js, the hub
# pages, sitemap.xml, robots.txt and 404.html.
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
import hashlib
import json
import math
import os
import re

from locations import LOCATIONS, COUNTRY_ORDER

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
}

with open(os.path.join(ROOT_DIR, "translations.json"), encoding="utf-8") as fh:
    TR = json.load(fh)

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
        "en": "Black Sea Water Temperature — Bulgaria, Turkey, Romania, Georgia, Russia",
        "bg": "Температура на водата в Черно море — България, Турция, Румъния, Грузия, Русия",
        "ru": "Температура воды в Черном море — Болгария, Турция, Румыния, Грузия, Россия",
        "tr": "Karadeniz Deniz Suyu Sıcaklığı — Bulgaristan, Türkiye, Romanya, Gürcistan, Rusya",
        "ro": "Temperatura apei Mării Negre — Bulgaria, Turcia, România, Georgia, Rusia",
    },
    "desc": {
        "en": ("Live and historical Black Sea water temperature for coastal towns across "
               "Bulgaria, Turkey, Romania, Georgia and Russia. Daily sea surface "
               "temperature, yearly comparisons, heatmaps and records."),
        "bg": ("Актуална и историческа температура на морската вода в Черно море за "
               "крайбрежни градове в България, Турция, Румъния, Грузия и Русия. Дневна "
               "температура, годишни сравнения, топлинни карти и рекорди."),
        "ru": ("Текущая и историческая температура воды в Черном море для прибрежных "
               "городов Болгарии, Турции, Румынии, Грузии и России. Ежедневная "
               "температура моря, сравнение по годам, тепловые карты и рекорды."),
        "tr": ("Bulgaristan, Türkiye, Romanya, Gürcistan ve Rusya'daki kıyı kasabaları "
               "için güncel ve geçmiş Karadeniz deniz suyu sıcaklığı. Günlük deniz "
               "sıcaklığı, yıllık karşılaştırmalar, ısı haritaları ve rekorlar."),
        "ro": ("Temperatura actuală și istorică a apei Mării Negre pentru localitățile "
               "de pe coastă din Bulgaria, Turcia, România, Georgia și Rusia. "
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
               "Turkey, Romania, Georgia and Russia on a single chart — overlay any "
               "locations across the years and on a Jan–Dec seasonal axis."),
        "bg": ("Сравнете температурата на морската вода в Черно море между крайбрежни "
               "градове в България, Турция, Румъния, Грузия и Русия на една графика — "
               "наложете локации през годините и на сезонна ос януари–декември."),
        "ru": ("Сравните температуру воды в Черном море в прибрежных городах Болгарии, "
               "Турции, Румынии, Грузии и России на одном графике — за все годы и на "
               "сезонной оси январь–декабрь."),
        "tr": ("Bulgaristan, Türkiye, Romanya, Gürcistan ve Rusya'daki kıyı "
               "kasabalarının Karadeniz su sıcaklığını tek grafikte karşılaştırın — "
               "yıllar boyunca ve Ocak–Aralık mevsim ekseninde."),
        "ro": ("Comparați temperatura apei Mării Negre în localitățile de pe coastă din "
               "Bulgaria, Turcia, România, Georgia și Rusia pe un singur grafic — de-a "
               "lungul anilor și pe o axă sezonieră ianuarie–decembrie."),
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


def build_head(title, description, path, lang, plotly=True, structured=(),
               noindex=False):
    """Generated <head> shared by every page; the SEO fields and language vary.

    path is the language-neutral site path ('' for the hub, 'burgas/', ...);
    plotly=False omits the ~1 MB Plotly bundle for pages with no charts
    (e.g. the photo gallery); structured is a list of JSON-LD objects;
    noindex=True (the 404 page) drops canonical/hreflang/og tags."""
    t = escape(title)
    d = escape(description)
    plotly_tag = ('    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>\n'
                  if plotly else "")
    canonical = escape(url_for(path, lang))
    if noindex:
        seo = '    <meta name="robots" content="noindex">\n'
    else:
        seo = ('    <link rel="canonical" href="{canonical}">\n'
               '{alternates}'
               '    <meta property="og:type" content="website">\n'
               '    <meta property="og:title" content="{title}">\n'
               '    <meta property="og:description" content="{desc}">\n'
               '    <meta property="og:url" content="{canonical}">\n'
               '    <meta property="og:locale" content="{og_locale}">\n'
               '{og_alternates}'
               '    <meta name="twitter:card" content="summary">\n'
               '{ld}').format(
                   canonical=canonical, alternates=hreflang_links(path),
                   title=t, desc=d, og_locale=OG_LOCALE[lang],
                   og_alternates="".join(
                       '    <meta property="og:locale:alternate" content="{}">\n'
                       .format(OG_LOCALE[other]) for other in LANGS if other != lang),
                   ld="".join(json_ld(obj) for obj in structured))
    return """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">
{seo}{plotly}    <link rel="icon" href="/favicon.svg">
    <link rel="stylesheet" href="/style.css">
    <script src="/i18n.{lang}.js"></script>
    <script src="/locations.js"></script>
    <script>window.LOCATION_ID = '{slug}'; window.LANG = '{lang}'; window.LANG_PREFIX = '{prefix}';</script>
    <script defer src="https://m.masoko.net/core-util" data-website-id="a6c69550-2eed-4ba4-8568-57dc4c66e466"></script>
</head>
""".format(lang=lang, title=t, desc=d, seo=seo, slug="{slug}",
           prefix=lang_prefix(lang), plotly=plotly_tag)


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

    return TRANSLATABLE_RE.sub(repl, html)


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
        lic = ('<a href="{url}" target="_blank" rel="noopener nofollow">{name}</a>'
               .format(url=license_url, name=license_name)) if license_name else ""
        items.append(
            '<figure class="gallery-item">'
            '<a class="gallery-link" href="{full}" data-full="{full}" '
            'data-page="{page}" data-artist="{artist}">'
            '<img src="{thumb}" alt="{title}" loading="lazy"{dims}></a>'
            '<figcaption class="gallery-caption">© {artist}{sep}{lic}</figcaption>'
            '</figure>'.format(
                full=full, page=page, artist=artist, thumb=thumb, title=title,
                dims=dims, sep=" · " if lic else "", lic=lic))
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
                       "min": min(raw), "max": max(raw)})
    return {
        "temp": last_temp, "date": last_dt,
        "first": rows[0][0], "norm": norm, "norm_years": len(prior_years),
        "months": months,
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
    return items


def seo_content_html(loc, lang, st):
    """Monthly climatology table + FAQ appended to the dashboard."""
    if not st:
        return ""
    rows = []
    for i, m in enumerate(st["months"]):
        if not m:
            continue
        rows.append(
            '            <tr><th scope="row">{month}</th><td>{avg}°C</td>'
            '<td>{min}°C</td><td>{max}°C</td></tr>'.format(
                month=escape(month_name(lang, i)), avg=fmt_temp(m["avg"]),
                min=fmt_temp(m["min"][0]), max=fmt_temp(m["max"][0])))
    faq = "\n".join(
        '        <div class="faq-item">\n'
        '            <h3>{q}</h3>\n'
        '            <p>{a}</p>\n'
        '        </div>'.format(q=escape(q), a=escape(a))
        for q, a in faq_items(loc, lang, st))
    return """    <section class="month-climate">
    <h2>{h2}</h2>
    <p class="tip">{note}</p>
    <div class="table-scroll">
    <table class="month-table">
        <thead><tr><th scope="col">{c_month}</th><th scope="col">{c_avg}</th><th scope="col">{c_min}</th><th scope="col">{c_max}</th></tr></thead>
        <tbody>
{rows}
        </tbody>
    </table>
    </div>
    </section>

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
        rows="\n".join(rows), faq_h2=escape(TR[lang]["faq_h2"]), faq=faq)


def distance_km(a, b):
    """Great-circle distance between two locations (haversine)."""
    lat1, lon1, lat2, lon2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(h))


NEARBY_COUNT = 6
# The main container's closing tag, right before the footer, in every template.
CONTAINER_END_RE = re.compile(r'</div>\s*<footer class="footer">')


def nearby_html(loc, lang, page_file):
    """Static links to the closest towns' page of the same kind, so every town
    page is reachable by crawlers from its neighbours, not only from the hub
    (the location dropdown is built client-side)."""
    others = sorted(((distance_km(loc, o), o) for o in LOCATIONS if o is not loc),
                    key=lambda pair: pair[0])
    page = "" if page_file == "index.html" else page_file
    links = "\n".join(
        '        <a class="nearby-link" href="/{slug}/{page}">{flag} {name} '
        '<span class="nearby-km">{km} km</span></a>'.format(
            slug=o["slug"], page=page, flag=o["flag"], name=escape(loc_name(o, lang)),
            km=int(round(km)))
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
    """[(name, absolute url)]: hub › town › page."""
    items = [(TR[lang]["crumb_home"], url_for("", lang)),
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
            "geo": {"@type": "GeoCoordinates", "latitude": loc["lat"],
                    "longitude": loc["lon"]}},
        "variableMeasured": {"@type": "PropertyValue",
                             "name": "Sea surface temperature", "unitText": "°C"},
        "distribution": [{"@type": "DataDownload", "encodingFormat": "text/csv",
                          "contentUrl": CSV_BASE + loc["csv_file"]}],
    }
    if st:
        ld["temporalCoverage"] = "{}/{}".format(st["first"][:10], st["date"][:10])
    return ld


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
                    faq = faq_items(loc, lang, st)
                    if faq:
                        structured.append(faq_ld(faq))
                    body = (body.replace("{today}", today_html(loc, lang, st))
                                .replace("{seo_content}", seo_content_html(loc, lang, st)))
                if page_file == "gallery.html":
                    body = body.replace("{gallery}", gallery_markup(
                        galleries.get(slug, []), loc_full(loc, lang)))
                body = body.replace('<div class="container">',
                                    '<div class="container">\n'
                                    + breadcrumb_html(crumbs, lang), 1)
                # Nearby links go at the end of the main container.
                body = CONTAINER_END_RE.sub(
                    lambda m: nearby_html(loc, lang, page_file) + m.group(0), body, 1)
                body = prefix_links(body, lang)
                head = build_head(title, desc, path, lang,
                                  plotly=meta.get("plotly", True),
                                  structured=structured)
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
            'lat: {lat}, lon: {lon}, country: "{country}" }},'.format(
                slug=loc["slug"], csv=loc["csv_file"],
                key=i18n_key(loc["slug"]), flag=loc["flag"],
                lat=loc["lat"], lon=loc["lon"], country=loc["country"]))
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
                '        <h3 class="hub-country" data-i18n="country_{country}">{label}</h3>\n'
                '        <div class="hub-grid">\n{cards}\n        </div>\n'
                '        </section>'.format(
                    country=country, label=escape(country_name(group[0], lang)),
                    cards="\n".join(cards)))
        website = {"@context": "https://schema.org", "@type": "WebSite",
                   "name": TR[lang]["hub_h1"], "url": url_for("", lang),
                   "inLanguage": lang, "description": HUB_META["desc"][lang]}
        head = build_head(HUB_META["title"][lang], HUB_META["desc"][lang],
                          "", lang, structured=[website]).replace("{slug}", "burgas")
        body = """<body>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
      integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"
      integrity="sha256-YU3qCpj/P06tdPBJGPax0bm6Q1wltfwjsho5TR4+TYc=" crossorigin="" />
<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"
      integrity="sha256-Hk4dIpcqOSb0hZjgyvFOP+cEmDXUKKNE/tT542ZbNQg=" crossorigin=""></script>

<nav class="nav">
    <div class="nav-inner">
        <a class="nav-brand" href="/" data-i18n="nav_brand">🌊 Black Sea Temp</a>
        <ul class="nav-links">
            <li><a href="/burgas/" data-i18n="nav_dashboard">Dashboard</a></li>
            <li><a href="/burgas/compare.html" data-i18n="nav_compare">Compare Years</a></li>
            <li><a href="/burgas/heatmap.html" data-i18n="nav_heatmap">Heatmap</a></li>
            <li><a href="/burgas/stats.html" data-i18n="nav_stats">Statistics</a></li>
            <li><a href="/burgas/gallery.html" data-i18n="nav_gallery">Photos</a></li>
            <li><a href="/compare-locations.html" data-i18n="nav_comparelocations">Compare Locations</a></li>
        </ul>
        <div class="lang-switch"></div>
    </div>
</nav>

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
</div>

<footer class="footer">
    <span data-i18n="footer_title">Black Sea Water Temperature</span>
    <a href="https://github.com/hjelev/Black_Sea_water_temperature" target="_blank" rel="noopener">GitHub</a>
    <a href="https://masoko.net" target="_blank" rel="noopener">masoko.net</a>
</footer>

<script src="/map.js"></script>
</body>
</html>
""".format(sections="\n".join(sections), search_ph=escape(TR[lang]["hub_search"]))
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
                          "compare-locations.html", lang).replace("{slug}", "burgas")
        body = template_body("compare-locations.html")
        body = prefix_links(body, lang)
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
        for page_file in PAGES:
            lastmod = st["date"][:10] if st and page_file in DATA_PAGES else None
            paths.append((site_path(loc["slug"], page_file), lastmod))
    paths.append(("compare-locations.html", latest))

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
                      plotly=False, noindex=True).replace("{slug}", "burgas")
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


def main():
    stats = load_all_stats()
    write_i18n_js()
    write_locations_js()
    write_location_pages(stats)
    write_hub(stats)
    write_compare_locations()
    write_sitemap(stats)
    write_robots()
    write_404()


if __name__ == "__main__":
    main()
