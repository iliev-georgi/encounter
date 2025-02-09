import streamlit as st
import folium
from sparql_functions import collect_encounters, get_labels
from pixelfed_functions import get_attached_media
from helper import get_jpeg_thumbnail, build_popup_iframe
from model import Location


def render_explore(
    user_info,
):  # User info not accessed on this stage but may be necessary to add personalized filtering functionality later

    encounters = (
        collect_encounters()
    )  # Providing a context other than the default one allows you flexibility to experiment with dummy encounters in development

    m = folium.Map()

    tooltips = get_labels([f"<{encounter.species}>" for encounter in encounters])

    center_x, center_y = Location.latitude, Location.longitude

    for encounter in encounters:
        attached_media = get_attached_media(
            encounter.evidence, st.session_state["token"]["access_token"]
        )

        thumbnail = get_jpeg_thumbnail(attached_media=attached_media)
        iframe = build_popup_iframe(encounter=encounter, thumbnail=thumbnail)

        popup = folium.Popup(iframe, min_width=150, max_width=150)
        folium.Marker(
            (encounter.location.latitude, encounter.location.longitude),
            tooltip=tooltips.get(encounter.species, "Unknown"),
            icon=folium.Icon(color="darkblue", icon="crow", prefix="fa"),
            popup=popup,
        ).add_to(m)
        center_x, center_y = encounter.location.latitude, encounter.location.longitude

    m.location = (center_x, center_y)  # Focus map on last added encounter

    st.components.v1.html(folium.Figure().add_child(m).render(), height=500)
