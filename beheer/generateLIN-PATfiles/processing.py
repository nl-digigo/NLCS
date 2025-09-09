import logging
import os
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd
from io import StringIO

logging.basicConfig()
logging.root.setLevel(logging.INFO)

def _env_default(key, default=""):
    return os.environ.get(key, default)


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
            username, password = _env_default("LDP_USERNAME"), _env_default("LDP_PASSWORD")
                
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

def setup_api_request(config, query='retrieveLinetypeInfo.rq'): #url, query='retrieveLinetypeInfo.rq', username=None, password=None):
    '''
    Retrieve the Lijntype information from the NLCS SPARQL endpoint.
    Input:
    - url (str): The URL of the NLCS publication (not the SPARQL endpoint!)
    - subjectFile (str): The path where the CSV output will be stored, including the .csv extension
    - query (str): The path to the query to retrieve the Lijntype information
    - username (str): The username of the necessary credentials to access the SPARQL endpoint [OPTIONAL]
    - password (str): The password of the necessary credentials to access the SPARQL endpoint [OPTIONAL]
    Output:
    - a dataframe containing the retrieved objects
    '''
    
    with open(os.path.abspath(query), "r") as f:
        queryLinetypes = f.read() 
    # config = {"url": configOriginal['url']}
    # if configOriginal['username']:
    #     config["username"] = configOriginal['username']
    #     config["password"] = configOriginal['password']
    laces_api = LacesRequest(config)
    str_clean = laces_api.run_query_clean_result(queryLinetypes)
    df = pd.read_csv(StringIO(str_clean))
    return df

def generate_lin(config):
    '''
    Creates a .lin file after retrieving Lijntype information from a SPARQL endpoint

    Input:
        - config (dict): a dictionary that contains all the information needed to run the script. Parameters are: 
            - url (str): the SPARQL endpoint, 
            - username (str): the Access Token key needed to access the endpoint [],
            - password (str): the Access Token password needed to access the endpoint,
            - default-graph-uri (list): ,
            - named-graph-uri (list):
    
    Output:
        - a Dataframe and a string of the retrieved information
    '''

    type_repository = config['url'].split("digitalbuildingdata/nlcs/")[1].split('/')[0]
    type_publication = 'definitief'
    if type_repository in ('test', 'acceptance'):
        type_publication = 'concept'
    
    version = config['url'].split('/')[-2].replace('_','.')

    lijntypes = f"Lin bestand gegenereerd uit de NLCS database versie {type_publication}-{version}"

    result = setup_api_request(config, query=config["query"])
    for _, lijntype in result.iterrows():
        lijntypes += f"\n\n*{lijntype.tgtLinetypeName},{lijntype.tgtLinetypeID if pd.notna(lijntype.tgtLinetypeID) else ''}"
        # if lijntypes[-1] == ',':
        #     lijntypes = lijntypes[:-1]
        lijntypes += f"\n{lijntype.tgtLinetypeInfo}"

    with open(f"NLCS-{type_publication}-{version.replace('.','-')}_linetypes.lin", "w") as f:
        f.write(lijntypes)
        f.close()
        logging.info(".lin file saved")
    
    return result, lijntypes

def generate_pat(config):
    '''
    Creates a .pat file after retrieving Arcering information from a SPARQL endpoint

    Input:
        - config (dict): a dictionary that contains all the information needed to run the script. Parameters are: 
            - url (str): the SPARQL endpoint, 
            - username (str): the Access Token key needed to access the endpoint [],
            - password (str): the Access Token password needed to access the endpoint,
            - default-graph-uri (list): ,
            - named-graph-uri (list):
    
    Output:
        - a Dataframe and a string of the retrieved information
    '''

    type_repository = config['url'].split("digitalbuildingdata/nlcs/")[1].split('/')[0]
    type_publication = 'definitief'
    if type_repository in ('test', 'acceptance'):
        type_publication = 'concept'
    
    version = config['url'].split('/')[-2].replace('_','.')

    allArcering = f";;\n;;pat definitie/bestand gegenereerd uit de NLCS database versie {type_publication}-{version}\n;;"

    result = setup_api_request(config, query=config["query"])
    for _, arcering in result.iterrows():

        ## Replace whitespaces to linebreaks
        allArcering += f"\n*{arcering.tgtArceringName},{arcering.tgtArceringVRKL_KORT}\n{arcering.tgtArceringVRKL_LANG}".replace(" ", "\n")
        singleArcering = f";;\n;;pat definitie/bestand gegenereerd uit de NLCS database versie {type_publication}-{version}\n;;"
        singleArcering += f"\n*{arcering.tgtArceringName},{arcering.tgtArceringVRKL_KORT}\n{arcering.tgtArceringVRKL_LANG}".replace(" ","\n")
    
        with open(f"{arcering.tgtArceringName}.pat", "w") as f:
            f.write(singleArcering)
            f.close()
            logging.info(f"{arcering.tgtArceringName}.pat file saved")

    with open(f"NLCS-allPatInOne.pat", "w") as f:
        f.write(allArcering)
        f.close()
        logging.info("NLCS-allPatInOne.pat file saved")

        # ## Default
        # allArcering += f"\n*{arcering.tgtArceringName},{arcering.tgtArceringVRKL_KORT}\n{arcering.tgtArceringVRKL_LANG}"
        # singleArcering = f";;\n;;pat definitie/bestand gegenereerd uit de NLCS database versie {type_publication}-{version}\n;;"
        # singleArcering += f"\n*{arcering.tgtArceringName},{arcering.tgtArceringVRKL_KORT}\n{arcering.tgtArceringVRKL_LANG}".replace(" ","\n")

    
        with open(f"{arcering.tgtArceringName}.pat", "w") as f:
            f.write(singleArcering)
            f.close()
            logging.info(f"{arcering.tgtArceringName}.pat file saved")

    with open(f"NLCS-allPatInOne.pat", "w") as f:
        f.write(allArcering)
        f.close()
        logging.info("NLCS-allPatInOne.pat file saved")
    
    return result, allArcering
