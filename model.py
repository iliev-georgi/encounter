from dataclasses import dataclass
from collections import namedtuple
from config import PASTABYTES_ENCOUNTER


@dataclass
class Suggestion():
    prefLabel: str
    language: str
    species: str
    wikipediaLink: str
    thumbnail: str
    abstract: str

@dataclass
class Location():
    id: str
    latitude: float = 42.698334
    longitude: float = 23.319941 # Sofia, Bulgaria

@dataclass
class Encounter():
    id: str
    user: str
    evidence: str
    species: str
    time: int
    location: Location
    context: str = PASTABYTES_ENCOUNTER

@dataclass
class ToAnnotate():
    id: str
    preview_url: str
    content: str
    time: int 