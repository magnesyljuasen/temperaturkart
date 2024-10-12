import requests
import pandas as pd
import re
import numpy as np
import geopandas as gpd
from scipy.spatial import Voronoi, voronoi_plot_2d
from shapely.geometry import Polygon, MultiPolygon, Point
import folium
import json
import matplotlib.pyplot as plt

df_station_data = pd.read_csv('stations.csv')
df_temperatures = pd.read_csv('temperatures.csv')

#--
points = np.column_stack((df_station_data['Longitude'], df_station_data['Latitude']))
vor = Voronoi(points)

polygons = []
for region in vor.regions:
    if not -1 in region and len(region) > 0:  # Check for finite regions
        polygon = vor.vertices[region]
        polygons.append(polygon)

polygon_data = []
for i, polygon in enumerate(polygons):
    for vertex in polygon:
        polygon_data.append({'Polygon_ID': i, 'X': vertex[0], 'Y': vertex[1]})

shapely_polygons = [Polygon(polygon) for polygon in polygons]
gdf = gpd.GeoDataFrame(geometry=shapely_polygons)
gdf['PolygonID'] = gdf.index


points_geometry = [Point(xy) for xy in zip(df_station_data['Longitude'], df_station_data['Latitude'])]
points_gdf = gpd.GeoDataFrame(df_station_data, geometry=points_geometry, crs="EPSG:4326")
joined = gpd.sjoin(gdf, points_gdf, how="inner", predicate="intersects")  # or "within" depending on your need
#joined = joined[['geometry', 'Navn', 'Latitude', 'Longitude', 'PolygonID']]

joined.to_file("polygons.geojson", driver="GeoJSON", encoding='utf-8')

with open('polygons.geojson', 'r', encoding='utf-8') as f:
    geojson_data = f.read()


#--
m = folium.Map(location=[62, 15], zoom_start=5)

folium.GeoJson(
    geojson_data,
    name='geojson',
    tooltip=folium.GeoJsonTooltip(
        fields=['Navn'],  # Add any fields you want to display
        aliases=['PolygonID:'],  # Alias for the field
        localize=True,
        sticky=False
    )
).add_to(m)

#for idx, row in df_station_data.iterrows():
#    folium.Marker(
#        location=[row['Latitude'], row['Longitude']],
#        tooltip=row['Navn'],  # Popup with the name of the location
        #icon=folium.Icon(color='blue', icon='info-sign', icon_size=(10, 10))
#    ).add_to(m)

m.save('map_with_polygons.html')
