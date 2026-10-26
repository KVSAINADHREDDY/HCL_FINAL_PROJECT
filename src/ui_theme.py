"""
UI Styling and Aesthetic Design System for Streamlit
Provides custom CSS, Google Fonts, KPI Cards, and Visual Components.
"""
import streamlit as st

def apply_custom_theme():
    """Injects high-end, modern CSS into the Streamlit application."""
    custom_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        color: #0F172A;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3.5rem;
        max-width: 1350px;
    }

    /* Gradient Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #1E3A8A 100%);
        border-radius: 18px;
        padding: 30px 36px;
        color: #FFFFFF;
        box-shadow: 0 10px 25px -5px rgba(15, 23, 42, 0.25), 0 8px 10px -6px rgba(15, 23, 42, 0.2);
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .hero-banner::after {
        content: '';
        position: absolute;
        top: -60px;
        right: -60px;
        width: 200px;
        height: 200px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.35) 0%, rgba(59, 130, 246, 0) 70%);
        border-radius: 50%;
        pointer-events: none;
    }

    .hero-title {
        font-size: 2.15rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin: 0 0 8px 0;
        background: linear-gradient(180deg, #FFFFFF 0%, #E2E8F0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: #94A3B8;
        font-weight: 400;
        max-width: 780px;
        line-height: 1.55;
        margin: 0;
    }

    .hero-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(59, 130, 246, 0.18);
        border: 1px solid rgba(96, 165, 250, 0.35);
        color: #93C5FD;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 12px;
    }

    /* Metric Cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 16px;
        margin-bottom: 24px;
    }

    .metric-card {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 20px 22px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.03), 0 1px 2px rgba(15, 23, 42, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        position: relative;
    }

    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 16px -4px rgba(15, 23, 42, 0.08), 0 2px 6px -2px rgba(15, 23, 42, 0.04);
        border-color: #CBD5E1;
    }

    .metric-label {
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .metric-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F172A;
        letter-spacing: -0.02em;
        margin-bottom: 4px;
    }

    .metric-sub {
        font-size: 0.8rem;
        color: #64748B;
        display: flex;
        align-items: center;
        gap: 4px;
    }

    .metric-sub.positive { color: #16A34A; }
    .metric-sub.warning { color: #D97706; }
    .metric-sub.highlight { color: #2563EB; }

    /* Custom Callout Cards */
    .card-panel {
        background: #FFFFFF;
        border-radius: 14px;
        border: 1px solid #E2E8F0;
        padding: 22px 24px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        margin-bottom: 20px;
    }

    .card-panel-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 14px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Badges */
    .status-pill {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    .pill-success {
        background-color: #DCFCE7;
        color: #15803D;
        border: 1px solid #86EFAC;
    }

    .pill-warning {
        background-color: #FEF3C7;
        color: #B45309;
        border: 1px solid #FCD34D;
    }

    .pill-danger {
        background-color: #FEE2E2;
        color: #B91C1C;
        border: 1px solid #FCA5A5;
    }

    .pill-info {
        background-color: #E0E7FF;
        color: #3730A3;
        border: 1px solid #C7D2FE;
    }

    /* Tab enhancements */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F1F5F9;
        padding: 6px;
        border-radius: 12px;
        margin-bottom: 20px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 18px;
        font-weight: 600;
        font-size: 0.88rem;
        color: #475569;
        background-color: transparent;
        border: none !important;
        transition: all 0.2s ease;
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #1D4ED8 !important;
        box-shadow: 0 2px 4px rgba(15, 23, 42, 0.08);
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.9rem;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
        padding: 0.5rem 1.2rem;
    }

    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }

    /* Code & formulas */
    .formula-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2563EB;
        border-radius: 8px;
        padding: 12px 16px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.88rem;
        color: #1E293B;
        margin: 10px 0;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def render_hero_header(title="Employee Overtime Cost Forecasting System",
                       subtitle="Workforce analytics, overtime driver discovery, and machine-learning powered payroll projections.",
                       status_badge="SRS v1.0 • Antigravity Verified"):
    """Renders the top hero banner."""
    html = f"""
    <div class="hero-banner">
        <div class="hero-badge">{status_badge}</div>
        <h1 class="hero-title">{title}</h1>
        <p class="hero-subtitle">{subtitle}</p>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_kpi_card(label: str, value: str, subtext: str = "", trend_type: str = "highlight", icon: str = ""):
    """Renders an individual high-aesthetic metric card."""
    icon_html = f"<span>{icon}</span>" if icon else ""
    html = f"""
    <div class="metric-card">
        <div class="metric-label">
            <span>{label}</span>
            {icon_html}
        </div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub {trend_type}">{subtext}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
