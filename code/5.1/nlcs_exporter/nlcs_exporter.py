import requests
import os
import logging
from requests.auth import HTTPBasicAuth
import pandas as pd
from io import StringIO
import glob
from pathlib import Path
from typing import Union

HOOFDGROEPPEN = [
    "AL", "GR", "SC", "HC", "HU", "MO", "AM", "MW", "BV", "IW", "IS", "BC",
    "WH", "KL", "MC", "KC", "VV", "VH", "KG", "OB", "VW", "RI", "OV", "GC",
    "ZZ", "GW", "GK", "FC", "IE", "FV", "IV", "SB", "ES", "OG", "KW"
]

SPARQL_ENDPOINT = "https://hub.laces.tech/digitalbuildingdata/nlcs/acceptance/nlcs-acceptatie/versions/rv_5_1_3/sparql"
ACCESS_TOKEN = ""
PASSWORD = ""

class LacesRequest():
    def __init__(self, config) -> None:
        url = config['url']
        if 'default-graph-uri' in config: 
            default_graphs = config['default-graph-uri'] 
        else: 
            default_graphs = []
        if 'named-graph-uri' in config: 
            named_graphs = config['named-graph-uri'] 
        else: 
            named_graphs = []

        parameters = {
            "default-graph-uri": default_graphs,
            "named-graph-uri": named_graphs
        }
        if 'username' in config and 'password' in config:
            username, password = config['username'] , config['password']
        else:
            # username, password = _env_default("LDP_USERNAME"), _env_default("LDP_PASSWORD") 
            print("Access token and/or password is not correct!")

        self._request = requests.Request(
            method="POST", url=url, params=parameters, headers={
                'Content-type': 'application/sparql-query',
                'Accept': 'text/csv',
            },
            auth=HTTPBasicAuth(username, password=password)
        )

    def send_request(self, query: str):
        return self.run_query(query)

    def run_query(self, query):
        self._request.data = query.encode("UTF-8")
        prepared = self._request.prepare()
        correct_url = self._request.url + '?'
        for graph in self._request.params['default-graph-uri']:
            correct_url += f'default-graph-uri={graph}&'
        for graph in self._request.params['named-graph-uri']:
            correct_url += f'named-graph-uri={graph}&'
        correct_url = correct_url[:-1]
        prepared.url = correct_url
        s = requests.Session()
        response = s.send(prepared)
        logging.info(response)
        return response
    
    def run_query_clean_result(self, query): 
        raw = self.run_query(query) 
        return convert_response(raw) 

def convert_response(output) -> str:
    data = output.text
    data = data.replace('\n\n', '\n')
    data = data.replace('\r\n', '\n')
    return data

def load_query(query_path):
    try:
        with open(query_path, 'r', encoding='utf-8') as f:
            query_template = f.read()
    except:
        print(f"FATAL ERROR: The query file was not found at '{query_path}'")
        raise
    return query_template

def build_query_with_hoofdgroup(template_path, hoofdgroup):
    """
    Reads a SPARQL query template from a .rq file, replaces the
    placeholder, and returns the final query string.
    
    Args:
        template_path (str): The file path to the .rq template file.
        search_term (str): The value to insert into the query.
        
    Returns:
        str: The final, ready-to-execute SPARQL query.
    """
    query_template = load_query(template_path)
    final_query = query_template.replace("$hoofdgroup_name", hoofdgroup)
    return final_query
    
def run_all_queries_in_folder(endpoint, input_path, output_path):
    """
    Validates data by control queries and outputs non-empty ones in CSV format. 
    """
    print(f"Running all queries in folder {input_path} for endpoint {endpoint}...")
    query_files = glob.glob(os.path.join(input_path, '*.rq'))
    for query_file in query_files:
        file_name = query_file.split('\\')[1].split(".")[0]
        print(f"Running query in {file_name}...")
        control_query = load_query(query_file)        
        results = endpoint.run_query_clean_result(control_query)
        len_result = len(results.split('\n'))
        if len_result > 2: 
            output_filename = f"{output_path}{file_name}.csv"
            df_objs = pd.read_csv(StringIO(results))            
            df_objs.to_csv(output_filename, sep=";", index=False)
            print(f"All non-empty query results have been saved in {output_filename}...")
        else:
            print(f"Data is validated, there is nothing to show in the {file_name} query result.")

def write_query_results(results, csv_output_path):
    df_objs = pd.read_csv(StringIO(results))
    df_objs.to_csv(csv_output_path, sep=";", index=False)

def merge_csv_files(
    input_folder: Union[str, Path], 
    output_file: Union[str, Path], 
    file_pattern: str = "*.csv"
    ):
    """
    Finds all CSV files in a folder that match a pattern, merges them
    into a single DataFrame, and saves the result to a new CSV file.

    It assumes all CSVs have the same (or compatible) headers. If headers
    differ, it will create a union of all columns, filling missing values
    with NaN.

    Args:
        input_folder (Union[str, Path]): 
            The path to the folder containing the CSV files to merge.
        output_file (Union[str, Path]): 
            The file path for the final merged CSV.
        file_pattern (str, optional): 
            The glob pattern to find files. Defaults to "*.csv" to match all CSVs.
    """
    folder_path = Path(input_folder)
    output_path = Path(output_file)

    # 1. Find all files in the input folder matching the pattern
    csv_files = sorted(list(folder_path.glob(file_pattern)))

    if not csv_files:
        print(f"Warning: No files found matching '{file_pattern}' in '{folder_path}'. No output file created.")
        return

    print(f"Found {len(csv_files)} files to merge:")
    for f in csv_files:
        print(f"  - {f.name}")

    # 2. Read each CSV into a list of pandas DataFrames
    df_list = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, delimiter=";")
            df_list.append(df)
        except pd.errors.EmptyDataError:
            print(f"Warning: Skipping empty file: {file.name}")
        except Exception as e:
            print(f"Error reading {file.name}: {e}")

    if not df_list:
        print("No data was successfully read. Output file will not be created.")
        return

    # 3. Concatenate all DataFrames in the list into a single DataFrame
    # ignore_index=True resets the index of the merged DataFrame to be continuous.
    print("\nMerging data...")
    merged_df = pd.concat(df_list, ignore_index=True)

    # 4. Save the merged DataFrame to the output file
    # index=False prevents pandas from writing a new index column to the CSV.
    print(f"Saving merged file to: {output_path}")
    merged_df.to_csv(output_path, index=False)

    print("✅ Merge complete.")
    print(f"Total rows in merged file: {len(merged_df)}")

if __name__ == "__main__":
    query_folder = "./code/5.1/nlcs_exporter/queries/"
    csv_folder = "./code/5.1/nlcs_exporter/CSV_results/"
    
    validations_input_folder = f"{query_folder}controle_queries/"
    validations_output_folder = f"{csv_folder}controles/"
    objects_output_folder = f"{csv_folder}objects/"

    try_input_path = f"{query_folder}try/"
    try_output_path = f"{csv_folder}try/"

    my_config = {
        "url": SPARQL_ENDPOINT,
        "username": ACCESS_TOKEN,
        "password": PASSWORD,
    }

    try:
        print("Initializing Laces client...")
        client = LacesRequest(config=my_config)
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"\nAn error occurred during the request: {e}")

    
    run_all_queries_in_folder(client, validations_input_folder, validations_output_folder)

    for hg in HOOFDGROEPPEN:
        try:
            print(f"\nSending objects query to the endpoint for hoofdgroup {hg}...")
            objects_output_path = f"{objects_output_folder}{hg}_sparql_results.csv"
            hoofdgroup_query = build_query_with_hoofdgroup(f"{query_folder}search_term_read_objects.rq", hg)
            results = client.run_query_clean_result(hoofdgroup_query)
            write_query_results(results, objects_output_path)

        except ValueError as e:
            print(f"Configuration Error: {e}")
        except Exception as e:
            print(f"\nAn error occurred during the request: {e}")

    merge_csv_files(objects_output_folder, f"{csv_folder}all_objects.csv")