# Parse water temperature data from www.stringmeteo.com 
# and save it as csv file so grafana can visualize it
# Python 3.7
import csv
import pandas as pd
from datetime import date
from datetime import datetime

baseurl = "https://www.stringmeteo.com/synop/sea_water.php?year="
csv_file = "sea_water_temp.csv"

def get_data_for_current_month(baseurl):
	url = baseurl + str(date.today().year) # Use this to parse stringmeteo.com site
	tables = pd.read_html(url, encoding="utf8") # Returns list of all tables on page
	data = tables[len(tables)-1] # Get the last table
	return data	

def extract_today_data(data):
	# take care for Feb as its shorter
	if date.today().month == 2:
		month_middle = 16
	else:
		month_middle = 17

	if date.today().day < month_middle: 
		data = data[[0,1,3]]
		index = [0,1,3]
		row_to_extract = date.today().day * 3 - 1
	else:
		data = data[[5,6,8]]
		index = [5,6,8]
		row_to_extract = date.today().day * 3 - 1 - ((month_middle -1) * 3)
	data = data.iloc[ row_to_extract : row_to_extract + 3 ]
	return data, index

def get_last_record_date(csv_file):
	# get the date of the last record in the csv
	with open(csv_file, "r") as file_object:
		last_line = file_object.readlines()[-1].split(",")[0].strip()
		last_record_date = datetime.strptime(last_line, '%Y-%m-%d %H:%M:%S')
	return last_record_date

def save_new_data(data, index, last_record_date):
	for x, row in data.iterrows():
		# skip empty records
		if "nan" not in str(row[index[2]]):
			timestamp = "{}-{}-{} {}:00:00".format(date.today().year,
				date.today().month, row[index[0]], row[index[1]].zfill(2))
			record_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
			if record_date > last_record_date:
				with open(csv_file, "a") as file_object:
					new_line = "{},{}\n".format(timestamp,  row[index[2]])
					file_object.write(new_line)

def get_data():
	data = get_data_for_current_month(baseurl)
	data, index = extract_today_data(data)
	last_record_date = get_last_record_date(csv_file)
	save_new_data(data, index, last_record_date)

if __name__ == '__main__':
	get_data()
