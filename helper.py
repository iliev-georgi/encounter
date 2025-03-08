from model import Location, Encounter
import hashlib
from sparql_functions import insert_encounter
from exception import SPARQLException
import base64, io
from PIL import Image
import branca
from datetime import datetime
import streamlit as st
from strings import *


def clear_keyup_input_for(input_id: str):
    to_clear = next(
        (
            key
            for key in st.session_state.keys()
            if key.startswith(f"st_keyup_{input_id}")
        ),
        False,
    )
    if to_clear:
        st.session_state[to_clear] = ""


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
    input_id=None,
    time=None,
    user=None,
    evidence=None,
    species=None,
    latitude=Location.latitude,
    longitude=Location.longitude,
    context=Encounter.context,
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
        context=context,
    )

    try:
        result = insert_encounter(encounter)
        if not result:
            raise SPARQLException(result.response.read())
    except Exception:
        print("SPARQL update failed.")

    clear_keyup_input_for(input_id)


def get_jpeg_thumbnail(attached_media: bytes, x=150, y=150):

    base64encoded_media = base64.b64encode(attached_media)

    buffer = io.BytesIO()
    imgdata = base64.b64decode(base64encoded_media)
    img = Image.open(io.BytesIO(imgdata))
    img.thumbnail((x, y), Image.Resampling.LANCZOS)  # x, y
    img.save(buffer, "JPEG")

    return base64.b64encode(buffer.getvalue())


def build_popup_iframe(encounter: Encounter, thumbnail: bytes) -> branca.element.IFrame:

    html = """
    <body style='font-size: 0.65em; font-family: sans-serif;'>
    <p>On <strong>{}</strong></p>
    <a href="{}" target="_blank"><img src="data:image/jpg;base64,{}">
    
    """.format

    iframe = branca.element.IFrame(
        html=html(
            datetime.fromtimestamp(encounter.time).strftime("%B %d, %Y"),
            encounter.species,
            thumbnail.decode(),
        ),
        width=200,
    )

    return iframe


def empty_feed(photo_sharing_url: str):
    st.warning(EMPTY_FEED.format(photo_sharing_url), icon=":material/owl:")
