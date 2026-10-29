import streamlit as st


def inject_ambient_background():
    """Injects floating ambient background blobs into the Streamlit app."""
    st.markdown("""
        <div class="ambient-blob blob-1"></div>
        <div class="ambient-blob blob-2"></div>
        <div class="ambient-blob blob-3"></div>
    """, unsafe_allow_html=True)


def apply_custom_theme():
    """Applies the 2026 Modern SaaS Glassmorphism Light Mode CSS theme."""
    st.markdown("""
    <style>
        /* Force Light Mode & Hide Theme Toggle */
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


        
        /* Hamburger Toggle Button Styling */
        button[key="sidebar_hamburger_collapse_btn"],
        button[key="sidebar_hamburger_expand_btn"] {
            font-size: 1.3rem !important;
            font-weight: 700 !important;
            line-height: 1 !important;
            padding: 0.35rem 0.6rem !important;
            min-height: 2.3rem !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }

        /* Ensure Streamlit native collapsed control is also styled as Hamburger */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: fixed !important;
            top: 12px !important;
            left: 14px !important;
            z-index: 9999999 !important;
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            padding: 4px 10px !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.15) !important;
            align-items: center !important;
            cursor: pointer !important;
        }

        /* Ensure sidebar collapse/expand controls are always accessible, prominent and clickable */
        [data-testid="collapsedControl"],
        [data-testid="stSidebarCollapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: fixed !important;
            top: 12px !important;
            left: 14px !important;
            z-index: 9999999 !important;
            background: rgba(255, 255, 255, 0.95) !important;
            backdrop-filter: blur(12px) !important;
            -webkit-backdrop-filter: blur(12px) !important;
            border: 1px solid #cbd5e1 !important;
            border-radius: 12px !important;
            padding: 4px 10px !important;
            box-shadow: 0 4px 14px rgba(37, 99, 235, 0.15) !important;
            align-items: center !important;
            cursor: pointer !important;
        }

        [data-testid="collapsedControl"] button,
        [data-testid="stSidebarCollapsedControl"] button {
            color: #1e293b !important;
        }

        [data-testid="collapsedControl"]::after,
        [data-testid="stSidebarCollapsedControl"]::after {
            content: " ☰ Sidebar";
            font-family: 'Outfit', sans-serif !important;
            font-size: 0.82rem !important;
            font-weight: 600 !important;
            color: #2563eb !important;
            margin-left: 6px !important;
            cursor: pointer !important;
        }

        button[data-testid="stSidebarCollapseButton"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            z-index: 999999 !important;
        }


        /* Spinner Color Match */
        .stSpinner > div > div { border-color: #3b82f6 transparent transparent transparent; }

        
    </style>
    """, unsafe_allow_html=True)


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
