import requests
import os
import logging
from requests.auth import HTTPBasicAuth
import pandas as pd
from io import StringIO
import glob
from pathlib import Path
from typing import List

# --- Configuration & Constants (Moved to top for easy modification) ---
# IMPORTANT: Replace these with your actual values or set as environment variables
# For simplicity, we'll put them here directly for this "basic" version.
SPARQL_ENDPOINT = "https://hub.laces.tech/digitalbuildingdata/nlcs/test/test/sparql"
# "https://hub.laces.tech/digitalbuildingdata/nlcs/acceptance/nlcs-acceptatie/versions/rv_5_1_3/sparql"
LDP_TOKEN_ID = ""      
LDP_PASSWORD = ""      

# Default folder paths
QUERY_FOLDER = "./code/5.1/nlcs_exporter/queries/"
CONTROL_QUERY_FOLDER = "./code/5.1/nlcs_exporter/queries/controle_queries/"
CSV_OUTPUT_ROOT_FOLDER = "tabellen/concept/5.1/"
CSV_CONTROLS_FOLDER = "tabellen/concept/5.1/controles/"
CSV_OBJECTS_FOLDER = "tabellen/concept/5.1/objectentabellen/"
# --- End Configuration ---


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
    

# --- Helper Functions ---
def load_query(query_path: str) -> str:
    """Loads a SPARQL query from a .rq file."""
    try:
        with open(query_path, 'r', encoding='utf-8') as f:
            query_template = f.read()
    except:
        print(f"FATAL ERROR: The query file was not found at '{query_path}'")
        raise
    return query_template

def build_parameterized_query(template_path: str, placeholder: str, value: str) -> str:
    """
    Reads a SPARQL query template, replaces a placeholder, and returns the query.
    e.g., placeholder="$hoofdgroup_name", value="SomeGroup"
    """
    query_template = load_query(template_path)
    if placeholder not in query_template:
        print(f"WARNING: Placeholder '{placeholder}' not found in query template: {template_path}")
    final_query = query_template.replace(placeholder, value)
    return final_query
    
def save_csv_results(
    csv_data: str,
    output_filepath: str,
    min_data_rows: int = 1, # Minimum 1 data row (after header) to save
    output_delimiter: str = ","
) -> bool:
    """
    Saves SPARQL query results (CSV string) to a CSV file.
    Checks if there's actual data beyond just the header.
    """
    lines = csv_data.split('\n')
    # If len(lines) is 0 or 1, it's either empty or just a header row.
    if len(lines) <= min_data_rows: # Header + 1 data row = 2 lines
        print(f"INFO: No significant data in results for '{os.path.basename(output_filepath)}'. No CSV saved.")
        return False

    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_filepath)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        df = pd.read_csv(StringIO(csv_data), delimiter=output_delimiter)
        
        # Check if DataFrame is empty after parsing (e.g., only header present)
        if df.empty:
            print(f"INFO: Results for '{os.path.basename(output_filepath)}' are empty after parsing. No CSV saved.")
            return False

        df.to_csv(output_filepath, sep=output_delimiter, index=False)
        print(f"INFO: Results saved to {output_filepath}")
        return True
    except pd.errors.EmptyDataError:
        print(f"INFO: No data found to save for '{os.path.basename(output_filepath)}'.")
        return False
    except Exception as e:
        print(f"ERROR: Failed to save CSV to {output_filepath}: {e}")
        return False

def run_queries_in_folder(
    client: LacesRequest,
    input_folder: str,
    output_folder: str,
    query_pattern: str = "*.rq"
) -> None:
    """
    Runs all SPARQL queries in a folder and saves non-empty results as CSVs.
    """
    print(f"\nINFO: Running all queries in folder '{input_folder}'...")
    os.makedirs(output_folder, exist_ok=True)
    query_files = glob.glob(os.path.join(input_folder, query_pattern))
    
    if not query_files:
        print(f"WARNING: No query files found matching '{query_pattern}' in '{input_folder}'.")
        return
    
    for query_file_path in query_files:
        # file_name = query_file.split('\\')[1].split(".")[0]
        file_name = os.path.splitext(os.path.basename(query_file_path))[0]
        print(f"INFO: Executing query from {query_file_path}...")
        try:
            query_content = load_query(query_file_path)
            results_text = client.run_query_clean_result(query_content)
            
            output_filepath = os.path.join(output_folder, f"{file_name}.csv")
            save_csv_results(results_text, output_filepath)
        except Exception as e:
            print(f"ERROR: Skipping query {query_file_path} due to an error: {e}")

        # control_query = load_query(query_file)        
        # results = endpoint.run_query_clean_result(control_query)
        # len_result = len(results.split('\n'))
        # if len_result > 2: 
        #     output_filename = f"{output_path}{file_name}.csv"
        #     df_objs = pd.read_csv(StringIO(results))            
        #     df_objs.to_csv(output_filename, sep=",", index=False)
        #     print(f"All non-empty query results have been saved in {output_filename}...")
        # else:
        #     print(f"Data is validated, there is nothing to show in the {file_name} query result.")

def run_query_write_result(endpoint, query_path, output_path):
    query = load_query(query_path)
    result = endpoint.run_query_clean_result(query)
    save_csv_results(result, output_path)

def merge_csv_files(
    input_folder: str,
    output_file_path: str,
    file_pattern: str = "*.csv",
    input_delimiter: str = ",",
    output_delimiter: str = ","
) -> None:
    """
    Finds all CSV files in a folder, merges them, and saves the result.
    Assumes all CSVs have compatible headers.
    """
    output_dir = os.path.dirname(output_file_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)

    csv_files = sorted(glob.glob(os.path.join(input_folder, file_pattern)))

    if not csv_files:
        print(f"WARNING: No files found matching '{file_pattern}' in '{input_folder}'. No merged output.")
        return

    print(f"\nINFO: Found {len(csv_files)} files to merge:")
    for f in csv_files:
        print(f"  - {os.path.basename(f)}")

    df_list = []
    for file in csv_files:
        try:
            df = pd.read_csv(file, delimiter=input_delimiter)
            df_list.append(df)
        except pd.errors.EmptyDataError:
            print(f"WARNING: Skipping empty file: {os.path.basename(file)}")
        except Exception as e:
            print(f"ERROR: Error reading {os.path.basename(file)}: {e}")

    if not df_list:
        print("INFO: No data successfully read for merging. Output file will not be created.")
        return

    print("INFO: Merging data...")
    merged_df = pd.concat(df_list, ignore_index=True)

    merged_df.to_csv(output_file_path, index=False, sep=output_delimiter)
    print(f"INFO: ✅ Merge complete. Saved to: {output_file_path}")
    print(f"INFO: Total rows in merged file: {len(merged_df)}")

def retrieve_hoofdgroepen(client: LacesRequest, query_path: str) -> List[str]:
    """
    Retrieves a list of 'hoofdgroepen' by running a specific SPARQL query.
    Assumes the query returns a CSV with a column named 'hoofdgroup_name'.
    """
    print(f"INFO: Retrieving hoofdgroepen using query: {os.path.basename(query_path)}")
    try:
        results_text = client.run_query_csv(load_query(query_path))
        df = pd.read_csv(StringIO(results_text))
        
        if df.empty or 'hoofdgroup_name' not in df.columns:
            print(f"WARNING: Hoofdgroepen query result is empty or missing 'hoofdgroup_name' column. Actual columns: {df.columns.tolist()}")
            return []
        
        hoofdgroepen = df['hoofdgroup_name'].tolist()
        print(f"INFO: Retrieved {len(hoofdgroepen)} hoofdgroepen.")
        return hoofdgroepen
    except Exception as e:
        print(f"ERROR: Failed to retrieve hoofdgroepen: {e}")
        return []


if __name__ == "__main__":
    hoofdgroepen_query_path = os.path.join(QUERY_FOLDER, "NLCS_Retrieve_Hoofdgroepen.rq")
    objects_query_template_path = os.path.join(QUERY_FOLDER, "search_term_read_objects.rq")

    my_config = {
        "url": SPARQL_ENDPOINT,
        "username": LDP_TOKEN_ID,
        "password": LDP_PASSWORD,
    }

    try:
        print("Initializing Laces client...")
        client = LacesRequest(config=my_config)
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"FATAL ERROR: Could not initialize Laces client: {e}. Exiting.")
        exit(1)
##################################################

    single_output_file = os.path.join(CSV_CONTROLS_FOLDER, "controle_id_uniqueness_all.csv")
    run_query_write_result(client, f"{CONTROL_QUERY_FOLDER}controle_id_uniqueness_all.rq", single_output_file)   
##################################################
    print("\n--- Running all validation queries in folder ---")
    run_queries_in_folder(client, CONTROL_QUERY_FOLDER, CSV_CONTROLS_FOLDER)
##################################################

    print("\n--- Retrieving Hoofdgroepen and running object queries ---")
    hoofdgroepen = retrieve_hoofdgroepen(client, hoofdgroepen_query_path)
    print(hoofdgroepen)

    for hg in hoofdgroepen:
        print(f"INFO: Sending objects query for hoofdgroup '{hg}'...")
        try:
            hoofdgroup_query = build_parameterized_query(
                    objects_query_template_path,
                    "$hoofdgroup_name", 
                    hg
                )
            objects_output_path = f"{CSV_OBJECTS_FOLDER}objecten-concept-5.1-{hg}.csv"
            results = client.run_query_clean_result(hoofdgroup_query)
            save_csv_results(results, objects_output_path)
        except Exception as e:
            print(f"ERROR: Failed to process query for hoofdgroup '{hg}': {e}")

    print("\n--- Merging all object CSV files ---")
    merged_objects_output_file = os.path.join(CSV_OUTPUT_ROOT_FOLDER, "all_objects-concept-5.1.csv")
    merge_csv_files(merged_objects_output_file, merged_objects_output_file)

    print("\nScript execution finished.")   
































