# 📊 Enterprise Resource Hub (Modular Jira Resource Tracker)

A modular Streamlit application for tracking Jira resource capacity, daily logged hours, recent activities, timesheet compliance, and portfolio risks.

## 📁 Project Architecture

```text
jira_resource_tracker/
├── app.py                      # Main Streamlit entry point & routing (~30 lines)
├── requirements.txt            # Project dependencies
├── .env.example                # Environment variable template
├── README.md                   # Documentation & setup guide
├── config/
│   ├── __init__.py
│   └── theme.py                # Glassmorphism CSS theme, ambient blobs & animations
├── services/
│   ├── __init__.py
│   ├── network.py              # Internet/DNS/socket connectivity checks & offline banners
│   └── jira_service.py         # Jira API authentication, JQL builder & issue fetching
├── processors/
│   ├── __init__.py
│   ├── data_processor.py       # Worklog, daily hours, recent activities & risk calculations
│   └── exporter.py             # Multi-sheet Excel (.xlsx) & CSV report generators
└── views/
    ├── __init__.py
    ├── login_view.py           # Login screen (Manual Entry & JSON Configuration)
    ├── sidebar_view.py         # Sidebar connection status, benchmark rules & cache controls
    └── dashboard_view.py       # Executive KPIs & 5-tab analytics workspace
```

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure environment variables (optional):**
   Copy `.env.example` to `.env` and fill in your Jira credentials.
3. **Run the application:**
   ```bash
   streamlit run app.py
   ```
