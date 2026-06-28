# One-time historical backfill of sea surface temperature from the Open-Meteo
# Marine API archive into each location's csv file.
#
# Usage:
#   python3 backfill.py            # backfill every location in locations.py
#   python3 backfill.py varna      # backfill a single location by slug
#
# The archive for the Black Sea cells used here only reaches back to late 2022
# (earlier dates return null); the per-location start_date in locations.py caps
# how far back we ask. Run once locally; the resulting csv is committed and then
# kept up to date by get_daily_temp.py. Re-running regenerates the file(s).
#
# Python 3.7+ , standard library only.
import json
import sys
import time
import urllib.request
from datetime import date, datetime

from locations import LOCATIONS

# Keep the same daily cadence as the rest of the series.
RECORD_HOURS = (6, 12, 18)


def build_api_url(lat, lon, start_date, end_date):
    return (
        "https://marine-api.open-meteo.com/v1/marine"
        "?latitude={lat}&longitude={lon}"
        "&hourly=sea_surface_temperature"
        "&timezone=UTC&start_date={start}&end_date={end}"
    ).format(lat=lat, lon=lon, start=start_date, end=end_date)


def fetch_json(url, retries=3, delay=5):
    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as error:  # noqa: BLE001 - retry on any network error
            last_error = error
            if attempt < retries - 1:
                time.sleep(delay)
    raise RuntimeError("Failed to fetch {} after {} attempts: {}".format(
        url, retries, last_error))


def get_readings(lat, lon, start_date, end_date):
    data = fetch_json(build_api_url(lat, lon, start_date, end_date))
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("sea_surface_temperature", [])
    if not times or not temps:
        raise RuntimeError("Open-Meteo returned no hourly data: {}".format(data))

    readings = []
    for iso_time, temp in zip(times, temps):
        moment = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M")
        if moment.hour not in RECORD_HOURS:
            continue
        if temp is None:
            continue
        readings.append((moment, round(float(temp), 1)))
    readings.sort(key=lambda item: item[0])
    return readings


def backfill_location(location):
    csv_file = location["csv_file"]
    end_date = date.today().isoformat()
    readings = get_readings(
        location["lat"], location["lon"], location["start_date"], end_date)
    with open(csv_file, "w") as file_object:
        file_object.write("date,temp\n")
        for moment, temp in readings:
            timestamp = moment.strftime("%Y-%m-%d %H:%M:%S")
            file_object.write("{},{}\n".format(timestamp, temp))
    print("{}: wrote {} record(s) to {} ({} .. {}).".format(
        location["name_en"], len(readings), csv_file,
        readings[0][0] if readings else "-",
        readings[-1][0] if readings else "-"))


def main():
    wanted = sys.argv[1] if len(sys.argv) > 1 else None
    targets = [l for l in LOCATIONS if wanted is None or l["slug"] == wanted]
    if not targets:
        slugs = ", ".join(l["slug"] for l in LOCATIONS)
        raise SystemExit("Unknown slug {!r}. Known slugs: {}".format(wanted, slugs))
    for location in targets:
        backfill_location(location)


if __name__ == '__main__':
    main()
