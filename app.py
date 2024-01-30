from dash import Dash, dcc, html, dash_table, Input, Output, State, callback, \
    no_update
import base64
import datetime
import io
import pandas as pd
import plotly.express as px

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Initialize the Dash app
app = Dash(__name__)

# Layout of the app
app.layout = html.Div([
    # Tabs component
    dcc.Tabs([
        # Overview tab
        dcc.Tab(label='Overview', children=[
            html.H2('File upload and overview'),

            # File upload component
            dcc.Upload(
                id='upload-data',
                children=html.Div(
                    ['Drag and Drop or ', html.A('Select a CSV File')]),
                multiple=False,
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

            html.H3('File information'),
            html.Pre(id='file-description'),
            # Table head
            dash_table.DataTable(id='head-table', columns=[])
        ]),

        # Histogram Tab
        dcc.Tab(label='Histogram', children=[
            # Dropdown to select column
            dcc.Dropdown(
                id='column-dropdown',
                options=["ObjectNumber", "Metadata_Site", "Metadata_Well",
                         "Intensity_MeanIntensity_DAPI",
                         "Intensity_MeanIntensity_OCT4",
                         "Intensity_MeanIntensity_SOX17"],
                # Options will be dynamically populated based on the
                # uploaded file
                value=None,
                multi=False,
                placeholder="Select a column"
            ),

            # Histogram plot
            dcc.Graph(id='histogram-plot')
        ])
    ])
])

# only load columns of interest
use_cols = ["ObjectNumber", "Metadata_Site", "Metadata_Well",
            "Intensity_MeanIntensity_DAPI", "Intensity_MeanIntensity_OCT4",
            "Intensity_MeanIntensity_SOX17"]


@callback(
    [Output('head-table', 'columns'),
     Output('head-table', 'data'),
     Output('file-description', 'children')],
    [Input('upload-data', 'contents'),
     State('upload-data', 'filename')]
)
def load_data(contents, filename):
    if contents is None:
        return no_update, no_update, no_update

    content_type, content_string = contents.split(',')
    df = pd.read_csv(
        io.StringIO(base64.b64decode(content_string).decode('utf-8')),
        usecols=use_cols)

    cols = [{'name': i, 'id': i} for i in df.columns]
    head_table = df.head().to_dict('records')
    n_rows = df.shape[0]
    file_info_text = f"File name: {filename} has a  total of {n_rows} rows. The first 5 are shown below"
    return cols, head_table, file_info_text


# Callback to update the histogram plot based on the selected column
@callback(
    Output('histogram-plot', 'figure'),
    [Input('column-dropdown', 'value'),
     Input('upload-data', 'contents')]
)
def update_histogram(selected_column, contents):
    if contents is None or selected_column is None:
        return no_update

    content_type, content_string = contents.split(',')
    decoded = pd.read_csv(
        io.StringIO(base64.b64decode(content_string).decode('utf-8')),
        usecols=use_cols)

    # Create histogram plot
    fig = px.histogram(decoded,
                       x=selected_column,
                       title=f'Histogram of {selected_column}',
                       nbins=400)

    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
