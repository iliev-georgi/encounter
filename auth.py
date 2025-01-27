from config import *
import streamlit as st
from streamlit_oauth import OAuth2Component
import json, requests


def sso_login_pixelfed():
    oauth2 = OAuth2Component(
        CLIENT_ID,
        CLIENT_SECRET,
        AUTHORIZE_URL,
        TOKEN_URL,
        REFRESH_TOKEN_URL,
        REVOKE_TOKEN_URL,
    )

    if "token" not in st.session_state:
        result = oauth2.authorize_button("Login", REDIRECT_URI, SCOPE)
        if result and "token" in result:
            st.session_state.token = result.get("token")
            st.rerun()
    else:
        verification_response = requests.get(
            f"{PIXELFED_BASE_URL_SCHEME}://{PIXELFED_BASE_URL}/api/v1/accounts/verify_credentials",
            headers={
                "Authorization": f"Bearer {st.session_state['token']['access_token']}"
            },
        )
        if verification_response.status_code != 200:
            del st.session_state["token"]
            st.rerun()

        return json.loads(verification_response.text)
