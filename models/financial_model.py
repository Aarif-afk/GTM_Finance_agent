"""
GTM Financial Model — all SaaS Go-To-Market metric calculations.

Computes MRR, ARR, CAC, LTV, LTV:CAC, Payback Period,
NRR, Sales Productivity, Burn Multiple, and growth rates.
"""

import pandas as pd
import numpy as np
from typing import Any


# ──────────────────────────────────────────────────────────────
# Benchmark thresholds for health-check color coding
# ──────────────────────────────────────────────────────────────
BENCHMARKS: dict[str, dict[str, Any]] = {
    "ltv_cac_ratio": {"healthy": 3.0, "warning": 2.0, "label": "LTV:CAC Ratio", "direction": "higher_better"},
    "cac": {"healthy": 500, "warning": 800, "label": "CAC ($)", "direction": "lower_better"},
    "payback_months": {"healthy": 12, "warning": 18, "label": "Payback Period (mo)", "direction": "lower_better"},
    "nrr_pct": {"healthy": 110, "warning": 100, "label": "Net Revenue Retention (%)", "direction": "higher_better"},
    "burn_multiple": {"healthy": 2.0, "warning": 3.0, "label": "Burn Multiple", "direction": "lower_better"},
    "mom_growth_pct": {"healthy": 5.0, "warning": 2.0, "label": "MoM Growth (%)", "direction": "higher_better"},
    "yoy_growth_pct": {"healthy": 50.0, "warning": 20.0, "label": "YoY Growth (%)", "direction": "higher_better"},
}


def compute_monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate raw data into monthly totals across all regions/products.

    Args:
        df: Raw GTM dataset with per-region, per-product rows.

    Returns:
        Monthly summary DataFrame sorted by date.
    """
    monthly = (
        df.groupby(pd.Grouper(key="date", freq="MS"))
        .agg(
            revenue=("revenue", "sum"),
            deals_closed=("deals_closed", "sum"),
            sales_headcount=("sales_headcount", "sum"),
            marketing_spend=("marketing_spend", "sum"),
            new_customers=("new_customers", "sum"),
            churned_customers=("churned_customers", "sum"),
        )
        .reset_index()
        .sort_values("date")
    )
    return monthly


def compute_gtm_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate all GTM financial metrics from raw data.

    Adds columns: mrr, arr, mom_growth_pct, yoy_growth_pct,
    cac, cumulative_customers, churn_rate, arpu, ltv, ltv_cac_ratio,
    payback_months, sales_productivity, nrr_pct, burn_multiple.

    Args:
        df: Raw GTM dataset.

    Returns:
        Monthly metrics DataFrame with all computed columns.
    """
    monthly = compute_monthly_summary(df)

    # MRR & ARR
    monthly["mrr"] = monthly["revenue"]
    monthly["arr"] = monthly["mrr"] * 12

    # Growth rates
    monthly["mom_growth_pct"] = monthly["mrr"].pct_change() * 100
    monthly["yoy_growth_pct"] = monthly["mrr"].pct_change(periods=12) * 100

    # CAC — Customer Acquisition Cost
    monthly["cac"] = np.where(
        monthly["new_customers"] > 0,
        monthly["marketing_spend"] / monthly["new_customers"],
        np.nan,
    )

    # Cumulative customer base (running net)
    monthly["net_new_customers"] = monthly["new_customers"] - monthly["churned_customers"]
    monthly["cumulative_customers"] = monthly["net_new_customers"].cumsum()
    # Ensure minimum of 1 to avoid div-by-zero
    monthly["cumulative_customers"] = monthly["cumulative_customers"].clip(lower=1)

    # Churn rate (monthly)
    monthly["churn_rate"] = np.where(
        monthly["cumulative_customers"].shift(1) > 0,
        monthly["churned_customers"] / monthly["cumulative_customers"].shift(1),
        0.0,
    )
    monthly["churn_rate"] = monthly["churn_rate"].clip(lower=0.001)  # floor to avoid inf LTV

    # ARPU — Average Revenue Per User (monthly)
    monthly["arpu"] = monthly["mrr"] / monthly["cumulative_customers"]

    # LTV — Lifetime Value
    monthly["ltv"] = monthly["arpu"] / monthly["churn_rate"]

    # LTV:CAC Ratio
    monthly["ltv_cac_ratio"] = np.where(
        monthly["cac"] > 0,
        monthly["ltv"] / monthly["cac"],
        np.nan,
    )

    # Payback Period (months)
    monthly["payback_months"] = np.where(
        monthly["arpu"] > 0,
        monthly["cac"] / monthly["arpu"],
        np.nan,
    )

    # Sales Productivity (revenue per headcount)
    monthly["sales_productivity"] = np.where(
        monthly["sales_headcount"] > 0,
        monthly["revenue"] / monthly["sales_headcount"],
        np.nan,
    )

    # Net Revenue Retention (NRR) — simplified proxy
    monthly["expansion_revenue"] = monthly["mrr"].diff().clip(lower=0)
    monthly["churned_revenue"] = monthly["churned_customers"] * monthly["arpu"]
    monthly["nrr_pct"] = np.where(
        monthly["mrr"].shift(1) > 0,
        ((monthly["mrr"].shift(1) + monthly["expansion_revenue"] - monthly["churned_revenue"])
         / monthly["mrr"].shift(1))
        * 100,
        np.nan,
    )

    # Burn Multiple = net_burn / net_new_ARR
    monthly["net_new_arr"] = monthly["arr"].diff()
    monthly["net_burn"] = monthly["marketing_spend"]  # simplified: marketing as burn proxy
    monthly["burn_multiple"] = np.where(
        monthly["net_new_arr"] > 0,
        monthly["net_burn"] / monthly["net_new_arr"],
        np.nan,
    )

    # Pipeline Coverage Ratio (simplified: deals * avg deal size / target)
    avg_deal_size = monthly["revenue"] / monthly["deals_closed"].clip(lower=1)
    monthly["pipeline_coverage"] = (monthly["deals_closed"] * avg_deal_size * 3) / monthly["revenue"].clip(lower=1)

    # Round for presentation
    float_cols = [
        "mom_growth_pct", "yoy_growth_pct", "cac", "churn_rate",
        "arpu", "ltv", "ltv_cac_ratio", "payback_months",
        "sales_productivity", "nrr_pct", "burn_multiple", "pipeline_coverage",
    ]
    for col in float_cols:
        if col in monthly.columns:
            monthly[col] = monthly[col].round(2)

    return monthly


def compute_regional_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute GTM metrics broken down by region.

    Args:
        df: Raw GTM dataset.

    Returns:
        DataFrame with metrics per region.
    """
    results = []
    for region in df["region"].unique():
        region_df = df[df["region"] == region].copy()
        metrics = compute_gtm_metrics(region_df)
        latest = metrics.iloc[-1].to_dict()
        latest["region"] = region
        results.append(latest)
    return pd.DataFrame(results)


def compute_product_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Compute GTM metrics broken down by product.

    Args:
        df: Raw GTM dataset.

    Returns:
        DataFrame with metrics per product.
    """
    results = []
    for product in df["product"].unique():
        product_df = df[df["product"] == product].copy()
        metrics = compute_gtm_metrics(product_df)
        latest = metrics.iloc[-1].to_dict()
        latest["product"] = product
        results.append(latest)
    return pd.DataFrame(results)


def get_health_status(value: float, metric_key: str) -> str:
    """Determine if a metric value is healthy, warning, or critical.

    Args:
        value: The metric value to check.
        metric_key: Key into the BENCHMARKS dict.

    Returns:
        One of 'healthy', 'warning', or 'critical'.
    """
    if metric_key not in BENCHMARKS or pd.isna(value):
        return "neutral"

    bench = BENCHMARKS[metric_key]
    if bench["direction"] == "higher_better":
        if value >= bench["healthy"]:
            return "healthy"
        elif value >= bench["warning"]:
            return "warning"
        else:
            return "critical"
    else:  # lower_better
        if value <= bench["healthy"]:
            return "healthy"
        elif value <= bench["warning"]:
            return "warning"
        else:
            return "critical"


def get_latest_metrics_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Get the latest month's metrics as a flat dictionary.

    Args:
        df: Raw GTM dataset.

    Returns:
        Dictionary of all latest metric values.
    """
    metrics_df = compute_gtm_metrics(df)
    if metrics_df.empty:
        return {}
    latest = metrics_df.iloc[-1]
    summary = {}
    for col in metrics_df.columns:
        val = latest[col]
        if isinstance(val, (np.integer, np.int64)):
            summary[col] = int(val)
        elif isinstance(val, (np.floating, np.float64)):
            summary[col] = round(float(val), 2)
        elif isinstance(val, pd.Timestamp):
            summary[col] = val.strftime("%Y-%m-%d")
        else:
            summary[col] = val
    return summary


def run_scenario_projection(
    df: pd.DataFrame,
    headcount_growth_pct: float = 0.0,
    marketing_change_pct: float = 0.0,
    churn_reduction_pct: float = 0.0,
    price_increase_pct: float = 0.0,
    months_forward: int = 12,
) -> pd.DataFrame:
    """Project future metrics based on assumption changes.

    Args:
        df: Raw GTM dataset.
        headcount_growth_pct: Percentage increase in sales headcount.
        marketing_change_pct: Percentage change in marketing spend.
        churn_reduction_pct: Percentage reduction in churn.
        price_increase_pct: Percentage increase in revenue (price).
        months_forward: Number of months to project.

    Returns:
        Projected monthly metrics DataFrame.
    """
    metrics = compute_gtm_metrics(df)
    if metrics.empty:
        return metrics

    last = metrics.iloc[-1].copy()
    last_date = last["date"]

    projections = []
    for i in range(1, months_forward + 1):
        proj = {}
        proj_date = last_date + pd.DateOffset(months=i)
        proj["date"] = proj_date
        proj["month"] = i

        # Revenue grows with price increase + organic momentum
        organic_growth = last.get("mom_growth_pct", 3.0) or 3.0
        monthly_growth = (1 + organic_growth / 100) * (1 + price_increase_pct / 100)
        proj["mrr"] = last["mrr"] * (monthly_growth ** i)
        proj["arr"] = proj["mrr"] * 12

        # Headcount grows
        proj["sales_headcount"] = last["sales_headcount"] * (1 + headcount_growth_pct / 100) ** i

        # Marketing changes
        proj["marketing_spend"] = last["marketing_spend"] * (1 + marketing_change_pct / 100) ** i

        # Customer dynamics
        churn_mult = max(0.1, 1 - churn_reduction_pct / 100)
        proj["churn_rate"] = last["churn_rate"] * (churn_mult ** i)
        proj["churned_customers"] = max(0, int(last["churned_customers"] * (churn_mult ** i)))
        proj["new_customers"] = max(1, int(last["new_customers"] * (monthly_growth ** i)))

        # Derived metrics
        proj["cumulative_customers"] = last["cumulative_customers"] + proj["new_customers"] * i - proj["churned_customers"] * i
        proj["cumulative_customers"] = max(1, proj["cumulative_customers"])
        proj["arpu"] = proj["mrr"] / proj["cumulative_customers"]
        proj["cac"] = proj["marketing_spend"] / max(1, proj["new_customers"])
        proj["ltv"] = proj["arpu"] / max(0.001, proj["churn_rate"])
        proj["ltv_cac_ratio"] = proj["ltv"] / max(1, proj["cac"])
        proj["payback_months"] = proj["cac"] / max(1, proj["arpu"])
        proj["sales_productivity"] = proj["mrr"] / max(1, proj["sales_headcount"])

        projections.append(proj)

    result = pd.DataFrame(projections)
    float_cols = ["mrr", "arr", "cac", "ltv", "ltv_cac_ratio", "payback_months",
                  "sales_productivity", "arpu", "churn_rate"]
    for col in float_cols:
        if col in result.columns:
            result[col] = result[col].round(2)

    return result
