# Fetch Black Sea (Burgas Bay) water surface temperature from the
# Open-Meteo Marine API and append new readings to a csv file.
#
# Previous source (www.stringmeteo.com) was put behind a "SuperJS"
# JavaScript anti-bot wall that blocks cloud/CI IPs, so it can no longer
# be scraped from GitHub Actions. Open-Meteo is a free, key-less JSON API.
#
# Python 3.7+ , standard library only.
import json
import time
import urllib.request
from datetime import datetime, timezone

# Locations to collect. Each writes its own csv file.
# The exact Sinemorets town coords snap to a land-masked cell (all null);
# lat=42.06/lon=28.0 snaps to the nearest sea cell (42.21N, 28.13E).
LOCATIONS = [
    {"name": "Burgas",     "lat": 42.47, "lon": 27.55, "csv_file": "sea_water_temp.csv"},
    {"name": "Sinemorets", "lat": 42.06, "lon": 28.0,  "csv_file": "sinemorets_water_temp.csv"},
]


def build_api_url(lat, lon):
    return (
        "https://marine-api.open-meteo.com/v1/marine"
        "?latitude={lat}&longitude={lon}"
        "&hourly=sea_surface_temperature"
        "&timezone=UTC&past_days=3&forecast_days=1"
    ).format(lat=lat, lon=lon)


# Keep the same daily cadence as the historical series.
RECORD_HOURS = (6, 12, 18)


def fetch_json(url, retries=3, delay=5):
    last_error = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as error:  # noqa: BLE001 - retry on any network error
            last_error = error
            if attempt < retries - 1:
                time.sleep(delay)
    raise RuntimeError("Failed to fetch {} after {} attempts: {}".format(
        url, retries, last_error))


def get_readings(api_url):
    data = fetch_json(api_url)
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("sea_surface_temperature", [])
    if not times or not temps:
        raise RuntimeError("Open-Meteo returned no hourly data: {}".format(data))

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    readings = []
    for iso_time, temp in zip(times, temps):
        # API time format is e.g. "2026-06-28T12:00"
        moment = datetime.strptime(iso_time, "%Y-%m-%dT%H:%M")
        if moment.hour not in RECORD_HOURS:
            continue
        if moment > now:  # skip future/forecast hours
            continue
        if temp is None:
            continue
        readings.append((moment, round(float(temp), 1)))
    return readings


def get_last_record_date(csv_file_name):
    # get the date of the last record in the csv
    with open(csv_file_name, "r") as file_object:
        last_line = file_object.readlines()[-1].split(",")[0].strip()
        return datetime.strptime(last_line, "%Y-%m-%d %H:%M:%S")


def save_new_data(readings, last_record_date, csv_file_name):
    new_rows = [(m, t) for m, t in readings if m > last_record_date]
    new_rows.sort(key=lambda item: item[0])
    with open(csv_file_name, "a") as file_object:
        for moment, temp in new_rows:
            timestamp = moment.strftime("%Y-%m-%d %H:%M:%S")
            file_object.write("{},{}\n".format(timestamp, temp))
    return len(new_rows)


def update_location(location):
    csv_file = location["csv_file"]
    api_url = build_api_url(location["lat"], location["lon"])
    readings = get_readings(api_url)
    last_record_date = get_last_record_date(csv_file)
    added = save_new_data(readings, last_record_date, csv_file)
    print("{}: added {} new record(s).".format(location["name"], added))


def get_data():
    for location in LOCATIONS:
        try:
            update_location(location)
        except Exception as error:  # noqa: BLE001 - don't let one location abort the rest
            print("{}: failed - {}".format(location["name"], error))


if __name__ == '__main__':
    get_data()
