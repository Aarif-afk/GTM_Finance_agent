"""
GTM Finance Intelligence Agent — Main Streamlit Application

A multi-agent AI system that automates Go-To-Market financial
analysis for SaaS/Tech companies, powered by Claude Opus.

Run with:  streamlit run app.py

Built by Arif Hossain — Finance Technologist | AI-Driven Finance Leader
"""

import sys
import os

# Ensure project root is on the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GTM Finance Intelligence Agent",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────
# Dark theme CSS — Bloomberg-terminal-inspired
# ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Main backgrounds */
    .stApp { background-color: #1a1a2e; }
    [data-testid="stSidebar"] { background-color: #0f0f23; }
    [data-testid="stHeader"] { background-color: #1a1a2e; }

    /* Text */
    .stApp, .stMarkdown, p, span, label, .stTextInput label {
        color: #E0E0E0 !important;
    }
    h1, h2, h3 { color: #CC785C !important; }

    /* Cards, inputs, containers */
    [data-testid="stMetricValue"] { color: #CC785C !important; }
    .stTextInput input, .stSelectbox select, .stTextArea textarea {
        background-color: #16213e !important;
        color: #E0E0E0 !important;
        border-color: #2a2a4a !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #16213e;
        border-radius: 10px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent;
        color: #8892b0;
        border-radius: 8px;
        padding: 8px 20px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #CC785C !important;
        color: #FFFFFF !important;
    }

    /* Buttons */
    .stButton button {
        background-color: #CC785C !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    .stButton button:hover {
        background-color: #E8A87C !important;
    }

    /* Download button */
    .stDownloadButton button {
        background-color: #41B883 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
    }

    /* DataFrames */
    [data-testid="stDataFrame"] {
        background-color: #16213e;
        border-radius: 10px;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: #16213e !important;
        color: #E0E0E0 !important;
        border-radius: 8px;
    }

    /* Slider */
    .stSlider [data-baseweb="slider"] {
        background-color: #16213e;
    }

    /* Spinner */
    .stSpinner > div { color: #CC785C !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: #1a1a2e; }
    ::-webkit-scrollbar-thumb { background: #CC785C; border-radius: 4px; }

    /* File uploader */
    [data-testid="stFileUploader"] {
        background-color: #16213e;
        border: 2px dashed #CC785C;
        border-radius: 10px;
        padding: 10px;
    }

    /* Hide default Streamlit footer */
    footer { visibility: hidden; }

    /* Custom footer */
    .custom-footer {
        position: fixed; bottom: 0; left: 0; right: 0;
        background: #0f0f23; padding: 8px 0; text-align: center;
        color: #8892b0; font-size: 12px; z-index: 999;
        border-top: 1px solid #2a2a4a;
    }
</style>
""", unsafe_allow_html=True)


# ──────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────
def _render_sidebar() -> None:
    """Render the sidebar with branding, API config, and data loading."""
    with st.sidebar:
        # Branding
        st.markdown(
            '<h1 style="color:#CC785C; font-size:22px; margin-bottom:0;">'
            '🚀 GTM Finance Agent</h1>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<p style="color:#8892b0; font-size:12px; margin-top:0;">'
            'AI-Powered GTM Financial Intelligence</p>',
            unsafe_allow_html=True,
        )
        st.markdown("---")

        # API Key
        st.markdown("### 🔑 API Configuration")
        api_key_input = st.text_input(
            "Anthropic API Key",
            type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="Enter your Anthropic API key. Get one at console.anthropic.com",
            key="api_key_input",
        )
        if api_key_input:
            st.session_state["anthropic_api_key"] = api_key_input
            os.environ["ANTHROPIC_API_KEY"] = api_key_input

        st.markdown("---")

        # Data loading
        st.markdown("### 📁 Data Source")

        data_source = st.radio(
            "Choose data source:",
            ["📊 Demo Mode (24 months)", "📤 Upload CSV"],
            index=0,
            key="data_source",
        )

        if data_source == "📊 Demo Mode (24 months)":
            if st.button("🚀 Load Demo Data", use_container_width=True, key="load_demo"):
                from data.demo_data import generate_demo_data
                st.session_state["gtm_data"] = generate_demo_data()
                st.success("✅ Demo data loaded — 24 months, 3 regions, 2 products")
                st.rerun()
        else:
            uploaded_file = st.file_uploader(
                "Upload your GTM data CSV",
                type=["csv"],
                help="Required columns: date, region, product, revenue, deals_closed, "
                     "sales_headcount, marketing_spend, new_customers, churned_customers",
            )
            if uploaded_file is not None:
                try:
                    df = pd.read_csv(uploaded_file)
                    from data.demo_data import validate_uploaded_data
                    is_valid, error_msg = validate_uploaded_data(df)
                    if is_valid:
                        df["date"] = pd.to_datetime(df["date"])
                        st.session_state["gtm_data"] = df
                        st.success(f"✅ Data loaded — {len(df)} rows")
                        st.rerun()
                    else:
                        st.error(f"❌ {error_msg}")
                except Exception as e:
                    st.error(f"❌ Error reading CSV: {e}")

        # Data status
        if "gtm_data" in st.session_state:
            df = st.session_state["gtm_data"]
            st.markdown("---")
            st.markdown("### 📋 Data Summary")
            st.markdown(
                f'<div style="background:#16213e; padding:10px; border-radius:8px; font-size:13px;">'
                f'<b style="color:#CC785C;">Rows:</b> {len(df):,}<br>'
                f'<b style="color:#CC785C;">Date Range:</b> {df["date"].min().strftime("%b %Y")} — '
                f'{df["date"].max().strftime("%b %Y")}<br>'
                f'<b style="color:#CC785C;">Regions:</b> {", ".join(df["region"].unique())}<br>'
                f'<b style="color:#CC785C;">Products:</b> {", ".join(df["product"].unique())}'
                f'</div>',
                unsafe_allow_html=True,
            )


# ──────────────────────────────────────────────────────────────
# Main content
# ──────────────────────────────────────────────────────────────
def _render_main() -> None:
    """Render the main content area with tabs."""
    # Header
    st.markdown(
        '<div style="text-align:center; padding:10px 0 20px 0;">'
        '<h1 style="color:#CC785C; font-size:32px; margin-bottom:4px;">'
        '🚀 GTM Finance Intelligence Agent</h1>'
        '<p style="color:#8892b0; font-size:14px;">'
        'Multi-Agent AI System for Go-To-Market Financial Analysis '
        '| Powered by Claude Opus</p></div>',
        unsafe_allow_html=True,
    )

    if "gtm_data" not in st.session_state:
        # Landing page
        st.markdown(
            '<div style="background:#16213e; padding:40px; border-radius:16px; '
            'text-align:center; margin:40px auto; max-width:700px; '
            'border:1px solid #CC785C;">'
            '<h2 style="color:#CC785C;">Welcome to GTM Finance Agent</h2>'
            '<p style="color:#E0E0E0; font-size:16px; line-height:1.8;">'
            'This AI-powered dashboard automates the work of a '
            'Senior Finance & Strategy GTM Manager.<br><br>'
            '👈 Use the sidebar to <b style="color:#CC785C;">load demo data</b> '
            'or <b style="color:#CC785C;">upload your CSV</b> to get started.</p>'
            '<div style="margin-top:24px; padding:16px; background:#1a1a2e; '
            'border-radius:10px; text-align:left;">'
            '<p style="color:#85CDCA; font-size:13px; margin:4px 0;">✅ Automated GTM Financial Modelling</p>'
            '<p style="color:#85CDCA; font-size:13px; margin:4px 0;">✅ AI Strategy Agent with 4 specialized tools</p>'
            '<p style="color:#85CDCA; font-size:13px; margin:4px 0;">✅ Interactive Scenario Planning</p>'
            '<p style="color:#85CDCA; font-size:13px; margin:4px 0;">✅ Board-Ready Excel Export</p>'
            '<p style="color:#85CDCA; font-size:13px; margin:4px 0;">✅ Natural Language Data Chat</p>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        return

    df = st.session_state["gtm_data"]

    # Tabbed layout
    from ui.dashboard import (
        render_overview_tab,
        render_gtm_model_tab,
        render_ai_analysis_tab,
        render_scenarios_tab,
        render_export_tab,
    )

    tabs = st.tabs([
        "📊 Overview",
        "📈 GTM Model",
        "🤖 AI Analysis",
        "🎛️ Scenarios",
        "📥 Export",
    ])

    with tabs[0]:
        render_overview_tab(df)

    with tabs[1]:
        render_gtm_model_tab(df)

    with tabs[2]:
        render_ai_analysis_tab(df)

    with tabs[3]:
        render_scenarios_tab(df)

    with tabs[4]:
        render_export_tab(df)


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────
def main() -> None:
    """Main application entry point."""
    _render_sidebar()

    # Chat sidebar (below data controls)
    df = st.session_state.get("gtm_data")
    from ui.chat import render_chat_sidebar
    render_chat_sidebar(df)

    _render_main()

    # Footer
    st.markdown(
        '<div class="custom-footer">'
        'Built by <b style="color:#CC785C;">Arif Hossain</b> — '
        'Finance Technologist | AI-Driven Finance Leader'
        '</div>',
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
