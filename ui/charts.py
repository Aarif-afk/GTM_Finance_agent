"""
Plotly interactive chart components for the GTM Finance dashboard.

All charts use a dark theme with the Anthropic-inspired color palette:
  Primary: #CC785C  |  Background: #1a1a2e  |  Cards: #16213e
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Color palette
# ──────────────────────────────────────────────────────────────
COLORS = {
    "primary": "#CC785C",
    "secondary": "#E8A87C",
    "accent": "#85CDCA",
    "success": "#41B883",
    "warning": "#F5A623",
    "danger": "#E74C3C",
    "bg": "#1a1a2e",
    "card": "#16213e",
    "text": "#E0E0E0",
    "grid": "#2a2a4a",
    "series": ["#CC785C", "#85CDCA", "#E8A87C", "#41B883", "#F5A623", "#9B59B6", "#3498DB"],
}

LAYOUT_DEFAULTS = dict(
    paper_bgcolor=COLORS["bg"],
    plot_bgcolor=COLORS["card"],
    font=dict(color=COLORS["text"], family="Inter, sans-serif"),
    margin=dict(l=50, r=30, t=50, b=40),
    xaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    yaxis=dict(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"]),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    hoverlabel=dict(bgcolor=COLORS["card"], font_size=12),
)


def _apply_layout(fig: go.Figure, title: str = "", height: int = 400) -> go.Figure:
    """Apply consistent dark-theme styling to a figure.

    Args:
        fig: Plotly figure to style.
        title: Chart title.
        height: Chart height in pixels.

    Returns:
        Styled figure.
    """
    fig.update_layout(
        title=dict(text=title, font=dict(size=16, color=COLORS["text"])),
        height=height,
        **LAYOUT_DEFAULTS,
    )
    return fig


def chart_arr_trend(metrics_df: pd.DataFrame) -> go.Figure:
    """Create an ARR trend line chart with area fill.

    Args:
        metrics_df: Monthly metrics DataFrame with 'date' and 'arr' columns.

    Returns:
        Plotly figure.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=metrics_df["date"],
        y=metrics_df["arr"],
        mode="lines+markers",
        name="ARR",
        line=dict(color=COLORS["primary"], width=3),
        marker=dict(size=6),
        fill="tozeroy",
        fillcolor="rgba(204, 120, 92, 0.15)",
        hovertemplate="<b>%{x|%b %Y}</b><br>ARR: $%{y:,.0f}<extra></extra>",
    ))
    return _apply_layout(fig, "📈 Annual Recurring Revenue (ARR) Trend")


def chart_mrr_growth(metrics_df: pd.DataFrame) -> go.Figure:
    """Create a dual-axis chart showing MRR and MoM growth rate.

    Args:
        metrics_df: Monthly metrics DataFrame.

    Returns:
        Plotly figure.
    """
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Bar(
            x=metrics_df["date"],
            y=metrics_df["mrr"],
            name="MRR ($)",
            marker_color=COLORS["primary"],
            opacity=0.7,
            hovertemplate="MRR: $%{y:,.0f}<extra></extra>",
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=metrics_df["date"],
            y=metrics_df["mom_growth_pct"],
            name="MoM Growth %",
            line=dict(color=COLORS["accent"], width=2),
            mode="lines+markers",
            marker=dict(size=5),
            hovertemplate="MoM: %{y:.1f}%<extra></extra>",
        ),
        secondary_y=True,
    )

    fig.update_yaxes(title_text="MRR ($)", secondary_y=False, gridcolor=COLORS["grid"])
    fig.update_yaxes(title_text="MoM Growth %", secondary_y=True, gridcolor=COLORS["grid"])
    return _apply_layout(fig, "📊 MRR & Month-over-Month Growth")


def chart_unit_economics(metrics_df: pd.DataFrame) -> go.Figure:
    """Create a multi-line chart of CAC, LTV, and ARPU trends.

    Args:
        metrics_df: Monthly metrics DataFrame.

    Returns:
        Plotly figure.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=metrics_df["date"], y=metrics_df["ltv"],
        name="LTV", line=dict(color=COLORS["success"], width=2),
        hovertemplate="LTV: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=metrics_df["date"], y=metrics_df["cac"],
        name="CAC", line=dict(color=COLORS["danger"], width=2),
        hovertemplate="CAC: $%{y:,.0f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=metrics_df["date"], y=metrics_df["arpu"],
        name="ARPU", line=dict(color=COLORS["secondary"], width=2, dash="dot"),
        hovertemplate="ARPU: $%{y:,.0f}<extra></extra>",
    ))

    return _apply_layout(fig, "💰 Unit Economics — LTV vs CAC vs ARPU")


def chart_ltv_cac_ratio(metrics_df: pd.DataFrame) -> go.Figure:
    """Create an LTV:CAC ratio chart with healthy threshold line.

    Args:
        metrics_df: Monthly metrics DataFrame.

    Returns:
        Plotly figure.
    """
    fig = go.Figure()

    # Color bars based on health
    colors = [
        COLORS["success"] if v >= 3.0 else COLORS["warning"] if v >= 2.0 else COLORS["danger"]
        for v in metrics_df["ltv_cac_ratio"].fillna(0)
    ]

    fig.add_trace(go.Bar(
        x=metrics_df["date"],
        y=metrics_df["ltv_cac_ratio"],
        marker_color=colors,
        name="LTV:CAC",
        hovertemplate="<b>%{x|%b %Y}</b><br>LTV:CAC: %{y:.1f}x<extra></extra>",
    ))

    # Healthy threshold line
    fig.add_hline(
        y=3.0, line_dash="dash", line_color=COLORS["success"],
        annotation_text="3.0x Healthy Threshold",
        annotation_font_color=COLORS["success"],
    )

    return _apply_layout(fig, "⚖️ LTV:CAC Ratio (Target: >3.0x)")


def chart_regional_comparison(df: pd.DataFrame) -> go.Figure:
    """Create a grouped bar chart comparing key metrics by region.

    Args:
        df: Raw GTM dataset.

    Returns:
        Plotly figure.
    """
    regional = df.groupby("region").agg(
        revenue=("revenue", "sum"),
        new_customers=("new_customers", "sum"),
        marketing_spend=("marketing_spend", "sum"),
    ).reset_index()

    regional["cac"] = regional["marketing_spend"] / regional["new_customers"].clip(lower=1)

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=("Total Revenue by Region", "CAC by Region"),
    )

    fig.add_trace(go.Bar(
        x=regional["region"], y=regional["revenue"],
        marker_color=COLORS["series"][:len(regional)],
        name="Revenue",
        hovertemplate="$%{y:,.0f}<extra></extra>",
    ), row=1, col=1)

    fig.add_trace(go.Bar(
        x=regional["region"], y=regional["cac"],
        marker_color=COLORS["series"][:len(regional)],
        name="CAC",
        showlegend=False,
        hovertemplate="$%{y:,.0f}<extra></extra>",
    ), row=1, col=2)

    fig.update_layout(showlegend=False)
    return _apply_layout(fig, "🌍 Regional Performance Comparison", height=380)


def chart_sales_productivity(metrics_df: pd.DataFrame) -> go.Figure:
    """Create a sales productivity trend chart.

    Args:
        metrics_df: Monthly metrics DataFrame.

    Returns:
        Plotly figure.
    """
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=metrics_df["date"],
        y=metrics_df["sales_productivity"],
        mode="lines+markers",
        name="Revenue / Headcount",
        line=dict(color=COLORS["accent"], width=2),
        fill="tozeroy",
        fillcolor="rgba(133, 205, 202, 0.1)",
        hovertemplate="<b>%{x|%b %Y}</b><br>Productivity: $%{y:,.0f}<extra></extra>",
    ))
    return _apply_layout(fig, "👥 Sales Productivity (Revenue per Headcount)")


def chart_nrr_trend(metrics_df: pd.DataFrame) -> go.Figure:
    """Create a Net Revenue Retention trend chart.

    Args:
        metrics_df: Monthly metrics DataFrame.

    Returns:
        Plotly figure.
    """
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=metrics_df["date"],
        y=metrics_df["nrr_pct"],
        mode="lines+markers",
        name="NRR %",
        line=dict(color=COLORS["primary"], width=3),
        marker=dict(size=6),
        hovertemplate="<b>%{x|%b %Y}</b><br>NRR: %{y:.1f}%<extra></extra>",
    ))

    fig.add_hline(
        y=100, line_dash="dot", line_color=COLORS["danger"],
        annotation_text="100% Break-even",
        annotation_font_color=COLORS["danger"],
    )
    fig.add_hline(
        y=110, line_dash="dash", line_color=COLORS["success"],
        annotation_text="110% Target",
        annotation_font_color=COLORS["success"],
    )

    return _apply_layout(fig, "🔄 Net Revenue Retention (NRR)")


def chart_scenario_comparison(
    current_metrics: pd.DataFrame,
    projected_metrics: pd.DataFrame,
    scenario_label: str = "Projected",
) -> go.Figure:
    """Create a side-by-side comparison of current vs projected metrics.

    Args:
        current_metrics: Current monthly metrics DataFrame.
        projected_metrics: Projected metrics DataFrame.
        scenario_label: Label for the projection scenario.

    Returns:
        Plotly figure.
    """
    fig = go.Figure()

    # Current ARR trend
    fig.add_trace(go.Scatter(
        x=current_metrics["date"],
        y=current_metrics["arr"],
        mode="lines",
        name="Current ARR",
        line=dict(color=COLORS["text"], width=2),
        hovertemplate="Current: $%{y:,.0f}<extra></extra>",
    ))

    # Projected ARR
    if "date" in projected_metrics.columns and "arr" in projected_metrics.columns:
        fig.add_trace(go.Scatter(
            x=projected_metrics["date"],
            y=projected_metrics["arr"],
            mode="lines+markers",
            name=f"{scenario_label} ARR",
            line=dict(color=COLORS["primary"], width=3, dash="dash"),
            marker=dict(size=6),
            hovertemplate=f"{scenario_label}: $%{{y:,.0f}}<extra></extra>",
        ))

    return _apply_layout(fig, f"📊 Current vs {scenario_label} — ARR Trajectory")


def chart_scenario_three_way(scenarios_json: str, current_arr: float = 0) -> go.Figure:
    """Create a Bull/Base/Bear scenario comparison chart.

    Args:
        scenarios_json: JSON string with scenario projections.
        current_arr: Current ARR for the starting point.

    Returns:
        Plotly figure.
    """
    import json
    scenarios = json.loads(scenarios_json) if isinstance(scenarios_json, str) else scenarios_json

    fig = go.Figure()

    scenario_colors = {
        "bull": COLORS["success"],
        "base": COLORS["primary"],
        "bear": COLORS["danger"],
    }
    scenario_labels = {
        "bull": "🐂 Bull Case",
        "base": "📊 Base Case",
        "bear": "🐻 Bear Case",
    }

    for key in ["bull", "base", "bear"]:
        if key not in scenarios:
            continue
        trajectory = scenarios[key].get("monthly_trajectory", [])
        if not trajectory:
            continue

        months = [0] + [t["month"] for t in trajectory]
        arr_values = [current_arr] + [t["arr"] for t in trajectory]

        fig.add_trace(go.Scatter(
            x=months,
            y=arr_values,
            mode="lines+markers",
            name=scenario_labels.get(key, key),
            line=dict(color=scenario_colors.get(key, COLORS["text"]), width=3),
            marker=dict(size=5),
            hovertemplate=f"{scenario_labels.get(key, key)}<br>Month %{{x}}: $%{{y:,.0f}}<extra></extra>",
        ))

    fig.update_xaxes(title_text="Months from Now", dtick=1)
    fig.update_yaxes(title_text="ARR ($)")
    return _apply_layout(fig, "🔮 12-Month Scenario Projections — ARR", height=450)


def chart_burn_multiple(metrics_df: pd.DataFrame) -> go.Figure:
    """Create a burn multiple trend chart.

    Args:
        metrics_df: Monthly metrics DataFrame.

    Returns:
        Plotly figure.
    """
    valid = metrics_df[metrics_df["burn_multiple"].notna() & (metrics_df["burn_multiple"] < 20)]

    fig = go.Figure()
    colors = [
        COLORS["success"] if v <= 2 else COLORS["warning"] if v <= 3 else COLORS["danger"]
        for v in valid["burn_multiple"]
    ]

    fig.add_trace(go.Bar(
        x=valid["date"],
        y=valid["burn_multiple"],
        marker_color=colors,
        name="Burn Multiple",
        hovertemplate="<b>%{x|%b %Y}</b><br>Burn Multiple: %{y:.1f}x<extra></extra>",
    ))

    fig.add_hline(
        y=2.0, line_dash="dash", line_color=COLORS["success"],
        annotation_text="2.0x Target",
        annotation_font_color=COLORS["success"],
    )

    return _apply_layout(fig, "🔥 Burn Multiple (Target: <2.0x)")


def chart_customer_dynamics(metrics_df: pd.DataFrame) -> go.Figure:
    """Create a stacked area chart of new vs churned customers.

    Args:
        metrics_df: Monthly metrics DataFrame.

    Returns:
        Plotly figure.
    """
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=metrics_df["date"],
        y=metrics_df["new_customers"],
        name="New Customers",
        marker_color=COLORS["success"],
        opacity=0.8,
        hovertemplate="New: %{y}<extra></extra>",
    ))

    fig.add_trace(go.Bar(
        x=metrics_df["date"],
        y=-metrics_df["churned_customers"],
        name="Churned Customers",
        marker_color=COLORS["danger"],
        opacity=0.8,
        hovertemplate="Churned: %{y}<extra></extra>",
    ))

    fig.add_trace(go.Scatter(
        x=metrics_df["date"],
        y=metrics_df["cumulative_customers"],
        name="Cumulative Customers",
        line=dict(color=COLORS["accent"], width=2),
        yaxis="y2",
        hovertemplate="Total: %{y:,.0f}<extra></extra>",
    ))

    fig.update_layout(
        barmode="relative",
        yaxis2=dict(
            overlaying="y", side="right", title="Cumulative",
            gridcolor=COLORS["grid"],
        ),
    )

    return _apply_layout(fig, "👥 Customer Dynamics — Acquisition vs Churn")
