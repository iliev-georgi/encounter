import streamlit as st
from config import APP_TITLE, HAMBURGER_MENU_ITEMS
from auth import sso_login_pixelfed
from streamlit_option_menu import option_menu
from options.annotate import render_annotate
from options.explore import render_explore

st.set_page_config(page_title=APP_TITLE, menu_items=HAMBURGER_MENU_ITEMS)

st.header(APP_TITLE)

st.image("images/skyline_2_cropped_mono_hi_contrast.png")

st.divider()

USER_INFO = sso_login_pixelfed()

if "token" in st.session_state:
    
    selected = option_menu(None, ["Annotate", "Explore"], 
        icons=['pin-map', 'map'], 
        menu_icon="cast", default_index=0, orientation="horizontal")
    
    match selected:
        case "Annotate":
            render_annotate(USER_INFO)
        case "Explore":
            render_explore(USER_INFO)
        case _:
            render_annotate(USER_INFO)