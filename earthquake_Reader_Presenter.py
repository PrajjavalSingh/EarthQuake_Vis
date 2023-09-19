import csv
import requests
import sqlite3
from io import StringIO
import pandas as pd

import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point

#starttime and endtime format yyyy#mm##dd
URL = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime=2023-09-09&endtime=2023-09-13"
try:
    earthquake_data_resp = requests.get( URL )
    earthquake_data_resp.raise_for_status()

    earthquake_csv = StringIO( earthquake_data_resp.text )
    df = pd.read_csv( earthquake_csv )

except requests.exceptions.RequestException as e:
    print( "Error:", e )
except StopIteration:
    print( "The CSV file appears to be empty." )
except csv.Error as e:
    print( "CSV Error:", e )
except Exception as e:
    print( "An unexpected error occurred:", e )

conn = sqlite3.connect('EarthQuake.db')
df.to_sql( 'EarthQuake_Data_Table', conn, if_exists='replace', index=False )

conn.commit()

cursor = conn.cursor()
query = 'SELECT * FROM EarthQuake_Data_Table ORDER BY time ASC'
try:
    cursor.execute( query )
except Exception as e:
    print( "Cursor execution raised exception : ", e )

rows = cursor.fetchall()

print(rows[0])

query = 'SELECT latitude FROM EarthQuake_Data_Table'
cursor.execute( query )
lat = cursor.fetchone()
latitudes = []
while lat is not None:
    latitudes.append(lat[0])
    lat = cursor.fetchone()

#latitudes = [list(lat) for lat in latitudes]

query = 'SELECT longitude FROM EarthQuake_Data_Table'
cursor.execute( query )
lon = cursor.fetchone()
longitudes = []
while lon is not None:
    longitudes.append(lon[0])
    lon = cursor.fetchone()

conn.close()

coordinates = list( zip(longitudes,latitudes) )
geometry = [Point(lon,lat) for lon,lat in coordinates]

# Create a GeoDataFrame from the points
world = gpd.read_file( gpd.datasets.get_path('naturalearth_lowres') )
ax = world.plot( figsize=(10,10), color='white', edgecolor='black' )
gdf = gpd.GeoDataFrame( geometry, columns=['geometry'] , crs="EPSG:4326" )
gdf.plot( ax=ax, marker='^', color='red', markersize=5 )

# Show the plot
plt.show()
