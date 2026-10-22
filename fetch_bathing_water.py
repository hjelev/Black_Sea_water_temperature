# Fetch the official EU bathing water quality classification (Bathing Water
# Directive, published yearly by the European Environment Agency) for the
# coastal bathing sites near each Bulgarian and Romanian location, and write
# bathing_water.json for build_site.py to bake into the dashboards.
#
# The classification changes once a year (published around May for the
# previous season), so this is run by hand, not in CI. Bump EEA_YEAR when the
# EEA publishes a newer BathingWater_Dyna_WM_<year> map service.
#
# Turkey, Ukraine, Georgia and Russia don't report to the EEA, so their
# locations get no entry.
#
# Python 3.7+, standard library only.
import json
import math
import os
import re
import urllib.parse
import urllib.request

from locations import LOCATIONS

EEA_YEAR = 2025
SERVICE = ("https://marine.discomap.eea.europa.eu/arcgis/rest/services/BathingWater/"
           "BathingWater_Dyna_WM_{}/MapServer/3/query".format(EEA_YEAR))
COUNTRIES = {"bulgaria": "BG", "romania": "RO"}
# Sites within this distance of the town centre count as the town's beaches.
RADIUS_KM = 5
MAX_SITES = 8
OUT_PATH = os.path.join(os.path.dirname(__file__), "bathing_water.json")


def fetch_sites():
    params = urllib.parse.urlencode({
        "where": "countryCode IN ({}) AND bwWaterCategory = 'Coastal'".format(
            ",".join("'{}'".format(c) for c in COUNTRIES.values())),
        "outFields": "bathingWaterName,bathingWaterIdentifier,longitude,latitude,"
                     "qualityStatus,qualityStatus_minus1",
        "returnGeometry": "false",
        "f": "json",
    })
    with urllib.request.urlopen(SERVICE + "?" + params, timeout=90) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "features" not in data:
        raise RuntimeError("EEA service returned no features: {}".format(data))
    return [f["attributes"] for f in data["features"]]


def distance_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, (lat1, lon1, lat2, lon2))
    h = (math.sin((lat2 - lat1) / 2) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(h))


def status_key(value):
    """'Excellent' -> 'excellent'; anything unrated -> 'none'."""
    value = (value or "").strip().lower()
    return value if value in ("excellent", "good", "sufficient", "poor") else "none"


def main():
    sites = fetch_sites()
    print("fetched {} coastal bathing sites".format(len(sites)))
    result = {"year": EEA_YEAR, "locations": {}}
    for loc in LOCATIONS:
        if loc["country"] not in COUNTRIES:
            continue
        near = []
        for s in sites:
            km = distance_km(loc["place_lat"], loc["place_lon"], s["latitude"], s["longitude"])
            if km <= RADIUS_KM:
                near.append({
                    # Bulgarian names are reported in capitals; keep Roman
                    # numerals (Mamaia VI, ...) as they are.
                    "name": re.sub(r"\w+", lambda m: m.group(0) if re.fullmatch(
                        r"[IVX]+", m.group(0)) else m.group(0).capitalize(),
                        s["bathingWaterName"]),
                    "id": s["bathingWaterIdentifier"],
                    "km": round(km, 1),
                    "status": status_key(s["qualityStatus"]),
                    "prev": status_key(s["qualityStatus_minus1"]),
                })
        near.sort(key=lambda s: s["km"])
        if near:
            result["locations"][loc["slug"]] = near[:MAX_SITES]
        print("{}: {} site(s)".format(loc["name_en"], len(near)))
    with open(OUT_PATH, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=1)
        fh.write("\n")
    print("wrote {}".format(OUT_PATH))


if __name__ == "__main__":
    main()
