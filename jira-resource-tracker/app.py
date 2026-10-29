import streamlit as st
from dotenv import load_dotenv
import urllib3

from config.theme import inject_ambient_background, apply_custom_theme
from views.login_view import render_login_view
from views.dashboard_view import render_dashboard_view

# Suppress SSL warnings for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure Streamlit page & environment
st.set_page_config(
    page_title="Jira Resource Tracker",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)
load_dotenv()

# Apply Glassmorphism UI Theme & Ambient Background
inject_ambient_background()
apply_custom_theme()

# Ensure sidebar state is tracked in session state
if 'show_sidebar' not in st.session_state:
    st.session_state['show_sidebar'] = True

# Route between Login View and Main Dashboard View
if 'jira_client' not in st.session_state:
    render_login_view()
else:
    render_dashboard_view()
