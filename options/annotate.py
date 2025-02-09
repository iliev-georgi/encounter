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
from model import Location
import folium
from streamlit_folium import st_folium


def render_annotate(user_info):

    to_annotate_list = get_statuses(
        user_info["id"], st.session_state["token"]["access_token"]
    )
    append_annotation_state_to(to_annotate_list)

    for to_annotate in to_annotate_list:
        if "last_location" not in st.session_state:
            st.session_state.last_location = (Location.latitude, Location.longitude)
        column1, column2 = st.columns([1, 2])
        with column1:
            attached_media = get_attached_media(
                to_annotate.preview_url, st.session_state["token"]["access_token"]
            )
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
                    name = st_keyup("Enter bird name", key=to_annotate.id)
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
                                on_click=register_encounter,
                                help=suggestion.abstract,
                                args=[
                                    to_annotate.time,
                                    user_info.get("url"),
                                    to_annotate.preview_url,
                                    suggestion.species,
                                    st.session_state.last_location[0],
                                    st.session_state.last_location[1],
                                ],
                            )
                with pin_tab:
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
                                icon=folium.Icon(
                                    color="darkblue", icon="crow", prefix="fa"
                                ),
                                tooltip=to_annotate.label,
                            )
                        )
                        center_x, center_y = to_annotate.lat, to_annotate.lng

                    st_data = st_folium(
                        map, center=(center_x, center_y), zoom=10
                    )
                    if st_data.get("last_clicked"):
                        st.session_state.last_location = (
                            st_data["last_clicked"]["lat"],
                            st_data["last_clicked"]["lng"],
                        )
