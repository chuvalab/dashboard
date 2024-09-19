from dash import Dash, dcc, html, Input, Output, \
    callback, no_update
from callbacks import callbacks
from pathlib import Path
from io import StringIO
import dash_uploader as du
import pandas as pd
import json
import os
import shutil
import plotly.express as px
import dash_bootstrap_components as dbc

width_histogram = 5
UPlOAD_FOLDER_ROOT = '/tmp/uploads/'
UPlOAD_FOLDER_STORE = '/tmp/store/'
Path(UPlOAD_FOLDER_ROOT).mkdir(parents=True, exist_ok=True)

# Initialize the Dash app
# Notice suppress_callback_exceptions=True, this might need to be turned off 
# for future debugging
app = Dash(__name__, 
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)
du.configure_upload(app, UPlOAD_FOLDER_ROOT)

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


# Callback to update the histogram A plot based on the selected column
@callback(
    [Output('histogram-plot-a', 'figure'),
     Output('histogram-plot-b', 'figure')],
    [Input('intermediate-value', 'data')]
)
def update_histogram(jsonified_df):
    if jsonified_df is None: # or selected_column is None:
        return no_update
    selected_column = "OCT4"
    df_filename = json.loads(jsonified_df)
    df = pd.read_json(StringIO(df_filename['df']), orient='split') 
    hist_oct4 = create_hist(df, selected_column="OCT4")
    hist_sox17 = create_hist(df, selected_column="SOX17")
    return hist_oct4, hist_sox17



def create_hist(df, selected_column):
    """
    Helper function that plots a histogram
    """
    max_value = df[selected_column].max()
    hist = px.histogram(df,
                        range_x=[0, max_value],
                        x=selected_column,
                        title=f'Histogram of {selected_column}',
                        nbins=400)
    return hist

@callback(Output('OCT4-slider', 'children'),
          Input('intermediate-value', 'data')
)
def create_oct4_slider(jsonified_df):
    if jsonified_df is None:
        oct4_max = 5
    else:
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
    if jsonified_df is None:
        sox17_max = 5
    else:
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
    if jsonified_df is None or oct4_low is None or sox17_low is None:
        return no_update

    df_filename = json.loads(jsonified_df)
    df = pd.read_json(StringIO(df_filename['df']), orient='split')
    matrix_well_counts = get_well_count_matrix(df, 
                                               oct4_low=oct4_low,
                                               sox17_low=sox17_low)
    heatmap_fig = px.imshow(matrix_well_counts)
    filter_description = f"Table has been filtered with SOX17>{sox17_low} and OCT4>{oct4_low} intensity levels"
    return heatmap_fig, filter_description


@callback(
    [Output('heatmap_pct-fig', 'figure')],
    [Input('intermediate-value', 'data'),
     Input('OCT4_low', 'value'),
     Input('SOX17_low', 'value')]
)
def heatmap(jsonified_df, oct4_low, sox17_low):
    if jsonified_df is None or oct4_low is None or sox17_low is None:
        return no_update

    df_filename = json.loads(jsonified_df)
    df = pd.read_json(StringIO(df_filename['df']), orient='split')
    well_count_matrix_selection = get_well_count_matrix(df=df, 
                                                        oct4_low=oct4_low,
                                                        sox17_low=sox17_low)
    well_count_matrix_complete = get_well_count_matrix(df=df)
    well_count_matrix_percent = 100*well_count_matrix_selection/\
        well_count_matrix_complete
    heatmap_fig = px.imshow(well_count_matrix_percent)
    return [heatmap_fig]


def get_well_count_matrix(df, oct4_low=0, sox17_low=0):
    """
    Returns a cell count matrix representing the cell counts in 
    each well in the physical plate where cells are grown. Input data 
    frame is filtered on minimum threshholds of oct4 and sox17
    """
    df = df[(df['OCT4']>oct4_low) & (df["SOX17"]>sox17_low)]
    well_counts = pd.DataFrame(df["Well"].value_counts())
    well_ids = well_counts.index.to_list()
    well_counts["row"] = [well[0] for well in well_ids]
    well_counts["cols"] = [well[1:] for well in well_ids]
    matrix_well_counts = well_counts.pivot(index="row", columns="cols",
                                           values="count")
    matrix_well_counts.fillna(0, inplace=True)
    return matrix_well_counts