# Fetch air temperature, UV index, wind speed and a short weather forecast
# from the Open-Meteo Forecast API (the same provider as the sea-temperature
# pipeline in get_daily_temp.py) and store a rolling 5-days-back +
# 5-days-forecast window per location, plus current conditions and a
# trailing 24h hourly temperature series.
#
# Unlike the sea-temperature csv files, this is not an append-only history:
# forecasts change every run and past days can be revised, so each run
# overwrites docs/weather/<slug>.json with the freshest full window rather
# than accumulating rows. The hourly series relies on Open-Meteo's own
# past_hours=24 window to self-limit to the last 24h - no local purge
# bookkeeping needed.
#
# Python 3.7+, standard library only.
import json
import os
import time
import urllib.request
from datetime import datetime, timezone

# Locations to collect are defined in locations.py, the single source of
# truth shared with get_daily_temp.py, backfill.py and build_site.py.
from locations import LOCATIONS

DAILY_VARS = (
    "temperature_2m_max,temperature_2m_min,"
    "uv_index_max,wind_speed_10m_max,weathercode"
)
CURRENT_VARS = (
    "temperature_2m,apparent_temperature,"
    "relative_humidity_2m,wind_speed_10m,weathercode"
)
HOURLY_VARS = "temperature_2m,weathercode"


def build_api_url(lat, lon):
    return (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude={lat}&longitude={lon}"
        "&daily={daily}&current={current}&hourly={hourly}"
        "&past_hours=24&forecast_hours=0"
        "&timezone=UTC&past_days=5&forecast_days=5"
    ).format(lat=lat, lon=lon, daily=DAILY_VARS,
              current=CURRENT_VARS, hourly=HOURLY_VARS)


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


def parse_daily(data):
    daily = data.get("daily", {})
    dates = daily.get("time", [])
    if not dates:
        raise RuntimeError("Open-Meteo returned no daily data: {}".format(data))

    temp_max = daily.get("temperature_2m_max", [])
    temp_min = daily.get("temperature_2m_min", [])
    uv_max = daily.get("uv_index_max", [])
    wind_max = daily.get("wind_speed_10m_max", [])
    code = daily.get("weathercode", [])

    days = []
    for i, date in enumerate(dates):
        days.append({
            "date": date,
            "temp_max": temp_max[i] if i < len(temp_max) else None,
            "temp_min": temp_min[i] if i < len(temp_min) else None,
            "uv_max": uv_max[i] if i < len(uv_max) else None,
            "wind_max": wind_max[i] if i < len(wind_max) else None,
            "code": code[i] if i < len(code) else None,
        })
    return days


def parse_current(data):
    current = data.get("current") or {}
    if "temperature_2m" not in current:
        return None
    return {
        "temp": current.get("temperature_2m"),
        "feels_like": current.get("apparent_temperature"),
        "humidity": current.get("relative_humidity_2m"),
        "wind": current.get("wind_speed_10m"),
        "code": current.get("weathercode"),
    }


def parse_hourly(data):
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    temps = hourly.get("temperature_2m", [])
    codes = hourly.get("weathercode", [])
    return [
        {
            "time": time,
            "temp": temps[i] if i < len(temps) else None,
            "code": codes[i] if i < len(codes) else None,
        }
        for i, time in enumerate(times)
    ]


def write_weather_file(slug, days, current, hourly):
    docs_dir = os.path.join(os.path.dirname(__file__), "docs", "weather")
    os.makedirs(docs_dir, exist_ok=True)
    path = os.path.join(docs_dir, "{}.json".format(slug))
    payload = {
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "days": days,
        "current": current,
        "hourly": hourly,
    }
    with open(path, "w") as file_object:
        json.dump(payload, file_object, indent=0)


def update_location(location):
    api_url = build_api_url(location["lat"], location["lon"])
    data = fetch_json(api_url)
    days = parse_daily(data)
    current = parse_current(data)
    hourly = parse_hourly(data)
    write_weather_file(location["slug"], days, current, hourly)
    print("{}: wrote {} day(s), current conditions, {} hourly reading(s).".format(
        location["name_en"], len(days), len(hourly)))


def get_data():
    for location in LOCATIONS:
        try:
            update_location(location)
        except Exception as error:  # noqa: BLE001 - don't let one location abort the rest
            print("{}: failed - {}".format(location["name_en"], error))


if __name__ == '__main__':
    get_data()
