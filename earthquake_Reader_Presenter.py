import sys
import requests
import sqlite3
from io import StringIO
import pandas as pd
import tkinter
from tkinter import messagebox
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import numpy as np


#starttime and endtime format yyyy-mm-dd
class DataFetcherAndPresenter:
    def __init__(self, starttime, endtime, minmag, maxmag ):
        self.starttime = starttime
        self.endtime = endtime
        self.minmag= minmag
        self.maxmag = maxmag

    @staticmethod
    def colorList():
        yellow = np.array( [1.0,1.0,0.0] )
        red = np.array( [1.0,0.0,0.0] )
        color_grad = np.linspace( yellow, red, 10 )
        hex_colors = ['#%02x%02x%02x' % (int(r * 255), int(g * 255), int(b * 255)) for r, g, b in color_grad]
        return hex_colors
    
    @staticmethod
    def getColor(r,g,b):
        return (r/256,g/256,b/256)

    def fetchdata(self):
        URL = "https://earthquake.usgs.gov/fdsnws/event/1/query?format=csv&starttime="+self.starttime+"&endtime="+self.endtime+"&minmagnitude="+self.minmag+"&maxmagnitude="+self.maxmag
        try:
            earthquake_data_resp = requests.get( URL )
            earthquake_data_resp.raise_for_status()

            earthquake_csv = StringIO( earthquake_data_resp.text )
            df = pd.read_csv( earthquake_csv )
            if df.empty:
                messagebox.showinfo("Information","There is no data to fetch")

        except requests.exceptions.RequestException as e:
            print( "Error:", e )
        except IOError as e:
            print( "Exception from creating csv : ", e )
        except Exception as e:
            print( "An unexpected error occurred:", e )

        self.conn = conn = sqlite3.connect('EarthQuake.db')
        df.to_sql( 'EarthQuake_Data_Table', conn, if_exists='replace', index=False )

        conn.commit()

    def getLatLongCoordinatesAndValidMags(self):
        coordinates = []
        mags = []
        for val in range(int(self.minmag),int(self.maxmag)):
            upper_bound = val + 0.999999999
            query = 'SELECT latitude FROM EarthQuake_Data_Table WHERE mag BETWEEN '+ str(val) +' AND ' + str(upper_bound)
            cursor = self.conn.cursor()
            try:
                cursor.execute( query )
            except sqlite3.Error as e:
                print( "Error in executing query : ", e )
            
            lat = cursor.fetchone()
            if lat is None:
                continue

            latitudes = []
            while lat is not None:
                latitudes.append(lat[0])
                lat = cursor.fetchone()

            query = 'SELECT longitude FROM EarthQuake_Data_Table WHERE mag BETWEEN '+ str(val) +' AND ' + str(upper_bound)
            cursor.execute( query )
            lon = cursor.fetchone()
            longitudes = []
            #mag_range = 
            while lon is not None:
                longitudes.append(lon[0])
                lon = cursor.fetchone()

            coordinates.append( list(zip(longitudes,latitudes)) )
            mags.append(val)
        
        return coordinates, mags

    def closeConn(self):
        self.conn.close()

    def displayOnWorldMap(self,coordinates,colidxs):
        world = gpd.read_file( gpd.datasets.get_path('naturalearth_lowres') )
        ax = world.plot( figsize=(12,5), color=DataFetcherAndPresenter.getColor(102,205,0), edgecolor=DataFetcherAndPresenter.getColor(50,100,120) ) 
        ax.set_facecolor( DataFetcherAndPresenter.getColor(0,139,139) )
        col_list = DataFetcherAndPresenter.colorList()
        idx = 0
        for coords in coordinates:
            geometry = [Point(lon,lat) for lon,lat in coords]
            # Create a GeoDataFrame from the points
            gdf = gpd.GeoDataFrame( geometry, columns=['geometry'] , crs="EPSG:4326" )
            color = col_list[colidxs[idx]]
            gdf.plot( ax=ax, marker='^', color=color, markersize=5 )
            idx += 1

        # Show the plot     
        plt.show()

nr_args = len(sys.argv)
if nr_args < 2:
    root = tkinter.Tk()
    root.withdraw()
    messagebox.showerror("Error","Insufficient number of arguments, expected start and end date")
else:
    startdate = sys.argv[1]
    enddate = sys.argv[2]
    minmag = sys.argv[3]
    maxmag = sys.argv[4]
    earthquakedata = DataFetcherAndPresenter(startdate,enddate,minmag,maxmag)
    earthquakedata.fetchdata()
    coordinates, colidxs = earthquakedata.getLatLongCoordinatesAndValidMags()
    earthquakedata.displayOnWorldMap( coordinates, colidxs )