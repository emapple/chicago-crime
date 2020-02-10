# Functions to read in data, for use in separate notebooks

import pandas as pd
import numpy as np
from shapely.geometry import point
import geopandas
import matplotlib.pyplot as plt

def read_crime_data(filename, usecols=[2, 5, 8, 19, 20], dtype={'Primary Type': str, 'Arrest': bool,
            'Latitude' : float, 'Longitude' : float}, clean=True, geofilename=None, **kwargs):
    """Convenience function for reading in crime data
    
    if clean, cleans data a bit
    if geofilename and clean, will replace missing Community Areas with those 
        inferred from their coordinates
    """
    data = pd.read_csv(filename, usecols=usecols, dtype=dtype, quotechar='"', index_col='Date', **kwargs)
    data.index = pd.to_datetime(data.index, format='%m/%d/%Y %I:%M:%S %p')
    if clean:
        if 'Description' in data.columns:
            data.loc[data['Description'] == '$300 AND UNDER', 'Description'] = '$500 AND UNDER'
        
        if geofilename is not None:
            geo_df = geopandas.read_file(geofilename)
            geo_df['area_num_1'] = geo_df['area_num_1'].astype(int)
            print('Filling in missing Community Area values...')
            points = add_missing_community_areas(data, geo_df)
            data.loc[(np.isnan(data['Community Area'])) | (data['Community Area'] == 0), 'Community Area'] = points

        if 'Longitude' in data.columns:
            data = data.loc[(data.Longitude > -90) | (np.isnan(data.Longitude))]

        data = data.loc[data.index.year <= 2019]
    
    data.sort_index(inplace=True)

    return data

def add_missing_community_areas(crime_df, geo_df):
    """Tries to fill in missing community area IDs"""

    missings = crime_df.loc[(np.isnan(crime_df['Community Area'])) | (crime_df['Community Area'] == 0)]
    points = missings.apply(lambda x: point.Point(x[['Longitude', 'Latitude']]), axis=1)
    community_areas = points.apply(check_for_intersection, args=(geo_df,)).values
    return community_areas

def check_for_intersection(p, geo_df):
    """Checks if a point p and the geometries overlap somewhere"""
    
    if np.isnan(p.x) or np.isnan(p.y):
        return np.nan
    intersection_area = geo_df['area_num_1'][geo_df['geometry'].apply(lambda x: x.intersects(p))].values
    if len(intersection_area) > 1:
        print('Multiple community areas match! Unclear how.')
        intersection_area = intersection_area[0]
    elif len(intersection_area) == 0:
        # If no intersection found, use the closest neighborhood
        # Most of these are on the edge of the city, very close
        intersection_area = geo_df['area_num_1'].loc[geo_df['geometry']\
                                                 .apply(lambda x: x.distance(p)).idxmin()]
    else:
        intersection_area = intersection_area[0]
    
    return intersection_area
