import requests
import pandas as pd
import re
import numpy as np
import geopandas as gpd
from scipy.spatial import Voronoi, voronoi_plot_2d
from shapely.geometry import Polygon, MultiPolygon
import folium
import json
import matplotlib.pyplot as plt



CLIENT_ID = 'c31090ab-d96e-46e5-a477-a5afc5180351'
CLIENT_SECRET = '221361d1-db05-46e0-9ff9-bcf0cd289d3c'

def get_stations():
    endpoint = 'https://frost.met.no/sources/v0.jsonld'
    parameters = {
    #    'elements': 'mean(air_temperature P1D)',
    #    'referencetime': '2010-04-01/2010-04-03',
    }
    r = requests.get(endpoint, parameters, auth=(CLIENT_ID,''))
    json = r.json()
    if r.status_code == 200:
        data = json['data']
    else:
        print('Error! Returned status code %s' % r.status_code)
        print('Message: %s' % json['error']['message'])
        print('Reason: %s' % json['error']['reason'])

    df = pd.DataFrame(data)
    df = df[df['@type'] == 'SensorSystem']
    weater_stations = df['id'].unique()
    return weater_stations, df

def get_available_timeseries(id):
    endpoint = 'https://frost.met.no/observations/availableTimeSeries/v0.jsonld'
    parameters = {
        'sources': f'{id}',
        'timeoffsets' : 'PT0H',
        'timeresolutions' : 'PT1H',
        'elements': 'air_temperature',
        'referencetime': '2022-01-01/2023-01-01',
    }
    r = requests.get(endpoint, parameters, auth=(CLIENT_ID,''))
    json = r.json()
    if r.status_code == 200:
        data = json['data']
        df = pd.DataFrame(data)
        df['validFrom'] = pd.to_datetime(df['validFrom'])
        df = df.sort_values(by='validFrom', ascending=False)
        df = df.reset_index()
        df_row = df.iloc[0,:]
        uri = df_row.uri
    else:
        uri = None
    return uri

def get_timeseries(uri):
    pattern = r"(referencetime=)[^&]+"
    new_referencetime = "referencetime=2022-01-01/2023-01-01"
    endpoint = re.sub(pattern, new_referencetime, uri)
    parameters = {}
    r = requests.get(endpoint, parameters, auth=(CLIENT_ID,''))
    json = r.json()
    if r.status_code == 200:
        data = json['data']
        df = pd.DataFrame(data)
        air_temperature = np.zeros(8760)
        for i in range(0, len(df)):
            air_temperature[i] = df['observations'][i][0]['value']
    else:
        air_temperature = None
    return air_temperature
  

weather_stations, df_weather_stations = get_stations()

air_temperatures, lats, longs, names = [], [], [], []
j = 0
df_air_temperature = pd.DataFrame()
for index, weather_station in enumerate(weather_stations):
    uri = get_available_timeseries(id=weather_station)
    if uri != None:
        air_temperature = get_timeseries(uri=uri)
        if isinstance(air_temperature, np.ndarray):
            df_weather_station = df_weather_stations[df_weather_stations['id'] == weather_station]
            df_weather_station_geometry = df_weather_station['geometry'].reset_index()['geometry'][0]['coordinates']
            lat, long = df_weather_station_geometry[1], df_weather_station_geometry[0]
            name = df_weather_station['name'].to_numpy()[0]
            
            air_temperatures.append(air_temperature)
            lats.append(lat)
            longs.append(long)
            names.append(name)

            df_air_temperature[name] = air_temperature
            print(f'Nr. {j}. Indeks nr. {index}.')
            if j == 10000:
                break
            j = j + 1

df_station_data = pd.DataFrame({
    'Navn' : names,
    'Latitude' : lats,
    'Longitude' : longs,
    'Lufttemperatur' : air_temperatures,
})

df_station_data.to_csv('stations.csv')
df_air_temperature.to_csv('temperatures.csv')