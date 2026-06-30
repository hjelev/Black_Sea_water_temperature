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
import os
import re
import time
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
    r"\bfolio\b|\bcodex\b|princess|\bprince\b|via julia|bandeira"
    r")", re.I)
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
    "prop": "imageinfo|categories",
    "iiprop": "url|extmetadata|mime|size",
    "iiurlwidth": THUMB_WIDTH,
    "cllimit": "max",
    "clshow": "!hidden",
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
        info = (p.get("imageinfo") or [{}])[0]
        if info.get("mime") not in ("image/jpeg", "image/png"):
            continue
        thumb, full = info.get("thumburl"), info.get("url")
        if not thumb or not full:
            continue
        meta = info.get("extmetadata", {}) or {}
        # Prefer nature/beach/scenic shots: matches in title or categories sort
        # first, generic scenic-town views fall behind but are kept.
        is_nature = bool(NATURE_RE.search(title) or
                         any(NATURE_RE.search(c) for c in cats))
        out.append({
            "_nature": is_nature,
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


def search_by_name(name):
    params = dict(IIPROPS)
    params.update({
        "generator": "search",
        "gsrsearch": name + " filetype:bitmap",
        "gsrnamespace": 6,
        "gsrlimit": 20,
    })
    return parse_pages(api_get(params), name)


def search_by_geo(lat, lon, name=""):
    params = dict(IIPROPS)
    params.update({
        "generator": "geosearch",
        "ggscoord": "{}|{}".format(lat, lon),
        "ggsradius": 10000,
        "ggslimit": 30,
        "ggsnamespace": 6,
    })
    return parse_pages(api_get(params), name)


def dedupe(images):
    seen, out = set(), []
    for im in images:
        if im["full"] in seen:
            continue
        seen.add(im["full"])
        out.append(im)
    return out


def fetch_location(loc):
    images = []
    try:
        images = search_by_name(loc["name_en"])
    except Exception as exc:
        print("  name search failed: {}".format(exc))
    deduped = dedupe(images)
    nature = sum(1 for im in deduped if im.get("_nature"))
    # Backfill from nearby coordinates (same nature filtering) when the name
    # search is thin OR light on actual nature/coastal content -- e.g. a coastal
    # city whose name returns mostly inland-village or townscape photos.
    if len(deduped) < PER_LOCATION or nature < 4:
        try:
            images += search_by_geo(loc["lat"], loc["lon"], loc["name_en"])
        except Exception as exc:
            print("  geo search failed: {}".format(exc))
    images = dedupe(images)
    # Stable sort: nature/beach/scenic shots first, relevance order preserved.
    images.sort(key=lambda im: not im.get("_nature"))
    images = images[:PER_LOCATION]
    for im in images:
        im.pop("_nature", None)
    return images


def main():
    galleries = {}
    for loc in LOCATIONS:
        imgs = fetch_location(loc)
        galleries[loc["slug"]] = imgs
        print("{}: {} photos".format(loc["name_en"], len(imgs)))
        time.sleep(0.5)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(galleries, fh, ensure_ascii=False, indent=1)
    print("wrote {} ({} locations)".format(OUT, len(galleries)))


if __name__ == "__main__":
    main()
