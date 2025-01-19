from model import Location, Encounter
import hashlib
from sparql_functions import insert_encounter
from exception import SPARQLException


def join_labels(lookup_table):
    seen = dict()
    for suggestion in lookup_table:
        suggestion.prefLabel = f"{suggestion.prefLabel} ({suggestion.language})"
        if suggestion.species in seen:
            seen[suggestion.species].prefLabel = (
                f"{seen[suggestion.species].prefLabel} / {suggestion.prefLabel}"
            )
        else:
            seen[suggestion.species] = suggestion

    return seen.values()


def register_encounter(
    time=None,
    user=None,
    evidence=None,
    species=None,
    latitude=42.698334,
    longitude=23.319941,
):

    location_seed = f"{latitude}_{longitude}"
    location = Location(
        id=hashlib.sha1(location_seed.encode()).hexdigest(),
        latitude=latitude,
        longitude=longitude,
    )

    encounter_seed = f"{time}_{user}_{evidence}_{species}_{location_seed}"
    encounter = Encounter(
        id=hashlib.sha1(encounter_seed.encode()).hexdigest(),
        user=user,
        evidence=evidence,
        species=species,
        time=time,
        location=location,
    )

    try:
        result = insert_encounter(encounter)
        if not result:
            raise SPARQLException(result.response.read())
    except Exception:
        print("SPARQL update failed.")
