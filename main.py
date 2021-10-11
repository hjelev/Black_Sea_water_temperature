# Parse water temperature data from www.stringmeteo.com 
# and save it as csv file so grafana can visualize it
# Python 3.9
import pandas as pd
import csv

baseurl = "http://192.168.0.106:8000/site/sea_water_"
# baseurl = "https://www.stringmeteo.com/synop/sea_water.php?year="

def get_data(from_date, to_date, raw1, raw2):
	result = {"date":"temp"}
	for year in range(from_date, to_date):
		print(year)
		url = baseurl + str(year) + ".html"
#		url = baseurl + str(year) # Use this to parse stringmeteo.com site
		tables = pd.read_html(url, encoding="utf8") # Returns list of all tables on page
		for i, table in enumerate(tables):
			data = table.drop(labels=[0,1], axis=0)
			# read the needed columns 
			first = data[[0,3]]
			second = data[[raw1,raw2]]
			# combine the 2 columns 
			fdata = dict(zip(str(year) +"-"+ str(i + 1).zfill(2) + "-" + first.loc[:,0]+" 00:00:00", first.loc[:,3])) | \
			dict(zip(str(year) +"-"+ str(i + 1).zfill(2) + "-" + second.loc[:,raw1]+" 00:00:00", second.loc[:,raw2])) 
			result = result | fdata
		# delete empty data	
		for k in list(result.keys()):
			if "." not in str(result[k]):
				del result[k]
	return result	
		
def combine_data():
	results = {"date":"temp"}
	# parse the data in 3 runs as diferent periods have different data
	results = results | get_data(2000,2011,6,9) 
	results = results | get_data(2011,2014,7,10) 
	results = results | get_data(2014,2022,5,8) 
	return results
	
def save_to_csv(results):	
	csv_file = "sea_water_temp.csv"
	with open(csv_file, 'w') as csv_file:  
		writer = csv.writer(csv_file)
		for key, value in results.items():
		   writer.writerow([key, value])
		   
if __name__ == '__main__':		   
	save_to_csv(combine_data())

# 2000 - 2010
# 6 - 9

# 2011 - 2013
# 7 - 10

# 2014 - 2021
# 5 - 8 
