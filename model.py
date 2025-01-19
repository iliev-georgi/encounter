from dataclasses import dataclass


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
    latitude: float
    longitude: float

@dataclass
class Encounter():
    id: str
    user: str
    evidence: str
    species: str
    time: int
    location: Location