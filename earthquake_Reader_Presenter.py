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

import plotly.express as px


#starttime and endtime format yyyy-mm-dd
class DataFetcherAndPresenter:
    def __init__(self, starttime, endtime, minmag, maxmag ):
        self.starttime = starttime
        self.endtime = endtime
        self.minmag = minmag
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
        col_list = DataFetcherAndPresenter.colorList()
        idx = -1
        custom_color_scale = []
        legends = []
        col_leg_map = {}
        coordinate_lists = []
        for coords in coordinates:
            idx = idx + 1
            magnitude_idx = colidxs[idx]
            col = col_list[magnitude_idx]
            key = f'Magnitude : {magnitude_idx}'
            custom_color_scale.append( col )
            col_leg_map[col] = key
            for lon, lat in coords:
                coordinate_lists.append({'Latitude': lat, 'Longitude': lon, 'Color' : col, 'Magnitude': magnitude_idx })
                legends.append( key )
                

        df = pd.concat([pd.DataFrame(data,index=[0]) for data in coordinate_lists])

        fig = px.scatter_geo(df,
                            lat = 'Latitude',
                            lon = 'Longitude',
                            color = 'Color',
                            title = f'Earthquakes between {self.starttime} - {self.endtime}',
                            scope = 'world',
                            projection ='natural earth',
                            color_discrete_sequence=custom_color_scale,
                            hover_name = legends,
                            width = 1500,
                            height = 750,
                            hover_data = { 'Color' : False }
                            )
        
        fig.update_layout(
                legend_title_text='Magnitude',
                showlegend=True,
                legend_traceorder='normal',
            )
        
        fig.for_each_trace(lambda trace: trace.update(name=col_leg_map.get(trace.name, trace.name)))
        
        fig.update_geos(
            showcoastlines=True,
            coastlinecolor='rgb(50,100,120)',
            showland=True,
            landcolor='rgb(102,205,0)',
            showocean=True,
            oceancolor='rgb(0,139,139)'
        )

        return fig.to_html( full_html=False )