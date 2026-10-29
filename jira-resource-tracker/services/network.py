import html
import socket
from urllib.parse import urlparse
import requests
import urllib3
import streamlit as st


def check_internet_connection(target_url=None, timeout=3.5):
    """
    Checks whether internet / network connectivity is available.
    1. If a target_url (e.g., Jira server URL) is provided, verifies DNS resolution and TCP reachability.
    2. Otherwise checks reachability against reliable public DNS endpoints (8.8.8.8:53, 1.1.1.1:53).
    Returns (is_connected: bool, reason: str).
    """
    if target_url:
        host = None
        try:
            parsed = urlparse(target_url if "://" in target_url else f"https://{target_url}")
            host = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == "https" else 80)
            if host:
                socket.getaddrinfo(host, port)
                with socket.create_connection((host, port), timeout=timeout):
                    return True, "Connected"
        except socket.gaierror:
            return False, f"Unable to resolve host '{host or target_url}'. Please check your internet connection, DNS, or VPN."
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
