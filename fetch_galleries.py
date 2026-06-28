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

# Skip files that are clearly not location photos.
SKIP_RE = re.compile(r"(map|flag|coat[ _]of[ _]arms|locator|logo|icon|"
                     r"diagram|chart|seal|\.svg$)", re.I)
TAG_RE = re.compile(r"<[^>]+>")

IIPROPS = {
    "prop": "imageinfo",
    "iiprop": "url|extmetadata|mime|size",
    "iiurlwidth": THUMB_WIDTH,
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


def parse_pages(data):
    out = []
    pages = (data.get("query", {}) or {}).get("pages", {}) or {}
    # Preserve the API's relevance/distance ordering via the 'index' field.
    for p in sorted(pages.values(), key=lambda p: p.get("index", 1e9)):
        title = p.get("title", "")
        if SKIP_RE.search(title):
            continue
        info = (p.get("imageinfo") or [{}])[0]
        if info.get("mime") not in ("image/jpeg", "image/png"):
            continue
        thumb, full = info.get("thumburl"), info.get("url")
        if not thumb or not full:
            continue
        meta = info.get("extmetadata", {}) or {}
        out.append({
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
    return parse_pages(api_get(params))


def search_by_geo(lat, lon):
    params = dict(IIPROPS)
    params.update({
        "generator": "geosearch",
        "ggscoord": "{}|{}".format(lat, lon),
        "ggsradius": 10000,
        "ggslimit": 30,
        "ggsnamespace": 6,
    })
    return parse_pages(api_get(params))


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
    if len(images) < 4:
        try:
            images += search_by_geo(loc["lat"], loc["lon"])
        except Exception as exc:
            print("  geo search failed: {}".format(exc))
    return dedupe(images)[:PER_LOCATION]


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
