from dash import Dash, dcc, html, dash_table, Input, Output, State, callback, no_update

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
    # File upload component
    dcc.Upload(
        id='upload-data',
        children=html.Div(['Drag and Drop or ', html.A('Select a CSV File')]),
        multiple=False
    ),

    # Dropdown to select column
    dcc.Dropdown(
        id='column-dropdown',
        options=["ObjectNumber", "Metadata_Site", "Metadata_Well",
                "Intensity_MeanIntensity_DAPI", "Intensity_MeanIntensity_OCT4",
                "Intensity_MeanIntensity_SOX17"],
        # Options will be dynamically populated based on the uploaded file
        value=None,
        multi=False,
        placeholder="Select a column"
    ),

    # Histogram plot
    dcc.Graph(id='histogram-plot')
])

# Callback to update the histogram plot based on the selected column
@app.callback(
    Output('histogram-plot', 'figure'),
    [Input('column-dropdown', 'value'),
     Input('upload-data', 'contents')]
)
def update_histogram(selected_column, contents):
    if contents is None or selected_column is None:
        return no_update

    # only load columns of interest
    use_cols = ["ObjectNumber", "Metadata_Site", "Metadata_Well",
                "Intensity_MeanIntensity_DAPI", "Intensity_MeanIntensity_OCT4",
                "Intensity_MeanIntensity_SOX17"]
    content_type, content_string = contents.split(',')
    decoded = pd.read_csv(
        io.StringIO(base64.b64decode(content_string).decode('utf-8')),
        usecols=use_cols)

    # Create histogram plot
    fig = px.histogram(decoded,
                       x=selected_column,
                       title=f'Histogram of {selected_column}')

    return fig


# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)

