from dash import Dash, dcc, html, dash_table, Input, Output, State, callback

import base64
import datetime
import io

import pandas as pd
import plotly.express as px

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([
    html.Div(children='Explore and analyze tables from icontent'),
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        }
    ),
    html.Hr(),

    dash_table.DataTable(data=df.to_dict('records'), page_size=6),

    # Dropdown to select column
    dcc.Dropdown(
        id='column-dropdown',
        options=[],
        # Options will be dynamically populated based on the uploaded file
        value=None,
        multi=False,
        placeholder="Select a column"
    ),
])

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)

    # only load columns of interest
    use_cols = ["ObjectNumber", "Metadata_Site", "Metadata_Well",
                "Intensity_MeanIntensity_DAPI", "Intensity_MeanIntensity_OCT4",
                "Intensity_MeanIntensity_SOX17"]
    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            df = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')),
                usecols=use_cols)
        elif 'xls' in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])

    return html.Div([
        html.H5(filename),
        html.H6(datetime.datetime.fromtimestamp(date)),

        html.H3('The first 5 rows of the file'),
        dash_table.DataTable(
            df.head().to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns]
        ),

        dcc.Markdown(f'''
        ### File overview
        The file has {len(df)} rows and {len(df.columns)} columns
        '''),

        html.Hr(),  # horizontal line

        # For debugging, display the raw contents provided by the web browser
        html.Div('Raw Content'),
        html.Pre(contents[0:200] + '...', style={
            'whiteSpace': 'pre-wrap',
            'wordBreak': 'break-all'
        })
    ])

@callback(Output('output-data-upload', 'children'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified'))
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children

if __name__ == '__main__':
    app.run(debug=True)
