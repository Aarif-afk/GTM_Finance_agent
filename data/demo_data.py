"""
Synthetic 24-month GTM dataset generator.

Produces realistic SaaS Go-To-Market data across multiple regions
and products for demonstration and testing purposes.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Optional


def generate_demo_data(months: int = 24, seed: int = 42) -> pd.DataFrame:
    """Generate a realistic synthetic 24-month SaaS GTM dataset.

    Creates monthly data for 3 regions × 2 products = 6 rows per month,
    with realistic growth curves, seasonality, and variance.

    Args:
        months: Number of months of data to generate (default 24).
        seed: Random seed for reproducibility.

    Returns:
        DataFrame with columns: date, region, product, revenue,
        deals_closed, sales_headcount, marketing_spend,
        new_customers, churned_customers.
    """
    np.random.seed(seed)

    regions = ["North America", "EMEA", "APAC"]
    products = ["Enterprise Platform", "Growth Suite"]

    # Base parameters per region (NA is largest, then EMEA, then APAC)
    region_config = {
        "North America": {
            "base_revenue": 180_000,
            "base_deals": 22,
            "base_headcount": 15,
            "base_marketing": 95_000,
            "base_new_customers": 28,
            "base_churn": 3,
            "growth_rate": 0.06,
        },
        "EMEA": {
            "base_revenue": 110_000,
            "base_deals": 14,
            "base_headcount": 10,
            "base_marketing": 60_000,
            "base_new_customers": 18,
            "base_churn": 2,
            "growth_rate": 0.08,
        },
        "APAC": {
            "base_revenue": 65_000,
            "base_deals": 9,
            "base_headcount": 6,
            "base_marketing": 35_000,
            "base_new_customers": 12,
            "base_churn": 2,
            "growth_rate": 0.10,
        },
    }

    # Product split (Enterprise = 65%, Growth = 35%)
    product_split = {
        "Enterprise Platform": 0.65,
        "Growth Suite": 0.35,
    }

    start_date = datetime(2024, 1, 1)
    rows = []

    for month_idx in range(months):
        current_date = start_date + timedelta(days=month_idx * 30)
        date_str = current_date.strftime("%Y-%m-%d")

        # Seasonality factor (Q4 boost, Q1 dip)
        quarter = (current_date.month - 1) // 3 + 1
        seasonality = {1: 0.92, 2: 1.0, 3: 1.03, 4: 1.12}[quarter]

        for region, cfg in region_config.items():
            # Compound growth with noise
            growth_mult = (1 + cfg["growth_rate"]) ** month_idx
            noise = np.random.normal(1.0, 0.05)

            for product, split in product_split.items():
                revenue = int(
                    cfg["base_revenue"]
                    * split
                    * growth_mult
                    * seasonality
                    * noise
                    * np.random.normal(1.0, 0.03)
                )

                deals = max(
                    1,
                    int(
                        cfg["base_deals"]
                        * split
                        * growth_mult
                        * seasonality
                        * np.random.normal(1.0, 0.1)
                    ),
                )

                # Headcount grows slower, step-wise quarterly
                hc_growth = 1 + (month_idx // 3) * 0.05
                headcount = max(
                    1,
                    int(cfg["base_headcount"] * split * hc_growth),
                )

                marketing = int(
                    cfg["base_marketing"]
                    * split
                    * (1 + cfg["growth_rate"] * 0.8) ** month_idx
                    * seasonality
                    * np.random.normal(1.0, 0.08)
                )

                new_cust = max(
                    1,
                    int(
                        cfg["base_new_customers"]
                        * split
                        * growth_mult
                        * seasonality
                        * np.random.normal(1.0, 0.12)
                    ),
                )

                # Churn grows slower than acquisition
                churn = max(
                    0,
                    int(
                        cfg["base_churn"]
                        * split
                        * (1 + cfg["growth_rate"] * 0.3) ** month_idx
                        * np.random.normal(1.0, 0.2)
                    ),
                )

                rows.append(
                    {
                        "date": date_str,
                        "region": region,
                        "product": product,
                        "revenue": revenue,
                        "deals_closed": deals,
                        "sales_headcount": headcount,
                        "marketing_spend": marketing,
                        "new_customers": new_cust,
                        "churned_customers": churn,
                    }
                )

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    return df


def validate_uploaded_data(df: pd.DataFrame) -> tuple[bool, str]:
    """Validate that an uploaded CSV has the required columns and types.

    Args:
        df: The uploaded DataFrame to validate.

    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    required_columns = [
        "date",
        "region",
        "product",
        "revenue",
        "deals_closed",
        "sales_headcount",
        "marketing_spend",
        "new_customers",
        "churned_customers",
    ]

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return False, f"Missing required columns: {', '.join(missing)}"

    # Check for numeric columns
    numeric_cols = [
        "revenue",
        "deals_closed",
        "sales_headcount",
        "marketing_spend",
        "new_customers",
        "churned_customers",
    ]
    for col in numeric_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            return False, f"Column '{col}' must be numeric, got {df[col].dtype}"

    # Try to parse dates
    try:
        pd.to_datetime(df["date"])
    except Exception:
        return False, "Column 'date' contains invalid date values."

    if len(df) == 0:
        return False, "Dataset is empty — please upload data with at least 1 row."

    return True, ""
