# Static site generator for the Black Sea water temperature site.
#
# Reads the page templates in templates/*.html, the location list in
# locations.py and the translation dictionary in translations.json, and writes
# one SEO-distinct set of pages per location *per language* into docs/<slug>/
# (Bulgarian, the default) and docs/en/<slug>/ (English), plus the generated
# docs/i18n.js, docs/locations.js and the root hub pages.
#
# All static text is baked into the HTML at build time (the data-i18n
# placeholders in the templates are filled per language), so search engines see
# fully translated pages. docs/i18n.js still ships the dictionary for dynamic
# content rendered client-side (charts, dropdowns, map popups); the page's
# language is fixed via window.LANG injected in <head>.
#
# Each page gets its own URL, <title>, meta description, canonical link and
# hreflang alternates so search engines index every town separately in both
# languages.
#
#   python3 build_site.py
#
# Run locally whenever templates/, locations.py, translations.json or the page
# metadata change, then commit the regenerated docs/. Not run in CI (data loads
# client-side from the csv files; the html is static).
#
# Python 3.7+ , standard library only.
import json
import os
import re

from locations import LOCATIONS, COUNTRY_ORDER

BASE_URL = "https://more.masoko.net"
ROOT_DIR = os.path.dirname(__file__)
DOCS_DIR = os.path.join(ROOT_DIR, "docs")
TEMPLATES_DIR = os.path.join(ROOT_DIR, "templates")

LANGS = ("bg", "en")  # bg first: it is the default language at the site root

with open(os.path.join(ROOT_DIR, "translations.json"), encoding="utf-8") as fh:
    TR = json.load(fh)

# Per-page SEO metadata, per language. {loc} = town name, {country} = country
# name (English or Bulgarian to match the page language), {year} = first data
# year.
PAGES = {
    "index.html": {
        "title": {
            "en": "{loc} Sea Water Temperature — Live Black Sea Data",
            "bg": "Температура на морската вода в {loc} — Черно море на живо",
        },
        "desc": {
            "en": ("Live and historical Black Sea water temperature at {loc}, "
                   "{country}. Daily sea surface temperature since {year}, with a "
                   "30-day trend and full history charts."),
            "bg": ("Актуална и историческа температура на морската вода в Черно "
                   "море при {loc}, {country}. Дневна температура на морската "
                   "повърхност от {year} г., с 30-дневна тенденция и графики с "
                   "пълната история."),
        },
    },
    "compare.html": {
        "title": {
            "en": "Compare Years — {loc} Black Sea Water Temperature",
            "bg": "Сравнение по години — температура на водата в {loc}",
        },
        "desc": {
            "en": ("Compare Black Sea water temperature at {loc}, {country} across "
                   "years on a Jan–Dec axis to spot seasonal patterns and warming "
                   "trends."),
            "bg": ("Сравнете температурата на морската вода в Черно море при "
                   "{loc}, {country} по години върху ос януари–декември, за да "
                   "откриете сезонни модели и тенденции на затопляне."),
        },
    },
    "heatmap.html": {
        "title": {
            "en": "Monthly Heatmap — {loc} Black Sea Water Temperature",
            "bg": "Месечна топлинна карта — температура на водата в {loc}",
        },
        "desc": {
            "en": ("Monthly Black Sea water temperature heatmap for {loc}, "
                   "{country} — average sea surface temperature per month across "
                   "every recorded year."),
            "bg": ("Месечна топлинна карта на температурата на морската вода при "
                   "{loc}, {country} — средна температура на морската повърхност "
                   "по месеци за всяка записана година."),
        },
    },
    "stats.html": {
        "title": {
            "en": "Statistics & Records — {loc} Black Sea Water Temperature",
            "bg": "Статистика и рекорди — температура на водата в {loc}",
        },
        "desc": {
            "en": ("All-time records and annual statistics for Black Sea water "
                   "temperature at {loc}, {country} — hottest and coldest readings, "
                   "yearly min/avg/max and the long-term trend."),
            "bg": ("Рекорди и годишна статистика за температурата на морската "
                   "вода в Черно море при {loc}, {country} — най-високи и "
                   "най-ниски стойности, годишни мин/ср/макс и дългосрочната "
                   "тенденция."),
        },
    },
    "gallery.html": {
        "title": {
            "en": "Photos — {loc} Black Sea Coast",
            "bg": "Снимки — {loc} на Черноморието",
        },
        "desc": {
            "en": ("Photos of {loc}, {country} on the Black Sea coast, sourced from "
                   "Wikimedia Commons — beaches, harbour and seaside views."),
            "bg": ("Снимки на {loc}, {country} по Черноморското крайбрежие от "
                   "Wikimedia Commons — плажове, пристанище и морски гледки."),
        },
        "plotly": False,  # photo page has no charts; skip the ~1 MB Plotly bundle
    },
}

HUB_META = {
    "title": {
        "en": "Black Sea Water Temperature — Bulgaria, Turkey, Romania, Georgia, Russia",
        "bg": "Температура на водата в Черно море — България, Турция, Румъния, Грузия, Русия",
    },
    "desc": {
        "en": ("Live and historical Black Sea water temperature for coastal towns across "
               "Bulgaria, Turkey, Romania, Georgia and Russia. Daily sea surface "
               "temperature, yearly comparisons, heatmaps and records."),
        "bg": ("Актуална и историческа температура на морската вода в Черно море за "
               "крайбрежни градове в България, Турция, Румъния, Грузия и Русия. Дневна "
               "температура, годишни сравнения, топлинни карти и рекорди."),
    },
}

COMPARE_LOCATIONS_META = {
    "title": {
        "en": "Compare Locations — Black Sea Water Temperature",
        "bg": "Сравнение на локации — температура на водата в Черно море",
    },
    "desc": {
        "en": ("Compare Black Sea water temperature across coastal towns in Bulgaria, "
               "Turkey, Romania, Georgia and Russia on a single chart — overlay any "
               "locations across the years and on a Jan–Dec seasonal axis."),
        "bg": ("Сравнете температурата на морската вода в Черно море между крайбрежни "
               "градове в България, Турция, Румъния, Грузия и Русия на една графика — "
               "наложете локации през годините и на сезонна ос януари–декември."),
    },
}

OG_LOCALE = {"bg": "bg_BG", "en": "en_US"}


def i18n_key(slug):
    return "loc_" + slug.replace("-", "")


def loc_name(loc, lang):
    return loc["name_bg"] if lang == "bg" else loc["name_en"]


def country_name(loc, lang):
    return loc["country_bg"] if lang == "bg" else loc["country_en"]


def locations_by_country():
    """Yield (country_slug, [locations]) in COUNTRY_ORDER, skipping empty groups."""
    for country in COUNTRY_ORDER:
        group = [loc for loc in LOCATIONS if loc["country"] == country]
        if group:
            yield country, group


def escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def url_for(path, lang):
    """Absolute URL for a site path ('', 'burgas/', 'burgas/compare.html', ...).
    English pages live under the /en/ prefix; Bulgarian is the site root."""
    prefix = "/en" if lang == "en" else ""
    return "{}{}/{}".format(BASE_URL, prefix, path)


def hreflang_links(path):
    """hreflang alternates for one page: bg (default, x-default) + en."""
    bg_url = escape(url_for(path, "bg"))
    en_url = escape(url_for(path, "en"))
    return ('    <link rel="alternate" hreflang="bg" href="{bg}">\n'
            '    <link rel="alternate" hreflang="en" href="{en}">\n'
            '    <link rel="alternate" hreflang="x-default" href="{bg}">\n'
            .format(bg=bg_url, en=en_url))


def build_head(title, description, path, lang, plotly=True):
    """Generated <head> shared by every page; the SEO fields and language vary.

    path is the language-neutral site path ('' for the hub, 'burgas/', ...);
    plotly=False omits the ~1 MB Plotly bundle for pages with no charts
    (e.g. the photo gallery)."""
    t = escape(title)
    d = escape(description)
    plotly_tag = ('    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>\n'
                  if plotly else "")
    canonical = escape(url_for(path, lang))
    prefix = "/en" if lang == "en" else ""
    return """<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{canonical}">
{alternates}    <meta property="og:type" content="website">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:url" content="{canonical}">
    <meta property="og:locale" content="{og_locale}">
    <meta name="twitter:card" content="summary">
{plotly}    <link rel="icon" href="/favicon.svg">
    <link rel="stylesheet" href="/style.css">
    <script src="/i18n.js"></script>
    <script src="/locations.js"></script>
    <script>window.LOCATION_ID = '{slug}'; window.LANG = '{lang}'; window.LANG_PREFIX = '{prefix}';</script>
    <script defer src="https://m.masoko.net/core-util" data-website-id="a6c69550-2eed-4ba4-8568-57dc4c66e466"></script>
</head>
""".format(lang=lang, title=t, desc=d, canonical=canonical,
           alternates=hreflang_links(path), og_locale=OG_LOCALE[lang],
           slug="{slug}", prefix=prefix, plotly=plotly_tag)


# Matches a leaf element carrying data-i18n="key" or data-i18n-html="key".
# Every translatable element in the templates holds plain text only (no child
# tags), so [^<]* is safe for the current content.
TRANSLATABLE_RE = re.compile(
    r'(<(\w+)[^>]*\bdata-i18n(-html)?="([^"]+)"[^>]*>)([^<]*)(</\2>)')


def bake(html, lang, loc=None):
    """Fill every data-i18n placeholder with the translated text for lang.

    The data-i18n attributes are kept in the output as provenance; the runtime
    no longer translates static text. Elements flagged data-i18n-loc get the
    ' for <Town, Country>' suffix appended (translated), mirroring the old
    client-side locSuffix()."""
    tr = TR[lang]

    def repl(m):
        open_tag, _tag, is_html, key, _old, close_tag = m.groups()
        val = tr.get(key, TR["en"].get(key, key))
        if not is_html:
            val = escape(val)
        if "data-i18n-loc" in open_tag and loc is not None:
            val += escape(" {} {}".format(tr["loc_connector"],
                                          tr[i18n_key(loc["slug"])]))
        return open_tag + val + close_tag

    return TRANSLATABLE_RE.sub(repl, html)


def prefix_links(body):
    """Rewrite root-absolute page links for the English tree (/x → /en/x).

    Applied to page bodies only: relative links (index.html, ...) already stay
    inside /en/<slug>/, script/css assets use src= or absolute URLs, and the
    <head> is built with the right URLs directly."""
    return body.replace('href="/', 'href="/en/')


def template_body(page_file):
    """Return everything after </head> from a template, with asset paths fixed."""
    with open(os.path.join(TEMPLATES_DIR, page_file), encoding="utf-8") as fh:
        html = fh.read()
    body = html[html.index("</head>") + len("</head>"):]
    # data.js lives at the site root, not in the per-location folder.
    body = body.replace('src="data.js"', 'src="/data.js"')
    return body


def load_galleries():
    """Per-location Commons photos cached by fetch_galleries.py. Optional: if the
    file is missing the gallery pages just render an empty-state message."""
    path = os.path.join(DOCS_DIR, "galleries.json")
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (FileNotFoundError, ValueError):
        return {}


def gallery_markup(images):
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
        title = escape(im.get("title") or "")
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


def site_path(slug, page_file):
    """Language-neutral path of a per-location page, as used in URLs."""
    if page_file == "index.html":
        return "{}/".format(slug)
    return "{}/{}".format(slug, page_file)


def out_dir_for(lang, *parts):
    base = DOCS_DIR if lang == "bg" else os.path.join(DOCS_DIR, "en")
    return os.path.join(base, *parts)


def write_location_pages():
    bodies = {page: template_body(page) for page in PAGES}
    galleries = load_galleries()
    for loc in LOCATIONS:
        slug = loc["slug"]
        year = loc["start_date"][:4]
        for lang in LANGS:
            out_dir = out_dir_for(lang, slug)
            os.makedirs(out_dir, exist_ok=True)
            for page_file, meta in PAGES.items():
                fields = dict(loc=loc_name(loc, lang),
                              country=country_name(loc, lang), year=year)
                title = meta["title"][lang].format(**fields)
                desc = meta["desc"][lang].format(**fields)
                head = build_head(title, desc, site_path(slug, page_file), lang,
                                  plotly=meta.get("plotly", True))
                body = bodies[page_file]
                if page_file == "gallery.html":
                    body = body.replace(
                        "{gallery}", gallery_markup(galleries.get(slug, [])))
                if lang == "en":
                    body = prefix_links(body)
                page = bake(head.replace("{slug}", slug) + body, lang, loc)
                with open(os.path.join(out_dir, page_file), "w", encoding="utf-8") as fh:
                    fh.write(page)
        print("{}: wrote {} pages x {} languages to docs/[en/]{}/".format(
            loc["name_en"], len(PAGES), len(LANGS), slug))


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


def write_i18n_js():
    """Regenerate docs/i18n.js from translations.json + the runtime template.

    translations.json is the single source of truth for every UI string; the
    browser gets it embedded as const I18N for the dynamic (chart/dropdown/map)
    strings, and build_site.py bakes the static page text from the same data."""
    en_keys, bg_keys = set(TR["en"]), set(TR["bg"])
    if en_keys != bg_keys:
        print("WARNING: translations.json en/bg key mismatch: {}".format(
            sorted(en_keys ^ bg_keys)))
    with open(os.path.join(TEMPLATES_DIR, "i18n_runtime.js"), encoding="utf-8") as fh:
        runtime = fh.read()
    header = ("// Generated by build_site.py from translations.json + "
              "templates/i18n_runtime.js — do not edit by hand.\n")
    body = "const I18N = {};\n\n".format(
        json.dumps(TR, ensure_ascii=False, indent=2))
    with open(os.path.join(DOCS_DIR, "i18n.js"), "w", encoding="utf-8") as fh:
        fh.write(header + body + runtime)
    print("wrote docs/i18n.js ({} keys per language)".format(len(en_keys)))


def write_hub():
    for lang in LANGS:
        sections = []
        for country, group in locations_by_country():
            cards = []
            for loc in group:
                cards.append(
                    '            <a class="hub-card" href="/{slug}/" data-loc="{slug}">\n'
                    '                <span class="hub-flag">{flag}</span>\n'
                    '                <span class="hub-temp"></span>\n'
                    '                <span class="hub-name" data-i18n="{key}">{name}</span>\n'
                    '            </a>'.format(
                        slug=loc["slug"], flag=loc["flag"],
                        key=i18n_key(loc["slug"]),
                        name=escape(loc["name_en"] + ", " + loc["country_en"])))
            sections.append(
                '        <h3 class="hub-country" data-i18n="country_{country}">{label}</h3>\n'
                '        <div class="hub-grid">\n{cards}\n        </div>'.format(
                    country=country, label=escape(group[0]["country_en"]),
                    cards="\n".join(cards)))
        head = build_head(HUB_META["title"][lang], HUB_META["desc"][lang],
                          "", lang).replace("{slug}", "burgas")
        body = """<body>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
      integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
      integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>

<nav class="nav">
    <div class="nav-inner">
        <a class="nav-brand" href="/" data-i18n="nav_brand">🌊 Black Sea Temp</a>
        <ul class="nav-links">
            <li><a href="/burgas/index.html" data-i18n="nav_dashboard">Dashboard</a></li>
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
    <div id="map"></div>

    <h2 data-i18n="hub_pick">Choose a location</h2>
{sections}
</div>

<footer class="footer">
    <span data-i18n="footer_title">Black Sea Water Temperature</span>
    <a href="https://github.com/hjelev/Black_Sea_water_temperature" target="_blank" rel="noopener">GitHub</a>
    <a href="https://masoko.net" target="_blank" rel="noopener">masoko.net</a>
</footer>

<script src="/map.js"></script>
</body>
</html>
""".format(sections="\n".join(sections))
        if lang == "en":
            body = prefix_links(body)
        page = bake(head + body, lang)
        out_dir = out_dir_for(lang)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "index.html"), "w", encoding="utf-8") as fh:
            fh.write(page)
        print("wrote docs/{}index.html (hub, {})".format(
            "en/" if lang == "en" else "", lang))


def write_compare_locations():
    """Global (non per-location) page that overlays multiple towns on one chart."""
    for lang in LANGS:
        head = build_head(COMPARE_LOCATIONS_META["title"][lang],
                          COMPARE_LOCATIONS_META["desc"][lang],
                          "compare-locations.html", lang).replace("{slug}", "burgas")
        body = template_body("compare-locations.html")
        if lang == "en":
            body = prefix_links(body)
        page = bake(head + body, lang)
        out_dir = out_dir_for(lang)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "compare-locations.html"), "w",
                  encoding="utf-8") as fh:
            fh.write(page)
        print("wrote docs/{}compare-locations.html".format(
            "en/" if lang == "en" else ""))


def write_sitemap():
    """Generate docs/sitemap.xml from LOCATIONS so it stays in sync with the
    actual pages. Every page is listed once per language, and each entry carries
    the bidirectional hreflang alternates Google recommends. URLs are produced
    by url_for(), the same helper used for each page's <link rel="canonical">,
    so the sitemap can never drift from the pages it lists."""
    paths = [("", "1.0")]
    for loc in LOCATIONS:
        for page_file in PAGES:
            priority = "0.8" if page_file == "index.html" else "0.6"
            paths.append((site_path(loc["slug"], page_file), priority))
    paths.append(("compare-locations.html", "0.7"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
             '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    count = 0
    for path, priority in paths:
        bg_url = escape(url_for(path, "bg"))
        en_url = escape(url_for(path, "en"))
        for url in (bg_url, en_url):
            count += 1
            lines.append("  <url>")
            lines.append("    <loc>{}</loc>".format(url))
            lines.append('    <xhtml:link rel="alternate" hreflang="bg" href="{}"/>'.format(bg_url))
            lines.append('    <xhtml:link rel="alternate" hreflang="en" href="{}"/>'.format(en_url))
            lines.append('    <xhtml:link rel="alternate" hreflang="x-default" href="{}"/>'.format(bg_url))
            lines.append("    <changefreq>daily</changefreq>")
            lines.append("    <priority>{}</priority>".format(priority))
            lines.append("  </url>")
    lines.append("</urlset>")
    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote docs/sitemap.xml ({} urls)".format(count))


def write_robots():
    """Generate docs/robots.txt; the Sitemap line stays tied to BASE_URL."""
    content = ("User-agent: *\n"
               "Allow: /\n\n"
               "Sitemap: {}/sitemap.xml\n".format(BASE_URL))
    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote docs/robots.txt")


def main():
    write_i18n_js()
    write_locations_js()
    write_location_pages()
    write_hub()
    write_compare_locations()
    write_sitemap()
    write_robots()


if __name__ == "__main__":
    main()
