from dash import Dash, dcc, html, dash_table, Input, Output, State, \
    callback, no_update
import uuid
import pprint
import json
import dash_bootstrap_components as dbc
import dash_uploader as du
import pandas as pd
import plotly.express as px


# Initialize the Dash app
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

UPlOAD_FOLDER_ROOT = '/tmp/uploads/'
du.configure_upload(app, UPlOAD_FOLDER_ROOT)


def get_upload_component(id):
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
        ]),

        # Heatmap Tab
        dcc.Tab(label='Heatmap', children=[
            html.H2('Heatmap of cell counts per well'),
            dcc.Graph(id='heatmap-fig')
        ])
    ]),
    # dcc.Store stores the intermediate value
    dcc.Store(id='intermediate-value'),
])


# only load columns of interest
use_cols = ["ObjectNumber", "Metadata_Site", "Metadata_Well",
            "Intensity_MeanIntensity_DAPI", "Intensity_MeanIntensity_OCT4",
            "Intensity_MeanIntensity_SOX17"]

@du.callback(
    output=[Output('callback-output', 'children'),
            Output('intermediate-value', 'data')],
    id='upload-data')
def callback_on_completion(status: du.UploadStatus):
    pprint.pprint(status.__dict__)
    html_element = html.Ul([html.Li(str(x)) for x in status.uploaded_files])
    latest_file = status.latest_file
    df = pd.read_csv(latest_file,
                     usecols=use_cols)
    df_dump = df.to_json(orient='split')
    df_dump_filename = {
        'df': df_dump,
        'filename': str(latest_file)
    }
    return html_element, json.dumps(df_dump_filename)



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
    df = pd.read_json(df_filename['df'], orient='split')
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
    decoded = pd.read_json(df_filename['df'], orient='split')

    # Create histogram plot
    fig = px.histogram(decoded,
                       x=selected_column,
                       title=f'Histogram of {selected_column}',
                       nbins=400)

    return fig

@callback(
    Output('heatmap-fig', 'figure'),
    Input('intermediate-value', 'data')
)
def heatmap(jsonified_df):
    if jsonified_df is None:
        return no_update

    df_filename = json.loads(jsonified_df)
    df = pd.read_json(df_filename['df'], orient='split')
    well_counts = pd.DataFrame(df["Metadata_Well"].value_counts())
    well_ids = well_counts.index.to_list()
    well_counts["row"] = [well[0] for well in well_ids]
    well_counts["cols"] = [well[1:] for well in well_ids]
    matrix_well_counts = well_counts.pivot(index="row", columns="cols",
                                           values="count")
    matrix_well_counts.fillna(0, inplace=True)
    heatmap_fig = px.imshow(matrix_well_counts)

    return heatmap_fig

# Run the app
if __name__ == '__main__':
    app.run_server(host='0.0.0.0', port=8050, debug=False)
