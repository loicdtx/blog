from datetime import datetime
import requests

end_point = 'https://earthquake.usgs.gov/fdsnws/event/1/query'

params = {'starttime': datetime(2017, 9, 8, 4, 30, 0),
          'endtime': datetime(2017, 9, 11, 4, 30, 0),
          'maxlatitude': 18,
          'minlatitude': 12.5,
          'maxlongitude': -91,
          'minlongitude': -103,
          'minmagnitude': 5,
          'orderby': 'time-asc',
          'format': 'geojson'}

r = requests.get(end_point, params = params)
if r.status_code == 200:
    with open('../html/data/eathquakes.geojon', 'w') as dst:
        dst.write(r.text)
