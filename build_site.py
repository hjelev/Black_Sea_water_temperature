# Static site generator for the Black Sea water temperature site.
#
# Reads the page templates in templates/*.html and the location list in
# locations.py, and writes one SEO-distinct set of pages per location into
# docs/<slug>/ , plus the generated docs/locations.js and the root hub page
# docs/index.html.
#
# Each location gets its own URL, <title>, meta description and canonical link
# so search engines index every town separately (the whole point of the
# per-location split). The page markup and inline Plotly logic are identical
# across locations and are reused verbatim from the templates; only the <head>
# and the injected window.LOCATION_ID differ.
#
#   python3 build_site.py
#
# Run locally whenever templates/, locations.py or the page metadata change,
# then commit the regenerated docs/. Not run in CI (data loads client-side
# from the csv files; the html is static).
#
# Python 3.7+ , standard library only.
import os

from locations import LOCATIONS, COUNTRY_ORDER

BASE_URL = "https://more.masoko.net"
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# Per-page SEO metadata. {loc} = English town name, {country} = English country
# name, {year} = first data year.
PAGES = {
    "index.html": {
        "title": "{loc} Sea Water Temperature — Live Black Sea Data",
        "desc": ("Live and historical Black Sea water temperature at {loc}, "
                 "{country}. Daily sea surface temperature since {year}, with a "
                 "30-day trend and full history charts."),
    },
    "compare.html": {
        "title": "Compare Years — {loc} Black Sea Water Temperature",
        "desc": ("Compare Black Sea water temperature at {loc}, {country} across "
                 "years on a Jan–Dec axis to spot seasonal patterns and warming "
                 "trends."),
    },
    "heatmap.html": {
        "title": "Monthly Heatmap — {loc} Black Sea Water Temperature",
        "desc": ("Monthly Black Sea water temperature heatmap for {loc}, "
                 "{country} — average sea surface temperature per month across "
                 "every recorded year."),
    },
    "stats.html": {
        "title": "Statistics & Records — {loc} Black Sea Water Temperature",
        "desc": ("All-time records and annual statistics for Black Sea water "
                 "temperature at {loc}, {country} — hottest and coldest readings, "
                 "yearly min/avg/max and the long-term trend."),
    },
}

NAV_KEY = "loc_{}"  # i18n key, e.g. loc_kamenbryag


def i18n_key(slug):
    return "loc_" + slug.replace("-", "")


def locations_by_country():
    """Yield (country_slug, [locations]) in COUNTRY_ORDER, skipping empty groups."""
    for country in COUNTRY_ORDER:
        group = [loc for loc in LOCATIONS if loc["country"] == country]
        if group:
            yield country, group


def escape(text):
    return (text.replace("&", "&amp;").replace("<", "&lt;")
                .replace(">", "&gt;").replace('"', "&quot;"))


def build_head(title, description, canonical):
    """Generated <head> shared by every page; only the SEO fields vary."""
    t = escape(title)
    d = escape(description)
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="description" content="{desc}">
    <link rel="canonical" href="{canonical}">
    <meta property="og:type" content="website">
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{desc}">
    <meta property="og:url" content="{canonical}">
    <meta name="twitter:card" content="summary">
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <link rel="icon" href="/favicon.svg">
    <link rel="stylesheet" href="/style.css">
    <script src="/i18n.js"></script>
    <script src="/locations.js"></script>
    <script>window.LOCATION_ID = '{slug}';</script>
    <script defer src="https://m.masoko.net/core-util" data-website-id="a6c69550-2eed-4ba4-8568-57dc4c66e466"></script>
</head>
""".format(title=t, desc=d, canonical=escape(canonical), slug="{slug}")


def template_body(page_file):
    """Return everything after </head> from a template, with asset paths fixed."""
    with open(os.path.join(TEMPLATES_DIR, page_file), encoding="utf-8") as fh:
        html = fh.read()
    body = html[html.index("</head>") + len("</head>"):]
    # data.js lives at the site root, not in the per-location folder.
    body = body.replace('src="data.js"', 'src="/data.js"')
    return body


def canonical_for(slug, page_file):
    if page_file == "index.html":
        return "{base}/{slug}/".format(base=BASE_URL, slug=slug)
    return "{base}/{slug}/{page}".format(base=BASE_URL, slug=slug, page=page_file)


def write_location_pages():
    bodies = {page: template_body(page) for page in PAGES}
    for loc in LOCATIONS:
        slug = loc["slug"]
        year = loc["start_date"][:4]
        out_dir = os.path.join(DOCS_DIR, slug)
        os.makedirs(out_dir, exist_ok=True)
        for page_file, meta in PAGES.items():
            title = meta["title"].format(
                loc=loc["name_en"], country=loc["country_en"], year=year)
            desc = meta["desc"].format(
                loc=loc["name_en"], country=loc["country_en"], year=year)
            head = build_head(title, desc, canonical_for(slug, page_file))
            page = head.replace("{slug}", slug) + bodies[page_file]
            with open(os.path.join(out_dir, page_file), "w", encoding="utf-8") as fh:
                fh.write(page)
        print("{}: wrote {} pages to docs/{}/".format(
            loc["name_en"], len(PAGES), slug))


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


def write_hub():
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
    head = build_head(
        "Black Sea Water Temperature — Bulgaria, Turkey, Romania, Georgia, Russia",
        ("Live and historical Black Sea water temperature for coastal towns across "
         "Bulgaria, Turkey, Romania, Georgia and Russia. Daily sea surface "
         "temperature, yearly comparisons, heatmaps and records."),
        BASE_URL + "/").replace("{slug}", "burgas")
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
    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as fh:
        fh.write(head + body)
    print("wrote docs/index.html (hub)")


def write_compare_locations():
    """Global (non per-location) page that overlays multiple towns on one chart."""
    head = build_head(
        "Compare Locations — Black Sea Water Temperature",
        ("Compare Black Sea water temperature across coastal towns in Bulgaria, "
         "Turkey, Romania, Georgia and Russia on a single chart — overlay any "
         "locations across the years and on a Jan–Dec seasonal axis."),
        BASE_URL + "/compare-locations.html").replace("{slug}", "burgas")
    body = template_body("compare-locations.html")
    with open(os.path.join(DOCS_DIR, "compare-locations.html"), "w", encoding="utf-8") as fh:
        fh.write(head + body)
    print("wrote docs/compare-locations.html")


def write_sitemap():
    """Generate docs/sitemap.xml from LOCATIONS so it stays in sync with the
    actual pages. URLs are produced by canonical_for(), the same helper used for
    each page's <link rel="canonical">, so the sitemap can never drift from the
    pages it lists."""
    urls = [(BASE_URL + "/", "1.0")]
    for loc in LOCATIONS:
        slug = loc["slug"]
        for page_file in PAGES:
            priority = "0.8" if page_file == "index.html" else "0.6"
            urls.append((canonical_for(slug, page_file), priority))
    urls.append((BASE_URL + "/compare-locations.html", "0.7"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for url, priority in urls:
        lines.append("  <url>")
        lines.append("    <loc>{}</loc>".format(escape(url)))
        lines.append("    <changefreq>daily</changefreq>")
        lines.append("    <priority>{}</priority>".format(priority))
        lines.append("  </url>")
    lines.append("</urlset>")
    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("wrote docs/sitemap.xml ({} urls)".format(len(urls)))


def write_robots():
    """Generate docs/robots.txt; the Sitemap line stays tied to BASE_URL."""
    content = ("User-agent: *\n"
               "Allow: /\n\n"
               "Sitemap: {}/sitemap.xml\n".format(BASE_URL))
    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as fh:
        fh.write(content)
    print("wrote docs/robots.txt")


def main():
    write_locations_js()
    write_location_pages()
    write_hub()
    write_compare_locations()
    write_sitemap()
    write_robots()


if __name__ == "__main__":
    main()
