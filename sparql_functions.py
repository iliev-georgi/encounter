from SPARQLWrapper import SPARQLWrapper, JSON, JSONLD
from rdflib import RDF, Namespace
from config import (
    AVIO_SPARQL_ENDPOINT,
    AVIO_SPARQL_AUTH_ENDPOINT,
    DBPEDIA_SPARQL_ENDPOINT,
    LOCAL_SPARQL_USER,
    LOCAL_SPARQL_PASSWORD,
    PASTABYTES_ENCOUNTER,
)
from model import Suggestion, Encounter, Location, ToAnnotate


def get_filtered_list(partial, endpoint=AVIO_SPARQL_ENDPOINT, limit=20):
    sparql = SPARQLWrapper(endpoint)
    query = f"""
            PREFIX avio: <http://www.yso.fi/onto/avio/>
            select * where {{
            ?species a avio:species .
            ?species skos:prefLabel ?prefLabel .
            ?prefLabel bif:contains "'{partial}*'" .
            OPTIONAL {{
                    ?species avio:linkToEnglishWikipedia ?wikipediaLink .
                    }}
            }}
            limit {limit}
            """

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
        suggestion.abstract = thumbnails.get(
            suggestion.wikipediaLink, ((None, "__No description available__"))
        )[1]


def insert_encounter(encounter: Encounter, endpoint=AVIO_SPARQL_AUTH_ENDPOINT):
    sparql = SPARQLWrapper(endpoint)
    sparql.setHTTPAuth("DIGEST")
    sparql.setCredentials(LOCAL_SPARQL_USER, LOCAL_SPARQL_PASSWORD)
    query = f"""
            PREFIX avio: <http://www.yso.fi/onto/avio/>
            PREFIX encounter: <https://encounter.pastabytes.com/v0.1.0/>
            PREFIX encounter-location: <https://encounter.pastabytes.com/v0.1.0/location/>
            PREFIX encounter-ontology: <https://encounter.pastabytes.com/v0.1.0/ontology/>
            PREFIX pixelfed: <https://pixelfed.pastabytes.com/>
    
            DELETE WHERE {{
            GRAPH <{encounter.context}> {{   
                    ?encounter_id a encounter-ontology:Encounter ;
                        encounter-ontology:hasLocation ?encounter_location_id ;
                        encounter-ontology:hasTime ?encounter_time ;
                        encounter-ontology:hasUser ?encounter_user ;
                        encounter-ontology:hasEvidence ?encounter_evidence .

                    <{encounter.evidence}> a encounter-ontology:Evidence ;
                        encounter-ontology:depicts ?encounter_species .
                    
                    ?encounter_species a encounter-ontology:Bird .
                }}
            }}

            INSERT DATA {{
                GRAPH <{encounter.context}> {{
                    encounter:{encounter.id} a encounter-ontology:Encounter ;
                        encounter-ontology:hasLocation encounter-location:{encounter.location.id} ;
                        encounter-ontology:hasTime "{encounter.time}"^^xsd:long ;
                        encounter-ontology:hasUser <{encounter.user}> ;
                        encounter-ontology:hasEvidence <{encounter.evidence}> .

                    encounter-location:{encounter.location.id} a encounter-ontology:Location ;
                        encounter-ontology:hasLatitude "{encounter.location.latitude}"^^xsd:float ;
                        encounter-ontology:hasLongitude "{encounter.location.longitude}"^^xsd:float .

                    <{encounter.user}> a encounter-ontology:User .

                    <{encounter.evidence}> a encounter-ontology:Evidence ;
                        encounter-ontology:depicts <{encounter.species}> .
                    
                    <{encounter.species}> a encounter-ontology:Bird .
                }}
            }}
            """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.method = "POST"
    result = sparql.query().convert()
    if result is not None:
        return (
            result.get("results")
            .get("bindings")[0]
            .get("callret-0")
            .get("value")
            .endswith("-- done")
        )

    return False


def collect_encounters(
    context: str = PASTABYTES_ENCOUNTER, endpoint: str = AVIO_SPARQL_ENDPOINT
) -> list[Encounter]:

    sparql = SPARQLWrapper(endpoint)
    ENCOUNTER_ONTOLOGY = Namespace("https://encounter.pastabytes.com/v0.1.0/ontology/")
    encounters = []
    query = f"""
            PREFIX encounter-ontology: <https://encounter.pastabytes.com/v0.1.0/ontology/>

            CONSTRUCT 
            WHERE {{
                GRAPH <{context}> {{
                    ?encounter_id a encounter-ontology:Encounter ;
                        encounter-ontology:hasLocation ?encounter_location_id ;
                        encounter-ontology:hasTime ?encounter_time ;
                        encounter-ontology:hasUser ?encounter_user ;
                        encounter-ontology:hasEvidence ?encounter_evidence .

                    ?encounter_location_id a encounter-ontology:Location ;
                        encounter-ontology:hasLatitude ?encounter_location_latitude ;
                        encounter-ontology:hasLongitude ?encounter_location_longitude .

                    ?encounter_user a encounter-ontology:User .

                    ?encounter_evidence a encounter-ontology:Evidence ;
                        encounter-ontology:depicts ?encounter_species .
                    
                    ?encounter_species a encounter-ontology:Bird .
                }}
            }}
            """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSONLD)
    sparql.method = "POST"
    result = sparql.query().convert()

    for encounter_id in result.subjects(RDF.type, ENCOUNTER_ONTOLOGY.Encounter):
        location_id = result.value(encounter_id, ENCOUNTER_ONTOLOGY.hasLocation)

        latitude = result.value(location_id, ENCOUNTER_ONTOLOGY.hasLatitude)
        longitude = result.value(location_id, ENCOUNTER_ONTOLOGY.hasLongitude)

        user = result.value(encounter_id, ENCOUNTER_ONTOLOGY.hasUser)
        evidence = result.value(encounter_id, ENCOUNTER_ONTOLOGY.hasEvidence)
        species = result.value(evidence, ENCOUNTER_ONTOLOGY.depicts)
        time = result.value(encounter_id, ENCOUNTER_ONTOLOGY.hasTime)

        location = Location(
            id=str(location_id), latitude=float(latitude), longitude=float(longitude)
        )

        encounters.append(
            Encounter(
                id=str(encounter_id),
                user=str(user),
                evidence=str(evidence),
                species=str(species),
                time=int(time),
                location=location,
                context=str(context),
            )
        )

    return encounters


def get_labels(
    species: list[str], endpoint=AVIO_SPARQL_ENDPOINT, lang: str = "en"
) -> dict:
    sparql = SPARQLWrapper(endpoint)
    query = f"""
            PREFIX avio: <http://www.yso.fi/onto/avio/>
            SELECT ?species ?prefLabel WHERE {{
            VALUES ?species {{ {" ".join(species)} }}
            ?species skos:prefLabel ?prefLabel .
            FILTER (lang(?prefLabel) = "{lang}")
            }}
            """

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    species_label_mappings = dict()
    for result in results["results"]["bindings"]:
        species_label_mappings[result["species"]["value"]] = result["prefLabel"][
            "value"
        ]

    return species_label_mappings


def append_annotation_state_to(
    statuses: list[ToAnnotate],
    endpoint=AVIO_SPARQL_ENDPOINT,
    context: str = PASTABYTES_ENCOUNTER,
):
    evidence_list = [f"<{status.preview_url}>" for status in statuses]
    query = f"""
            PREFIX encounter-ontology: <https://encounter.pastabytes.com/v0.1.0/ontology/>

            CONSTRUCT 
            {{   
                    ?encounter_id a encounter-ontology:Encounter ;
                        encounter-ontology:hasLocation ?encounter_location_id ;
                        encounter-ontology:hasTime ?encounter_time ;
                        encounter-ontology:hasUser ?encounter_user ;
                        encounter-ontology:hasEvidence ?encounter_evidence .

                    ?encounter_location_id a encounter-ontology:Location ;
                        encounter-ontology:hasLatitude ?encounter_location_latitude ;
                        encounter-ontology:hasLongitude ?encounter_location_longitude .

                    ?encounter_user a encounter-ontology:User .

                    ?encounter_evidence a encounter-ontology:Evidence ;
                        encounter-ontology:depicts ?encounter_species .
                    
                    ?encounter_species a encounter-ontology:Bird .
                }}

            WHERE {{ 
            GRAPH <{context}> {{
                    VALUES ?encounter_evidence {{ {" ".join(evidence_list)} }}
                    ?encounter_id a encounter-ontology:Encounter ;
                        encounter-ontology:hasLocation ?encounter_location_id ;
                        encounter-ontology:hasTime ?encounter_time ;
                        encounter-ontology:hasUser ?encounter_user ;
                        encounter-ontology:hasEvidence ?encounter_evidence .

                    ?encounter_location_id a encounter-ontology:Location ;
                        encounter-ontology:hasLatitude ?encounter_location_latitude ;
                        encounter-ontology:hasLongitude ?encounter_location_longitude .

                    ?encounter_user a encounter-ontology:User .

                    ?encounter_evidence a encounter-ontology:Evidence ;
                        encounter-ontology:depicts ?encounter_species .
                    
                    ?encounter_species a encounter-ontology:Bird .
            }}
            }}
            """
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSONLD)
    sparql.method = "POST"
    result = sparql.query().convert()

    ENCOUNTER_ONTOLOGY = Namespace("https://encounter.pastabytes.com/v0.1.0/ontology/")

    for evidence in result.objects(predicate=ENCOUNTER_ONTOLOGY.hasEvidence):
        for status in statuses:
            if status.preview_url == str(evidence):
                status.annotated = True
                encounter = next(result.subjects(predicate=ENCOUNTER_ONTOLOGY.hasEvidence, object=evidence))
                location = next(result.objects(subject=encounter, predicate=ENCOUNTER_ONTOLOGY.hasLocation))
                lng = next(result.objects(subject=location, predicate=ENCOUNTER_ONTOLOGY.hasLongitude))
                lat = next(result.objects(subject=location, predicate=ENCOUNTER_ONTOLOGY.hasLatitude))
                species = next(result.objects(subject=evidence, predicate=ENCOUNTER_ONTOLOGY.depicts))
                species_label_map = get_labels([f"<{str(species)}>"])
                status.label = species_label_map.get(str(species), "Unknown")
                status.lng = float(lng)
                status.lat = float(lat)
