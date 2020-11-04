import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from uszipcode import SearchEngine, SimpleZipcode, Zipcode

sns.set(style='darkgrid')

def choropleth_plot(geo_data, table, headers):
    """
    Create a choropleth map based off of GeoJSON zip code polygons.
    Input:
        geo_data : geojson filename
        table : dataframe with data
        headers : LIST - names of headers in table. Zipcode column goes first
    Output:
        Choropleth map
    """
    map_out = folium.Map(location=[40.6831, -73.9712], zoom_start=11, tiles = None)
    folium.TileLayer('CartoDB positron', name='Light Map', control=False).add_to(map_out)
    map_out.choropleth(
            geo_data = geo_data,
            fill_opacity = 1.0,
            line_opacity = 0.8,
            data = table,
            nan_fill_opacity = 0.0,
            columns = headers,
            key_on = 'feature.properties.postalcode',
    #         threshold_scale=myscale
            )
    
    return map_out

def choropleth_plot_income(geo_data, table, headers):
    """
    Create a choropleth map based off of GeoJSON zip code polygons.
    Input:
        geo_data : geojson filename
        table : dataframe with data
        headers : LIST - names of headers in table. Zipcode column goes first
    Output:
        Choropleth map
    """
    map_out = folium.Map(location=[40.6831, -73.9712], zoom_start=11, tiles = None)
    folium.TileLayer('CartoDB positron', name='Light Map', control=False).add_to(map_out)
    map_out.choropleth(
            geo_data = geo_data,
            fill_opacity = 1.0,
            line_opacity = 0.8,
            data = table,
            nan_fill_opacity = 0.0,
            columns = headers,
            key_on = 'feature.properties.postalcode',
            fill_color='YlGn'
    #         threshold_scale=myscale
            )
    
    return map_out

def count_winning_pairs(sample_1, sample_2):
    """
    Count winning pairs for Mann Whitney U-Test for hypothesis testing
    """
    sample_1, sample_2 = np.array(sample_1), np.array(sample_2)
    n_total_wins = 0
    for x in sample_1:
        n_wins = np.sum(x > sample_2) + 0.5*np.sum(x == sample_2)
        n_total_wins += n_wins
    return n_total_wins

def setup_df(filename):
    """
    Set up initial dataframe from 2017-2019
    In: filename
    Out: DataFrame
    """
    df = pd.read_csv(filename)
    df = df.drop(['PHONE', 'Community Board', 'Council District', 'BIN', 'BBL', 'NTA'], axis=1)
    df['INSPECTION DATE'] = pd.to_datetime(df['INSPECTION DATE'])
    trim = df.loc[df['INSPECTION DATE'].dt.year.isin([2017, 2018, 2019])]
    
    return trim
    
def get_income_df(df):
    """
    Attach zip code median income data to dataframe
    In: DataFrame
    Out: DataFrame w/ Median Income column
    """
    search = SearchEngine()
    zipcodes = list(df['ZIPCODE'].dropna().unique())
    zipcodes = list(map(int, zipcodes))
    zipcodes = sorted(zipcodes)
    zipcodes.remove(12345)
    zipcodes.remove(30339)
    zipdf = pd.DataFrame(zipcodes)
    income = []
    for zip_ in zipcodes:
        tosearch = search.by_zipcode(zip_)
        income.append(tosearch.median_household_income)

    zipdf['Median_Income'] = income
    zipdf.set_index(0, inplace=True)
    df.ZIPCODE = df.ZIPCODE.fillna(0)
    df = df.astype({'ZIPCODE': int})
    trim_inc = df.join(zipdf, on='ZIPCODE', how='left')
    
    return trim_inc

def get_zipcode_groups(df):
    """
    Convert unique dataframe into zipcode-grouped dataframe
    """
    search = SearchEngine()
    for idx, row in df.iterrows():
        if np.isnan(row['Latitude']):
            lat = search.by_zipcode(row['ZIPCODE']).lat
            long = search.by_zipcode(row['ZIPCODE']).lng
            df.loc[idx, 'Latitude'] = lat
            df.loc[idx, 'Longitude'] = long
    zipcode_meanscores = df.groupby('ZIPCODE').SCORE.mean()
    zipcode_medianscores = df.groupby('ZIPCODE').SCORE.median()
    zipcode_data = pd.DataFrame(zipcode_meanscores)
    zipcode_data.drop([0,12345,30339],axis=0,inplace=True)
    zipcode_data.rename({'SCORE':'mean_score'}, axis=1, inplace=True)
    
    vc = df.groupby('ZIPCODE').GRADE.value_counts()
    zipcode_data['median_score'] = zipcode_medianscores
    zipcode_data['A'] = 0
    zipcode_data['B'] = 0
    zipcode_data['C'] = 0
    vc = vc.drop(0)
    for idx, val in vc.iteritems():
        zipcode_data.loc[idx[0], idx[1]] = val
    zipcode_data.drop(['N', 'Z', 'P'], axis=1, inplace=True)
    zipcode_data.drop([12345, 30339], axis=0, inplace=True)
    zipcode_data['total_graded'] = zipcode_data['A'] + zipcode_data['B'] + zipcode_data['C']
    zipcode_data[['A','B','C','total_graded']] = zipcode_data[['A', 'B', 'C', 'total_graded']].astype(int)
    zipcode_data['percentage_A'] = zipcode_data['A']/zipcode_data['total_graded'] * 100
    zipcode_data = zipcode_data.reset_index()
    zipcode_data['ZIPCODE'] = zipcode_data['ZIPCODE'].astype('str') 
    
    return zipcode_data