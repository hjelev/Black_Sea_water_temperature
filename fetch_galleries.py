#!/usr/bin/env python3
# Fetch a handful of representative Wikimedia Commons photos per location and
# cache them in docs/galleries.json, consumed by build_site.py to render the
# per-location /<slug>/gallery.html pages.
#
# This is a NETWORK step, kept separate from the deterministic static build.
# Run it occasionally to refresh the cache, then rebuild and commit:
#
#   python3 fetch_galleries.py     # writes docs/galleries.json
#   python3 build_site.py          # bakes photos into docs/<slug>/gallery.html
#
# Images are hot-linked from upload.wikimedia.org with author + license
# attribution shown next to each one (a Commons licensing requirement).
#
# Python 3.7+ , standard library only.
import json
import math
import os
import re
import time
import unicodedata
import urllib.parse
import urllib.request

from locations import LOCATIONS

API = "https://commons.wikimedia.org/w/api.php"
DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
OUT = os.path.join(DOCS_DIR, "galleries.json")
USER_AGENT = ("BlackSeaTempGallery/1.0 (https://more.masoko.net; "
              "https://github.com/hjelev/Black_Sea_water_temperature)")
PER_LOCATION = 8
THUMB_WIDTH = 480

# Skip files that are clearly not location photos. Checked against both the
# file title and its categories so locator-map / building / museum categories are
# caught even when the filename itself looks innocent.
SKIP_RE = re.compile(
    r"("
    # graphics / maps / non-photographic
    r"map|flag|coat[ _]of[ _]arms|locator|logo|icon|diagram|chart|seal|collage|"
    r"\.svg$|within bulgaria|within .* (municipality|province)|-he\.png$|"
    # religious buildings
    r"church|cathedral|chapel|monaster|mosque|basilica|synagogue|temple|"
    # museums / archaeology / fossils
    r"museum|paleontolog|palaeontolog|fossil|archaeolog|archeolog|treasure|"
    r"exhibit|artefact|artifact|"
    # monuments / memorials / public art / tombs / official buildings
    r"monument|memorial|\bstatue|fountain|\bbattle\b|mausoleum|grabmal|\btomb\b|"
    r"library|bibliothek|town ?hall|\bmayors?\b|administration|municipal office|"
    # vehicles / ads / sport trophies
    r"police|\bcar\b|\bbus\b|\btram\b|advert|\bad\b|trophy|\bcup\b|"
    r"airport|automobile|motorcycle|"
    # military / war
    r"aircraft|warship|\bnaval\b|\bUSS\b|kiev-class|marines|submarine|destroyer|"
    r"\bbomb|bombard|\bwar\b|wartime|interwar|détruit|destroyed|"
    # events / construction
    r"olympic|\bconstruction\b|"
    # space / planetary nomenclature
    r"ISS\d|view of earth|astronaut|olympus mons|\bcrater\b|"
    # historical documents / royalty (saint-name collisions)
    r"\bfolio\b|\bcodex\b|princess|\bprince\b|via julia|bandeira|"
    # hotel / venue promo shots, infrastructure, ships, archive photos
    r"\bhotel|restaurant|\bradar\b|\binterior\b|\bIMO\b|tanker|cargo ship|"
    r"hilton|хилтон|reading.hall|muzeu|stadium|stadion|tribune|\bship\b|cruise|\bSSS\b|"
    r"locomotive|railway|\btrain\b|\bgara\b|rafting|yayla|uzungöl|long lake|"
    r"hist\. ?foto|\bussr\b|\bссср\b|rian archive|dust storm|"
    # book plates / archive scans / space-station shots
    r"\bp\.\s?\d+|LABW|apollo|soyuz|"
    # civic buildings / events / cemeteries
    r"antarctic|glacier|\bpeak\b|livingston island|\bnunatak|"
    r"cemetery|гробищ|post.office|chitalishte|читалище|bread oven|terror|терорист"
    r")", re.I)
# Archive photos (a year 1800-1989 in the title) look dated next to the live data.
OLD_YEAR_RE = re.compile(r"(?<!\d)(18\d\d|19[0-8]\d)(?!\d)")
# Strong "this is the seaside" title terms, multilingual (bg/ru/ro/tr/ka-latin).
COAST_TITLE_RE = re.compile(
    r"(beach|coast|shore|seaside|\bsea\b|black sea|\bbay\b|cliff|\bcape\b|"
    r"aerial|drone|panorama|\bview\b|sunset|sunrise|harbou?r|marina|\bport\b|"
    r"плаж|пляж|море|бряг|берег|бухт|залив|plaj|litoral|sahil|plaj|deniz|"
    r"strand|küste|plaża|morze)", re.I)
# Positive nature / beach / scenic terms. Used to RANK (not hard-filter) kept
# images so beach and coast shots lead each gallery, while generic-title scenic
# town views are still allowed through. Note: 'panorama\b' must not match the
# unrelated 'panoramio' filename token from panoramio.com imports.
NATURE_RE = re.compile(
    r"(beach|coast|coastline|shore|seaside|seascape|\bsea\b|black sea|sand|dune|"
    r"cliff|rock|\bcape\b|\bbay\b|gulf|lagoon|cove|bird|wildlife|sunset|sunrise|"
    r"\bwave|nature|reserve|landscape|panorama\b|scenic|aerial|\bview\b|forest|"
    r"\btree|meadow|\bhill|flower|sunflower|garden|\bpark\b|waterfall|river|lake|"
    r"\bmouth\b)", re.I)
# Skip photos OF people: location names like "Irakli" double as personal names,
# so the name search drags in portraits. Commons files them in person categories.
PERSON_CAT_RE = re.compile(r"(births|deaths|portraits?|politician|"
                           r"minister|president|ambassador|diplomat|governor|mayor|"
                           r"footballer|athlete|actor|actress|singer|musician|"
                           r"film director|writer|officials?|"
                           r"people named|men named|women named|selfies|"
                           r"\(given name\)|\(surname\)|"
                           r"in \d{4}$)", re.I)  # "<Person> in 2015" biographical cats
# Explicit title overrides for stubborn false positives.
TITLE_BLOCK_RE = re.compile(r"\bportrait\b", re.I)
# Keep real-world photos only: drop documents, scans and artwork/paintings.
# Checked against both the file title and its categories.
NON_PHOTO_RE = re.compile(r"(painting|drawing|engraving|illustration|lithograph|"
                          r"etching|sketch|watercolou?r|fresco|mural|artwork|"
                          r"poster|stamp|banknote|\bcoin|medal|"
                          r"document|manuscript|\bletter|certificate|"
                          r"newspaper|page from|scan of|blueprint|screenshot)", re.I)
TAG_RE = re.compile(r"<[^>]+>")

# Place nouns that legitimately follow a location name in a geographic category
# ("Sozopol Island", "Varna Bay") and must not be read as a person's surname.
PLACE_NOUN = (r"Beach|Bay|Gulf|Port|Harbou?r|Cape|Marina|Reserve|Island|Lighthouse|"
              r"Peninsula|Resort|Lake|River|Sea|Coast|Monastery|Church|Cathedral|"
              r"Mosque|Necropolis|Fortress|Castle|Bridge|Park|Garden|Station|Museum|"
              r"Municipality|Province|District|Village|Town|City|Region|Oblast|Raion")
# Trailing words stripped from a location name to expose a one-word "given name"
# root ("Irakli Beach" -> "Irakli", "Sunny Beach" -> "Sunny").
TAIL_STRIP = {"beach", "bay", "coast", "gulf"}


def location_name_re(name_en):
    """For a location whose name doubles as a personal given name (the beach
    "Irakli" vs. the common Georgian name Irakli), return a regex matching person
    categories "<Name> <Surname>" so portraits are dropped without enumerating
    every politician. Returns None for multi-word place names, which have no such
    collision and would risk false positives (e.g. "Golden Sands")."""
    words = name_en.split()
    while len(words) > 1 and words[-1].lower() in TAIL_STRIP:
        words = words[:-1]
    if len(words) != 1:
        return None
    return re.compile(r"^" + re.escape(words[0]) +
                      r" (?!(?:" + PLACE_NOUN + r")\b)[A-Z][\w.-]+$")

IIPROPS = {
    "prop": "imageinfo|categories|coordinates",
    "iiprop": "url|extmetadata|mime|size",
    "iiurlwidth": THUMB_WIDTH,
    "cllimit": "max",
    "clshow": "!hidden",
    "colimit": "max",
}

# Photos geotagged farther than this from the location are a different place
# that merely shares the name (Green Cape, Australia; La Rize, France) or an
# inland excursion (Uzungöl from Trabzon).
MAX_KM = 15
# Skip low-resolution originals; they look soft in the lightbox.
MIN_WIDTH = 1000
# At most this many photos from one author per location, so one prolific
# uploader's series can't fill a whole gallery.
PER_ARTIST = 2

# Extra Commons search queries for locations whose display name is ambiguous or
# rarely used on Commons. Each location is also searched as "<name_en>",
# "<name_en> beach" and its local-language name.
EXTRA_QUERIES = {
    "sveti-konstantin": ["Sveti Konstantin Varna", "Saints Constantine and Helena resort",
                         "Konstantin i Elena beach"],
    "irakli": ["Irakli beach Bulgaria"],
    "cape-kaliakra": ["Kaliakra"],
    "trabzon": ["Trabzon sahil", "Trabzon Black Sea"],
    "rize": ["Rize sahil", "Rize Black Sea"],
    "sinop": ["Sinop sahil", "Sinop Black Sea"],
    "sile": ["Şile plaj", "Sile beach"],
    "constanta": ["Constanța plaja", "Constanta beach"],
    "olimp": ["Olimp Romania", "Olimp Mangalia"],
    "vadu": ["Vadu beach", "Corbu beach", "Plaja Vadu", "Plaja Corbu"],
    "green-cape": ["Mtsvane Kontskhi", "Green Cape Batumi", "Green Cape Georgia",
                   "Batumi Botanical Garden"],
    "kvariati": ["Kvariati beach"],
    "shekvetili": ["Shekvetili beach"],
    "sochi": ["Sochi beach", "Sochi Black Sea"],
    "abrau-durso": ["Durso beach", "Abrau-Durso lake"],
    "byala": ["Byala Varna beach", "Byala Bulgaria Black Sea", "Бяла плаж"],
    "dyuni": ["Duni resort Bulgaria", "Dyuni beach", "Arkutino"],
    "kiten": ["Kiten Bulgaria", "Kiten beach"],
    "ravda": ["Ravda Bulgaria"],
    "chernomorets": ["Chernomorets Bulgaria"],
    "tsarevo": ["Tsarevo Bulgaria"],
    "shabla": ["Shabla lighthouse", "Cape Shabla"],
    "krapets": ["Krapets Bulgaria"],
    "durankulak": ["Durankulak lake"],
    "shkorpilovtsi": ["Shkorpilovtsi beach", "Kamchia river mouth"],
}
# Native-script names for non-Bulgarian locations (name_bg covers Bulgaria).
LOCAL_NAMES = {
    "sochi": "Сочи", "anapa": "Анапа", "gelendzhik": "Геленджик",
    "novorossiysk": "Новороссийск", "abrau-durso": "Абрау-Дюрсо",
    "constanta": "Constanța", "sile": "Şile",
}
# Per-location title blocks for namesakes that the generic filters can't tell
# apart (FC Chernomorets of Varna/Odesa matches).
LOCATION_BLOCK = {
    "chernomorets": re.compile(r"(варна|varna|урал|odesa|одеса|fc\b|футбол)", re.I),
}
# Name fragments that count as "the title names this place" for ranking.
NAME_ALIASES = {
    "sveti-konstantin": ["konstantin", "константин"],
    "cape-kaliakra": ["kaliakra", "калиакра"],
    "irakli": ["irakli", "иракли"],
    # "Green Cape" alone is mostly Green Cape, NSW (Australia), so require the
    # Georgian name; likewise "Vadu" is a common Romanian village name.
    "green-cape": ["mtsvane", "makhinjauri", "batumi botanical", "ботанич"],
    "vadu": ["vadu ct", "vadu 20", "vadu beach", "plaja vadu", "dune vadu",
             "corbu, romania", "plaja corbu", "corbu beach"],
    "abrau-durso": ["abrau", "durso", "абрау", "дюрсо"],
    "constanta": ["constanța", "constanta", "constanţa", "tomis"],
    "sile": ["şile", "sile"],
    # Another Byala lies inland near Ruse; only trust its seaside photos.
    "byala": ["byala beach", "byala, varna", "byala varna", "byala bulgaria black",
              "бяла, варн", "бяла плаж", "бяла - плаж"],
    "dyuni": ["dyuni", "duni", "дюни", "arkutino", "аркутино"],
    # Russian "обзор" means "overview"; only the Latin spelling is the town.
    "obzor": ["obzor"],
    "nessebar": ["nessebar", "nesebar", "nesebyr", "несебър", "несебр"],
    "shkorpilovtsi": ["shkorpilovtsi", "škorpilovci", "шкорпиловци", "kamchia",
                      "камчия"],
}


def api_get(params):
    params = dict(params)
    params.update({"action": "query", "format": "json"})
    url = API + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def clean(text):
    if not text:
        return ""
    return TAG_RE.sub("", text).strip()


def parse_pages(data, name_en=""):
    out = []
    name_re = location_name_re(name_en) if name_en else None
    pages = (data.get("query", {}) or {}).get("pages", {}) or {}
    # Preserve the API's relevance/distance ordering via the 'index' field.
    for p in sorted(pages.values(), key=lambda p: p.get("index", 1e9)):
        title = p.get("title", "")
        if TITLE_BLOCK_RE.search(title):
            continue
        cats = [c.get("title", "").replace("Category:", "").strip()
                for c in (p.get("categories") or [])]
        # Block obvious non-nature subjects (maps, buildings, museums, monuments,
        # vehicles, ...) by title OR category.
        if SKIP_RE.search(title) or any(SKIP_RE.search(c) for c in cats):
            continue
        if any(PERSON_CAT_RE.search(c) for c in cats):
            continue
        # "<Location> <Surname>" categories (e.g. "Irakli Gharibashvili") are
        # people named after the place; drop them but spare the place's own name.
        if name_re and any(c.lower() != name_en.lower() and name_re.match(c)
                           for c in cats):
            continue
        if NON_PHOTO_RE.search(title) or any(NON_PHOTO_RE.search(c) for c in cats):
            continue
        # An eponymous category exactly equal to the filename (e.g. "Irakli
        # Kvirikadze.jpg" filed only under "Category:Irakli Kvirikadze") marks a
        # single-subject portrait. Require a multi-word stem so legit one-word
        # place names ("Sozopol") are kept.
        stem = re.sub(r"\.[a-z0-9]+$", "", title.replace("File:", ""),
                      flags=re.I).strip()
        if " " in stem and any(c.lower() == stem.lower() for c in cats):
            continue
        if OLD_YEAR_RE.search(title):
            continue
        info = (p.get("imageinfo") or [{}])[0]
        if info.get("mime") not in ("image/jpeg", "image/png"):
            continue
        if (info.get("width") or 0) < MIN_WIDTH or \
                (info.get("height") or 0) > (info.get("width") or 0) * 1.4:
            continue  # low-res, or a tall portrait crop that tiles badly
        thumb, full = info.get("thumburl"), info.get("url")
        if not thumb or not full:
            continue
        meta = info.get("extmetadata", {}) or {}
        # Prefer nature/beach/scenic shots: matches in title or categories sort
        # first, generic scenic-town views fall behind but are kept.
        is_nature = bool(NATURE_RE.search(title) or
                         any(NATURE_RE.search(c) for c in cats))
        coords = (p.get("coordinates") or [None])[0]
        out.append({
            "_nature": is_nature,
            "_coast": bool(COAST_TITLE_RE.search(title)),
            "_coord": (coords["lat"], coords["lon"]) if coords else None,
            "_wide": (info.get("width") or 0) >= 2000,
            "title": title.replace("File:", ""),
            "thumb": thumb,
            "full": full,
            "page": info.get("descriptionurl", ""),
            "w": info.get("thumbwidth"),
            "h": info.get("thumbheight"),
            "artist": clean((meta.get("Artist") or {}).get("value")) or "Wikimedia Commons",
            "license": clean((meta.get("LicenseShortName") or {}).get("value")),
            "licenseUrl": (meta.get("LicenseUrl") or {}).get("value", ""),
        })
    return out


def search_by_name(query, name_en):
    params = dict(IIPROPS)
    params.update({
        "generator": "search",
        "gsrsearch": query + " filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": 30,
    })
    return parse_pages(api_get(params), name_en)


def search_by_geo(lat, lon, name=""):
    params = dict(IIPROPS)
    params.update({
        "generator": "geosearch",
        "ggscoord": "{}|{}".format(lat, lon),
        "ggsradius": 10000,
        "ggslimit": 50,
        "ggsnamespace": 6,
    })
    return parse_pages(api_get(params), name)


def km_between(a, b):
    lat1, lon1, lat2, lon2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    h = (math.sin((lat2 - lat1) / 2) ** 2 +
         math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(h))


def fold(text):
    """Lowercase and strip diacritics so 'Constanța' matches 'Constanta'."""
    text = unicodedata.normalize("NFKD", text.lower())
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def series_key(title):
    """Collapse numbered series ('Shekvetili Park 42.jpg', 'Sunny Beach 3.jpg',
    '... - panoramio (5).jpg') to one key so a gallery shows one of each."""
    stem = re.sub(r"\.[a-z0-9]+$", "", title, flags=re.I)
    stem = re.sub(r"\(.*?\)|panoramio|\d+", " ", fold(stem))
    return frozenset(re.sub(r"[\W_]+", " ", stem).split())


def queries_for(loc):
    qs = [loc["name_en"], loc["name_en"] + " beach"]
    local = LOCAL_NAMES.get(loc["slug"]) or (
        loc["name_bg"] if loc["country"] == "bulgaria" else None)
    if local:
        qs.append(local)
    return qs + EXTRA_QUERIES.get(loc["slug"], [])


def mentions(title, aliases):
    # Anchor at a word start so "Rize" doesn't match "prize".
    return any(re.search(r"(?<!\w)" + re.escape(a), title) for a in aliases)


def name_aliases(loc):
    aliases = NAME_ALIASES.get(loc["slug"]) or [loc["name_en"], loc["name_bg"]]
    return [fold(a) for a in aliases + [LOCAL_NAMES.get(loc["slug"], "")] if a]


def candidates(loc):
    """All filtered, scored photos for a location, best first."""
    images = []
    for q in queries_for(loc):
        try:
            images += search_by_name(q, loc["name_en"])
        except Exception as exc:
            print("  search {!r} failed: {}".format(q, exc))
        time.sleep(0.3)
    try:
        images += search_by_geo(loc["lat"], loc["lon"], loc["name_en"])
    except Exception as exc:
        print("  geo search failed: {}".format(exc))

    aliases = name_aliases(loc)
    others = [a for o in LOCATIONS if o["slug"] != loc["slug"]
              for a in name_aliases(o)]
    here = (loc["lat"], loc["lon"])
    out = []
    for im in dedupe(images):
        title = fold(im["title"])
        block = LOCATION_BLOCK.get(loc["slug"])
        if block and block.search(title):
            continue
        named = mentions(title, aliases)
        if not named and mentions(title, others):
            continue  # a neighbouring tracked location's photo
        if im["_coord"]:
            dist = km_between(here, im["_coord"])
            if dist > MAX_KM:
                continue
        elif not named:
            continue  # no geotag and not named after the place: can't trust it
        else:
            dist = MAX_KM
        im["_score"] = (4 * named + 3 * im["_coast"] + im["_nature"] +
                        im["_wide"] + (1 if dist < 6 else 0))
        out.append(im)
    out.sort(key=lambda im: -im["_score"])
    return out


def dedupe(images):
    seen, out = set(), []
    for im in images:
        if im["full"] in seen:
            continue
        seen.add(im["full"])
        out.append(im)
    return out


def pick(cands, taken):
    """Top PER_LOCATION photos, one per numbered series, PER_ARTIST max, skipping
    photos another location claimed with a better score."""
    chosen, series, artists = [], set(), {}
    for im in cands:
        if im["full"] in taken:
            continue
        key = series_key(im["title"])
        if key in series or artists.get(im["artist"], 0) >= PER_ARTIST:
            continue
        series.add(key)
        artists[im["artist"]] = artists.get(im["artist"], 0) + 1
        chosen.append(im)
        if len(chosen) == PER_LOCATION:
            break
    return chosen


def main():
    pool = {}
    for loc in LOCATIONS:
        pool[loc["slug"]] = candidates(loc)
        print("{}: {} candidates".format(loc["name_en"], len(pool[loc["slug"]])))

    # A photo matching several nearby locations (Balchik/Albena, Varna/Sveti
    # Konstantin) belongs to the one where it scores best, so no two galleries
    # repeat a photo.
    best = {}
    for slug, cands in pool.items():
        for im in cands:
            if im["full"] not in best or im["_score"] > best[im["full"]][1]:
                best[im["full"]] = (slug, im["_score"])

    galleries = {}
    for slug, cands in pool.items():
        taken = {url: owner for url, (owner, _) in best.items() if owner != slug}
        imgs = pick(cands, taken)
        for im in imgs:
            for k in [k for k in im if k.startswith("_")]:
                im.pop(k)
        galleries[slug] = imgs
        print("{}: {} photos".format(slug, len(imgs)))

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(galleries, fh, ensure_ascii=False, indent=1)
    print("wrote {} ({} locations)".format(OUT, len(galleries)))


if __name__ == "__main__":
    main()
