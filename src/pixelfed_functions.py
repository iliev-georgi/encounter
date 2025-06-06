import requests
import streamlit as st
from config import PIXELFED_BASE_URL, PIXELFED_BASE_URL_SCHEME
from src.model import ToAnnotate
from urllib.parse import urlparse, urlunparse
from dateutil import parser
import json


def get_statuses(user_id: str, bearer_token: str) -> list[ToAnnotate]:
    user_statuses = json.loads(
        requests.get(
            f"{PIXELFED_BASE_URL_SCHEME}://{PIXELFED_BASE_URL}/api/v1/accounts/{user_id}/statuses",
            headers={"Authorization": f"Bearer {bearer_token}"},
        ).text
    )

    to_annotate_list = []

    for user_status in user_statuses:
        preview_url_parsed = urlparse(
            user_status["media_attachments"][0]["preview_url"]
        )
        preview_url_localized = urlunparse(
            preview_url_parsed._replace(netloc=PIXELFED_BASE_URL)
        )
        to_annotate_list.append(
            ToAnnotate(
                user_status["id"],
                preview_url_localized,
                user_status["content"],
                parser.parse(user_status["created_at"]).strftime("%s"),
            )
        )

    return to_annotate_list


@st.cache_data
def get_attached_media(media_url, bearer_token) -> bytes:
    r = requests.get(
        media_url,
        headers={"Authorization": f"Bearer {bearer_token}"},
    )

    # This check should handle all cases of missing media, either due to deletion or insufficient permissions or otherwise
    if r.status_code != 200:
        with open("images/Not_found.jpg", "rb") as not_found:
            return not_found.read()

    return r.content


def tag_media(
    status_id, content, bearer_token
):  # Not used anywhere; kept to illustrate how we coud post comments on the Pixelfed API

    status_create_url = f"http://{PIXELFED_BASE_URL}/api/v1/statuses"

    payload = dict()
    payload["in_reply_to_id"] = status_id
    payload["status"] = f"This is the bird {content}!"
    requests.post(
        status_create_url,
        headers={"Authorization": f"Bearer {bearer_token}"},
        data=payload,
    )
