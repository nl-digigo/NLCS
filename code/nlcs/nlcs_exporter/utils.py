from rdflib import Graph

# This is to use on LDP, for getting the correct export uris of the 2_NLCS_Expired_Concepts.ttl
# So that the IncreasingIDnumbers query can work correctly!

def build_query(values_list):
    # Build VALUES block
    values_str = " ".join(f'"{v}"' for v in values_list)

    query = f"""
    PREFIX skos: <http://www.w3.org/2004/02/skos/core#>

    SELECT ?s
    WHERE {{
        VALUES ?v {{ {values_str} }}

        ?s skos:prefLabel ?v .
    }}
    """
    return query

def get_export_uris_of_imported_concepts(import_file):
    """    
    Reads input uris and their labels from ttl file and returns a query 
    to be sent to the graph for retrieving export uris.

    :param import_file: path to the ttl file which is imported to laces
    """
    g = Graph()
    g.parse(import_file, format="ttl")

    # query = """
    # PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    # prefix otl: <http://www.laces.tech/publication/ns/semmtech/live/laces/schema/otl-manager/> 

    # SELECT DISTINCT ?objectURI ?label
    # WHERE {
    #     ?objectURI rdf:type otl:PhysicalObject .
    #     ?objectURI otl:attr-Conceptual-name ?label .
    # }
    # """

    query = """
    PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
    prefix otl: <http://www.laces.tech/publication/ns/semmtech/live/laces/schema/otl-manager/> 

    SELECT DISTINCT ?objectURI ?label
    WHERE {
        ?objectURI rdf:type otl:Document .
        ?objectURI otl:attr-Conceptual-name ?label .
    }
    """

    results = g.query(query)
    uris = [str(row.objectURI) for row in results]
    labels = [str(row.label) for row in results]

    print(f"Found {len(uris)} uris")

    return build_query(labels)


if __name__ == "__main__":
    import_file = "./code/nlcs/controls_within_versions/helpers/2_NLCS_Expired_Concepts.ttl"
    print(get_export_uris_of_imported_concepts(import_file))

    