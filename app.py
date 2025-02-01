import streamlit as st
from config import APP_TITLE
from auth import sso_login_pixelfed
from streamlit_option_menu import option_menu
from options.annotate import render

st.set_page_config(page_title=APP_TITLE)

st.header(APP_TITLE)

st.image("images/skyline_2_cropped_mono_hi_contrast.png")

st.divider()

USER_INFO = sso_login_pixelfed()

if "token" in st.session_state:
    
    selected = option_menu(None, ["Annotate", "Explore"], 
        icons=['pin-map', 'map'], 
        menu_icon="cast", default_index=0, orientation="horizontal")
    
    if selected == "Annotate":
        render(USER_INFO)