# Parse water temperature data from www.stringmeteo.com 
# and save it as csv file. Python 3.7 is needed
import io
import time
import pandas as pd
from datetime import date
from datetime import datetime
from bs4 import BeautifulSoup
import urllib.request

baseUrlAir = "https://www.sinoptik.bg/burgas-bulgaria-100732770"
baseurl = "https://www.stringmeteo.com/synop/sea_water.php?year="
csv_file = "sea_water_temp.csv"

# The server serves a stub page (no tables) to the default urllib User-Agent
# from cloud/CI IPs, so fetch with a browser User-Agent and retry.
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/124.0.0.0 Safari/537.36")


def fetch_html(url, retries=3, delay=5):
    last_error = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as error:  # noqa: BLE001 - retry on any network error
            last_error = error
            if attempt < retries - 1:
                time.sleep(delay)
    raise RuntimeError("Failed to fetch {} after {} attempts: {}".format(
        url, retries, last_error))


def get_data_for_current_month(base_url):
    url = base_url + str(date.today().year)  # Use this to parse stringmeteo.com site
    html = fetch_html(url)
    tables = pd.read_html(io.StringIO(html))  # Returns list of all tables on page
    if date.today().month - 1 >= len(tables):
        raise RuntimeError(
            "Expected at least {} tables for month {}, found {}".format(
                date.today().month, date.today().month, len(tables)))
    data = tables[date.today().month - 1]
    return data


def extract_today_temperatures(data):
    # take care for Feb as its shorter
    if date.today().month == 2:
        month_middle = 16
    else:
        month_middle = 17

    if date.today().day < month_middle:
        data = data[[0, 1, 3]]
        index = [0, 1, 3]
        row_to_extract = date.today().day * 3 - 1
    else:
        data = data[[5, 6, 8]]
        index = [5, 6, 8]
        row_to_extract = date.today().day * 3 - 1 - ((month_middle - 1) * 3)
    data = data.iloc[row_to_extract: row_to_extract + 3]
    return data, index


def get_last_record_date(csv_file_name):
    # get the date of the last record in the csv
    with open(csv_file_name, "r") as file_object:
        last_line = file_object.readlines()[-1].split(",")[0].strip()
        last_record_date = datetime.strptime(last_line, '%Y-%m-%d %H:%M:%S')
    return last_record_date


def save_new_data(data, index, last_record_date, csv_file_name):
    for x, row in data.iterrows():
        water_temp = str(row[index[2]])
        # skip empty records
        if ("nan" not in water_temp) and ("-" not in water_temp):
            timestamp = "{}-{:02d}-{} {}:00:00".format(date.today().year,
                                                   date.today().month,
                                                   row[index[0]],
                                                   row[index[1]].zfill(2))
            record_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            if record_date > last_record_date:
                with open(csv_file_name, "a") as file_object:
                    new_line = "{},{}\n".format(timestamp, water_temp)
                    file_object.write(new_line)

def get_data():
    data = get_data_for_current_month(baseurl)
    data, index = extract_today_temperatures(data)
    last_record_date = get_last_record_date(csv_file)
    save_new_data(data, index, last_record_date, csv_file)


if __name__ == '__main__':
    get_data()
