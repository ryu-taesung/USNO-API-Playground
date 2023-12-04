def extract_sunrise_sunset(data_file_path):
    from datetime import date, datetime, timedelta, time
    import re
    
    # Utility functions
    def daterange(start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)
    
    def is_dst(dt):
        if dt.year < 2007:
            raise ValueError("Year not supported for DST check.")
        dst_start = datetime(dt.year, 3, 8, 2, 0)
        dst_start += timedelta(6 - dst_start.weekday())
        dst_end = datetime(dt.year, 11, 1, 2, 0)
        dst_end += timedelta(6 - dst_end.weekday())
        return dst_start <= dt < dst_end
    
    # Reading data from file
    with open(data_file_path, 'r') as file:
        lines = file.readlines()
    
    # Extract year
    year_match = re.findall(r'for\s(\d{4})', lines[1])
    if year_match:
        year = int(year_match[0])
    else:
        raise ValueError("Unable to extract year from the data.")
    
    lines = lines[9:]
    
    start_date = date(year, 1, 1)
    end_date = date(year, 12, 31) + timedelta(days=1)
    
    results = {}
    
    for single_date in daterange(start_date, end_date):
        month = int(single_date.strftime('%m'))
        day = int(single_date.strftime('%d'))
        line = lines[day-1][4:]
        start = 11*(month - 1)
        sunrise, sunset = line[start:start+9].split()
        time_sunrise = time(int(sunrise[0:2]), int(sunrise[2:]))
        time_sunset = time(int(sunset[0:2]), int(sunset[2:]))
        
        if is_dst(datetime.combine(single_date, time_sunrise)):
            dst_sunrise = datetime.combine(single_date, time_sunrise) + timedelta(hours=1)
            sunrise = str(dst_sunrise.time()).replace(':', '')[0:4]
        
        if is_dst(datetime.combine(single_date, time_sunset)):
            dst_sunset = datetime.combine(single_date, time_sunset) + timedelta(hours=1)
            sunset = str(dst_sunset.time()).replace(':', '')[0:4]
        
        key = single_date.strftime('%Y%m%d')
        results[key] = (sunrise, sunset)
    
    return results

# Main guard
if __name__ == "__main__":
    data_file_path = 'usno_sunrise_sunset_2024.txt'  # This can be changed or passed as an argument
    sunrise_sunset_data = extract_sunrise_sunset(data_file_path)
    for key, value in sunrise_sunset_data.items():
        print(f"{key} = {value[0]}, {value[1]}")
