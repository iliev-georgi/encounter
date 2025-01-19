from SPARQLWrapper import SPARQLWrapper, JSON
from config import AVIO_SPARQL_ENDPOINT, DBPEDIA_SPARQL_ENDPOINT, PASTABYTES_ENCOUNTER, LOCAL_SPARQL_USER, LOCAL_SPARQL_PASSWORD
from model import Suggestion, Encounter


def get_filtered_list(partial, endpoint=AVIO_SPARQL_ENDPOINT, limit=20):
    sparql = SPARQLWrapper(endpoint)
    query = """
            PREFIX avio: <http://www.yso.fi/onto/avio/>
            select * where {{
            ?species a avio:species .
            ?species skos:prefLabel ?prefLabel .
            ?prefLabel bif:contains "'{}*'" .
            OPTIONAL {{
                    ?species avio:linkToEnglishWikipedia ?wikipediaLink .
                    }}
            }}
            limit {}
            """.format(
        partial, limit
    )
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    lookup_table = []
    for result in results["results"]["bindings"]:
        lookup_table.append(
            Suggestion(
                prefLabel=result["prefLabel"]["value"],
                language=result["prefLabel"]["xml:lang"],
                species=result["species"]["value"],
                wikipediaLink=result["wikipediaLink"]["value"],
                thumbnail=None,
                abstract=None,
            )
        )

    return lookup_table


def append_previews_to(lookup_table, endpoint=DBPEDIA_SPARQL_ENDPOINT):
    sparql = SPARQLWrapper(endpoint)
    values = []
    for suggestion in lookup_table:
        values.append(f"<{suggestion.wikipediaLink}>")

    query = """
            SELECT DISTINCT ?wikipediaLink ?thumbnail ?abstract WHERE {{
            VALUES ?wikipediaLink {{ {} }}
            ?dbo1 foaf:isPrimaryTopicOf ?wikipediaLink .
            {{  ?dbo1 dbo:wikiPageRedirects ?dbo2 .
                ?dbo2 dbo:thumbnail ?thumbnail .
                 OPTIONAL {{ ?dbo2 dbo:abstract ?abstract .
                            FILTER (lang(?abstract) = "en")}}
            }}
            UNION
            {{  ?dbo1 dbo:thumbnail ?thumbnail .
                OPTIONAL {{ ?dbo1 dbo:abstract ?abstract .
                            FILTER (lang(?abstract) = "en") }}
            }}
            }}
            """.format(
        " ".join(values)
    )

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    thumbnails = dict()
    for result in results["results"]["bindings"]:
        thumbnails[result["wikipediaLink"]["value"]] = (
            result["thumbnail"]["value"],
            result["abstract"]["value"],
        )

    for suggestion in lookup_table:
        suggestion.thumbnail = thumbnails.get(suggestion.wikipediaLink, ((None, None)))[
            0
        ]
        suggestion.abstract = thumbnails.get(suggestion.wikipediaLink, ((None, "__No description available__")))[
            1
        ]


def insert_encounter(encounter: Encounter, endpoint=AVIO_SPARQL_ENDPOINT):
    sparql = SPARQLWrapper(endpoint)
    sparql.setCredentials(LOCAL_SPARQL_USER, LOCAL_SPARQL_PASSWORD)
    query = """
            PREFIX avio: <http://www.yso.fi/onto/avio/>
            PREFIX encounter: <https://encounter.pastabytes.com/>
            PREFIX encounter-location: <https://encounter.pastabytes.com/location/>
            PREFIX encounter-ontology: <https://encounter.pastabytes.com/ontology/>
            PREFIX pixelfed: <https://pixelfed.pastabytes.com/>

            INSERT DATA {{
                GRAPH <{}> {{
                    encounter:{} a encounter-ontology:Encounter ;
                        encounter-ontology:hasLocation encounter-location:{} ;
                        encounter-ontology:hasTime "{}"^^xsd:long ;
                        encounter-ontology:hasUser <{}> ;
                        encounter-ontology:hasEvidence <{}> .

                    encounter-location:{} a encounter-ontology:Location ;
                        encounter-ontology:hasLatitude "{}"^^xsd:float ;
                        encounter-ontology:hasLongitude "{}"^^xsd:float .

                    <{}> a encounter-ontology:User .

                    <{}> a encounter-ontology:Evidence ;
                        encounter-ontology:depicts <{}> .
                    
                    <{}> a encounter-ontology:Bird .
                }}
            }}
            """.format(
        PASTABYTES_ENCOUNTER,
        encounter.id,
        encounter.location.id,
        encounter.time,
        encounter.user,
        encounter.evidence,
        encounter.location.id,
        encounter.location.latitude,
        encounter.location.longitude,
        encounter.user,
        encounter.evidence,
        encounter.species,
        encounter.species,
    )
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.method = "POST"
    result = sparql.query().convert()
    if result is not None:
        return result.get("results").get("bindings")[0].get("callret-0").get("value").endswith("-- done")

    return False
