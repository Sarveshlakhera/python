import streamlit as st
from services.network import check_internet_connection


def render_sidebar(is_online_now, net_status_msg):
    """
    Renders the sidebar with connection status, benchmark thresholds, and cache controls.
    Includes the hamburger toggle button (☰) in the sidebar header to collapse the sidebar.
    Returns (daily_target_hrs, stale_days_threshold, exclude_weekends).
    """
    with st.sidebar:
        # Header with Title and Hamburger Collapse Button
        col_title, col_toggle = st.columns([3.2, 1.2])
        with col_title:
            st.markdown("<h2 style='margin:0; padding:0; text-align:left; font-size:1.45rem;'>Atlassian Jira</h2>", unsafe_allow_html=True)
        with col_toggle:
            if st.button("☰", key="sidebar_hamburger_collapse_btn", help="Collapse sidebar", use_container_width=True):
                st.session_state['show_sidebar'] = False
                st.rerun()

        st.markdown("<div style='margin-bottom: 0.5rem;'></div>", unsafe_allow_html=True)

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
            online_check, _ = check_internet_connection(st.session_state.get('jira_url'))
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

    return daily_target_hrs, stale_days_threshold, exclude_weekends
