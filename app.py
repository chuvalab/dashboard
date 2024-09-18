from dash import Dash, dcc, html, dash_table, Input, Output, State, \
    callback, no_update
import dash_bootstrap_components as dbc
from callbacks.callbacks import *
from pathlib import Path
import uuid
import pprint
import os
import shutil
import dash_uploader as du
import pandas as pd


def emtpy_dir(folder):
    """Remove all files from a folder"""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def get_upload_component(id):
    emtpy_dir(UPlOAD_FOLDER_ROOT)
    return du.Upload(
        id=id,
        max_file_size=3800,  # in Mb
        filetypes=['csv', 'gz'],
        upload_id=uuid.uuid1(),  # Unique session id
    )


# Layout of the app
app.layout = html.Div([
    # Tabs component
    dcc.Tabs([
        # Overview tab
        dcc.Tab(label='Overview', children=[
            html.H2('File upload and overview'),
            # File upload component
            get_upload_component(id='upload-data'),
            html.Div(id='callback-output'),
            html.Br(),
            html.Button('Store File', id='button-store-file'),
            html.Div(id='stored-file-confirm',
                     children='Click on "Store File" button if you want to permanently '
                              'store the file. Please keep in mind disk space is limited'),
            html.Br(),
            html.H3('File information'),
            html.Pre(id='file-description'),
            # Table head
            dash_table.DataTable(id='head-table', columns=[])
        ]),

        # Histograms and Heatmap Tab
        dcc.Tab(label='Histograms and Heatmap', children=[
            html.H2('Select a column to plot the histogram of its values'),
            dbc.Row(
                [
                    # Dropdown to select column A
                    dbc.Col(
                        dcc.Dropdown(
                            id='column-dropdown-a',
                            options=["Well", "Site", "Cell", "OCT4", "SOX17"],
                            # Options will be dynamically populated based on the
                            # uploaded file
                            value="OCT4",
                            multi=False,
                            placeholder="Select a column"
                    ),
                    width=width_histogram),
                    # Dropdown to select column B
                    dbc.Col(
                        dcc.Dropdown(
                            id='column-dropdown-b',
                            options=["Well", "Site", "Cell", "OCT4", "SOX17"],
                            # Options will be dynamically populated based on the
                            # uploaded file
                            value="SOX17",
                            multi=False,
                            placeholder="Select a column"
                    ),
                    width=width_histogram),
                ]
            ),
            dbc.Row(
                [
                    # Hist A
                    dbc.Col(
                        dcc.Graph(id='histogram-plot-a'),
                        width=width_histogram
                    ),
                    # Hist B
                    dbc.Col(
                        dcc.Graph(id='histogram-plot-b'),
                        width=width_histogram
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                            # Slider to select OCT4 lower limit
                            [html.H2('Select OCT4 lower limit'),
                            html.Br(),
                            html.Div(id='OCT4-slider')],
                            width=width_histogram),
                    dbc.Col(
                            # Slider to select SOX17 lower limit
                            [html.H2('Select SOX17 lower limit'),
                            html.Br(),
                            html.Div(id='SOX17-slider')],
                            width=width_histogram) 
                ]
            ),
            # Heatmap cell counts
            html.Br(),
            html.H2('Heatmap of cell counts per well'),
            html.Div(id='filter-description'),
            dcc.Graph(id='heatmap-fig'),

            # Heatmap percent cells double positive
            html.Br(),
            html.H2('Heatmap percent of double positive cell counts \
                    per well'),
            dcc.Graph(id='heatmap_pct-fig'),
        ]),

    ]),
    # dcc.Store stores the intermediate value
    dcc.Store(id='intermediate-value'),
])



# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)