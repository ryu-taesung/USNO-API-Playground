import json
import urllib.request
import datetime as dt
import xml.etree.ElementTree as ET
import time
import sys

def get_latlong_from_zip():
    zipcode = input("Enter zip code: ")
    lat_long_lookup_url = f"https://graphical.weather.gov/xml/sample_products/browser_interface/ndfdXMLclient.php?listZipCodeList={zipcode}"

    zip_req = urllib.request.urlopen(lat_long_lookup_url)
    zip_data = zip_req.read()
    tree = ET.fromstring(zip_data)
    lat_long = tree.find('latLonList').text

    with open('latlong.txt', 'w', encoding='utf-8') as f:
        f.write(lat_long)
    
    return lat_long

def get_latlong_from_file():
    with open('latlong.txt', 'r', encoding='utf-8') as f:
        return f.read()

def get_moon_and_sun_data(date, lat_long):
    api_url = f"https://aa.usno.navy.mil/api/rstt/oneday?date={date}&coords={lat_long}&tz=-5&dst=true"
    req = urllib.request.urlopen(api_url)
    data = req.read()
    encoding = req.info().get_content_charset('utf-8')
    resp_json = json.loads(data.decode(encoding))

    moon_illum = resp_json['properties']['data']['fracillum']
    moon_phase = resp_json['properties']['data']['curphase']
    day_of_week = resp_json['properties']['data']['day_of_week']
    print(f"\nDate: {date} {day_of_week}")
    print(f"Moon phase: {moon_phase}, Illumination: {moon_illum}")

    for item in resp_json['properties']['data']['sundata']:
        if item['phen'].lower() in ['rise','set']:
            print(f"{item['phen']}: {item['time']}")

if __name__ == "__main__":
    num_days = 4  # Default value
    if len(sys.argv) == 2:
        num_days = int(sys.argv[1])
        if num_days > 30:
            print("Maximum allowed days is 30. Setting to 30.")
            num_days = 30

    try:
        lat_long = get_latlong_from_file()
    except FileNotFoundError:
        lat_long = get_latlong_from_zip()

    today = dt.datetime.today()

    for i in range(num_days):
        date_str = (today + dt.timedelta(days=i)).strftime('%Y-%m-%d')
        get_moon_and_sun_data(date_str, lat_long)
        time.sleep(1)  # To prevent sending requests too quickly
