import streamlit as st
import requests
from io import BytesIO
from sparql_functions import (
    get_filtered_list,
    append_previews_to,
    append_annotation_state_to,
)
from st_keyup import st_keyup
from config import *
from helper import join_labels
from helper import register_encounter
from pixelfed_functions import get_statuses, get_attached_media
from model import Location, ToAnnotate
import folium
from streamlit_folium import st_folium
from datetime import datetime


def update_plot_and_register_encounter(
    to_annotate: ToAnnotate,
    marker_label: str,
    user: str,
    species: str,
    latitude: float,
    longitude: float,
):
    
    # update location and label on map
    to_annotate.label = marker_label
    to_annotate.lat = latitude
    to_annotate.lng = longitude

    # persist encounter
    register_encounter(
        input_id=to_annotate.id,
        time=to_annotate.time,
        user=user,
        evidence=to_annotate.preview_url,
        species=species,
        latitude=latitude,
        longitude=longitude,
    )


@st.fragment
def plot_encounter_location(to_annotate):
    center_x, center_y = Location.latitude, Location.longitude
    map = folium.Map()
    map.add_child(folium.LatLngPopup())
    if all(
        mandatory is not None
        for mandatory in [
            to_annotate.lat,
            to_annotate.lng,
            to_annotate.label,
        ]
    ):
        map.add_child(
            folium.Marker(
                location=(to_annotate.lat, to_annotate.lng),
                icon=folium.Icon(color="darkblue", icon="crow", prefix="fa"),
                tooltip=to_annotate.label,
            )
        )
        center_x, center_y = to_annotate.lat, to_annotate.lng
        st.session_state.last_location[to_annotate.id] = (center_x, center_y)

    st_data = st_folium(map, center=(center_x, center_y), zoom=10, key=to_annotate.id)
    if st_data.get("last_clicked"):
        st.session_state.last_location[to_annotate.id] = (
            st_data["last_clicked"]["lat"],
            st_data["last_clicked"]["lng"],
        )
        to_annotate.lat = st_data["last_clicked"]["lat"]
        to_annotate.lng = st_data["last_clicked"]["lng"]
        if not to_annotate.label:
            to_annotate.label = "Unknown"


@st.fragment
def suggest_species(to_annotate, user_info):
    name = st_keyup("Enter bird name", key=to_annotate.id, debounce=500)
    if name and len(name) > 3:
        lookup_table = get_filtered_list(name)
        append_previews_to(lookup_table)
        lookup_table = join_labels(lookup_table)
    else:
        lookup_table = dict()
    for suggestion in lookup_table:
        column1, column2 = st.columns([1, 2])
        with column1:
            try:
                if (
                    suggestion.thumbnail
                    and requests.get(
                        suggestion.thumbnail,
                        timeout=3,
                        allow_redirects=True,
                    ).status_code
                    != 404
                ):
                    st.image(suggestion.thumbnail)
                else:
                    st.markdown("**No preview found**")
            except:
                st.markdown("__Preview error__")
        with column2:
            st.button(
                suggestion.prefLabel,
                on_click=update_plot_and_register_encounter,
                help=suggestion.abstract,
                kwargs=dict(
                    to_annotate=to_annotate,
                    marker_label=suggestion.prefLabel,
                    user=user_info.get("url"),
                    species=suggestion.species,
                    latitude=st.session_state.last_location[to_annotate.id][0],
                    longitude=st.session_state.last_location[to_annotate.id][1],
                ),
            )


def render_annotate(user_info):

    to_annotate_list = get_statuses(
        user_info["id"], st.session_state["token"]["access_token"]
    )
    append_annotation_state_to(to_annotate_list)

    for to_annotate in to_annotate_list:
        if "last_location" not in st.session_state:
            st.session_state.last_location = dict()
        st.session_state.last_location[to_annotate.id] = (
            Location.latitude,
            Location.longitude,
        )
        column1, column2 = st.columns([1, 2])
        with column1:
            attached_media = get_attached_media(
                to_annotate.preview_url, st.session_state["token"]["access_token"]
            )
            with st.container(border=True):
                st.caption(datetime.fromtimestamp(int(to_annotate.time)).strftime('%B %d, %Y'))
                st.image(BytesIO(attached_media), caption=to_annotate.content)
        with column2:
            check_mark = (
                ":white_check_mark:" if to_annotate.annotated else ":grey_question:"
            )
            with st.expander(f"Annotate {check_mark}"):
                search_tab, pin_tab = st.tabs(
                    [":mag: Search species", ":round_pushpin: Pin location"]
                )
                with search_tab:
                    suggest_species(to_annotate=to_annotate, user_info=user_info)

                with pin_tab:
                    plot_encounter_location(to_annotate=to_annotate)
