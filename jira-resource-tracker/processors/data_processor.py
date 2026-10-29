from datetime import datetime, timedelta
import pandas as pd
import streamlit as st


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


def process_issues_to_dataframe(
    jira_client,
    issues,
    start_date,
    end_date,
    is_time_logging_mode,
    base_url="",
    stale_days_threshold=5
):
    """
    Processes raw Jira issues into three structured DataFrames:
    1. df_main: Resource capacity, estimates, logged hours, epic rollups, and health flags.
    2. df_daily: Daily worklog hours per resource and ticket.
    3. df_activities: Chronological feed of worklogs, comments, changelog updates, and active statuses.
    """
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
