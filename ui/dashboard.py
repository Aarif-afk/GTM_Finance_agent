"""
Main dashboard layout for the GTM Finance Intelligence Agent.

Renders the tabbed interface: Overview, GTM Model, AI Analysis,
Scenarios, and Export — with all interactive components.
"""

import json
import streamlit as st
import pandas as pd
import numpy as np
from typing import Any

from models.financial_model import (
    compute_gtm_metrics,
    get_health_status,
    get_latest_metrics_summary,
    run_scenario_projection,
    BENCHMARKS,
)
from ui.charts import (
    chart_arr_trend,
    chart_mrr_growth,
    chart_unit_economics,
    chart_ltv_cac_ratio,
    chart_regional_comparison,
    chart_sales_productivity,
    chart_nrr_trend,
    chart_scenario_comparison,
    chart_scenario_three_way,
    chart_burn_multiple,
    chart_customer_dynamics,
)


# ──────────────────────────────────────────────────────────────
# Helper: metric card with health coloring
# ──────────────────────────────────────────────────────────────
def _metric_card(label: str, value: str, health: str = "neutral", delta: str = "") -> str:
    """Generate HTML for a styled metric card.

    Args:
        label: Metric label.
        value: Formatted metric value.
        health: One of 'healthy', 'warning', 'critical', 'neutral'.
        delta: Optional delta/change string.

    Returns:
        HTML string for the metric card.
    """
    color_map = {
        "healthy": "#41B883",
        "warning": "#F5A623",
        "critical": "#E74C3C",
        "neutral": "#85CDCA",
    }
    border_color = color_map.get(health, color_map["neutral"])
    delta_html = f'<div style="font-size:12px;color:{border_color};margin-top:2px;">{delta}</div>' if delta else ""

    return f"""
    <div style="background:#16213e; padding:16px 20px; border-radius:10px;
                border-left:4px solid {border_color}; margin:4px 0;">
        <div style="color:#8892b0; font-size:12px; text-transform:uppercase;
                    letter-spacing:1px; margin-bottom:4px;">{label}</div>
        <div style="color:{border_color}; font-size:26px; font-weight:700;">{value}</div>
        {delta_html}
    </div>"""


def render_overview_tab(df: pd.DataFrame) -> None:
    """Render the Overview tab with KPI cards and key charts.

    Args:
        df: Raw GTM dataset.
    """
    metrics_df = compute_gtm_metrics(df)
    latest = get_latest_metrics_summary(df)

    # KPI cards row
    st.markdown("### 📊 Key Performance Indicators")
    cols = st.columns(5)

    kpis = [
        ("ARR", f"${latest.get('arr', 0):,.0f}", "arr"),
        ("MRR", f"${latest.get('mrr', 0):,.0f}", "mrr"),
        ("LTV:CAC", f"{latest.get('ltv_cac_ratio', 0):.1f}x", "ltv_cac_ratio"),
        ("CAC", f"${latest.get('cac', 0):,.0f}", "cac"),
        ("NRR", f"{latest.get('nrr_pct', 0):.1f}%", "nrr_pct"),
    ]

    for i, (label, value, key) in enumerate(kpis):
        health = get_health_status(latest.get(key, 0), key) if key in BENCHMARKS else "neutral"
        with cols[i]:
            st.markdown(_metric_card(label, value, health), unsafe_allow_html=True)

    # Second row of KPIs
    cols2 = st.columns(5)
    kpis2 = [
        ("MoM Growth", f"{latest.get('mom_growth_pct', 0):.1f}%", "mom_growth_pct"),
        ("Payback", f"{latest.get('payback_months', 0):.1f} mo", "payback_months"),
        ("Burn Multiple", f"{latest.get('burn_multiple', 0):.1f}x", "burn_multiple"),
        ("Sales Prod.", f"${latest.get('sales_productivity', 0):,.0f}", "sales_productivity"),
        ("Customers", f"{latest.get('cumulative_customers', 0):,.0f}", "cumulative_customers"),
    ]

    for i, (label, value, key) in enumerate(kpis2):
        health = get_health_status(latest.get(key, 0), key) if key in BENCHMARKS else "neutral"
        with cols2[i]:
            st.markdown(_metric_card(label, value, health), unsafe_allow_html=True)

    st.markdown("---")

    # Charts
    col_left, col_right = st.columns(2)
    with col_left:
        st.plotly_chart(chart_arr_trend(metrics_df), use_container_width=True)
    with col_right:
        st.plotly_chart(chart_mrr_growth(metrics_df), use_container_width=True)

    col_left2, col_right2 = st.columns(2)
    with col_left2:
        st.plotly_chart(chart_ltv_cac_ratio(metrics_df), use_container_width=True)
    with col_right2:
        st.plotly_chart(chart_regional_comparison(df), use_container_width=True)


def render_gtm_model_tab(df: pd.DataFrame) -> None:
    """Render the GTM Financial Model tab with the full metrics table.

    Args:
        df: Raw GTM dataset.
    """
    st.markdown("### 📈 Full GTM Financial Model")

    metrics_df = compute_gtm_metrics(df)

    # Display columns
    display_cols = [
        "date", "mrr", "arr", "mom_growth_pct", "yoy_growth_pct",
        "cac", "ltv", "ltv_cac_ratio", "payback_months",
        "sales_productivity", "nrr_pct", "burn_multiple",
        "new_customers", "churned_customers", "cumulative_customers",
    ]
    available_cols = [c for c in display_cols if c in metrics_df.columns]
    display_df = metrics_df[available_cols].copy()
    display_df["date"] = display_df["date"].dt.strftime("%Y-%m")

    # Style function for color coding
    def _color_cell(val: Any, col: str) -> str:
        """Return CSS color based on metric health."""
        if pd.isna(val) or col not in BENCHMARKS:
            return ""
        status = get_health_status(float(val), col)
        if status == "healthy":
            return "color: #41B883"
        elif status == "warning":
            return "color: #F5A623"
        elif status == "critical":
            return "color: #E74C3C"
        return ""

    # Apply styling
    styled = display_df.style.apply(
        lambda row: [_color_cell(row.get(c), c) for c in display_df.columns],
        axis=1,
    ).format({
        "mrr": "${:,.0f}",
        "arr": "${:,.0f}",
        "mom_growth_pct": "{:.1f}%",
        "yoy_growth_pct": "{:.1f}%",
        "cac": "${:,.0f}",
        "ltv": "${:,.0f}",
        "ltv_cac_ratio": "{:.1f}x",
        "payback_months": "{:.1f}",
        "sales_productivity": "${:,.0f}",
        "nrr_pct": "{:.1f}%",
        "burn_multiple": "{:.1f}x",
    }, na_rep="—")

    st.dataframe(styled, use_container_width=True, height=600)

    # Charts below the table
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(chart_unit_economics(metrics_df), use_container_width=True)
    with col2:
        st.plotly_chart(chart_sales_productivity(metrics_df), use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.plotly_chart(chart_nrr_trend(metrics_df), use_container_width=True)
    with col4:
        st.plotly_chart(chart_burn_multiple(metrics_df), use_container_width=True)

    st.plotly_chart(chart_customer_dynamics(metrics_df), use_container_width=True)


def render_ai_analysis_tab(df: pd.DataFrame) -> None:
    """Render the AI Strategy Agent analysis tab.

    Args:
        df: Raw GTM dataset.
    """
    st.markdown("### 🤖 AI Strategy Agent — Powered by Claude Opus")
    st.markdown(
        '<div style="background:#16213e; padding:12px 16px; border-radius:8px; margin-bottom:16px;">'
        '<span style="color:#CC785C;">⚡ The agent will autonomously call 4 analysis tools in sequence, '
        'then synthesize findings into a CFO-level executive memo.</span></div>',
        unsafe_allow_html=True,
    )

    # Check for API key
    api_key = st.session_state.get("anthropic_api_key", "")
    if not api_key:
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY", "")

    if not api_key or api_key == "your-anthropic-api-key-here":
        st.warning("⚠️ Please enter your Anthropic API key in the sidebar to run the AI agent.")
        return

    # Run button
    if st.button("🚀 Run Full GTM Analysis", type="primary", use_container_width=True):
        from agents.gtm_agent import run_agent_analysis

        # Status display
        status_container = st.container()
        steps_expander = st.expander("🔍 Agent Thinking Steps (Real-time)", expanded=True)

        step_logs = []

        def status_callback(step: str, detail: str = "") -> None:
            """Callback to show agent progress in the UI."""
            step_logs.append(f"**{step}** — {detail}")
            with steps_expander:
                for log in step_logs:
                    st.markdown(log)

        with st.spinner("🤖 Agent is analyzing your GTM data..."):
            result = run_agent_analysis(df, status_callback=status_callback)

        # Store result in session state
        st.session_state["agent_result"] = result

    # Display results if available
    if "agent_result" in st.session_state:
        result = st.session_state["agent_result"]

        # Show tool call steps
        if result.get("steps"):
            with st.expander("🔧 Tool Calls Made by Agent", expanded=False):
                for i, step in enumerate(result["steps"], 1):
                    st.markdown(f"**Step {i}: `{step['tool']}`**")
                    st.json(step.get("input", {}))
                    st.code(step.get("output_preview", ""), language="json")

        # Show the executive narrative
        st.markdown("---")
        st.markdown("### 📋 Executive Memo")
        st.markdown(
            f'<div style="background:#16213e; padding:24px; border-radius:12px; '
            f'border:1px solid #CC785C; line-height:1.7;">'
            f'{result.get("narrative", "No narrative generated.")}'
            f'</div>',
            unsafe_allow_html=True,
        )

        # Show scenario chart if data available
        scenarios_json = result.get("scenarios_json", "{}")
        if scenarios_json and scenarios_json != "{}":
            st.markdown("---")
            st.markdown("### 🔮 Scenario Projections")
            latest = get_latest_metrics_summary(df)
            current_arr = latest.get("arr", 0)
            fig = chart_scenario_three_way(scenarios_json, current_arr)
            st.plotly_chart(fig, use_container_width=True)


def render_scenarios_tab(df: pd.DataFrame) -> None:
    """Render the Interactive Scenario Planner tab.

    Args:
        df: Raw GTM dataset.
    """
    st.markdown("### 🎛️ Interactive Scenario Planner")
    st.markdown("Adjust the sliders to model different growth scenarios in real time.")

    metrics_df = compute_gtm_metrics(df)
    latest = get_latest_metrics_summary(df)

    # Sliders
    col1, col2 = st.columns(2)
    with col1:
        hc_growth = st.slider(
            "👥 Headcount Growth (%/month)", -10.0, 20.0, 3.0, 0.5,
            help="Monthly percentage increase in sales headcount",
        )
        mktg_change = st.slider(
            "📢 Marketing Spend Change (%/month)", -30.0, 50.0, 5.0, 1.0,
            help="Monthly percentage change in marketing budget",
        )
    with col2:
        churn_reduction = st.slider(
            "🔄 Churn Reduction (%/month)", -20.0, 50.0, 5.0, 1.0,
            help="Monthly percentage reduction in customer churn",
        )
        price_increase = st.slider(
            "💰 Price Increase (%/month)", -10.0, 20.0, 0.0, 0.5,
            help="Monthly percentage price increase on new contracts",
        )

    # Run projection
    projected = run_scenario_projection(
        df,
        headcount_growth_pct=hc_growth,
        marketing_change_pct=mktg_change,
        churn_reduction_pct=churn_reduction,
        price_increase_pct=price_increase,
        months_forward=12,
    )

    if projected.empty:
        st.warning("Unable to generate projections. Please check your data.")
        return

    final = projected.iloc[-1]

    # Side-by-side comparison
    st.markdown("---")
    st.markdown("### 📊 Current vs Projected (12 Months)")

    comparison_metrics = [
        ("ARR", f"${latest.get('arr', 0):,.0f}", f"${final.get('arr', 0):,.0f}"),
        ("MRR", f"${latest.get('mrr', 0):,.0f}", f"${final.get('mrr', 0):,.0f}"),
        ("LTV:CAC", f"{latest.get('ltv_cac_ratio', 0):.1f}x", f"{final.get('ltv_cac_ratio', 0):.1f}x"),
        ("CAC", f"${latest.get('cac', 0):,.0f}", f"${final.get('cac', 0):,.0f}"),
        ("Payback Period", f"{latest.get('payback_months', 0):.1f} mo", f"{final.get('payback_months', 0):.1f} mo"),
        ("Sales Productivity", f"${latest.get('sales_productivity', 0):,.0f}", f"${final.get('sales_productivity', 0):,.0f}"),
    ]

    cols = st.columns(3)
    for i, (label, current, proj) in enumerate(comparison_metrics):
        with cols[i % 3]:
            st.markdown(
                f'<div style="background:#16213e; padding:14px; border-radius:10px; margin:6px 0;">'
                f'<div style="color:#8892b0; font-size:12px; text-transform:uppercase;">{label}</div>'
                f'<div style="display:flex; justify-content:space-between; margin-top:8px;">'
                f'<div><span style="color:#E0E0E0; font-size:11px;">Current</span><br>'
                f'<span style="color:#85CDCA; font-size:18px; font-weight:600;">{current}</span></div>'
                f'<div style="color:#CC785C; font-size:20px; align-self:center;">→</div>'
                f'<div><span style="color:#E0E0E0; font-size:11px;">Projected</span><br>'
                f'<span style="color:#CC785C; font-size:18px; font-weight:600;">{proj}</span></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    # Projection chart
    st.markdown("---")
    fig = chart_scenario_comparison(metrics_df, projected, "Projected")
    st.plotly_chart(fig, use_container_width=True)

    # Projected metrics table
    with st.expander("📋 Monthly Projection Details", expanded=False):
        display_proj = projected[["month", "mrr", "arr", "cac", "ltv_cac_ratio", "payback_months"]].copy()
        st.dataframe(
            display_proj.style.format({
                "mrr": "${:,.0f}",
                "arr": "${:,.0f}",
                "cac": "${:,.0f}",
                "ltv_cac_ratio": "{:.1f}x",
                "payback_months": "{:.1f}",
            }),
            use_container_width=True,
        )


def render_export_tab(df: pd.DataFrame) -> None:
    """Render the Board-Ready Report Export tab.

    Args:
        df: Raw GTM dataset.
    """
    st.markdown("### 📥 Board-Ready Report Export")
    st.markdown(
        "Generate a professionally formatted Excel report with 4 tabs: "
        "Executive Summary, Full GTM Model, Scenario Analysis, and AI Recommendations."
    )

    # Export options
    col1, col2 = st.columns(2)
    with col1:
        company_name = st.text_input("Company Name", value="SaaS Corp", key="export_company")
    with col2:
        report_period = st.text_input("Report Period", value="FY2024-2025", key="export_period")

    if st.button("📊 Generate Board Report", type="primary", use_container_width=True):
        from exports.excel_export import generate_board_report

        with st.spinner("📝 Building your board-ready report..."):
            agent_result = st.session_state.get("agent_result", {})
            try:
                excel_buffer = generate_board_report(
                    df=df,
                    company_name=company_name,
                    report_period=report_period,
                    agent_narrative=agent_result.get("narrative", ""),
                    scenarios_json=agent_result.get("scenarios_json", "{}"),
                    recommendations_json=agent_result.get("recommendations_json", "{}"),
                )

                st.success("✅ Report generated successfully!")
                st.download_button(
                    label="⬇️ Download Excel Report",
                    data=excel_buffer.getvalue(),
                    file_name=f"GTM_Board_Report_{company_name.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"❌ Error generating report: {e}")

    # Preview what will be in the report
    with st.expander("📋 Report Preview — What's Included", expanded=True):
        st.markdown("""
        | Tab | Contents |
        |-----|----------|
        | **Executive Summary** | Key KPI metrics table with health indicators |
        | **Full GTM Model** | All 24 months of financial model data |
        | **Scenario Analysis** | Bull / Base / Bear projections for 12 months |
        | **AI Recommendations** | Agent's strategic narrative and action items |
        
        All tabs include professional formatting with color coding, borders, and conditional formatting.
        """)
