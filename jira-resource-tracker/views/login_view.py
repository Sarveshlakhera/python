import os
import json
import streamlit as st
from services.network import check_internet_connection, is_network_error, render_no_internet_banner
from services.jira_service import authenticate_jira


def render_login_view():
    """Renders the professional glassmorphic Jira login screen."""
    # Hide sidebar toggle specifically on login screen
    st.markdown("<style>[data-testid='collapsedControl'], [data-testid='stSidebarCollapsedControl'] { display: none !important; }</style>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)

        st.markdown("""
            <div style='text-align: center; margin-bottom: 10px;'>
                <img src='https://cdn.icon-icons.com/icons2/2699/PNG/512/atlassian_jira_logo_icon_170511.png' width='80'>
            </div>
            <h2>📊 Enterprise Resource Hub</h2>
            <p style='text-align: center; color: #64748b;'>Sign in to access Jira portfolio metrics</p>
        """, unsafe_allow_html=True)

        # Proactive startup internet check on login screen
        startup_online, startup_reason = check_internet_connection()
        if not startup_online:
            render_no_internet_banner("loading the login screen", startup_reason)

        with st.container(border=True):
            tab1, tab2 = st.tabs(["Manual Entry", "JSON Configuration"])

            with tab1:
                jira_url = st.text_input("Workspace URL", value=os.getenv("JIRA_URL", ""), placeholder="https://domain.atlassian.net")
                jira_email = st.text_input("Email Address", value=os.getenv("JIRA_EMAIL", ""))
                jira_token = st.text_input("API Token", value=os.getenv("JIRA_API_TOKEN", ""), type="password")

                if st.button("Secure Login", type="primary", use_container_width=True):
                    if not all([jira_url, jira_email, jira_token]):
                        st.error("All fields are required.")
                    else:
                        with st.spinner("Checking network & authenticating..."):
                            jira, clean_url, error = authenticate_jira(jira_url, jira_email, jira_token)
                            if error:
                                if error.startswith("NETWORK_OFFLINE::"):
                                    render_no_internet_banner("signing in to Jira", error.replace("NETWORK_OFFLINE::", ""))
                                else:
                                    st.error(error)
                            else:
                                try:
                                    st.session_state['project_mapping'] = {f"{p.name} ({p.key})": p.key for p in jira.projects()}
                                    st.session_state['jira_client'] = jira
                                    st.session_state['jira_url'] = clean_url
                                    st.rerun()
                                except Exception as e:
                                    if is_network_error(e):
                                        render_no_internet_banner("loading Jira projects", str(e))
                                    else:
                                        st.error(f"Failed to load projects: {str(e)}")

            with tab2:
                st.markdown("Paste your environment configuration JSON below:")
                json_template = '{\n  "JIRA_URL": "https://system.atlassian.net",\n  "JIRA_EMAIL": "user@example.com",\n  "JIRA_API_TOKEN": "your_api_token"\n}'
                json_input = st.text_area("Configuration Payload", value=json_template, height=150)

                if st.button("Login via JSON", type="primary", use_container_width=True):
                    try:
                        creds = json.loads(json_input)
                        j_url = creds.get("JIRA_URL", "").strip()
                        j_email = creds.get("JIRA_EMAIL", "").strip()
                        j_token = creds.get("JIRA_API_TOKEN", "").strip()

                        if not all([j_url, j_email, j_token]):
                            st.error("JSON is missing required keys: JIRA_URL, JIRA_EMAIL, or JIRA_API_TOKEN")
                        else:
                            with st.spinner("Checking network & authenticating via JSON payload..."):
                                jira, clean_url, error = authenticate_jira(j_url, j_email, j_token)
                                if error:
                                    if error.startswith("NETWORK_OFFLINE::"):
                                        render_no_internet_banner("signing in via JSON configuration", error.replace("NETWORK_OFFLINE::", ""))
                                    else:
                                        st.error(error)
                                else:
                                    try:
                                        st.session_state['project_mapping'] = {f"{p.name} ({p.key})": p.key for p in jira.projects()}
                                        st.session_state['jira_client'] = jira
                                        st.session_state['jira_url'] = clean_url
                                        st.rerun()
                                    except Exception as e:
                                        if is_network_error(e):
                                            render_no_internet_banner("loading Jira projects", str(e))
                                        else:
                                            st.error(f"Failed to load projects: {str(e)}")
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format. Please ensure you are using standard JSON with double quotes and colons.")

        st.markdown("<p style='text-align: center; font-size: 12px; color: #b3bac5; margin-top: 20px;'>Protected by TLS Encryption</p>", unsafe_allow_html=True)
