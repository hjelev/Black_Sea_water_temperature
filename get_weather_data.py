# Fetch air temperature, UV index, wind speed and a short weather forecast
# from the Open-Meteo Forecast API (the same provider as the sea-temperature
# pipeline in get_daily_temp.py) and store a rolling 5-days-back +
# 5-days-forecast window per location, plus current conditions and a
# trailing 48h hourly temperature series. Each file also carries sea state
# (waves + a sea-temperature forecast) from the Open-Meteo Marine API and
# air quality / pollen from the Open-Meteo Air Quality API; either may be
# null if that API fails, without losing the weather itself.
#
# Unlike the sea-temperature csv files, this is not an append-only history:
# forecasts change every run and past days can be revised, so each run
# overwrites docs/weather/<slug>.json with the freshest full window rather
# than accumulating rows. The hourly series relies on Open-Meteo's own
# past_hours=48 window to self-limit to the last 48h - no local purge
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
    "uv_index_max,wind_speed_10m_max,wind_direction_10m_dominant,weathercode,"
    "sunrise,sunset"
)
CURRENT_VARS = (
    "temperature_2m,apparent_temperature,"
    "relative_humidity_2m,wind_speed_10m,wind_direction_10m,"
    "uv_index,weathercode"
)
HOURLY_VARS = "temperature_2m,weathercode"
MARINE_CURRENT_VARS = "wave_height,wave_direction,wave_period,sea_surface_temperature"
MARINE_DAILY_VARS = "wave_height_max,wave_direction_dominant,wave_period_max"
POLLEN_TYPES = ("alder", "birch", "grass", "mugwort", "olive", "ragweed")
AIR_CURRENT_VARS = "european_aqi,pm2_5,pm10," + ",".join(
    "{}_pollen".format(p) for p in POLLEN_TYPES)


def build_api_url(lat, lon):
    return (
        "https://api.open-meteo.com/v1/forecast"
        "?latitude={lat}&longitude={lon}"
        "&daily={daily}&current={current}&hourly={hourly}"
        "&past_hours=48&forecast_hours=0"
        "&timezone=UTC&past_days=5&forecast_days=5"
    ).format(lat=lat, lon=lon, daily=DAILY_VARS,
              current=CURRENT_VARS, hourly=HOURLY_VARS)


def build_marine_url(lat, lon):
    # Hourly SST is averaged per day below: the Marine API has no daily SST.
    return (
        "https://marine-api.open-meteo.com/v1/marine"
        "?latitude={lat}&longitude={lon}"
        "&current={current}&daily={daily}&hourly=sea_surface_temperature"
        "&timezone=UTC&past_days=3&forecast_days=7"
    ).format(lat=lat, lon=lon, current=MARINE_CURRENT_VARS, daily=MARINE_DAILY_VARS)


def build_air_url(lat, lon):
    return (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        "?latitude={lat}&longitude={lon}&current={current}&timezone=UTC"
    ).format(lat=lat, lon=lon, current=AIR_CURRENT_VARS)


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
    wind_dir = daily.get("wind_direction_10m_dominant", [])
    code = daily.get("weathercode", [])
    # ISO times in UTC (timezone=UTC), e.g. "2026-10-22T04:41".
    sunrise = daily.get("sunrise", [])
    sunset = daily.get("sunset", [])

    days = []
    for i, date in enumerate(dates):
        days.append({
            "date": date,
            "temp_max": temp_max[i] if i < len(temp_max) else None,
            "temp_min": temp_min[i] if i < len(temp_min) else None,
            "uv_max": uv_max[i] if i < len(uv_max) else None,
            "wind_max": wind_max[i] if i < len(wind_max) else None,
            "wind_dir": wind_dir[i] if i < len(wind_dir) else None,
            "code": code[i] if i < len(code) else None,
            "sunrise": sunrise[i] if i < len(sunrise) else None,
            "sunset": sunset[i] if i < len(sunset) else None,
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
        "wind_dir": current.get("wind_direction_10m"),
        "uv": current.get("uv_index"),
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


def parse_marine(data):
    """Current sea state plus one row per day: max wave height, dominant
    wave direction, max period and the daily mean/min/max sea temperature."""
    current = data.get("current") or {}
    daily = data.get("daily", {})
    sst_by_day = {}
    hourly = data.get("hourly", {})
    for time_str, sst in zip(hourly.get("time", []),
                             hourly.get("sea_surface_temperature", [])):
        if sst is not None:
            sst_by_day.setdefault(time_str[:10], []).append(sst)

    def pick(key, i):
        values = daily.get(key, [])
        return values[i] if i < len(values) else None

    days = []
    for i, date in enumerate(daily.get("time", [])):
        sst = sst_by_day.get(date)
        days.append({
            "date": date,
            "wave_max": pick("wave_height_max", i),
            "wave_dir": pick("wave_direction_dominant", i),
            "period_max": pick("wave_period_max", i),
            "sst": round(sum(sst) / len(sst), 1) if sst else None,
            "sst_min": min(sst) if sst else None,
            "sst_max": max(sst) if sst else None,
        })
    return {
        "current": {
            "wave": current.get("wave_height"),
            "wave_dir": current.get("wave_direction"),
            "period": current.get("wave_period"),
            "sst": current.get("sea_surface_temperature"),
        } if current else None,
        "days": days,
    }


def parse_air(data):
    current = data.get("current") or {}
    if "european_aqi" not in current:
        return None
    return {
        "aqi": current.get("european_aqi"),
        "pm2_5": current.get("pm2_5"),
        "pm10": current.get("pm10"),
        "pollen": {p: current.get("{}_pollen".format(p)) for p in POLLEN_TYPES},
    }


def fetch_optional(url, parse, label):
    """Marine and air data are extras: a failure leaves them null instead
    of dropping the location's weather file."""
    try:
        return parse(fetch_json(url))
    except Exception as error:  # noqa: BLE001
        print("  {} unavailable: {}".format(label, error))
        return None


def append_current(hourly, current, now):
    # Open-Meteo's hourly series only carries fully-finalized hours, so it
    # can lag the live "current" reading by 1-2h. Splice current on as the
    # newest point (using the same `now` as the file's "updated" field) so
    # the chart's last point always matches what just got fetched, instead
    # of looking stuck an hour or two behind.
    if current is None:
        return hourly
    now_str = now.strftime("%Y-%m-%dT%H:%M")
    if hourly and now_str <= hourly[-1]["time"]:
        return hourly
    return hourly + [{
        "time": now_str,
        "temp": current["temp"],
        "code": current["code"],
    }]


def write_weather_file(slug, days, current, hourly, now, marine=None, air=None):
    docs_dir = os.path.join(os.path.dirname(__file__), "docs", "weather")
    os.makedirs(docs_dir, exist_ok=True)
    path = os.path.join(docs_dir, "{}.json".format(slug))
    payload = {
        "updated": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "days": days,
        "current": current,
        "hourly": hourly,
        "marine": marine,
        "air": air,
    }
    with open(path, "w") as file_object:
        json.dump(payload, file_object, indent=0)


def update_location(location):
    api_url = build_api_url(location["lat"], location["lon"])
    data = fetch_json(api_url)
    now = datetime.now(timezone.utc)
    days = parse_daily(data)
    current = parse_current(data)
    hourly = append_current(parse_hourly(data), current, now)
    marine = fetch_optional(build_marine_url(location["lat"], location["lon"]),
                            parse_marine, "marine")
    air = fetch_optional(build_air_url(location["place_lat"], location["place_lon"]),
                         parse_air, "air quality")
    write_weather_file(location["slug"], days, current, hourly, now, marine, air)
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
