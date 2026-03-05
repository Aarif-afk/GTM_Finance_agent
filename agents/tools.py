"""
Agent tool functions for the GTM Finance Intelligence Agent.

Four tools that the Claude Opus agent can call in its agentic loop:
1. analyze_unit_economics  — structured JSON of all GTM metrics
2. identify_risks          — flags metrics below benchmark thresholds
3. generate_recommendations — CFO-level strategic recommendations
4. build_scenario_model    — Bull / Base / Bear 12-month projections
"""

import json
import pandas as pd
import numpy as np
from typing import Any

from models.financial_model import (
    compute_gtm_metrics,
    compute_regional_metrics,
    compute_product_metrics,
    get_health_status,
    get_latest_metrics_summary,
    run_scenario_projection,
    BENCHMARKS,
)


def analyze_unit_economics(df: pd.DataFrame) -> str:
    """Compute all GTM unit economics and return structured JSON.

    Args:
        df: Raw GTM dataset.

    Returns:
        JSON string with comprehensive unit economics analysis.
    """
    metrics_df = compute_gtm_metrics(df)
    latest = get_latest_metrics_summary(df)

    # Trend data (last 6 months)
    recent = metrics_df.tail(6)
    trends = {}
    for col in ["mrr", "arr", "cac", "ltv_cac_ratio", "nrr_pct", "burn_multiple"]:
        if col in recent.columns:
            values = recent[col].dropna().tolist()
            trends[col] = {
                "values": [round(v, 2) if isinstance(v, float) else v for v in values],
                "direction": "improving" if len(values) >= 2 and values[-1] > values[-2] else "declining",
            }

    # Regional breakdown
    regional = compute_regional_metrics(df)
    regional_data = {}
    for _, row in regional.iterrows():
        region = row.get("region", "Unknown")
        regional_data[region] = {
            "mrr": round(float(row.get("mrr", 0)), 2),
            "cac": round(float(row.get("cac", 0)), 2),
            "ltv_cac_ratio": round(float(row.get("ltv_cac_ratio", 0)), 2),
            "nrr_pct": round(float(row.get("nrr_pct", 0)), 2),
        }

    result = {
        "analysis_type": "unit_economics",
        "latest_metrics": latest,
        "trends_6m": trends,
        "regional_breakdown": regional_data,
        "total_months_analyzed": len(metrics_df),
        "data_start": metrics_df["date"].min().strftime("%Y-%m-%d") if not metrics_df.empty else None,
        "data_end": metrics_df["date"].max().strftime("%Y-%m-%d") if not metrics_df.empty else None,
    }

    return json.dumps(result, default=str, indent=2)


def identify_risks(metrics_json: str) -> str:
    """Identify GTM metrics that fall below healthy benchmark thresholds.

    Args:
        metrics_json: JSON string from analyze_unit_economics output.

    Returns:
        JSON string listing all identified risks with severity levels.
    """
    data = json.loads(metrics_json)
    latest = data.get("latest_metrics", {})
    trends = data.get("trends_6m", {})

    risks = []

    # Check each benchmarked metric
    metric_checks = [
        ("ltv_cac_ratio", "LTV:CAC Ratio", latest.get("ltv_cac_ratio")),
        ("cac", "Customer Acquisition Cost", latest.get("cac")),
        ("payback_months", "Payback Period", latest.get("payback_months")),
        ("nrr_pct", "Net Revenue Retention", latest.get("nrr_pct")),
        ("burn_multiple", "Burn Multiple", latest.get("burn_multiple")),
        ("mom_growth_pct", "Month-over-Month Growth", latest.get("mom_growth_pct")),
    ]

    for key, label, value in metric_checks:
        if value is None or (isinstance(value, float) and np.isnan(value)):
            continue

        status = get_health_status(float(value), key)
        bench = BENCHMARKS.get(key, {})

        if status == "critical":
            risks.append({
                "metric": label,
                "current_value": round(float(value), 2),
                "healthy_threshold": bench.get("healthy"),
                "severity": "HIGH",
                "status": "critical",
                "recommendation_area": f"Immediate action needed on {label}",
            })
        elif status == "warning":
            risks.append({
                "metric": label,
                "current_value": round(float(value), 2),
                "healthy_threshold": bench.get("healthy"),
                "severity": "MEDIUM",
                "status": "warning",
                "recommendation_area": f"Monitor and improve {label}",
            })

    # Check trend deterioration
    for metric_key, trend_data in trends.items():
        if trend_data.get("direction") == "declining" and metric_key in [
            "mrr", "ltv_cac_ratio", "nrr_pct"
        ]:
            risks.append({
                "metric": f"{metric_key} trend",
                "current_value": trend_data["values"][-1] if trend_data["values"] else None,
                "severity": "MEDIUM",
                "status": "declining_trend",
                "recommendation_area": f"Reverse declining trend in {metric_key}",
            })

    # Check regional imbalances
    regional = data.get("regional_breakdown", {})
    if regional:
        ltv_cac_values = {r: d.get("ltv_cac_ratio", 0) for r, d in regional.items()}
        if ltv_cac_values:
            worst_region = min(ltv_cac_values, key=ltv_cac_values.get)
            if ltv_cac_values[worst_region] < 3.0:
                risks.append({
                    "metric": f"Regional LTV:CAC — {worst_region}",
                    "current_value": ltv_cac_values[worst_region],
                    "healthy_threshold": 3.0,
                    "severity": "MEDIUM",
                    "status": "underperforming_region",
                    "recommendation_area": f"Improve unit economics in {worst_region}",
                })

    result = {
        "total_risks_identified": len(risks),
        "high_severity_count": sum(1 for r in risks if r["severity"] == "HIGH"),
        "medium_severity_count": sum(1 for r in risks if r["severity"] == "MEDIUM"),
        "risks": sorted(risks, key=lambda x: 0 if x["severity"] == "HIGH" else 1),
    }

    return json.dumps(result, default=str, indent=2)


def generate_recommendations(risks_json: str, metrics_json: str) -> str:
    """Generate CFO-level strategic recommendations based on risks and metrics.

    Args:
        risks_json: JSON string from identify_risks output.
        metrics_json: JSON string from analyze_unit_economics output.

    Returns:
        JSON string with prioritized strategic recommendations.
    """
    risks = json.loads(risks_json)
    metrics = json.loads(metrics_json)
    latest = metrics.get("latest_metrics", {})

    recommendations = []

    # LTV:CAC recommendations
    ltv_cac = latest.get("ltv_cac_ratio", 0)
    if ltv_cac and ltv_cac < 3.0:
        recommendations.append({
            "priority": "P0 — Critical",
            "area": "Unit Economics",
            "title": "Improve LTV:CAC Ratio to Sustainable Levels",
            "current_state": f"LTV:CAC at {ltv_cac:.1f}x (target: >3.0x)",
            "actions": [
                "Reduce CAC by optimizing marketing channel mix — shift 20% of spend to highest-converting channels",
                "Increase LTV through upsell/cross-sell programs targeting existing customer base",
                "Implement customer health scoring to proactively reduce churn",
                "Consider price increase of 5-10% on new contracts to improve ARPU",
            ],
            "expected_impact": "Improving LTV:CAC to 3.0x+ would signal sustainable, investable growth",
        })
    elif ltv_cac and ltv_cac >= 5.0:
        recommendations.append({
            "priority": "P1 — Strategic",
            "area": "Growth Investment",
            "title": "LTV:CAC Indicates Room to Invest More Aggressively",
            "current_state": f"LTV:CAC at {ltv_cac:.1f}x (above 5.0x threshold)",
            "actions": [
                "Increase marketing spend by 30-40% to capture more market share",
                "Expand sales team by 2-3 reps per quarter",
                "Launch new geographic expansion initiatives",
            ],
            "expected_impact": "Accelerate growth while LTV:CAC remains healthy",
        })

    # CAC recommendations
    cac = latest.get("cac", 0)
    if cac and cac > 500:
        recommendations.append({
            "priority": "P1 — High",
            "area": "Customer Acquisition",
            "title": "Reduce Customer Acquisition Cost",
            "current_state": f"CAC at ${cac:,.0f} (target: <$500)",
            "actions": [
                "Audit marketing spend by channel — identify and cut underperforming channels",
                "Invest in product-led growth (PLG) motions to reduce reliance on outbound sales",
                "Implement referral program to generate lower-cost organic leads",
                "Improve sales enablement to shorten deal cycles and reduce cost-per-deal",
            ],
            "expected_impact": f"Reducing CAC to $500 would improve LTV:CAC by {((cac / 500) - 1) * 100:.0f}%",
        })

    # NRR recommendations
    nrr = latest.get("nrr_pct", 0)
    if nrr and nrr < 110:
        recommendations.append({
            "priority": "P1 — High",
            "area": "Revenue Retention",
            "title": "Boost Net Revenue Retention Above 110%",
            "current_state": f"NRR at {nrr:.1f}% (target: >110%)",
            "actions": [
                "Launch structured customer success program with QBRs for top-tier accounts",
                "Build expansion revenue playbook: identify upsell triggers in product usage data",
                "Implement proactive churn prevention using health scores",
                "Create tiered pricing to capture more value from power users",
            ],
            "expected_impact": "Every 5pp improvement in NRR compounds significantly over 12-24 months",
        })

    # Growth recommendations
    mom_growth = latest.get("mom_growth_pct", 0)
    if mom_growth is not None and mom_growth < 5:
        recommendations.append({
            "priority": "P1 — High",
            "area": "Revenue Growth",
            "title": "Accelerate Monthly Revenue Growth",
            "current_state": f"MoM growth at {mom_growth:.1f}% (target: >5%)",
            "actions": [
                "Double down on highest-performing regions and products",
                "Launch targeted outbound campaign for enterprise segment",
                "Explore strategic partnerships for channel distribution",
                "Implement quarterly pricing reviews to capture market willingness-to-pay",
            ],
            "expected_impact": "Reaching 5%+ MoM growth puts the company on track for T2D3 growth",
        })

    # Burn multiple
    burn = latest.get("burn_multiple", 0)
    if burn and burn > 2.0:
        recommendations.append({
            "priority": "P0 — Critical",
            "area": "Capital Efficiency",
            "title": "Reduce Burn Multiple to Sustainable Levels",
            "current_state": f"Burn multiple at {burn:.1f}x (target: <2.0x)",
            "actions": [
                "Audit all non-essential operating expenses for immediate cuts",
                "Shift marketing mix toward lower-cost, higher-efficiency channels",
                "Implement zero-based budgeting for next quarter",
                "Consider extending runway by deferring non-critical hires",
            ],
            "expected_impact": "Reducing burn multiple below 2.0x extends runway and improves fundraising positioning",
        })

    # Always add a forward-looking recommendation
    arr = latest.get("arr", 0)
    recommendations.append({
        "priority": "P2 — Strategic",
        "area": "Strategic Planning",
        "title": "12-Month ARR Trajectory Planning",
        "current_state": f"Current ARR: ${arr:,.0f}" if arr else "ARR data unavailable",
        "actions": [
            "Model Bull/Base/Bear scenarios for board presentation",
            "Identify 3 key levers for ARR acceleration",
            "Set quarterly OKRs tied to GTM financial metrics",
            "Plan hiring roadmap aligned with revenue milestones",
        ],
        "expected_impact": "Clear strategic roadmap with data-driven milestones",
    })

    result = {
        "total_recommendations": len(recommendations),
        "recommendations": recommendations,
        "executive_summary": (
            f"Analysis identified {risks.get('total_risks_identified', 0)} risks "
            f"({risks.get('high_severity_count', 0)} high severity). "
            f"{len(recommendations)} strategic recommendations generated."
        ),
    }

    return json.dumps(result, default=str, indent=2)


def build_scenario_model(df: pd.DataFrame, assumptions: dict[str, Any] | None = None) -> str:
    """Build Bull/Base/Bear scenario projections for the next 12 months.

    Args:
        df: Raw GTM dataset.
        assumptions: Optional dict to override default scenario assumptions.

    Returns:
        JSON string with three scenario projections.
    """
    scenarios = {
        "bull": {
            "label": "Bull Case — Aggressive Growth",
            "headcount_growth_pct": 8.0,
            "marketing_change_pct": 15.0,
            "churn_reduction_pct": 20.0,
            "price_increase_pct": 5.0,
        },
        "base": {
            "label": "Base Case — Steady State",
            "headcount_growth_pct": 3.0,
            "marketing_change_pct": 5.0,
            "churn_reduction_pct": 5.0,
            "price_increase_pct": 0.0,
        },
        "bear": {
            "label": "Bear Case — Market Headwinds",
            "headcount_growth_pct": 0.0,
            "marketing_change_pct": -10.0,
            "churn_reduction_pct": -10.0,
            "price_increase_pct": -3.0,
        },
    }

    if assumptions:
        for scenario_key, overrides in assumptions.items():
            if scenario_key in scenarios and isinstance(overrides, dict):
                scenarios[scenario_key].update(overrides)

    results = {}
    for key, params in scenarios.items():
        label = params.pop("label", key)
        proj = run_scenario_projection(df, **params, months_forward=12)
        params["label"] = label  # restore

        if not proj.empty:
            final = proj.iloc[-1]
            results[key] = {
                "label": label,
                "assumptions": {k: v for k, v in params.items() if k != "label"},
                "month_12_projection": {
                    "arr": round(float(final.get("arr", 0)), 0),
                    "mrr": round(float(final.get("mrr", 0)), 0),
                    "ltv_cac_ratio": round(float(final.get("ltv_cac_ratio", 0)), 2),
                    "payback_months": round(float(final.get("payback_months", 0)), 1),
                    "cac": round(float(final.get("cac", 0)), 0),
                    "sales_productivity": round(float(final.get("sales_productivity", 0)), 0),
                },
                "monthly_trajectory": [
                    {
                        "month": int(row.get("month", i + 1)),
                        "arr": round(float(row.get("arr", 0)), 0),
                        "mrr": round(float(row.get("mrr", 0)), 0),
                    }
                    for i, (_, row) in enumerate(proj.iterrows())
                ],
            }

    return json.dumps(results, default=str, indent=2)


# ──────────────────────────────────────────────────────────────
# Tool definitions for the Anthropic API tool_use schema
# ──────────────────────────────────────────────────────────────

TOOL_DEFINITIONS = [
    {
        "name": "analyze_unit_economics",
        "description": (
            "Analyze the GTM dataset and compute all SaaS unit economics metrics "
            "including MRR, ARR, CAC, LTV, LTV:CAC ratio, NRR, burn multiple, "
            "growth rates, and regional breakdowns. Returns structured JSON."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "analysis_scope": {
                    "type": "string",
                    "description": "Scope of analysis: 'full', 'regional', or 'product'",
                    "enum": ["full", "regional", "product"],
                },
            },
            "required": ["analysis_scope"],
        },
    },
    {
        "name": "identify_risks",
        "description": (
            "Identify risks by checking all GTM metrics against industry benchmark "
            "thresholds. Flags metrics that are in warning or critical territory. "
            "Requires the output from analyze_unit_economics as input."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "metrics_json": {
                    "type": "string",
                    "description": "JSON string output from analyze_unit_economics tool",
                },
            },
            "required": ["metrics_json"],
        },
    },
    {
        "name": "generate_recommendations",
        "description": (
            "Generate CFO-level strategic recommendations based on identified risks "
            "and current metrics. Produces prioritized action items with expected impact. "
            "Requires outputs from both identify_risks and analyze_unit_economics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "risks_json": {
                    "type": "string",
                    "description": "JSON string output from identify_risks tool",
                },
                "metrics_json": {
                    "type": "string",
                    "description": "JSON string output from analyze_unit_economics tool",
                },
            },
            "required": ["risks_json", "metrics_json"],
        },
    },
    {
        "name": "build_scenario_model",
        "description": (
            "Build Bull/Base/Bear financial scenario projections for the next 12 months. "
            "Projects ARR, MRR, LTV:CAC, payback period, and other key metrics under "
            "different assumption sets."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "scenario_type": {
                    "type": "string",
                    "description": "Type of scenario analysis to run",
                    "enum": ["all_scenarios", "custom"],
                },
            },
            "required": ["scenario_type"],
        },
    },
]
