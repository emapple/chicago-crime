import numpy as np
import plotly.graph_objects as go
import json
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import urllib.request
import sqlite3
from contextlib import closing

# load census data -- we use populations to calculate crime rate
censusurl = ('https://datahub.cmap.illinois.gov/dataset/5700ba1a-b173-4391-a26e-48b198e830c8/resource/b30b47bf-bb0d-46b6-853b-47270fb7f626/download/CCASF12010CMAP.xlsx')
censusdata = pd.read_excel(censusurl, index_col=1, header=1, skiprows=0)
censusdata.index.name = 'Community Area'

# the geojson for the ap
geourl = 'https://data.cityofchicago.org/api/geospatial/cauq-8yn6?method=export&format=GeoJSON'
with urllib.request.urlopen(geourl) as url:
    geojson = json.loads(url.read().decode())
    # THANK YOU to https://plot.ly/~empet/15238/tips-to-get-a-right-geojson-dict-to-defi/#/
    # for solving a json issue, solved by the code below
    # the json object must have an id key
    for k in range(len(geojson['features'])):
        geojson['features'][k]['id'] = geojson[
            'features'][k]['properties']['area_num_1']


# query database for available widget options
with closing(sqlite3.connect('crime.db')) as db:
    with db as cur:
        # dropdown menu is the unique crime types
        query = """SELECT DISTINCT type
                   FROM crime"""
        dropdown_crimes = cur.execute(query).fetchall()
        dropdown_crimes = [s.title() for s, in dropdown_crimes]
        # get full available date range
        query = 'SELECT min(year), max(year) FROM crime'
        min_year, max_year = cur.execute(query).fetchone()


def format_df(df, primary_type, year_range):
    """Aggregate crime rate based on type and years"""
    df = df.copy()
    # rate is incidence per 100k people per year
    df['Rate'] = (df['num_crime'] / censusdata['Total Population']
                  * 1e5 / (np.diff(year_range) + 1))
    # missing community areas had 0 incidences
    df = df.replace(np.nan, 0)
    # formatting the hovertext
    df['Text'] = (censusdata['Geog'] + '<br>' + '<br>'
                  'Rate: ' + df['Rate'].apply(lambda x: f'{x:.1f}') + '<br>'
                  'Total Number: ' + df["num_crime"].astype(str) + '<br>'
                  'Population: ' + censusdata["Total Population"].astype(str))
    return df

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
application = app.server

app.layout = html.Div(
    style={'width': '700px', 'justify-content': 'center', 'margin': '0 auto'},
    children=[
        html.Div(style={'height': '100px'}, children=[
            html.Div(style={'height': '50px'}, children=[dcc.Dropdown(
                id='crime-type',
                options=[{'label': x, 'value': x}
                         for x in dropdown_crimes],
                value='Homicide',
                placeholder='Select a Crime Type',
                clearable=False
            )]),

            html.Div([dcc.RangeSlider(
                id='date-range',
                value=(2010, 2015),
                min=min_year,
                max=max_year,
                step=1,
                marks={2001: '2001', 2004: '2004', 2007: '2007',
                       2010: '2010', 2013: '2013', 2016: '2016', 2019: '2019'}
            )]),
        ]),
        dcc.Graph(id='crime-map-graph', style={'height': '600px', 'width': '600px',
                                               'margin': '0 auto'})
    ])


@app.callback(
    Output('crime-map-graph', 'figure'),
    [Input('crime-type', 'value'),
     Input('date-range', 'value')])
def update_graph(crime_type, date_range):
    query = """SELECT community_area, 
                      COUNT(*) as num_crime
               FROM crime
               WHERE type = ?
                   AND year >= ?
                   AND year <= ?
               GROUP BY community_area
               ORDER BY community_area"""
    with closing(sqlite3.connect('crime.db')) as db:
        df = pd.read_sql_query(query, db,
                               params=(crime_type.upper(), *date_range),
                               index_col='community_area',)

    # remove anything with missing community area
    df.loc[df.index.dropna(), :]
    # dfview = reagg(df, crime_type, date_range)

    # convert count to rate, add hovertext
    df = format_df(df, crime_type, date_range)
    trace = go.Choroplethmapbox(geojson=geojson,
                                locations=df.index, z=df['Rate'],
                                featureidkey='properties.area_num_1',
                                colorscale='viridis',
                                colorbar_title='Number<br>per 100k<br>per year',
                                hoverinfo='text', hovertext=df['Text'])
    return {'data': [trace],
            'layout': go.Layout(margin=dict(l=0, r=0, t=60, b=0),
                                title_text=f'Chicago {crime_type.title()} rate, '
                                + f'{date_range[0]}-{date_range[1]}',
                                mapbox_style='open-street-map',
                                mapbox_center={'lat': 41.88, 'lon': -87.63},
                                mapbox_zoom=9, mapbox_uirevision=True)}

if __name__ == '__main__':
    application.run(port=8080)
