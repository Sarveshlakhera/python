import streamlit as st
from jira import JIRA, JIRAError
import pandas as pd
import altair as alt
import os
import json
from dotenv import load_dotenv
from datetime import datetime, timedelta
import urllib3

# Suppress the SSL warning for corporate networks
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- UI CONFIGURATION ---
st.set_page_config(page_title="Jira Resource Tracker", layout="wide", page_icon="📊", initial_sidebar_state="expanded")
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
        /* Hide the top right toolbar to prevent users from toggling dark mode */
        [data-testid="stToolbar"] {
            display: none !important;
        }

        /* Force standard text to dark gray (Light Mode aesthetics) */
        .stApp, .stMarkdown, p, label, li, span {
            color: #1e293b !important;
        }

        /* Preserve title gradients and primary button text */
        h1, h2, h3, h4, h5, h6 {
            color: inherit !important;
        }
        .stButton>button[kind="primary"] {
            color: #ffffff !important;
        }
        .stButton>button[kind="primary"] * {
            color: #ffffff !important;
        }
        
        /* --------------------------------------------------- */

        /* Import Google Font */
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');

        /* Apply Font Globally */
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
            opacity: 0.6;
            pointer-events: none; 
        }
        
        .blob-1 {
            top: -10%; left: -10%;
            width: 50vw; height: 50vw;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255, 65, 108, 0.3) 0%, rgba(255, 65, 108, 0) 70%);
            animation: float1 20s infinite alternate ease-in-out;
        }
        
        .blob-2 {
            bottom: -20%; right: -10%;
            width: 60vw; height: 60vw;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(37, 99, 235, 0.3) 0%, rgba(139, 92, 246, 0) 70%);
            animation: float2 25s infinite alternate-reverse ease-in-out;
        }

        .blob-3 {
            top: 20%; right: 20%;
            width: 40vw; height: 40vw;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(139, 92, 246, 0.2) 0%, rgba(139, 92, 246, 0) 70%);
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
            background: rgba(255, 255, 255, 0.4) !important;
            backdrop-filter: blur(25px) !important;
            -webkit-backdrop-filter: blur(25px) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.5) !important;
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
            filter: drop-shadow(0px 4px 15px rgba(37, 99, 235, 0.2));
            margin-bottom: 0.5rem !important;
        }

        /* Glassmorphism Metrics (KPI Cards) */
        .stMetric {
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(15px);
            -webkit-backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.8);
            border-radius: 18px;
            padding: 1.5rem;
            box-shadow: 0 4px 16px rgba(0,0,0,0.02);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.3s ease;
        }
        .stMetric:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 24px rgba(0,0,0,0.05);
        }

        /* Glassmorphism Containers (replaces default st.container borders) */
        [data-testid="stVerticalBlock"] > div[style*="border"] {
            border: 1px solid rgba(255,255,255,0.8) !important;
            border-radius: 18px !important;
            background: rgba(255,255,255,0.5) !important;
            backdrop-filter: blur(10px) !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.02) !important;
        }

        /* Glassmorphism Buttons */
        .stButton>button {
            border-radius: 12px !important;
            border: 1px solid rgba(255,255,255,0.6) !important;
            background: rgba(255,255,255,0.7) !important;
            backdrop-filter: blur(10px) !important;
            font-weight: 500 !important;
            color: #27272a !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02) !important;
        }

        .stButton>button:hover {
            background: #18181b !important;
            color: #ffffff !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1) !important;
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

        /* Spinner Color Match */
        .stSpinner > div > div { border-color: #3b82f6 transparent transparent transparent; }
        
        /* Hide sidebar by default on the login screen */
        [data-testid="collapsedControl"] { display: none; }
    </style>
    """, unsafe_allow_html=True)

# Apply Theme immediately
apply_custom_theme()


# --- CORE FUNCTIONS ---
def math_success_animation():
    """Injects CSS to display a floating math/numbers animation on success."""
    st.markdown("""
        <style>
        .math-float {
            position: fixed;
            bottom: -50px;
            color: rgba(37, 99, 235, 0.8);
            font-size: 2.2rem;
            font-family: 'Outfit', sans-serif;
            font-weight: 700;
            z-index: 99999;
            animation: floatMathUp 3.5s ease-in forwards;
            pointer-events: none;
        }
        @keyframes floatMathUp {
            0% { transform: translateY(0) rotate(0deg); opacity: 1; }
            100% { transform: translateY(-120vh) rotate(360deg); opacity: 0; }
        }
        </style>
        <div class="math-float" style="left: 5%; animation-duration: 3.5s; animation-delay: 0s;">∑</div>
        <div class="math-float" style="left: 15%; animation-duration: 4.2s; animation-delay: 0.2s;">∫</div>
        <div class="math-float" style="left: 25%; animation-duration: 3.1s; animation-delay: 0.5s;">%</div>
        <div class="math-float" style="left: 35%; animation-duration: 4.5s; animation-delay: 0.1s;">π</div>
        <div class="math-float" style="left: 45%; animation-duration: 3.2s; animation-delay: 0.3s;">∞</div>
        <div class="math-float" style="left: 55%; animation-duration: 3.8s; animation-delay: 0.6s;">42</div>
        <div class="math-float" style="left: 65%; animation-duration: 4.1s; animation-delay: 0.4s;">3.14</div>
        <div class="math-float" style="left: 75%; animation-duration: 3.4s; animation-delay: 0.7s;">01</div>
        <div class="math-float" style="left: 85%; animation-duration: 4.2s; animation-delay: 0.2s;">√</div>
        <div class="math-float" style="left: 95%; animation-duration: 3.6s; animation-delay: 0.5s;">ƒ(x)</div>
        """, unsafe_allow_html=True)

def authenticate_jira(url, email, token):
    """Establish connection to Jira API with session state."""
    try:
        jira = JIRA(server=url, basic_auth=(email, token), options={'verify': False})
        jira.current_user() 
        return jira, None
    except JIRAError as e:
        return None, f"Authentication Failed: {e.text}"
    except Exception as e:
        return None, f"An error occurred: {str(e)}"

def get_project_metadata(jira, projects):
    cache_key = f"metadata_{'-'.join(projects)}"
    if cache_key in st.session_state: return st.session_state[cache_key]
        
    project_keys = ", ".join([f'"{p}"' for p in projects])
    jql = f'project in ({project_keys})'
    
    issues = jira.enhanced_search_issues(jql_str=jql, maxResults=False, fields="assignee,status")
    assignees, statuses = set(), set()
    
    for i in issues:
        assignees.add(i.fields.assignee.displayName if hasattr(i.fields, 'assignee') and i.fields.assignee else "Unassigned")
        statuses.add(i.fields.status.name if hasattr(i.fields, 'status') and i.fields.status else "Unknown")
        
    result = (sorted(list(assignees)), sorted(list(statuses)))
    st.session_state[cache_key] = result
    return result

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
        jql += f' AND resolution = Unresolved'
        
    if statuses:
        status_list = [f'"{s}"' for s in statuses]
        jql += f' AND status in ({", ".join(status_list)})'
        
    jql += ' ORDER BY updated DESC'
    return jql

def fetch_issues(jira, jql_query):
    with st.spinner('Fetching detailed task data from Jira...'):
        issues = jira.enhanced_search_issues(
            jql_str=jql_query, maxResults=False, 
            fields="project,summary,assignee,status,issuetype,timeoriginalestimate,timespent,timeestimate,worklog,duedate"
        )
    return list(issues)

def process_issues_to_dataframe(jira_client, issues, start_date, end_date, is_time_logging_mode):
    data = []
    progress_bar = st.progress(0, text="Analyzing worklogs and calculating hours...")
    time_col_name = "Time Spent in Period (hrs)" if is_time_logging_mode else "Total Time Logged (hrs)"
    
    for idx, issue in enumerate(issues):
        progress_bar.progress((idx + 1) / len(issues), text=f"Processing task {issue.key}...")
        fields = issue.fields
        
        orig_est_hours = (getattr(fields, 'timeoriginalestimate', 0) or 0) / 3600.0
        rem_est_hours = (getattr(fields, 'timeestimate', 0) or 0) / 3600.0
        current_assignee = fields.assignee.displayName if hasattr(fields, 'assignee') and fields.assignee else "Unassigned"
        
        due_date_val = getattr(fields, 'duedate', None)
        due_date_str = due_date_val if due_date_val else "Not Set"
        
        author_time_spent = {}
        worklogs = getattr(fields, 'worklog', None)
        worklog_list = worklogs.worklogs if worklogs else []
        
        if worklogs and worklogs.total > len(worklog_list):
            try: worklog_list = jira_client.worklogs(issue.key)
            except: pass
                    
        for wl in worklog_list:
            try:
                author = wl.author.displayName if hasattr(wl, 'author') and wl.author else "Unknown"
                time_spent_seconds = int(getattr(wl, 'timeSpentSeconds', 0))
                
                if is_time_logging_mode:
                    started = getattr(wl, 'started', '')
                    if started:
                        wl_date = datetime.strptime(started.split('T')[0], "%Y-%m-%d").date()
                        if start_date <= wl_date <= end_date:
                            author_time_spent[author] = author_time_spent.get(author, 0) + time_spent_seconds
                else:
                    author_time_spent[author] = author_time_spent.get(author, 0) + time_spent_seconds
            except: continue
                
        involved_users = set(author_time_spent.keys())
        involved_users.add(current_assignee)
        
        for user in involved_users:
            user_time_spent_hrs = author_time_spent.get(user, 0) / 3600.0
            is_assignee = (user == current_assignee)
            
            if not is_assignee and user_time_spent_hrs == 0: continue
            
            user_orig_est = round(orig_est_hours, 2) if is_assignee else 0.0
            user_rem_est = round(rem_est_hours, 2) if is_assignee else 0.0
            role = "Assignee & Contributor" if is_assignee and user_time_spent_hrs > 0 else "Assignee" if is_assignee else "Contributor"

            data.append({
                "Resource": user,
                "Ticket Role": role,
                "Project": fields.project.name,
                "Issue Key": issue.key,
                "Summary": fields.summary,
                "Current Ticket Assignee": current_assignee,
                "Status": fields.status.name,
                "Issue Type": fields.issuetype.name,
                "Due Date": due_date_str,
                "Original Estimate (hrs)": user_orig_est,
                time_col_name: round(user_time_spent_hrs, 2),
                "Remaining Estimate (hrs)": user_rem_est
            })
            
    progress_bar.empty()
    return pd.DataFrame(data), time_col_name

# --- APPLICATION ROUTING ---
if 'jira_client' not in st.session_state:
    # ==========================================
    # PROFESSIONAL LOGIN PAGE
    # ==========================================
    
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # Professional Jira Banner integration
        st.markdown("""
            <div style='text-align: center; margin-bottom: 10px;'>
                <img src='https://cdn.icon-icons.com/icons2/2699/PNG/512/atlassian_jira_logo_icon_170511.png' width='80'>
            </div>
            <h2>📊 Enterprise Resource Hub</h2>
            <p style='text-align: center; color: #64748b;'>Sign in to access Jira portfolio metrics</p>
        """, unsafe_allow_html=True)
        
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
                        with st.spinner("Authenticating..."):
                            jira, error = authenticate_jira(jira_url, jira_email, jira_token)
                            if error:
                                st.error(error)
                            else:
                                st.session_state['jira_client'] = jira
                                st.session_state['project_mapping'] = {f"{p.name} ({p.key})": p.key for p in jira.projects()}
                                st.rerun()
            
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
                            with st.spinner("Authenticating via JSON payload..."):
                                jira, error = authenticate_jira(j_url, j_email, j_token)
                                if error:
                                    st.error(error)
                                else:
                                    st.session_state['jira_client'] = jira
                                    st.session_state['project_mapping'] = {f"{p.name} ({p.key})": p.key for p in jira.projects()}
                                    st.rerun()
                    except json.JSONDecodeError:
                        st.error("Invalid JSON format. Please ensure you are using standard JSON with double quotes and colons.")
        
        st.markdown("<p style='text-align: center; font-size: 12px; color: #b3bac5; margin-top: 20px;'>Protected by TLS Encryption</p>", unsafe_allow_html=True)

else:
    # ==========================================
    # MAIN DASHBOARD UI
    # ==========================================
    
    st.markdown("""<style>[data-testid="collapsedControl"] { display: block; }</style>""", unsafe_allow_html=True)
    
    with st.sidebar:
        st.title("Atlassian Jira")
        st.success("✅ Connected securely")
        if st.button("Logout", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

    st.title("📊 Enterprise Resource Hub")
    
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
            all_assignees, all_statuses = get_project_metadata(st.session_state['jira_client'], selected_projects)
            
        with st.container(border=True):
            st.markdown("#### 2️⃣ Define Data Scope & Filters")
            
            fetch_mode_options = [
                "Time Logging Mode: Track hours logged during a specific date range",
                "Capacity Mode: View current active tickets and their total historical worklogs"
            ]
            selected_mode = st.radio("Select Tracking Mode:", options=fetch_mode_options)
            is_time_logging_mode = selected_mode == fetch_mode_options[0]
            
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Date Bounds**")
                d1, d2 = st.columns(2)
                start_date = d1.date_input("From Date", value=datetime.today() - timedelta(days=7), disabled=not is_time_logging_mode)
                end_date = d2.date_input("To Date", value=datetime.today(), disabled=not is_time_logging_mode)
                if not is_time_logging_mode: st.caption("ℹ️ Dates are disabled in Capacity Mode.")
            
            with col2:
                st.markdown("**Resource & Status Filters**")
                select_all = st.checkbox("Select All Resources")
                if select_all:
                    selected_assignees = st.multiselect("Resources", options=all_assignees, default=all_assignees, disabled=True)
                else:
                    selected_assignees = st.multiselect("Resources", options=all_assignees, default=[], placeholder="Select individuals...")
                
                selected_statuses = st.multiselect("Statuses", options=all_statuses, default=all_statuses)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 Generate Dashboard", type="primary", use_container_width=True):
            if not selected_assignees:
                st.warning("⚠️ Please select at least one Resource before generating.")
            else:
                jql = build_jql(selected_projects, start_date, end_date, selected_assignees, selected_statuses, is_time_logging_mode)
                issues = fetch_issues(st.session_state['jira_client'], jql)
                
                if not issues:
                    st.info("No data found for the selected criteria.")
                    if 'processed_df' in st.session_state: del st.session_state['processed_df']
                else:
                    df, time_col = process_issues_to_dataframe(st.session_state['jira_client'], issues, start_date, end_date, is_time_logging_mode)
                    st.session_state['processed_df'] = df
                    st.session_state['time_col'] = time_col
                    st.success(f"Successfully processed {len(issues)} tickets!")
                    
                    # TRIGGER CUSTOM MATH ANIMATION HERE
                    math_success_animation()
                    
        # --- RENDER RESULTS ---
        if 'processed_df' in st.session_state:
            df = st.session_state['processed_df']
            time_col = st.session_state['time_col']
            
            filtered_df = df[
                (df['Resource'].isin(selected_assignees)) & 
                (df['Status'].isin(selected_statuses))
            ]
            
            st.markdown("---")
            st.markdown("### 📈 Performance & Capacity Overview")
            
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            kpi1.metric("Tickets Evaluated", len(filtered_df['Issue Key'].unique()))
            kpi2.metric("Original Estimate (hrs)", round(filtered_df['Original Estimate (hrs)'].sum(), 1))
            kpi3.metric("Total Logged (hrs)", round(filtered_df[time_col].sum(), 1))
            kpi4.metric("Remaining Estimate (hrs)", round(filtered_df['Remaining Estimate (hrs)'].sum(), 1))
            
            agg_df = filtered_df.groupby("Resource")[["Original Estimate (hrs)", time_col, "Remaining Estimate (hrs)"]].sum().reset_index()
            
            if not agg_df.empty:
                melted_df = pd.melt(agg_df, id_vars=['Resource'], 
                                    value_vars=["Original Estimate (hrs)", time_col, "Remaining Estimate (hrs)"],
                                    var_name='Metric', value_name='Hours')
                
                # Transparent background to fit glassmorphism theme
                chart = alt.Chart(melted_df).mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3).encode(
                    x=alt.X('Resource:N', title="", axis=alt.Axis(labelAngle=-0, labelOverlap=True)),
                    y=alt.Y('Hours:Q', title="Hours Logged / Estimated"),
                    color=alt.Color('Metric:N', 
                                    scale=alt.Scale(range=['#4C78A8', '#F58518', '#E45756']), 
                                    legend=alt.Legend(title="", orient="top", padding=10)),
                    xOffset='Metric:N',
                    tooltip=['Resource', 'Metric', 'Hours']
                ).properties(height=450).configure_view(strokeOpacity=0).configure_axis(grid=False).configure(background='transparent')
                
                st.altair_chart(chart, use_container_width=True)

            st.markdown("### 📋 Deep-Dive Data Table")
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            
            st.download_button(
                label="📥 Download Data Export (CSV)",
                data=filtered_df.to_csv(index=False).encode('utf-8'),
                file_name=f'jira_export_{datetime.today().strftime("%Y-%m-%d")}.csv',
                mime='text/csv',
            )