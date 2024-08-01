from dash import Dash, dcc, html, dash_table, Input, Output, State, \
    callback, no_update
from pathlib import Path
from io import StringIO
import uuid
import pprint
import json
import os
import shutil
import dash_bootstrap_components as dbc
import dash_uploader as du
import pandas as pd
import plotly.express as px


# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

UPlOAD_FOLDER_ROOT = '/tmp/uploads/'
UPlOAD_FOLDER_STORE = '/tmp/store/'
Path(UPlOAD_FOLDER_ROOT).mkdir(parents=True, exist_ok=True)
du.configure_upload(app, UPlOAD_FOLDER_ROOT)


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

        # Histogram Tab
        dcc.Tab(label='Histogram', children=[
            html.H2('Select a column to plot the histogram of the values'),

            # Dropdown to select column
            dcc.Dropdown(
                id='column-dropdown',
                options=["Well", "Site", "Cell", "OCT4", "SOX17"],
                # Options will be dynamically populated based on the
                # uploaded file
                value=None,
                multi=False,
                placeholder="Select a column"
            ),

            # Histogram plot
            dcc.Graph(id='histogram-plot'),

            # Slider to select OCT4 lower limit
            html.H2('Select OCT4 lower limit'),
            html.Br(),
            html.Div(id='OCT4-slider'),

            # Slider to select SOX17 lower limit
            html.H2('Select SOX17 lower limit'),
            html.Br(),
            html.Div(id='SOX17-slider'),
        ]),

        # Heatmap Tab
        dcc.Tab(label='Heatmap', children=[
            html.H2('Heatmap of cell counts per well'),
            html.Div(id='filter-description'),
            dcc.Graph(id='heatmap-fig')
        ])
    ]),
    # dcc.Store stores the intermediate value
    dcc.Store(id='intermediate-value'),
])


# only load columns of interest
use_cols = ["Well", "Site", "Cell", "OCT4", "SOX17"]

@du.callback(
    output=[Output('callback-output', 'children'),
            Output('intermediate-value', 'data')],
    id='upload-data')
def callback_on_completion(status: du.UploadStatus):
    html_element = html.Ul([html.Li(str(x)) for x in status.uploaded_files])
    latest_file = status.latest_file
    df = pd.read_csv(latest_file,
                     usecols=use_cols)
    sox17_max = df["SOX17"].max()
    oct4_max = df["OCT4"].max()
    df_dump = df.to_json(orient='split')
    df_dump_filename = {
        'df': df_dump,
        'filename': str(latest_file),
        'sox17_max': sox17_max,
        'oct4_max': oct4_max
    }
    return html_element, json.dumps(df_dump_filename)


@callback(Output("stored-file-confirm", "children"),
          [Input("button-store-file", "n_clicks"),
           Input('intermediate-value', 'data')])
def store_file(n_clicks, jsonified_df):
    if n_clicks is None or jsonified_df is None:
        return no_update
    elif n_clicks > 0:
        df_filename = json.loads(jsonified_df)
        filename = df_filename['filename']
        if not os.path.exists(UPlOAD_FOLDER_STORE):
            os.makedirs(UPlOAD_FOLDER_STORE)
        shutil.copy(filename, UPlOAD_FOLDER_STORE)
        return f"File has been successfuly copied in {UPlOAD_FOLDER_STORE}"


@callback(
    [Output('head-table', 'columns'),
     Output('head-table', 'data'),
     Output('file-description', 'children')],
    [Input('intermediate-value', 'data')]
)
def load_data(jsonified_df):
    if jsonified_df is None:
        return no_update, no_update, no_update

    df_filename = json.loads(jsonified_df)
    df = pd.read_json(StringIO(df_filename['df']), orient='split')
    cols = [{'name': i, 'id': i} for i in df.columns]
    head_table = df.head().to_dict('records')
    n_rows = df.shape[0]
    file_info_text = f"File has a  total of {n_rows} rows. The first 5 are shown below"
    return cols, head_table, file_info_text


# Callback to update the histogram plot based on the selected column
@callback(
    Output('histogram-plot', 'figure'),
    [Input('column-dropdown', 'value'),
     Input('intermediate-value', 'data')]
)
def update_histogram(selected_column, jsonified_df):
    if jsonified_df is None or selected_column is None:
        return no_update

    df_filename = json.loads(jsonified_df)
    decoded = pd.read_json(StringIO(df_filename['df']), orient='split')

    # Create histogram plot
    fig = px.histogram(decoded,
                       x=selected_column,
                       title=f'Histogram of {selected_column}',
                       nbins=400)

    return fig

@callback(Output('OCT4-slider', 'children'),
          Input('intermediate-value', 'data')
)
def create_oct4_slider(jsonified_df):
    df_filename = json.loads(jsonified_df)
    oct4_max = df_filename["oct4_max"]
    oct4_slider = dcc.Slider(id='OCT4_low',
                              min=0, 
                              max=oct4_max, 
                              marks={0: "0", oct4_max:str(oct4_max)}, 
                              tooltip={"placement": "bottom", "always_visible": True},
                              value=round(oct4_max/2, 1))
    return oct4_slider

@callback(Output('SOX17-slider', 'children'),
          Input('intermediate-value', 'data')
)
def create_sox17_slider(jsonified_df):
    df_filename = json.loads(jsonified_df)
    sox17_max = df_filename["sox17_max"]
    sox17_slider = dcc.Slider(id='SOX17_low',
                              min=0, 
                              max=sox17_max, 
                              marks={0: "0", sox17_max:str(sox17_max)}, 
                              tooltip={"placement": "bottom", "always_visible": True},
                              value=round(sox17_max/2, 1))
    return sox17_slider


@callback(
    [Output('heatmap-fig', 'figure'),
     Output('filter-description', 'children')],
    [Input('intermediate-value', 'data'),
     Input('OCT4_low', 'value'),
     Input('SOX17_low', 'value')]
)
def heatmap(jsonified_df, oct4_low, sox17_low):
    if jsonified_df is None:
        return no_update

    df_filename = json.loads(jsonified_df)
    df = pd.read_json(StringIO(df_filename['df']), orient='split')
    df = df[(df['OCT4']>oct4_low) & (df["SOX17"]>sox17_low)]
    well_counts = pd.DataFrame(df["Well"].value_counts())
    well_ids = well_counts.index.to_list()
    well_counts["row"] = [well[0] for well in well_ids]
    well_counts["cols"] = [well[1:] for well in well_ids]
    matrix_well_counts = well_counts.pivot(index="row", columns="cols",
                                           values="count")
    matrix_well_counts.fillna(0, inplace=True)
    heatmap_fig = px.imshow(matrix_well_counts)
    filter_description = f"Table has been filtered for SOX17>{sox17_low} and OCT4>{sox17_low} intensity levels"
    return heatmap_fig, filter_description

# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=True)