import html
from datetime import datetime, timedelta
import pandas as pd
import altair as alt
import streamlit as st

from config.theme import math_success_animation
from services.network import check_internet_connection, render_no_internet_banner
from services.jira_service import get_project_metadata, build_jql, fetch_issues
from processors.data_processor import get_working_days_list, process_issues_to_dataframe
from processors.exporter import build_excel_workbook
from views.sidebar_view import render_sidebar


def render_dashboard_view():
    """Renders the main authenticated dashboard workspace."""
    # Enforce explicit sidebar visibility state via Python session state and CSS
    sidebar_visible = st.session_state.get('show_sidebar', True)
    if sidebar_visible:
        st.markdown("""
        <style>
            section[data-testid="stSidebar"],
            [data-testid="stSidebar"] {
                display: block !important;
                transform: none !important;
                visibility: visible !important;
                opacity: 1 !important;
                left: 0 !important;
                min-width: 19rem !important;
                max-width: 22rem !important;
                z-index: 100 !important;
                transition: transform 0.25s ease-in-out, opacity 0.25s ease-in-out !important;
            }
            [data-testid="collapsedControl"],
            [data-testid="stSidebarCollapsedControl"] {
                display: none !important;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            section[data-testid="stSidebar"],
            [data-testid="stSidebar"] {
                display: none !important;
                transform: translateX(-100%) !important;
                visibility: hidden !important;
                opacity: 0 !important;
                width: 0 !important;
                min-width: 0 !important;
                transition: transform 0.25s ease-in-out, opacity 0.25s ease-in-out !important;
            }
        </style>
        """, unsafe_allow_html=True)

    today_d = datetime.today().date()
    if 'filter_start_date' not in st.session_state:
        st.session_state['filter_start_date'] = today_d - timedelta(days=7)
    if 'filter_end_date' not in st.session_state:
        st.session_state['filter_end_date'] = today_d

    is_online_now, net_status_msg = check_internet_connection(st.session_state.get('jira_url'))
    daily_target_hrs, stale_days_threshold, exclude_weekends = render_sidebar(is_online_now, net_status_msg)

    # Dashboard Header:
    # When sidebar is collapsed, show the hamburger toggle button (☰) at the top-left to uncollapse it.
    # When sidebar is expanded, the hamburger toggle button lives inside the sidebar header, so the dashboard header is clean.
    if not sidebar_visible:
        col_ham, col_title = st.columns([0.18, 3.82])
        with col_ham:
            st.write("")
            if st.button("☰", key="sidebar_hamburger_expand_btn", help="Expand sidebar", use_container_width=True):
                st.session_state['show_sidebar'] = True
                st.rerun()
        with col_title:
            st.title("📊 Enterprise Resource Hub")
    else:
        st.title("📊 Enterprise Resource Hub")


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

    if not selected_projects:
        return

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
            start_date = d1.date_input("From Date", key="filter_start_date", disabled=not is_time_logging_mode)
            end_date = d2.date_input("To Date", key="filter_end_date", disabled=not is_time_logging_mode)
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

    if 'processed_df' not in st.session_state:
        return

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

    # Executive KPI Strip
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

    tab_overview, tab_activities, tab_risk, tab_distribution, tab_data = st.tabs([
        "📊 Capacity & Daily Hours",
        "🕒 Recent Activities",
        "⚠️ Compliance & Risk Radar",
        "🎯 Work Distribution & Epics",
        "📋 Deep-Dive Data & Exports"
    ])

    with tab_overview:
        _render_tab_overview(filtered_df, filtered_daily_df, time_col, daily_target_hrs)

    with tab_activities:
        _render_tab_activities(filtered_activities_df)

    with tab_risk:
        _render_tab_risk(
            filtered_df,
            filtered_daily_df,
            selected_assignees,
            working_days,
            daily_target_hrs,
            stale_days_threshold,
            is_time_logging_mode,
            time_col
        )

    with tab_distribution:
        _render_tab_distribution(filtered_df, time_col)

    with tab_data:
        _render_tab_data(filtered_df, filtered_daily_df, filtered_activities_df, time_col)


def _render_tab_overview(filtered_df, filtered_daily_df, time_col, daily_target_hrs):
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


def _render_tab_activities(filtered_activities_df):
    with st.container(border=True):
        st.markdown("#### 🕒 Recent Activities Performed by Selected Resource")
        if filtered_activities_df.empty:
            st.info("No recent activities found for the selected resource(s) and criteria.")
            return

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


def _render_tab_risk(
    filtered_df,
    filtered_daily_df,
    selected_assignees,
    working_days,
    daily_target_hrs,
    stale_days_threshold,
    is_time_logging_mode,
    time_col
):
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


def _render_tab_distribution(filtered_df, time_col):
    if filtered_df.empty:
        st.info("No data available to analyze work distribution.")
        return

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


def _render_tab_data(filtered_df, filtered_daily_df, filtered_activities_df, time_col):
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
