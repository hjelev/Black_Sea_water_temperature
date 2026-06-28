# One-time historical backfill of Sinemorets sea surface temperature from the
# Open-Meteo Marine API archive into sinemorets_water_temp.csv.
#
# The archive for this Black Sea cell only reaches back to 2023-01-01 (earlier
# dates return null). Run once locally; the resulting csv is committed and then
# kept up to date by get_daily_temp.py. Re-running regenerates the file.
#
# Python 3.7+ , standard library only.
import json
import time
import urllib.request
from datetime import date, datetime

csv_file = "sinemorets_water_temp.csv"

# Nearest valid sea cell to Sinemorets (snaps to 42.21N, 28.13E).
LATITUDE = 42.06
LONGITUDE = 28.0

START_DATE = "2023-01-01"

# Keep the same daily cadence as the rest of the series.
RECORD_HOURS = (6, 12, 18)


def build_api_url(start_date, end_date):
    return (
        "https://marine-api.open-meteo.com/v1/marine"
        "?latitude={lat}&longitude={lon}"
        "&hourly=sea_surface_temperature"
        "&timezone=UTC&start_date={start}&end_date={end}"
    ).format(lat=LATITUDE, lon=LONGITUDE, start=start_date, end=end_date)


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


def get_readings(end_date):
    data = fetch_json(build_api_url(START_DATE, end_date))
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


def main():
    end_date = date.today().isoformat()
    readings = get_readings(end_date)
    with open(csv_file, "w") as file_object:
        file_object.write("date,temp\n")
        for moment, temp in readings:
            timestamp = moment.strftime("%Y-%m-%d %H:%M:%S")
            file_object.write("{},{}\n".format(timestamp, temp))
    print("Wrote {} record(s) to {} ({} .. {}).".format(
        len(readings), csv_file,
        readings[0][0] if readings else "-",
        readings[-1][0] if readings else "-"))


if __name__ == '__main__':
    main()
