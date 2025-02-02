import streamlit as st
import folium
from sparql_functions import collect_encounters, get_labels
from pixelfed_functions import get_attached_media
from helper import get_jpeg_thumbnail, build_popup_iframe


def render_explore(
    user_info,
):  # User info not accessed on this stage but may be necessary to add personalized filtering functionality later

    encounters = (
        collect_encounters(context = "https://encounter.pastabytes.test")
    )  # Providing a context other than the default one allows you flexibility to experiment with dummy encounters in development

    m = folium.Map()

    tooltips = get_labels([f"<{encounter.species}>" for encounter in encounters])

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
            popup=popup,
        ).add_to(m)

    m.location = (
        encounter.location.latitude,
        encounter.location.longitude,
    )  # Focus map on last added encounter

    st.components.v1.html(folium.Figure().add_child(m).render(), height=500)
