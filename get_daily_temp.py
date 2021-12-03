# Parse water temperature data from www.stringmeteo.com 
# and save it as csv file. Python 3.7 is needed
import pandas as pd
from datetime import date
from datetime import datetime
from bs4 import BeautifulSoup
import urllib

baseUrlAir = "https://www.sinoptik.bg/burgas-bulgaria-100732770"
baseurl = "https://www.stringmeteo.com/synop/sea_water.php?year="
csv_file = "sea_water_temp.csv"


def get_air_temp(url):
    html = urllib.request.urlopen(url )
    soup = BeautifulSoup(html, 'html.parser')
    div = soup.findAll('span', attrs={'class': 'wfCurrentTemp'})
    temp = div[0].text.split("°")[0]
    timestamp = "{}-{}-{} {}:00:00".format(datetime.today().year,
                                           datetime.today().month, datetime.today().day, datetime.today().hour)
    return temp

def get_data_for_current_month(base_url):
    url = base_url + str(date.today().year)  # Use this to parse stringmeteo.com site
    tables = pd.read_html(url, encoding="utf8")  # Returns list of all tables on page
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


def save_new_data(data, index, last_record_date, csv_file_name, temp):
    for x, row in data.iterrows():
        water_temp = str(row[index[2]])
        # skip empty records
        if ("nan" not in water_temp) and ("-" not in water_temp):
            timestamp = "{}-{}-{} {}:00:00".format(date.today().year,
                                                   date.today().month,
                                                   row[index[0]],
                                                   row[index[1]].zfill(2))
            record_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            if record_date > last_record_date:
                with open(csv_file_name, "a") as file_object:
                    new_line = "{},{},{}\n".format(timestamp, water_temp, temp)
                    file_object.write(new_line)


def get_data():
    data = get_data_for_current_month(baseurl)
    data, index = extract_today_temperatures(data)
    last_record_date = get_last_record_date(csv_file)
    save_new_data(data, index, last_record_date, csv_file, get_air_temp(baseUrlAir))


if __name__ == '__main__':
    get_data()
