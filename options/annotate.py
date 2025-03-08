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
from helper import join_labels, register_encounter, empty_feed
from sparql_functions import delete_encounter
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

    update_verb = "Updating" if to_annotate.annotated else "Registering"

    st.toast(f"{update_verb} encounter...")

    # update location and label on map
    to_annotate.label = marker_label
    to_annotate.lat = latitude
    to_annotate.lng = longitude

    # update annotation state
    to_annotate.annotated = True

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

    st.toast(f"Done {update_verb.lower()} encounter.")


def update_plot_and_delete_encounter(to_annotate: ToAnnotate):

    st.toast("Deleting encounter...")

    # update location and label on map
    to_annotate.label = None
    to_annotate.lat = None
    to_annotate.lng = None

    # update annotation state
    to_annotate.annotated = False

    # delete encounter
    delete_encounter(evidence=to_annotate.preview_url)

    st.toast(f"Encounter deleted.")


def move_page(current_search_term_evidence_pair: str, step: int):
    st.session_state.page[current_search_term_evidence_pair] = (
        st.session_state.page[current_search_term_evidence_pair] + step
    )


def init_page_marker_for(current_search_term_evidence_pair: str, evidence: str):
    # Remove obsolete pagination states
    for search_term_evidence_pair in [str(key) for key in st.session_state.page.keys()]:
        if (
            search_term_evidence_pair.endswith(f"_{evidence}")
            and search_term_evidence_pair != current_search_term_evidence_pair
        ):
            st.session_state.page.pop(search_term_evidence_pair)

    if current_search_term_evidence_pair not in st.session_state.page:
        st.session_state.page[current_search_term_evidence_pair] = 0


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


def suggest_species(to_annotate, user_info):
    search_bar_prefill = to_annotate.label if to_annotate.annotated else ""
    name = st_keyup(
        "Enter bird name",
        placeholder=search_bar_prefill,
        key=to_annotate.id,
        debounce=500,
    )
    current_search_term_evidence_pair = f"{name}_{to_annotate.id}"
    init_page_marker_for(current_search_term_evidence_pair, to_annotate.id)
    if name and len(name) > 3:
        lookup_table = get_filtered_list(
            name,
            limit=RESULT_PAGE_SIZE,
            offset=st.session_state.page[current_search_term_evidence_pair]
            * RESULT_PAGE_SIZE,
        )
        append_previews_to(lookup_table)
        lookup_table = join_labels(lookup_table)
    else:
        st.session_state.last_location[to_annotate.id][0]
        lookup_table = dict()

    for suggestion in lookup_table:
        column1, column2, column3 = st.columns([3, 5, 1])
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
                key=f"{suggestion.species}_{to_annotate.id}",
                on_click=update_plot_and_register_encounter,
                kwargs=dict(
                    to_annotate=to_annotate,
                    marker_label=suggestion.prefLabel,
                    user=user_info.get("url"),
                    species=suggestion.species,
                    latitude=st.session_state.last_location[to_annotate.id][0],
                    longitude=st.session_state.last_location[to_annotate.id][1],
                ),
            )
        with column3:
            st.caption(
                "",
                help=suggestion.abstract,
            )

    # Pagination
    less = (
        True if st.session_state.page[current_search_term_evidence_pair] > 0 else False
    )
    more = True if len(lookup_table) == RESULT_PAGE_SIZE else False
    column1, column2, _ = st.columns([1, 1, 4])
    if less:
        with column1:
            st.button(
                label="",
                icon=":material/keyboard_double_arrow_left:",
                help="previous",
                type="tertiary",
                on_click=move_page,
                args=[current_search_term_evidence_pair, -1],
            )
    if more:
        with column2:
            st.button(
                label="",
                icon=":material/keyboard_double_arrow_right:",
                help="next",
                type="tertiary",
                on_click=move_page,
                args=[current_search_term_evidence_pair, 1],
            )


def suggest_delete(to_annotate: ToAnnotate):
    explain = f"You are about to delete the encounter linking this evidence to the **{to_annotate.label.strip()}**."
    column1, column2 = st.columns([1, 3])
    with column1:
        st.button(
            "Delete",
            key=f"delete_{to_annotate.id}",
            on_click=update_plot_and_delete_encounter,
            kwargs=dict(
                to_annotate=to_annotate,
            ),
        )
    with column2:
        st.caption(
            "",
            help=explain,
        )


@st.fragment
def render_row(to_annotate: ToAnnotate, user_info):
    st.session_state.last_location[to_annotate.id] = (
        Location.latitude,
        Location.longitude,
    )
    check_mark = (
        ":material/check_circle:"
        if to_annotate.annotated
        else ":material/indeterminate_question_box:"
    )
    evidence_help = (
        f"There is already an encounter with the **{to_annotate.label.strip()}** linking to this evidence. You can still modify it using the location picker and the search bar in the *Annotate* section"
        if to_annotate.annotated
        else "There is no encounter linked to this evidence. Create one using the location picker and the search bar in the *Annotate* section"
    )
    column1, column2 = st.columns([1, 2])
    with column1:
        attached_media = get_attached_media(
            to_annotate.preview_url, st.session_state["token"]["access_token"]
        )
        with st.container(border=True):
            st.caption(
                datetime.fromtimestamp(int(to_annotate.time)).strftime("%B %d, %Y"),
                help=evidence_help,
            )
            st.image(BytesIO(attached_media), caption=to_annotate.content)
    with column2:
        annotate = st.empty()
        with annotate.expander(f"Annotate {check_mark}"):
            if to_annotate.annotated:
                pin_tab, search_tab, delete_tab = st.tabs(
                    [
                        ":material/pin_drop: Pin location",
                        ":material/search: Search species",
                        ":material/delete: Delete encounter",
                    ]
                )
            else:
                pin_tab, search_tab = st.tabs(
                    [
                        ":material/pin_drop: Pin location",
                        ":material/search: Search species",
                    ]
                )

            with pin_tab:
                plot_encounter_location(to_annotate=to_annotate)

            with search_tab:
                suggest_species(to_annotate=to_annotate, user_info=user_info)

            if to_annotate.annotated:
                with delete_tab:
                    suggest_delete(to_annotate=to_annotate)


def render_annotate(user_info):

    to_annotate_list = get_statuses(
        user_info["id"], st.session_state["token"]["access_token"]
    )

    # Stop early in case of empty feed
    if not to_annotate_list:
        empty_feed(f"{PIXELFED_BASE_URL_SCHEME}://{PIXELFED_BASE_URL}")
        return

    append_annotation_state_to(to_annotate_list)

    # Initialize state
    if "last_location" not in st.session_state:
        st.session_state.last_location = dict()
    if "page" not in st.session_state:
        st.session_state.page = dict()

    for to_annotate in to_annotate_list:
        render_row(to_annotate=to_annotate, user_info=user_info)
