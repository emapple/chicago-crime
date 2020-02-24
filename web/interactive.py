import numpy as np
import plotly.offline as poff
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from ipywidgets import widgets
import json
import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

# Cleanup
# domestic violence has its own, separate column, 
# and both of these are too rare to plot meaningfully
censusdata = pd.read_excel('/home/elaad/Documents/DatAnalysis/datasets/CCASF12010CMAP.xlsx',
                          index_col=1, header=1, skiprows=0)
censusdata.index.name = 'Community Area'

with open('/home/elaad/Documents/DatAnalysis/datasets/Boundaries_Community_Areas.geojson') as f:
    geojson = json.load(f)
    # THANK YOU to https://plot.ly/~empet/15238/tips-to-get-a-right-geojson-dict-to-defi/#/
    # for solving an issue, solved by the code below
    for k in range(len(geojson['features'])):
                    geojson['features'][k]['id'] = geojson['features'][k]['properties']['area_num_1']

df = pd.read_hdf('/home/elaad/Documents/DatAnalysis/datasets/crime_aggregated.hdf5')

def reagg(df, primary_type, year_range):
    """Aggregate crime rate based on type and years"""
    dfview = df.xs(primary_type.upper(), level='Primary Type') \
                            .loc[np.arange(year_range[0], year_range[1] + 1)].groupby('Community Area') \
                            .agg({'Count': np.sum, 'Rate': np.mean}) \
                            .reindex(np.arange(1, 78), fill_value=0)
    dfview['Text'] = censusdata['Geog'] + '<br>' + '<br>' + \
                    'Rate: ' + dfview['Rate'].apply(lambda x: f'{x:.1f}') + '<br>' + \
                    'Total Number: ' + dfview['Count'].astype(str) + '<br>' + \
                    'Population: ' + censusdata['Total Population'].astype(str)
    return dfview

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div(style={'width': '700px', 'justify-content':'center', 'margin':'0 auto'}, children=[
    html.Div(style={'height':'100px'}, children=[
        html.Div(style={'height':'50px'}, children=[dcc.Dropdown(
            id='crime-type',
            options=[{'label': x, 'value': x} for x in df.index.levels[1].str.title()],
            value='Homicide',
            placeholder='Select a Crime Type',
            clearable=False
            )]),

        html.Div([dcc.RangeSlider(
            id='date-range',
            value=(2010, 2015),
            min=df.index.levels[0].min(),
            max=df.index.levels[0].max(),
            step=1,
            marks={2001: '2001', 2004: '2004', 2007: '2007', 2010: '2010', 2013: '2013', 2016: '2016', 2019: '2019'}
            )]),
        ]),
    dcc.Graph(id='crime-map-graph', style={'height': '600px', 'width': '600px',
        'margin':'0 auto'})
    ])

@app.callback(
        Output('crime-map-graph', 'figure'),
        [Input('crime-type', 'value'),
         Input('date-range', 'value')])
def update_graph(crime_type, date_range):
    dfview = reagg(df, crime_type, date_range)
    trace = go.Choroplethmapbox(geojson=geojson,
                    locations=dfview.index, z=dfview['Rate'], 
                    featureidkey='properties.area_num_1',
                    colorscale='viridis',
                    colorbar_title='Number<br>per 100k<br>per year',
                    hoverinfo='text', hovertext=dfview['Text'])
    return {'data': [trace],
            'layout': go.Layout(margin=dict(l=0, r=0, t=60, b=0),
                  title_text=f'Chicago {crime_type.title()} rate, '  \
                + f'{date_range[0]}-{date_range[1]}',
                mapbox_style='open-street-map', 
                mapbox_center={'lat': 41.88, 'lon': -87.63},
                mapbox_zoom=9, mapbox_uirevision=True)}
    
if __name__ == '__main__':
    app.run_server(debug=True)
