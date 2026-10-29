import streamlit as st
from jira import JIRA, JIRAError
from services.network import check_internet_connection, is_network_error


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
    """Fetches and caches assignees and statuses for the selected Jira projects."""
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
    """Builds the JQL query string based on selected filters and tracking mode."""
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
    """Fetches Jira issues matching the JQL query with session caching and network error handling."""
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
