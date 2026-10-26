import streamlit as st
from jira import JIRA, JIRAError
import pandas as pd
import altair as alt
import os
import io
import json
import html
import socket
from urllib.parse import urlparse
from dotenv import load_dotenv
from datetime import datetime, timedelta, date
import urllib3
import requests

# Suppress the SSL warning for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- UI CONFIGURATION ---
st.set_page_config(
    page_title="Jira Resource Tracker",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)
load_dotenv()

# ------------------------------------------------------
# Ambient Background Injection
# ------------------------------------------------------
st.markdown("""
    <div class="ambient-blob blob-1"></div>
    <div class="ambient-blob blob-2"></div>
    <div class="ambient-blob blob-3"></div>
""", unsafe_allow_html=True)

# ------------------------------------------------------
# 2026 Modern SaaS UI Theme (Glassmorphism & Minimalism)
# ------------------------------------------------------
def apply_custom_theme():
    st.markdown("""
    <style>
        /* ---------------------------------------------------
           FORCE LIGHT MODE & DISABLE THEME TOGGLE
           --------------------------------------------------- */
        [data-testid="stToolbar"] {
            display: none !important;
        }

        .stApp, .stMarkdown, p, label, li, span {
            color: #1e293b !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: inherit !important;
        }
        .stButton>button[kind="primary"] {
            color: #ffffff !important;
        }
        .stButton>button[kind="primary"] * {
            color: #ffffff !important;
        }

        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

        html, body, [class*="css"], .stTextInput > label, .stSelectbox > label, .stMarkdown {
            font-family: 'Outfit', sans-serif !important;
        }

        header {background-color: transparent !important;}

        /* Main App Background */
        .stApp {
            background-color: #fafbfc !important;
            background-image: radial-gradient(circle at 10% 20%, rgba(240, 242, 250, 0.8) 0%, rgba(255, 255, 255, 0.8) 90%);
        }

        /* Ambient Blobs Animation */
        .ambient-blob {
            position: fixed;
            filter: blur(90px);
            z-index: 0;
            opacity: 0.55;
            pointer-events: none;
        }

        .blob-1 {
            top: -10%; left: -10%;
            width: 50vw; height: 50vw;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255, 65, 108, 0.28) 0%, rgba(255, 65, 108, 0) 70%);
            animation: float1 20s infinite alternate ease-in-out;
        }

        .blob-2 {
            bottom: -20%; right: -10%;
            width: 60vw; height: 60vw;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(37, 99, 235, 0.28) 0%, rgba(139, 92, 246, 0) 70%);
            animation: float2 25s infinite alternate-reverse ease-in-out;
        }

        .blob-3 {
            top: 20%; right: 20%;
            width: 40vw; height: 40vw;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.18) 0%, rgba(139, 92, 246, 0) 70%);
            animation: float3 22s infinite alternate ease-in-out;
        }

        @keyframes float1 { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(10%, 15%) scale(1.1); } }
        @keyframes float2 { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(-15%, -10%) scale(1.2); } }
        @keyframes float3 { 0% { transform: translate(0, 0) scale(1); } 100% { transform: translate(-20%, 20%) scale(1.15); } }

        .block-container, [data-testid="stSidebar"] {
            z-index: 1;
        }

        /* Glassmorphism Sidebar */
        [data-testid="stSidebar"] {
            background: rgba(255, 255, 255, 0.45) !important;
            backdrop-filter: blur(25px) !important;
            -webkit-backdrop-filter: blur(25px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.6) !important;
        }

        /* Animated Title Gradient */
        @keyframes title-flow {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        h1, h2 {
            font-weight: 800 !important;
            letter-spacing: -1px;
            text-align: center;
            background: linear-gradient(-45deg, #FF4B2B, #FF416C, #2563eb, #8B5CF6);
            background-size: 300% 300%;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            animation: title-flow 6s ease infinite;
            filter: drop-shadow(0px 4px 15px rgba(37, 99, 235, 0.18));
            margin-bottom: 0.4rem !important;
        }

        /* Glassmorphism Metrics (KPI Cards) */
        .stMetric {
            background: rgba(255, 255, 255, 0.75);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.85);
            border-radius: 16px;
            padding: 1.15rem 1.25rem;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03);
            transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s ease;
        }
        .stMetric:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 22px rgba(15, 23, 42, 0.06);
        }

        /* Glassmorphism Containers */
        [data-testid="stVerticalBlock"] > div[style*="border"] {
            border: 1px solid rgba(226, 232, 240, 0.85) !important;
            border-radius: 18px !important;
            background: rgba(255, 255, 255, 0.62) !important;
            backdrop-filter: blur(12px) !important;
            box-shadow: 0 4px 16px rgba(15, 23, 42, 0.025) !important;
        }

        /* Glassmorphism Buttons */
        .stButton>button {
            border-radius: 10px !important;
            border: 1px solid rgba(203, 213, 225, 0.7) !important;
            background: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(10px) !important;
            font-weight: 500 !important;
            color: #1e293b !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02) !important;
        }

        .stButton>button:hover {
            background: #1e293b !important;
            color: #ffffff !important;
            transform: translateY(-1px) !important;
            box-shadow: 0 6px 14px rgba(15, 23, 42, 0.08) !important;
        }
        .stButton>button:hover * {
            color: #ffffff !important;
        }

        /* Primary Button Override */
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
            color: #ffffff !important;
            border: none !important;
        }
        .stButton>button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3) !important;
        }

        /* Modern Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: rgba(255, 255, 255, 0.55);
            padding: 6px 10px;
            border-radius: 14px;
            border: 1px solid rgba(226, 232, 240, 0.8);
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px;
            padding: 8px 16px;
            font-weight: 600;
        }

        /* Activity Feed Cards */
        .activity-card {
            background: rgba(255, 255, 255, 0.78);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid rgba(226, 232, 240, 0.9);
            border-left: 4px solid #2563eb;
            border-radius: 14px;
            padding: 0.85rem 1.15rem;
            margin-bottom: 0.65rem;
            box-shadow: 0 2px 10px rgba(15, 23, 42, 0.025);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .activity-card:hover {
            transform: translateY(-1px);
            box-shadow: 0 6px 16px rgba(37, 99, 235, 0.07);
        }
        .activity-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            align-items: center;
            font-size: 0.8rem;
            color: #64748b !important;
            margin-bottom: 0.3rem;
        }
        .activity-badge {
            background: rgba(37, 99, 235, 0.1);
            color: #1d4ed8 !important;
            padding: 0.12rem 0.55rem;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.74rem;
        }
        .activity-resource {
            background: rgba(139, 92, 246, 0.12);
            color: #6d28d9 !important;
            padding: 0.12rem 0.55rem;
            border-radius: 999px;
            font-weight: 600;
            font-size: 0.74rem;
        }
        .activity-title {
            font-weight: 600;
            font-size: 0.94rem;
            color: #0f172a !important;
            margin-bottom: 0.2rem;
        }
        .activity-title a {
            color: #2563eb !important;
            text-decoration: none;
            font-weight: 700;
        }
        .activity-title a:hover {
            text-decoration: underline;
        }
        .activity-detail {
            font-size: 0.86rem;
            color: #334155 !important;
        }

        /* Offline / No-Internet Banner Card */
        .offline-banner {
            background: rgba(254, 242, 242, 0.92);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid rgba(248, 113, 113, 0.6);
            border-left: 6px solid #dc2626;
            border-radius: 16px;
            padding: 1.1rem 1.4rem;
            margin-bottom: 1rem;
            box-shadow: 0 6px 20px rgba(220, 38, 38, 0.08);
        }
        .offline-banner-title {
            font-weight: 700;
            font-size: 1.05rem;
            color: #991b1b !important;
            margin-bottom: 0.3rem;
        }
        .offline-banner-sub {
            font-size: 0.9rem;
            color: #7f1d1d !important;
            margin-bottom: 0.4rem;
        }
        .offline-banner-tips {
            font-size: 0.83rem;
            color: #991b1b !important;
            margin: 0;
            padding-left: 1.2rem;
        }

        /* Spinner Color Match */
        .stSpinner > div > div { border-color: #3b82f6 transparent transparent transparent; }

        /* Hide sidebar by default on the login screen */
        [data-testid="collapsedControl"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

apply_custom_theme()


# --- NETWORK & INTERNET CONNECTIVITY HELPERS ---
def check_internet_connection(target_url=None, timeout=3.5):
    """
    Checks whether internet / network connectivity is available.
    1. If a target_url (e.g., Jira server URL) is provided, verifies DNS resolution and TCP reachability.
    2. Otherwise checks reachability against reliable public DNS endpoints (8.8.8.8:53, 1.1.1.1:53).
    Returns (is_connected: bool, reason: str).
    """
    if target_url:
        try:
            parsed = urlparse(target_url if "://" in target_url else f"https://{target_url}")
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            if host:
                socket.getaddrinfo(host, port)
                with socket.create_connection((host, port), timeout=timeout):
                    return True, "Connected"
        except socket.gaierror:
            return False, f"Unable to resolve host '{host}'. Please check your internet connection, DNS, or VPN."
        except (socket.timeout, TimeoutError):
            return False, f"Connection to '{target_url}' timed out. Please verify your internet or corporate VPN connection."
        except OSError as e:
            return False, f"Network unreachable while contacting '{target_url}' ({e}). Please check your internet connection."

    # Fallback check against public DNS servers (Google & Cloudflare)
    for host, port in [("8.8.8.8", 53), ("1.1.1.1", 53)]:
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True, "Connected"
        except OSError:
            continue

    # Secondary fallback via DNS lookup
    try:
        socket.gethostbyname("atlassian.com")
        return True, "Connected"
    except OSError:
        return False, "No active internet connection detected on this device."


def is_network_error(exc):
    """Determines whether an exception was caused by an internet outage, DNS failure, or connection drop."""
    if isinstance(exc, (
        requests.exceptions.ConnectionError,
        requests.exceptions.Timeout,
        urllib3.exceptions.MaxRetryError,
        urllib3.exceptions.NewConnectionError,
        socket.gaierror,
        socket.timeout,
        TimeoutError,
        ConnectionError,
    )):
        return True

    err_str = str(exc).lower()
    network_keywords = [
        "failed to establish a new connection",
        "max retries exceeded",
        "name or service not known",
        "nodename nor servname provided",
        "getaddrinfo failed",
        "temporary failure in name resolution",
        "network is unreachable",
        "no route to host",
        "connection timed out",
        "read timed out",
        "connection aborted",
        "connection reset",
        "remote end closed connection",
        "cannot connect to proxy",
    ]
    return any(k in err_str for k in network_keywords)


def render_no_internet_banner(action_context="communicating with Jira", details=None):
    """Renders a clear, user-friendly offline alert banner when internet connectivity is unavailable."""
    extra_html = f"<div class='offline-banner-sub'><b>Details:</b> {html.escape(str(details))}</div>" if details else ""
    st.markdown(f"""
        <div class="offline-banner">
            <div class="offline-banner-title">🌐 Internet Connection Unavailable</div>
            <div class="offline-banner-sub">
                The application could not reach Jira while <b>{html.escape(action_context)}</b> because your internet or network connection appears to be offline or unreachable.
            </div>
            {extra_html}
            <ul class="offline-banner-tips">
                <li>Check that your Wi-Fi or Ethernet connection is active and has internet access.</li>
                <li>If your Jira server is hosted on an internal corporate network, verify that your VPN or proxy is connected.</li>
                <li>Once your internet connection is restored, click <b>🚀 Generate Dashboard</b> or <b>🔄 Refresh Jira Cache</b> to retry.</li>
            </ul>
        </div>
    """, unsafe_allow_html=True)


# --- CORE HELPER FUNCTIONS ---
def math_success_animation():
    """Injects CSS to display a subtle floating math/numbers animation on success."""
    st.markdown("""
        <style>
        .math-float {
            position: fixed;
            bottom: -50px;
            color: rgba(37, 99, 235, 0.75);
            font-size: 2.0rem;
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            z-index: 99999;
            animation: floatMathUp 3.2s ease-in forwards;
            pointer-events: none;
        }
        @keyframes floatMathUp {
            0% { transform: translateY(0) rotate(0deg); opacity: 1; }
            100% { transform: translateY(-120vh) rotate(360deg); opacity: 0; }
        }
        </style>
        <div class="math-float" style="left: 8%; animation-duration: 3.2s; animation-delay: 0s;">∑</div>
        <div class="math-float" style="left: 22%; animation-duration: 3.8s; animation-delay: 0.2s;">∫</div>
        <div class="math-float" style="left: 38%; animation-duration: 3.0s; animation-delay: 0.4s;">%</div>
        <div class="math-float" style="left: 54%; animation-duration: 3.9s; animation-delay: 0.1s;">π</div>
        <div class="math-float" style="left: 70%; animation-duration: 3.3s; animation-delay: 0.3s;">∞</div>
        <div class="math-float" style="left: 86%; animation-duration: 3.5s; animation-delay: 0.5s;">ƒ(x)</div>
        """, unsafe_allow_html=True)

def authenticate_jira(url, email, token):
    """Establish connection to Jira API with clear internet/network error handling."""
    clean_url = url.strip().rstrip("/")
    is_online, net_reason = check_internet_connection(clean_url)
    if not is_online:
        return None, clean_url, f"NETWORK_OFFLINE::{net_reason}"

    try:
        jira = JIRA(
            server=clean_url,
            basic_auth=(email.strip(), token.strip()),
            options={'verify': False},
            timeout=15,
            max_retries=1
        )
        jira.current_user()
        return jira, clean_url, None
    except JIRAError as e:
        if is_network_error(e):
            return None, clean_url, "NETWORK_OFFLINE::Unable to reach the Jira server. Please check your internet connection or VPN."
        return None, clean_url, f"Authentication Failed: {e.text}"
    except Exception as e:
        if is_network_error(e):
            return None, clean_url, "NETWORK_OFFLINE::Internet connection is unavailable or the Jira server could not be reached."
        return None, clean_url, f"An error occurred: {str(e)}"

def get_project_metadata(jira, projects):
    cache_key = f"metadata_{'-'.join(sorted(projects))}"
    if cache_key in st.session_state:
        return st.session_state[cache_key], None

    is_online, net_reason = check_internet_connection(st.session_state.get('jira_url'))
    if not is_online:
        return ([], []), net_reason

    project_keys = ", ".join([f'"{p}"' for p in projects])
    jql = f'project in ({project_keys})'

    try:
        issues = jira.enhanced_search_issues(jql_str=jql, maxResults=False, fields="assignee,status")
    except Exception as e:
        if is_network_error(e):
            return ([], []), "Internet connection was lost while loading project metadata."
        return ([], []), f"Failed to load project metadata: {str(e)}"

    assignees, statuses = set(), set()
    for i in issues:
        assignees.add(i.fields.assignee.displayName if hasattr(i.fields, 'assignee') and i.fields.assignee else "Unassigned")
        statuses.add(i.fields.status.name if hasattr(i.fields, 'status') and i.fields.status else "Unknown")

    result = (sorted(list(assignees)), sorted(list(statuses)))
    st.session_state[cache_key] = result
    return result, None

def build_jql(projects, start_date, end_date, assignees, statuses, is_time_logging_mode):
    project_keys = ", ".join([f'"{p}"' for p in projects])
    jql = f'project in ({project_keys})'

    if is_time_logging_mode:
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        if assignees:
            assignee_list = ["EMPTY" if a == "Unassigned" else f'"{a}"' for a in assignees]
            author_list = [f'"{a}"' for a in assignees if a != "Unassigned"]
            if author_list:
                jql += f' AND (assignee in ({", ".join(assignee_list)}) OR worklogAuthor in ({", ".join(author_list)}))'
            else:
                jql += f' AND assignee in ({", ".join(assignee_list)})'

        jql += f' AND worklogDate >= "{start_str}" AND worklogDate <= "{end_str}"'
    else:
        if assignees:
            assignee_list = ["EMPTY" if a == "Unassigned" else f'"{a}"' for a in assignees]
            jql += f' AND assignee in ({", ".join(assignee_list)})'
        jql += ' AND resolution = Unresolved'

    if statuses:
        status_list = [f'"{s}"' for s in statuses]
        jql += f' AND status in ({", ".join(status_list)})'

    jql += ' ORDER BY updated DESC'
    return jql

def fetch_issues(jira, jql_query, force_refresh=False):
    if 'jql_cache' not in st.session_state:
        st.session_state['jql_cache'] = {}

    if not force_refresh and jql_query in st.session_state['jql_cache']:
        return st.session_state['jql_cache'][jql_query], None

    is_online, net_reason = check_internet_connection(st.session_state.get('jira_url'))
    if not is_online:
        return None, net_reason

    fields_str = (
        "project,summary,assignee,status,issuetype,priority,parent,"
        "timeoriginalestimate,timespent,timeestimate,worklog,duedate,comment,updated,created,resolution"
    )
    with st.spinner('Fetching detailed task and activity data from Jira...'):
        try:
            try:
                issues = list(jira.enhanced_search_issues(
                    jql_str=jql_query,
                    maxResults=False,
                    fields=fields_str,
                    expand="changelog"
                ))
            except TypeError:
                issues = list(jira.enhanced_search_issues(
                    jql_str=jql_query,
                    maxResults=False,
                    fields=fields_str
                ))
        except Exception as e:
            if is_network_error(e):
                return None, "Internet connection dropped while fetching tickets from Jira."
            return None, f"Error fetching Jira tickets: {str(e)}"

    st.session_state['jql_cache'][jql_query] = issues
    return issues, None

def extract_jira_text(raw_val):
    """Safely extracts plain text from Jira strings or Atlassian Document Format (ADF) objects."""
    if not raw_val:
        return ""
    if isinstance(raw_val, str):
        return raw_val.strip()
    if isinstance(raw_val, dict):
        texts = []
        def _walk(node):
            if isinstance(node, dict):
                if node.get("type") == "text" and "text" in node:
                    texts.append(node["text"])
                for child in node.get("content", []):
                    _walk(child)
            elif isinstance(node, list):
                for item in node:
                    _walk(item)
        _walk(raw_val)
        return " ".join(texts).strip()
    if hasattr(raw_val, "content"):
        try:
            return extract_jira_text(raw_val.__dict__)
        except Exception:
            return str(raw_val).strip()
    return str(raw_val).strip()

def parse_jira_timestamp(ts_str):
    """Parses a Jira ISO timestamp into (datetime_str, date_obj)."""
    if not ts_str or not isinstance(ts_str, str):
        return None, None
    try:
        date_part = ts_str.split('T')[0]
        time_part = ts_str.split('T')[1][:5] if 'T' in ts_str and len(ts_str.split('T')[1]) >= 5 else "00:00"
        dt_date = datetime.strptime(date_part, "%Y-%m-%d").date()
        return f"{date_part} {time_part}", dt_date
    except Exception:
        return None, None

def get_working_days_list(start_d, end_d, exclude_weekends=True):
    """Returns a sorted list of YYYY-MM-DD strings between start_d and end_d."""
    if not start_d or not end_d or end_d < start_d:
        return []
    days = []
    curr = start_d
    while curr <= end_d:
        if not exclude_weekends or curr.weekday() < 5:
            days.append(curr.strftime("%Y-%m-%d"))
        curr += timedelta(days=1)
    return days

def process_issues_to_dataframe(jira_client, issues, start_date, end_date, is_time_logging_mode, base_url="", stale_days_threshold=5):
    data = []
    daily_logs = []
    activities = []
    progress_bar = st.progress(0, text="Analyzing worklogs, daily hours, risk flags, and recent activities...")
    time_col_name = "Time Spent in Period (hrs)" if is_time_logging_mode else "Total Time Logged (hrs)"
    today_date = datetime.today().date()
    done_statuses = {"done", "closed", "resolved", "completed", "cancelled", "canceled"}

    for idx, issue in enumerate(issues):
        progress_bar.progress((idx + 1) / len(issues), text=f"Processing task {issue.key}...")
        fields = issue.fields

        orig_est_hours = (getattr(fields, 'timeoriginalestimate', 0) or 0) / 3600.0
        rem_est_hours = (getattr(fields, 'timeestimate', 0) or 0) / 3600.0
        total_issue_spent_hrs = (getattr(fields, 'timespent', 0) or 0) / 3600.0

        current_assignee = fields.assignee.displayName if hasattr(fields, 'assignee') and fields.assignee else "Unassigned"
        project_name = fields.project.name if hasattr(fields, 'project') and fields.project else "Unknown"
        status_name = fields.status.name if hasattr(fields, 'status') and fields.status else "Unknown"
        issue_type_name = fields.issuetype.name if hasattr(fields, 'issuetype') and fields.issuetype else "Task"
        priority_name = fields.priority.name if hasattr(fields, 'priority') and fields.priority else "Medium"
        summary_text = getattr(fields, 'summary', '')
        ticket_url = f"{base_url}/browse/{issue.key}" if base_url else issue.key

        # Parent / Epic Rollup extraction
        parent_obj = getattr(fields, 'parent', None)
        if parent_obj and hasattr(parent_obj, 'key'):
            parent_summary = getattr(getattr(parent_obj, 'fields', None), 'summary', '')
            parent_label = f"{parent_obj.key}: {parent_summary[:45]}" if parent_summary else parent_obj.key
        else:
            parent_label = "Independent / No Parent"

        due_date_val = getattr(fields, 'duedate', None)
        due_date_str = due_date_val if due_date_val else "Not Set"
        due_date_obj = None
        if due_date_val:
            try:
                due_date_obj = datetime.strptime(due_date_val, "%Y-%m-%d").date()
            except Exception:
                due_date_obj = None

        updated_str = getattr(fields, 'updated', '')
        ts_updated, u_date = parse_jira_timestamp(updated_str)
        days_inactive = (today_date - u_date).days if u_date else 0

        is_resolved = (getattr(fields, 'resolution', None) is not None) or (status_name.lower() in done_statuses)
        is_overdue = bool(due_date_obj and due_date_obj < today_date and not is_resolved)
        is_overrun = bool(orig_est_hours > 0 and total_issue_spent_hrs > orig_est_hours)
        is_stale = bool(not is_resolved and days_inactive >= stale_days_threshold)
        is_unestimated = bool(not is_resolved and orig_est_hours == 0)

        health_badges = []
        if is_overdue:
            health_badges.append("⏰ Overdue")
        if is_overrun:
            health_badges.append("🔥 Over Estimate")
        if is_stale:
            health_badges.append(f"🕸️ Stale ({days_inactive}d)")
        if is_unestimated:
            health_badges.append("⚠️ Unestimated")
        health_status = " | ".join(health_badges) if health_badges else "✅ On Track"

        author_time_spent = {}
        worklogs = getattr(fields, 'worklog', None)
        worklog_list = worklogs.worklogs if worklogs else []

        if worklogs and worklogs.total > len(worklog_list):
            try:
                worklog_list = jira_client.worklogs(issue.key)
            except Exception:
                pass

        for wl in worklog_list:
            try:
                author = wl.author.displayName if hasattr(wl, 'author') and wl.author else "Unknown"
                time_spent_seconds = int(getattr(wl, 'timeSpentSeconds', 0))
                started = getattr(wl, 'started', '')
                ts_formatted, wl_date = parse_jira_timestamp(started)
                wl_hours = time_spent_seconds / 3600.0
                wl_comment = extract_jira_text(getattr(wl, 'comment', ''))

                in_period = True
                if is_time_logging_mode:
                    in_period = bool(wl_date and (start_date <= wl_date <= end_date))

                if in_period:
                    author_time_spent[author] = author_time_spent.get(author, 0) + time_spent_seconds
                    if wl_date and wl_hours > 0:
                        daily_logs.append({
                            "Resource": author,
                            "Date": wl_date.strftime("%Y-%m-%d"),
                            "Issue Key": issue.key,
                            "Ticket URL": ticket_url,
                            "Summary": summary_text,
                            "Project": project_name,
                            "Issue Type": issue_type_name,
                            "Priority": priority_name,
                            "Parent / Epic": parent_label,
                            "Status": status_name,
                            "Hours Logged": round(wl_hours, 2)
                        })
                    if ts_formatted:
                        detail_msg = f"Logged {round(wl_hours, 2)} hrs"
                        if wl_comment:
                            snippet = wl_comment if len(wl_comment) <= 140 else wl_comment[:137] + "..."
                            detail_msg += f" — \"{snippet}\""
                        activities.append({
                            "Timestamp": ts_formatted,
                            "Date": wl_date.strftime("%Y-%m-%d") if wl_date else "",
                            "Resource": author,
                            "Activity Type": "⏱️ Worklog Logged",
                            "Project": project_name,
                            "Issue Key": issue.key,
                            "Ticket URL": ticket_url,
                            "Summary": summary_text,
                            "Status": status_name,
                            "Details": detail_msg
                        })
            except Exception:
                continue

        # Extract Comments as Recent Activities
        comment_container = getattr(fields, 'comment', None)
        comment_list = getattr(comment_container, 'comments', []) if comment_container else []
        for c in comment_list:
            try:
                c_author = c.author.displayName if hasattr(c, 'author') and c.author else "Unknown"
                c_created = getattr(c, 'created', '') or getattr(c, 'updated', '')
                ts_formatted, c_date = parse_jira_timestamp(c_created)
                if not ts_formatted:
                    continue
                if is_time_logging_mode and c_date and not (start_date <= c_date <= end_date):
                    continue
                c_body = extract_jira_text(getattr(c, 'body', ''))
                snippet = c_body if len(c_body) <= 140 else c_body[:137] + "..."
                activities.append({
                    "Timestamp": ts_formatted,
                    "Date": c_date.strftime("%Y-%m-%d") if c_date else "",
                    "Resource": c_author,
                    "Activity Type": "💬 Comment Added",
                    "Project": project_name,
                    "Issue Key": issue.key,
                    "Ticket URL": ticket_url,
                    "Summary": summary_text,
                    "Status": status_name,
                    "Details": f"Commented: \"{snippet}\"" if snippet else "Added a comment on ticket"
                })
            except Exception:
                continue

        # Extract Changelog / Status & Field Transitions if available
        changelog = getattr(issue, 'changelog', None)
        histories = getattr(changelog, 'histories', []) if changelog else []
        recorded_changelog_for_assignee = False
        for history in histories:
            try:
                h_author = history.author.displayName if hasattr(history, 'author') and history.author else "Unknown"
                h_created = getattr(history, 'created', '')
                ts_formatted, h_date = parse_jira_timestamp(h_created)
                if not ts_formatted:
                    continue
                if is_time_logging_mode and h_date and not (start_date <= h_date <= end_date):
                    continue
                changes = []
                for item in getattr(history, 'items', []):
                    field_name = getattr(item, 'field', 'field')
                    from_str = getattr(item, 'fromString', '') or 'None'
                    to_str = getattr(item, 'toString', '') or 'None'
                    if field_name.lower() in ('status', 'resolution', 'assignee', 'priority', 'duedate', 'timeestimate'):
                        changes.append(f"{field_name.capitalize()}: {from_str} → {to_str}")
                if changes:
                    if h_author == current_assignee:
                        recorded_changelog_for_assignee = True
                    activities.append({
                        "Timestamp": ts_formatted,
                        "Date": h_date.strftime("%Y-%m-%d") if h_date else "",
                        "Resource": h_author,
                        "Activity Type": "🔄 Ticket Updated",
                        "Project": project_name,
                        "Issue Key": issue.key,
                        "Ticket URL": ticket_url,
                        "Summary": summary_text,
                        "Status": status_name,
                        "Details": "; ".join(changes)
                    })
            except Exception:
                continue

        # Fallback activity record from issue `updated` timestamp for the current assignee
        if ts_updated and current_assignee != "Unassigned" and not recorded_changelog_for_assignee:
            if not is_time_logging_mode or (u_date and start_date <= u_date <= end_date):
                activities.append({
                    "Timestamp": ts_updated,
                    "Date": u_date.strftime("%Y-%m-%d") if u_date else "",
                    "Resource": current_assignee,
                    "Activity Type": "📌 Active Ticket Status",
                    "Project": project_name,
                    "Issue Key": issue.key,
                    "Ticket URL": ticket_url,
                    "Summary": summary_text,
                    "Status": status_name,
                    "Details": f"Assigned {issue_type_name} currently in '{status_name}' status"
                })

        involved_users = set(author_time_spent.keys())
        involved_users.add(current_assignee)

        for user in involved_users:
            user_time_spent_hrs = author_time_spent.get(user, 0) / 3600.0
            is_assignee = (user == current_assignee)

            if not is_assignee and user_time_spent_hrs == 0:
                continue

            user_orig_est = round(orig_est_hours, 2) if is_assignee else 0.0
            user_rem_est = round(rem_est_hours, 2) if is_assignee else 0.0
            role = (
                "Assignee & Contributor" if is_assignee and user_time_spent_hrs > 0
                else "Assignee" if is_assignee
                else "Contributor"
            )

            data.append({
                "Resource": user,
                "Ticket Role": role,
                "Project": project_name,
                "Issue Key": issue.key,
                "Ticket URL": ticket_url,
                "Summary": summary_text,
                "Parent / Epic": parent_label,
                "Current Ticket Assignee": current_assignee,
                "Status": status_name,
                "Issue Type": issue_type_name,
                "Priority": priority_name,
                "Due Date": due_date_str,
                "Days Inactive": days_inactive,
                "Health Status": health_status,
                "Is Overdue": is_overdue,
                "Is Overrun": is_overrun,
                "Is Stale": is_stale,
                "Is Unestimated": is_unestimated,
                "Original Estimate (hrs)": user_orig_est,
                time_col_name: round(user_time_spent_hrs, 2),
                "Remaining Estimate (hrs)": user_rem_est
            })

    progress_bar.empty()
    df_main = pd.DataFrame(data)
    df_daily = pd.DataFrame(daily_logs)
    df_activities = pd.DataFrame(activities)
    if not df_activities.empty:
        df_activities = df_activities.sort_values(by="Timestamp", ascending=False).reset_index(drop=True)
    return df_main, time_col_name, df_daily, df_activities

def build_excel_workbook(filtered_df, filtered_daily_df, filtered_activities_df, time_col):
    """Generates a multi-sheet Excel (.xlsx) report in memory for one-click download."""
    output = io.BytesIO()
    engine = None
    for candidate in ("xlsxwriter", "openpyxl"):
        try:
            __import__(candidate)
            engine = candidate
            break
        except ImportError:
            continue

    if not engine:
        return None

    with pd.ExcelWriter(output, engine=engine) as writer:
        # Sheet 1: Resource Summary
        if not filtered_df.empty:
            summary_df = (
                filtered_df.groupby("Resource", as_index=False)
                .agg(
                    Tickets_Involved=("Issue Key", "nunique"),
                    Original_Estimate_hrs=("Original Estimate (hrs)", "sum"),
                    Logged_hrs=(time_col, "sum"),
                    Remaining_Estimate_hrs=("Remaining Estimate (hrs)", "sum"),
                    Overdue_Tickets=("Is Overdue", "sum"),
                    Over_Estimate_Tickets=("Is Overrun", "sum"),
                    Stale_Tickets=("Is Stale", "sum")
                )
            )
            summary_df.to_excel(writer, sheet_name="Resource Summary", index=False)

        # Sheet 2: Daily Timesheet Matrix (Pivot)
        if not filtered_daily_df.empty:
            pivot_df = filtered_daily_df.pivot_table(
                index="Resource",
                columns="Date",
                values="Hours Logged",
                aggfunc="sum",
                fill_value=0.0
            ).round(2)
            pivot_df["Total Hours"] = pivot_df.sum(axis=1).round(2)
            pivot_df.reset_index().to_excel(writer, sheet_name="Daily Timesheet Matrix", index=False)

        # Sheet 3: Ticket Deep Dive
        if not filtered_df.empty:
            export_cols = [
                c for c in filtered_df.columns
                if c not in ("Is Overdue", "Is Overrun", "Is Stale", "Is Unestimated")
            ]
            filtered_df[export_cols].to_excel(writer, sheet_name="Ticket Deep Dive", index=False)

        # Sheet 4: Recent Activities Log
        if not filtered_activities_df.empty:
            filtered_activities_df.to_excel(writer, sheet_name="Recent Activities", index=False)

    return output.getvalue()


# --- APPLICATION ROUTING ---
if 'jira_client' not in st.session_state:
    # ==========================================
    # PROFESSIONAL LOGIN PAGE
    # ==========================================
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

else:
    # ==========================================
    # MAIN DASHBOARD UI
    # ==========================================
    st.markdown("""<style>[data-testid="collapsedControl"] { display: block; }</style>""", unsafe_allow_html=True)

    # Initialize default date bounds in session state for Quick Date Presets
    today_d = datetime.today().date()
    if 'filter_start_date' not in st.session_state:
        st.session_state['filter_start_date'] = today_d - timedelta(days=7)
    if 'filter_end_date' not in st.session_state:
        st.session_state['filter_end_date'] = today_d

    # Check live internet status
    is_online_now, net_status_msg = check_internet_connection(st.session_state.get('jira_url'))

    with st.sidebar:
        st.title("Atlassian Jira")
        if is_online_now:
            st.success("🟢 Connected & Online")
        else:
            st.error("🔴 Offline — No Internet")
            st.caption(net_status_msg)

        if st.session_state.get('jira_url'):
            st.caption(f"🌐 {st.session_state['jira_url']}")

        st.markdown("#### ⚙️ Benchmarks & Rules")
        daily_target_hrs = st.number_input(
            "Daily Target Hours",
            min_value=1.0, max_value=16.0, value=8.0, step=0.5,
            help="Standard daily billable/capacity hours per resource."
        )
        stale_days_threshold = st.slider(
            "Stale Ticket Threshold (Days)",
            min_value=2, max_value=21, value=5,
            help="Flag active tickets that have had no updates for this many days."
        )
        exclude_weekends = st.checkbox(
            "Exclude Weekends (Sat/Sun)",
            value=True,
            help="Ignore Saturdays and Sundays when calculating utilization and missing timesheet logs."
        )

        st.markdown("#### 🔄 Cache & Session")
        if st.button("🔄 Refresh Jira Cache", use_container_width=True):
            online_check, reason_check = check_internet_connection(st.session_state.get('jira_url'))
            if not online_check:
                st.toast("⚠️ Cannot refresh cache while offline.", icon="🌐")
            else:
                st.session_state['jql_cache'] = {}
                for k in list(st.session_state.keys()):
                    if k.startswith("metadata_"):
                        del st.session_state[k]
                st.toast("Jira cache cleared! Next run will fetch fresh data.", icon="✅")

        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.title("📊 Enterprise Resource Hub")

    # Display prominent top banner if internet is disconnected
    if not is_online_now:
        render_no_internet_banner("reaching the Jira server", net_status_msg)
        if 'processed_df' in st.session_state:
            st.info("ℹ️ **Offline Mode Active**: You can still explore and export your previously generated dashboard below while your connection is restored.")

    with st.container(border=True):
        st.markdown("#### 1️⃣ Select Projects")
        project_map = st.session_state.get('project_mapping', {})
        selected_project_displays = st.multiselect(
            "Choose one or more projects to load environment filters:",
            options=list(project_map.keys()),
            placeholder="Search projects by name or key..."
        )
        selected_projects = [project_map[display_name] for display_name in selected_project_displays]

    if selected_projects:
        with st.spinner("Analyzing environment..."):
            (all_assignees, all_statuses), meta_err = get_project_metadata(st.session_state['jira_client'], selected_projects)

        if meta_err:
            render_no_internet_banner("loading project assignees and statuses", meta_err)

        with st.container(border=True):
            st.markdown("#### 2️⃣ Define Data Scope & Filters")

            fetch_mode_options = [
                "Time Logging Mode: Track hours logged during a specific date range",
                "Capacity Mode: View current active tickets and their total historical worklogs"
            ]
            selected_mode = st.radio("Select Tracking Mode:", options=fetch_mode_options, horizontal=True)
            is_time_logging_mode = selected_mode == fetch_mode_options[0]

            col1, col2 = st.columns([1.15, 1.25])
            with col1:
                st.markdown("**Date Bounds & Quick Presets**")
                p1, p2, p3, p4 = st.columns(4)
                if p1.button("Today", use_container_width=True, disabled=not is_time_logging_mode):
                    st.session_state['filter_start_date'] = today_d
                    st.session_state['filter_end_date'] = today_d
                if p2.button("This Week", use_container_width=True, disabled=not is_time_logging_mode):
                    st.session_state['filter_start_date'] = today_d - timedelta(days=today_d.weekday())
                    st.session_state['filter_end_date'] = today_d
                if p3.button("Last 7 Days", use_container_width=True, disabled=not is_time_logging_mode):
                    st.session_state['filter_start_date'] = today_d - timedelta(days=7)
                    st.session_state['filter_end_date'] = today_d
                if p4.button("This Month", use_container_width=True, disabled=not is_time_logging_mode):
                    st.session_state['filter_start_date'] = today_d.replace(day=1)
                    st.session_state['filter_end_date'] = today_d

                d1, d2 = st.columns(2)
                start_date = d1.date_input(
                    "From Date",
                    key="filter_start_date",
                    disabled=not is_time_logging_mode
                )
                end_date = d2.date_input(
                    "To Date",
                    key="filter_end_date",
                    disabled=not is_time_logging_mode
                )
                if not is_time_logging_mode:
                    st.caption("ℹ️ Date bounds apply to Time Logging Mode.")

            with col2:
                st.markdown("**Resource & Status Filters**")
                select_all = st.checkbox("Select All Resources")
                if select_all:
                    selected_assignees = st.multiselect("Resources", options=all_assignees, default=all_assignees, disabled=True)
                else:
                    selected_assignees = st.multiselect("Resources", options=all_assignees, default=[], placeholder="Select individuals...")

                selected_statuses = st.multiselect("Statuses", options=all_statuses, default=all_statuses)

        if st.button("🚀 Generate Dashboard", type="primary", use_container_width=True):
            if not selected_assignees:
                st.warning("⚠️ Please select at least one Resource before generating.")
            elif is_time_logging_mode and end_date < start_date:
                st.warning("⚠️ 'To Date' cannot be earlier than 'From Date'.")
            else:
                jql = build_jql(selected_projects, start_date, end_date, selected_assignees, selected_statuses, is_time_logging_mode)
                issues, fetch_err = fetch_issues(st.session_state['jira_client'], jql)

                if fetch_err:
                    render_no_internet_banner("fetching Jira tickets and worklogs", fetch_err)
                elif not issues:
                    st.info("No data found for the selected criteria.")
                    for key in ['processed_df', 'daily_df', 'activities_df']:
                        if key in st.session_state:
                            del st.session_state[key]
                else:
                    df, time_col, daily_df, activities_df = process_issues_to_dataframe(
                        st.session_state['jira_client'],
                        issues,
                        start_date,
                        end_date,
                        is_time_logging_mode,
                        base_url=st.session_state.get('jira_url', ''),
                        stale_days_threshold=stale_days_threshold
                    )
                    st.session_state['processed_df'] = df
                    st.session_state['time_col'] = time_col
                    st.session_state['daily_df'] = daily_df
                    st.session_state['activities_df'] = activities_df
                    st.success(f"Processed {len(issues)} tickets across {len(selected_assignees)} selected resource(s).")
                    math_success_animation()

        # ==========================================
        # UNCLUTTERED TABBED DASHBOARD RESULTS
        # ==========================================
        if 'processed_df' in st.session_state:
            df = st.session_state['processed_df']
            time_col = st.session_state['time_col']
            daily_df = st.session_state.get('daily_df', pd.DataFrame())
            activities_df = st.session_state.get('activities_df', pd.DataFrame())

            filtered_df = df[
                (df['Resource'].isin(selected_assignees)) &
                (df['Status'].isin(selected_statuses))
            ] if not df.empty else df

            filtered_daily_df = daily_df[
                (daily_df['Resource'].isin(selected_assignees)) &
                (daily_df['Status'].isin(selected_statuses))
            ] if not daily_df.empty else pd.DataFrame()

            filtered_activities_df = activities_df[
                (activities_df['Resource'].isin(selected_assignees)) &
                (activities_df['Status'].isin(selected_statuses))
            ] if not activities_df.empty else pd.DataFrame()

            # Compute Top-Level Executive KPIs
            unique_tickets_count = len(filtered_df['Issue Key'].unique()) if not filtered_df.empty else 0
            total_orig_est = round(filtered_df['Original Estimate (hrs)'].sum(), 1) if not filtered_df.empty else 0.0
            total_logged_hrs = round(filtered_df[time_col].sum(), 1) if not filtered_df.empty else 0.0
            total_rem_est = round(filtered_df['Remaining Estimate (hrs)'].sum(), 1) if not filtered_df.empty else 0.0

            working_days = get_working_days_list(start_date, end_date, exclude_weekends=exclude_weekends)
            num_resources = max(1, len([r for r in selected_assignees if r != "Unassigned"]))
            if is_time_logging_mode and working_days:
                expected_capacity_hrs = len(working_days) * num_resources * daily_target_hrs
                utilization_pct = round((total_logged_hrs / expected_capacity_hrs) * 100, 1) if expected_capacity_hrs > 0 else 0.0
                util_label = f"{utilization_pct}%"
                util_delta = f"{len(working_days)} working day(s)"
            else:
                util_label = f"{round((total_logged_hrs / total_orig_est) * 100, 1)}%" if total_orig_est > 0 else "N/A"
                util_delta = "Logged vs. Estimate"

            at_risk_tickets = 0
            if not filtered_df.empty:
                risk_mask = filtered_df['Is Overdue'] | filtered_df['Is Overrun'] | filtered_df['Is Stale']
                at_risk_tickets = filtered_df[risk_mask]['Issue Key'].nunique()

            st.markdown("### 📈 Executive Portfolio Snapshot")
            k1, k2, k3, k4, k5 = st.columns(5)
            k1.metric("Tickets Evaluated", unique_tickets_count)
            k2.metric("Original Estimate", f"{total_orig_est} hrs")
            k3.metric("Total Logged", f"{total_logged_hrs} hrs", delta=f"{total_rem_est} hrs remaining", delta_color="off")
            k4.metric("Resource Utilization", util_label, delta=util_delta, delta_color="off")
            k5.metric("Attention Needed", f"{at_risk_tickets} ticket(s)", delta="Overdue / Overrun / Stale", delta_color="inverse" if at_risk_tickets > 0 else "off")

            # Clean Navigation Tabs to prevent visual clutter
            tab_overview, tab_activities, tab_risk, tab_distribution, tab_data = st.tabs([
                "📊 Capacity & Daily Hours",
                "🕒 Recent Activities",
                "⚠️ Compliance & Risk Radar",
                "🎯 Work Distribution & Epics",
                "📋 Deep-Dive Data & Exports"
            ])

            # ----------------------------------------------------------
            # TAB 1: CAPACITY & DAILY HOURS LOGGED
            # ----------------------------------------------------------
            with tab_overview:
                with st.container(border=True):
                    st.markdown("#### 📅 Daily Hours Logged by Selected Resource")
                    if filtered_daily_df.empty:
                        st.info("No daily worklog entries found for the selected resource(s) and filters.")
                    else:
                        ctrl_col1, ctrl_col2 = st.columns([2, 1])
                        with ctrl_col1:
                            daily_chart_style = st.radio(
                                "Visualization Style:",
                                options=["Grouped Bar", "Stacked Bar", "Line & Area Trend"],
                                horizontal=True,
                                key="daily_chart_style_radio"
                            )
                        with ctrl_col2:
                            show_target_line = st.checkbox(f"Show {daily_target_hrs}h Daily Target Line", value=True)

                        daily_grouped = (
                            filtered_daily_df.groupby(["Date", "Resource"], as_index=False)
                            .agg(
                                Hours_Logged=("Hours Logged", "sum"),
                                Tickets_Worked=("Issue Key", lambda keys: ", ".join(sorted(set(keys))))
                            )
                        )
                        daily_grouped["Hours Logged"] = daily_grouped["Hours_Logged"].round(2)

                        tooltip_daily = [
                            alt.Tooltip('Date:N', title='Date'),
                            alt.Tooltip('Resource:N', title='Resource'),
                            alt.Tooltip('Hours Logged:Q', title='Hours Logged', format='.2f'),
                            alt.Tooltip('Tickets_Worked:N', title='Tickets Worked')
                        ]

                        if daily_chart_style == "Grouped Bar":
                            base_daily_chart = alt.Chart(daily_grouped).mark_bar(
                                cornerRadiusTopLeft=4, cornerRadiusTopRight=4
                            ).encode(
                                x=alt.X('Date:N', title="Date", sort='ascending', axis=alt.Axis(labelAngle=-30)),
                                y=alt.Y('Hours Logged:Q', title="Hours Logged per Day"),
                                color=alt.Color('Resource:N', scale=alt.Scale(scheme='tableau10'), legend=alt.Legend(title="Resource", orient="top")),
                                xOffset='Resource:N',
                                tooltip=tooltip_daily
                            )
                        elif daily_chart_style == "Stacked Bar":
                            base_daily_chart = alt.Chart(daily_grouped).mark_bar(
                                cornerRadiusTopLeft=4, cornerRadiusTopRight=4
                            ).encode(
                                x=alt.X('Date:N', title="Date", sort='ascending', axis=alt.Axis(labelAngle=-30)),
                                y=alt.Y('Hours Logged:Q', title="Hours Logged per Day", stack='zero'),
                                color=alt.Color('Resource:N', scale=alt.Scale(scheme='tableau10'), legend=alt.Legend(title="Resource", orient="top")),
                                tooltip=tooltip_daily
                            )
                        else:
                            base_daily_chart = alt.Chart(daily_grouped).mark_line(
                                point=alt.OverlayMarkDef(size=70, filled=True),
                                strokeWidth=3,
                                interpolate='monotone'
                            ).encode(
                                x=alt.X('Date:N', title="Date", sort='ascending', axis=alt.Axis(labelAngle=-30)),
                                y=alt.Y('Hours Logged:Q', title="Hours Logged per Day"),
                                color=alt.Color('Resource:N', scale=alt.Scale(scheme='tableau10'), legend=alt.Legend(title="Resource", orient="top")),
                                tooltip=tooltip_daily
                            )

                        if show_target_line:
                            target_rule = alt.Chart(pd.DataFrame({'Target': [daily_target_hrs]})).mark_rule(
                                color='#ef4444', strokeDash=[6, 4], strokeWidth=2
                            ).encode(
                                y='Target:Q',
                                tooltip=[alt.Tooltip('Target:Q', title='Daily Target (hrs)')]
                            )
                            combined_daily_chart = base_daily_chart + target_rule
                        else:
                            combined_daily_chart = base_daily_chart

                        st.altair_chart(
                            combined_daily_chart
                            .properties(height=360)
                            .configure_view(strokeOpacity=0)
                            .configure_axis(grid=True, gridColor='rgba(148, 163, 184, 0.2)')
                            .configure(background='transparent'),
                            use_container_width=True
                        )

                        with st.expander("🔎 View Daily Worklog Breakdown by Ticket"):
                            st.dataframe(
                                filtered_daily_df.sort_values(by=["Date", "Resource"], ascending=[False, True]),
                                column_config={
                                    "Ticket URL": st.column_config.LinkColumn("Jira Link", display_text="Open Ticket ↗")
                                },
                                use_container_width=True,
                                hide_index=True
                            )

                with st.container(border=True):
                    st.markdown("#### 📈 Estimated vs. Logged vs. Remaining Hours by Resource")
                    if not filtered_df.empty:
                        agg_df = filtered_df.groupby("Resource")[["Original Estimate (hrs)", time_col, "Remaining Estimate (hrs)"]].sum().reset_index()
                        if not agg_df.empty:
                            melted_df = pd.melt(
                                agg_df,
                                id_vars=['Resource'],
                                value_vars=["Original Estimate (hrs)", time_col, "Remaining Estimate (hrs)"],
                                var_name='Metric',
                                value_name='Hours'
                            )
                            cap_chart = alt.Chart(melted_df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
                                x=alt.X('Resource:N', title="", axis=alt.Axis(labelAngle=0)),
                                y=alt.Y('Hours:Q', title="Hours"),
                                color=alt.Color(
                                    'Metric:N',
                                    scale=alt.Scale(range=['#4C78A8', '#F58518', '#E45756']),
                                    legend=alt.Legend(title="", orient="top")
                                ),
                                xOffset='Metric:N',
                                tooltip=['Resource', 'Metric', alt.Tooltip('Hours:Q', format='.2f')]
                            ).properties(height=360).configure_view(strokeOpacity=0).configure_axis(grid=False).configure(background='transparent')
                            st.altair_chart(cap_chart, use_container_width=True)

            # ----------------------------------------------------------
            # TAB 2: RECENT ACTIVITIES BY SELECTED RESOURCE
            # ----------------------------------------------------------
            with tab_activities:
                with st.container(border=True):
                    st.markdown("#### 🕒 Recent Activities Performed by Selected Resource")
                    if filtered_activities_df.empty:
                        st.info("No recent activities found for the selected resource(s) and criteria.")
                    else:
                        f_col1, f_col2, f_col3, f_col4 = st.columns([1.3, 1.1, 1.1, 0.9])
                        available_act_types = sorted(filtered_activities_df["Activity Type"].unique().tolist())
                        with f_col1:
                            selected_act_types = st.multiselect(
                                "Activity Type:",
                                options=available_act_types,
                                default=available_act_types
                            )
                        with f_col2:
                            search_query = st.text_input("Search Ticket or Details:", placeholder="e.g. PROJ-101, API, bug...")
                        with f_col3:
                            activity_view_mode = st.radio(
                                "View Mode:",
                                options=["Timeline Cards", "Table View"],
                                horizontal=True
                            )
                        with f_col4:
                            max_items = st.slider(
                                "Max Items:",
                                min_value=5,
                                max_value=max(10, min(100, len(filtered_activities_df))),
                                value=min(15, max(5, len(filtered_activities_df))),
                                step=5
                            )

                        shown_activities = filtered_activities_df[
                            filtered_activities_df["Activity Type"].isin(selected_act_types)
                        ]
                        if search_query.strip():
                            q = search_query.strip().lower()
                            shown_activities = shown_activities[
                                shown_activities["Issue Key"].str.lower().str.contains(q, na=False) |
                                shown_activities["Summary"].str.lower().str.contains(q, na=False) |
                                shown_activities["Details"].str.lower().str.contains(q, na=False)
                            ]
                        shown_activities = shown_activities.head(max_items)

                        if shown_activities.empty:
                            st.info("No activities match your current filter criteria.")
                        elif activity_view_mode == "Timeline Cards":
                            for _, row in shown_activities.iterrows():
                                safe_resource = html.escape(str(row["Resource"]))
                                safe_type = html.escape(str(row["Activity Type"]))
                                safe_ts = html.escape(str(row["Timestamp"]))
                                safe_key = html.escape(str(row["Issue Key"]))
                                safe_url = html.escape(str(row.get("Ticket URL", "")))
                                safe_summary = html.escape(str(row["Summary"]))
                                safe_status = html.escape(str(row["Status"]))
                                safe_project = html.escape(str(row["Project"]))
                                safe_details = html.escape(str(row["Details"]))

                                key_html = (
                                    f'<a href="{safe_url}" target="_blank">[{safe_key}]</a>'
                                    if safe_url.startswith("http") else f"[{safe_key}]"
                                )

                                st.markdown(f"""
                                    <div class="activity-card">
                                        <div class="activity-meta">
                                            <span class="activity-resource">👤 {safe_resource}</span>
                                            <span class="activity-badge">{safe_type}</span>
                                            <span>🗓️ {safe_ts}</span>
                                            <span>• 📁 {safe_project}</span>
                                            <span>• 🏷️ Status: <b>{safe_status}</b></span>
                                        </div>
                                        <div class="activity-title">{key_html} {safe_summary}</div>
                                        <div class="activity-detail">{safe_details}</div>
                                    </div>
                                """, unsafe_allow_html=True)
                        else:
                            st.dataframe(
                                shown_activities,
                                column_config={
                                    "Ticket URL": st.column_config.LinkColumn("Jira Link", display_text="Open Ticket ↗")
                                },
                                use_container_width=True,
                                hide_index=True
                            )

            # ----------------------------------------------------------
            # TAB 3: COMPLIANCE, OVERDUE & STALE RADAR
            # ----------------------------------------------------------
            with tab_risk:
                # 1. Timesheet Compliance & Missing Logs Detector
                with st.container(border=True):
                    st.markdown("#### 🗓️ Timesheet Compliance & Missing Worklog Detector")
                    if not is_time_logging_mode:
                        st.info("Switch to **Time Logging Mode** to audit daily timesheet compliance across a specific date range.")
                    else:
                        active_people = [r for r in selected_assignees if r != "Unassigned"]
                        if not active_people or not working_days:
                            st.info("No working days or assigned resources in the selected range.")
                        else:
                            grid_rows = []
                            missing_records = []
                            logged_lookup = {}
                            if not filtered_daily_df.empty:
                                for (res, dt_str), grp in filtered_daily_df.groupby(["Resource", "Date"]):
                                    logged_lookup[(res, dt_str)] = round(grp["Hours Logged"].sum(), 2)

                            for res in active_people:
                                row_dict = {"Resource": res}
                                zero_days = []
                                under_days = []
                                total_res_hrs = 0.0
                                for d_str in working_days:
                                    hrs = logged_lookup.get((res, d_str), 0.0)
                                    row_dict[d_str] = hrs
                                    total_res_hrs += hrs
                                    if hrs == 0:
                                        zero_days.append(d_str)
                                    elif hrs < daily_target_hrs:
                                        under_days.append(f"{d_str} ({hrs}h)")
                                row_dict["Total Logged (hrs)"] = round(total_res_hrs, 2)
                                row_dict["Target (hrs)"] = round(len(working_days) * daily_target_hrs, 1)
                                grid_rows.append(row_dict)

                                if zero_days or under_days:
                                    missing_records.append({
                                        "Resource": res,
                                        "Zero-Log Days Count": len(zero_days),
                                        "Zero-Log Dates (0h)": ", ".join(zero_days) if zero_days else "None",
                                        f"Under-Target Dates (<{daily_target_hrs}h)": ", ".join(under_days) if under_days else "None",
                                        "Period Logged / Target": f"{round(total_res_hrs, 1)}h / {round(len(working_days) * daily_target_hrs, 1)}h"
                                    })

                            if missing_records:
                                st.warning(f"Found {len(missing_records)} resource(s) with missing or under-target daily worklogs across {len(working_days)} working day(s).")
                                st.dataframe(pd.DataFrame(missing_records), use_container_width=True, hide_index=True)
                            else:
                                st.success(f"All selected resources met the {daily_target_hrs}h daily target across all {len(working_days)} working day(s)!")

                            with st.expander("📊 View Complete Daily Timesheet Matrix (Resource × Date)"):
                                st.dataframe(pd.DataFrame(grid_rows), use_container_width=True, hide_index=True)

                # 2. Overdue, Estimate Overrun & Stale Tickets Radar
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    with st.container(border=True):
                        st.markdown("#### 🔥 Overdue & Estimate Overrun Alerts")
                        if filtered_df.empty:
                            st.info("No ticket data available.")
                        else:
                            overrun_df = (
                                filtered_df[filtered_df['Is Overdue'] | filtered_df['Is Overrun']]
                                .drop_duplicates(subset=["Issue Key"])
                                [["Issue Key", "Ticket URL", "Summary", "Current Ticket Assignee", "Status", "Due Date", "Original Estimate (hrs)", time_col, "Health Status"]]
                            )
                            if overrun_df.empty:
                                st.success("✅ No overdue or over-estimate tickets found!")
                            else:
                                st.dataframe(
                                    overrun_df,
                                    column_config={
                                        "Ticket URL": st.column_config.LinkColumn("Jira Link", display_text="Open ↗")
                                    },
                                    use_container_width=True,
                                    hide_index=True
                                )

                with r_col2:
                    with st.container(border=True):
                        st.markdown(f"#### 🕸️ Stale Active Tickets (≥ {stale_days_threshold} Days Inactive)")
                        if filtered_df.empty:
                            st.info("No ticket data available.")
                        else:
                            stale_df = (
                                filtered_df[filtered_df['Is Stale']]
                                .drop_duplicates(subset=["Issue Key"])
                                .sort_values(by="Days Inactive", ascending=False)
                                [["Issue Key", "Ticket URL", "Summary", "Current Ticket Assignee", "Status", "Days Inactive", "Health Status"]]
                            )
                            if stale_df.empty:
                                st.success(f"✅ No active tickets have been stale for {stale_days_threshold}+ days!")
                            else:
                                st.dataframe(
                                    stale_df,
                                    column_config={
                                        "Ticket URL": st.column_config.LinkColumn("Jira Link", display_text="Open ↗")
                                    },
                                    use_container_width=True,
                                    hide_index=True
                                )

            # ----------------------------------------------------------
            # TAB 4: WORK DISTRIBUTION & EPIC ROLLUPS
            # ----------------------------------------------------------
            with tab_distribution:
                if filtered_df.empty:
                    st.info("No data available to analyze work distribution.")
                else:
                    d_col1, d_col2 = st.columns(2)
                    with d_col1:
                        with st.container(border=True):
                            st.markdown("#### 🧩 Hours Logged by Issue Type")
                            type_agg = (
                                filtered_df.groupby("Issue Type", as_index=False)
                                .agg(Hours=(time_col, "sum"), Tickets=("Issue Key", "nunique"))
                            )
                            type_agg["Hours"] = type_agg["Hours"].round(2)
                            type_chart = alt.Chart(type_agg).mark_arc(innerRadius=55, cornerRadius=6).encode(
                                theta=alt.Theta("Hours:Q"),
                                color=alt.Color("Issue Type:N", scale=alt.Scale(scheme="category10"), legend=alt.Legend(orient="bottom")),
                                tooltip=["Issue Type", alt.Tooltip("Hours:Q", format=".2f"), "Tickets"]
                            ).properties(height=300).configure_view(strokeOpacity=0).configure(background='transparent')
                            st.altair_chart(type_chart, use_container_width=True)

                    with d_col2:
                        with st.container(border=True):
                            st.markdown("#### ⚡ Hours Logged by Priority")
                            prio_agg = (
                                filtered_df.groupby("Priority", as_index=False)
                                .agg(Hours=(time_col, "sum"), Tickets=("Issue Key", "nunique"))
                            )
                            prio_agg["Hours"] = prio_agg["Hours"].round(2)
                            prio_chart = alt.Chart(prio_agg).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
                                y=alt.Y("Priority:N", sort='-x', title=""),
                                x=alt.X("Hours:Q", title="Hours Logged"),
                                color=alt.Color("Priority:N", scale=alt.Scale(scheme="tealblues"), legend=None),
                                tooltip=["Priority", alt.Tooltip("Hours:Q", format=".2f"), "Tickets"]
                            ).properties(height=300).configure_view(strokeOpacity=0).configure_axis(grid=False).configure(background='transparent')
                            st.altair_chart(prio_chart, use_container_width=True)

                    with st.container(border=True):
                        st.markdown("#### 🗂️ Parent Story / Epic Effort Rollup")
                        epic_rollup = (
                            filtered_df.groupby("Parent / Epic", as_index=False)
                            .agg(
                                Child_Tickets=("Issue Key", "nunique"),
                                Resources_Involved=("Resource", lambda r: ", ".join(sorted(set(r)))),
                                Original_Estimate_hrs=("Original Estimate (hrs)", "sum"),
                                Logged_hrs=(time_col, "sum"),
                                Remaining_Estimate_hrs=("Remaining Estimate (hrs)", "sum")
                            )
                            .sort_values(by="Logged_hrs", ascending=False)
                        )
                        epic_rollup["Original_Estimate_hrs"] = epic_rollup["Original_Estimate_hrs"].round(2)
                        epic_rollup["Logged_hrs"] = epic_rollup["Logged_hrs"].round(2)
                        epic_rollup["Remaining_Estimate_hrs"] = epic_rollup["Remaining_Estimate_hrs"].round(2)
                        st.dataframe(epic_rollup, use_container_width=True, hide_index=True)

            # ----------------------------------------------------------
            # TAB 5: DEEP-DIVE DATA TABLE & MULTI-FORMAT EXPORTS
            # ----------------------------------------------------------
            with tab_data:
                with st.container(border=True):
                    st.markdown("#### 📋 Comprehensive Ticket & Resource Table")
                    display_cols = [
                        c for c in filtered_df.columns
                        if c not in ("Is Overdue", "Is Overrun", "Is Stale", "Is Unestimated")
                    ]
                    st.dataframe(
                        filtered_df[display_cols],
                        column_config={
                            "Ticket URL": st.column_config.LinkColumn("Jira Link", display_text="Open Ticket ↗")
                        },
                        use_container_width=True,
                        hide_index=True
                    )

                    st.markdown("#### 📥 Export Reports")
                    exp_col1, exp_col2, exp_col3 = st.columns(3)

                    excel_bytes = build_excel_workbook(filtered_df, filtered_daily_df, filtered_activities_df, time_col)
                    with exp_col1:
                        if excel_bytes:
                            st.download_button(
                                label="📊 Download Multi-Sheet Excel (.xlsx)",
                                data=excel_bytes,
                                file_name=f'jira_portfolio_report_{datetime.today().strftime("%Y-%m-%d")}.xlsx',
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                type="primary",
                                use_container_width=True
                            )
                        else:
                            st.caption("Install `xlsxwriter` or `openpyxl` for `.xlsx` export.")

                    with exp_col2:
                        st.download_button(
                            label="📥 Download Capacity Data (CSV)",
                            data=filtered_df[display_cols].to_csv(index=False).encode('utf-8'),
                            file_name=f'jira_capacity_export_{datetime.today().strftime("%Y-%m-%d")}.csv',
                            mime='text/csv',
                            use_container_width=True
                        )

                    with exp_col3:
                        if not filtered_activities_df.empty:
                            st.download_button(
                                label="📥 Download Activity Log (CSV)",
                                data=filtered_activities_df.to_csv(index=False).encode('utf-8'),
                                file_name=f'jira_recent_activities_{datetime.today().strftime("%Y-%m-%d")}.csv',
                                mime='text/csv',
                                use_container_width=True
                            )