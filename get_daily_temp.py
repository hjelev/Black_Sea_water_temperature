# Parse water temperature data from www.stringmeteo.com 
# and save it as csv file so grafana can visualize it
# Python 3.9
import pandas as pd
from datetime import date
import csv
from datetime import datetime

baseurl = "https://www.stringmeteo.com/synop/sea_water.php?year="
csv_file = "sea_water_temp.csv"
	
def get_data():
	url = baseurl + str(date.today().year) # Use this to parse stringmeteo.com site
	tables = pd.read_html(url, encoding="utf8") # Returns list of all tables on page
	data = tables[len(tables)-1] # Get the last table
	# TBD: need to take care for Feb as its shorter
	if date.today().day < 17: 
		data = data[[0,1,3]]
		index = [0,1,3]
		row_to_extract = date.today().day * 3 - 1
	else:
		data = data[[5,6,8]]
		index = [5,6,8]
		row_to_extract = date.today().day * 3 - 1 - (16*3)

	data = data.iloc[ row_to_extract : row_to_extract + 3 ]

	# get the date of the last record in the csv
	with open(csv_file, "r") as file_object:
		last_line = file_object.readlines()[-1].split(",")[0].strip()
		last_record_date = datetime.strptime(last_line, '%Y-%m-%d %H:%M:%S')
	# Check and save daily temp. records
	for x, row in data.iterrows():
		timestamp = "{}-{}-{} {}:00:00".format(date.today().year, date.today().month, row[index[0]], row[index[1]].zfill(2))
		record_date = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
		if record_date > last_record_date:
			with open(csv_file, "a") as file_object:
				new_line = "{},{}\n".format(timestamp,  row[index[2]])
				file_object.write(new_line)
	
	return 	
		
if __name__ == '__main__':		   
	get_data()
