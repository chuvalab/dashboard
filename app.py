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
    return du.Upload(
        id=id,
        max_file_size=3800,  # in Mb
        filetypes=['csv', 'gz'],
        upload_id=uuid.uuid1(),  # Unique session id
        max_files=3,
        default_style={
            'width': '50%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
            }
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
            html.Div(id='file-description'),
        ]),

        # Histograms and Heatmap Tab
        dcc.Tab(label='Histograms and Heatmap', children=[
            html.H2('Histograms of OCT4 and SOX17 intensity values'),
            html.Div(id='histograms'),
            
            # Heatmap cell counts
            html.Br(),
            html.H2('Heatmap of total cell counts per well'),
            dcc.Graph(id='heatmap-fig'),

            # Heatmap percent cells double positive
            html.Br(),
            html.H2('Heatmap of percentage of double positive cell counts \
                    per well'),
            html.P("""The percentage of cells that are double positive 
                   (SOX17 and OCT4 above the set threshold)"""),
            html.Div(id='filter-description'),
            dcc.Graph(id='heatmap_pct-fig'),
        ]),

    ]),
    # dcc.Store stores the intermediate value
    dcc.Store(id='intermediate-value'),
])


# Run the app
if __name__ == '__main__':
    emtpy_dir(UPlOAD_FOLDER_ROOT)
    app.run_server(host='0.0.0.0', port=8050, debug=True)