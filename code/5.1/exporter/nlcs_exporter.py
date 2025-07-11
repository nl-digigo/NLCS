import requests
import os
import logging
from requests.auth import HTTPBasicAuth
import pandas as pd
from io import StringIO
import glob

HOOFDGROEPPEN = [
    "AL", "GR", "SC", "HC", "HU", "MO", "AM", "MW", "BV", "IW", "IS", "BC",
    "WH", "KL", "MC", "KC", "VV", "VH", "KG", "OB", "VW", "RI", "OV", "GC",
    "ZZ", "GW", "GK", "FC", "IE", "FV", "IV", "SB", "ES", "OG", "KW"
]

SPARQL_ENDPOINT = "https://hub.laces.tech/digitalbuildingdata/nlcs/acceptance/nlcs-acceptatie/versions/rv_5_1_3/sparql"
ACCESS_TOKEN = "bd974f55-3de6-49e0-8423-cb883367b451"
PASSWORD = "Teq3PZj2jdAtLWZuBmm3"

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

def build_query_from_file(template_path, hoofdgroup):
    """
    Reads a SPARQL query template from a .rq file, replaces the
    placeholder, and returns the final query string.
    
    Args:
        template_path (str): The file path to the .rq template file.
        search_term (str): The value to insert into the query.
        
    Returns:
        str: The final, ready-to-execute SPARQL query.
    """
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            query_template = f.read()

        final_query = query_template.replace("$hoofdgroup_name", hoofdgroup)
        
        return final_query
    
    except FileNotFoundError:
        print(f"FATAL ERROR: The query file was not found at '{template_path}'")
        raise

def validate_result(endpoint, validations_folder_path):
    """
    Validates data by control queries and outputs non-empty ones in CSV format. 
    """
    print("Validation started...")
    query_files = glob.glob(os.path.join(validations_folder_path, '*.rq'))
    for query_file in query_files:
        file_name = query_file.split('\\')[1].split(".")[0]
        print(f"Validating for {file_name}...")
        with open(query_file, 'r', encoding='utf-8') as f:
            control_query = f.read()
        
        validation = endpoint.run_query_clean_result(control_query)
        len_validation = len(validation.split('\n'))
        if len_validation > 2: 
            output_filename = f"code/5.1/exporter/CSV_results/validations/validation_{file_name}.csv"
            print(f"Validation results has been saved in {output_filename}...")
            df_objs = pd.read_csv(StringIO(validation))            
            df_objs.to_csv(output_filename, sep=";", index=False)
        else:
            print(f"Data is validated, there is nothing in the {file_name} query result.")

def generate_csv_per_hoofdgroup(hoofdgroup, endpoint):
    hoofdgroup_query = build_query_from_file('code/5.1/exporter/queries/read_objects.rq', hoofdgroup)
    results = endpoint.run_query_clean_result(hoofdgroup_query)
    df_objs = pd.read_csv(StringIO(results))
    output_filename = f"{path}{hg}_sparql_results.csv"
    df_objs.to_csv(output_filename, sep=";", index=False)

if __name__ == "__main__":
    path = "./CSV_results/"
    validations_folder_path = "code/5.1/exporter/queries/controle_queries/"

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

    validate_result(client, validations_folder_path)
    
    for hg in HOOFDGROEPPEN:
        try:
            print(f"\nSending objects query to the endpoint for hoofdgroup {hg}...")
            generate_csv_per_hoofdgroup(hg, client)

        except ValueError as e:
            print(f"Configuration Error: {e}")
        except Exception as e:
            print(f"\nAn error occurred during the request: {e}")