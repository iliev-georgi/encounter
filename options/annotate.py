import streamlit as st
import requests
from io import BytesIO
from sparql_functions import get_filtered_list, append_previews_to
from st_keyup import st_keyup
from config import *
from helper import join_labels
from helper import register_encounter
from pixelfed_functions import get_statuses, get_attached_media


def render_annotate(user_info):

    to_annotate_list = get_statuses(user_info["id"], st.session_state["token"]["access_token"])

    for to_annotate in to_annotate_list:
        column1, column2 = st.columns([1, 2])
        with column1:
            attached_media = get_attached_media(to_annotate.preview_url, st.session_state["token"]["access_token"])
            st.image(BytesIO(attached_media), caption=to_annotate.content)
        with column2:
            with st.expander("Annotate"):
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
                                suggestion.species
                            ],
                        )