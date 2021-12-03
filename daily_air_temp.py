from bs4 import BeautifulSoup
import urllib
from datetime import datetime


csv_file = "Burgas_air_temp.csv"
baseUrl = "https://www.sinoptik.bg/burgas-bulgaria-100732770"
html = urllib.request.urlopen(baseUrl )
soup = BeautifulSoup(html, 'html.parser')
div = soup.findAll('span', attrs={'class': 'wfCurrentTemp'})
temp = div[0].text.split("°")[0]
timestamp = "{}-{}-{} {}:00:00".format(datetime.today().year,
                                       datetime.today().month, datetime.today().day, datetime.today().hour)
new_line = "{},{}\n".format(timestamp, temp)
print(new_line)
with open(csv_file, "a") as file_object:
    file_object.write(new_line)

