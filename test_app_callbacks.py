import pandas as pd
import pytest
import mock
import json


from app import load_data

def test_load_data(mocker):
    columns = ["a", "b", "c"]
    df = pd.DataFrame([[1, 2, 3], [4, 5, 6], [7, 8, 9]], columns=columns)
    df_dump = df.to_json(orient='split')
    df_dump_filename = {
        'df': df_dump,
        'filename': str("path/to/file.txt")
    }
    jsonified_df = json.dumps(df_dump_filename)

    cols, head_table, file_info_text = load_data(jsonified_df)

    assert type(cols) == list
    assert cols == [{'name': 'a', 'id': 'a'}, {'name': 'b', 'id': 'b'}, {'name': 'c', 'id': 'c'}]
    assert type(head_table) == list
    assert head_table == [{'a': 1, 'b': 2, 'c': 3}, {'a': 4, 'b': 5, 'c': 6}, {'a': 7, 'b': 8, 'c': 9}]
    assert type(file_info_text) == str
    assert file_info_text == "File has a  total of 3 rows. The first 5 are shown below"

