"""
GTM Strategy Agent — Claude Opus agentic loop with tool use.

Orchestrates a multi-step analysis pipeline:
  1. analyze_unit_economics  →  structured metrics
  2. identify_risks          →  benchmark comparisons
  3. generate_recommendations →  strategic actions
  4. build_scenario_model    →  Bull / Base / Bear projections

Synthesizes all outputs into a CFO-level executive narrative.
"""

import os
import json
import anthropic
import pandas as pd
import streamlit as st
from typing import Any, Generator
from dotenv import load_dotenv

from agents.tools import (
    analyze_unit_economics,
    identify_risks,
    generate_recommendations,
    build_scenario_model,
    TOOL_DEFINITIONS,
)

load_dotenv()


def _get_client() -> anthropic.Anthropic:
    """Create an Anthropic client using the API key from env or Streamlit secrets.

    Returns:
        Configured Anthropic client.

    Raises:
        ValueError: If no API key is found.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY") or st.session_state.get("anthropic_api_key")
    if not api_key or api_key == "your-anthropic-api-key-here":
        raise ValueError(
            "Anthropic API key not found. Please set ANTHROPIC_API_KEY in your "
            ".env file or enter it in the sidebar."
        )
    return anthropic.Anthropic(api_key=api_key)


def _execute_tool(tool_name: str, tool_input: dict, df: pd.DataFrame) -> str:
    """Execute a tool function by name with the given inputs.

    Args:
        tool_name: Name of the tool to execute.
        tool_input: Input parameters for the tool.
        df: The GTM dataset (passed to tools that need raw data).

    Returns:
        JSON string result from the tool.
    """
    if tool_name == "analyze_unit_economics":
        return analyze_unit_economics(df)
    elif tool_name == "identify_risks":
        metrics_json = tool_input.get("metrics_json", "")
        return identify_risks(metrics_json)
    elif tool_name == "generate_recommendations":
        risks_json = tool_input.get("risks_json", "")
        metrics_json = tool_input.get("metrics_json", "")
        return generate_recommendations(risks_json, metrics_json)
    elif tool_name == "build_scenario_model":
        return build_scenario_model(df)
    else:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})


def run_agent_analysis(
    df: pd.DataFrame,
    status_callback: Any = None,
) -> dict[str, Any]:
    """Run the full GTM Strategy Agent agentic loop.

    The agent autonomously calls tools in sequence, then synthesizes
    all results into a CFO-level executive memo.

    Args:
        df: Raw GTM dataset.
        status_callback: Optional callable(step_name, detail) for UI updates.

    Returns:
        Dictionary with keys:
        - 'steps': list of tool call records
        - 'narrative': the final executive memo
        - 'metrics_json': raw metrics data
        - 'risks_json': raw risks data
        - 'recommendations_json': raw recommendations data
        - 'scenarios_json': raw scenario data
    """
    client = _get_client()

    def _status(step: str, detail: str = "") -> None:
        if status_callback:
            status_callback(step, detail)

    _status("🔄 Initializing", "Starting GTM Strategy Agent...")

    system_prompt = """You are a Senior Finance & Strategy GTM Manager at a top-tier SaaS company.
Your role is to conduct a comprehensive Go-To-Market financial analysis using the tools available to you.

You MUST call all four tools in this exact sequence:
1. First, call analyze_unit_economics with analysis_scope="full" to get the complete metrics picture.
2. Then, call identify_risks with the metrics_json output from step 1.
3. Next, call generate_recommendations with both the risks_json from step 2 AND the metrics_json from step 1.
4. Finally, call build_scenario_model with scenario_type="all_scenarios" to project future outcomes.

After all tools have returned results, synthesize everything into a 500-word CFO-level executive narrative memo.

The memo MUST include:
- Opening with the company's current ARR and growth trajectory
- Key unit economics (LTV:CAC, CAC, NRR, Burn Multiple) with specific numbers
- Top 3 risks identified with severity levels
- Top 3 actionable recommendations with expected impact
- Bull/Base/Bear 12-month ARR projections with specific dollar amounts
- A clear "Bottom Line" conclusion with the single most important action

Format as a professional memo with headers and bullet points. Use specific numbers throughout."""

    messages = [
        {
            "role": "user",
            "content": (
                "Please run a complete GTM financial analysis on our SaaS dataset. "
                "Call all four analysis tools in sequence, then write the executive memo. "
                "Our leadership team needs this for the upcoming board meeting."
            ),
        }
    ]

    steps = []
    tool_results = {}
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        _status(f"🤖 Agent Thinking (Step {iteration})", "Claude is analyzing...")

        try:
            response = client.messages.create(
                model="claude-opus-4-20250514",
                max_tokens=4096,
                system=system_prompt,
                tools=TOOL_DEFINITIONS,
                messages=messages,
            )
        except anthropic.APIError as e:
            _status("❌ API Error", str(e))
            return {
                "steps": steps,
                "narrative": f"Agent encountered an API error: {e}",
                "error": str(e),
            }

        # Process response content blocks
        assistant_content = response.content
        tool_use_blocks = []
        text_blocks = []

        for block in assistant_content:
            if block.type == "tool_use":
                tool_use_blocks.append(block)
            elif block.type == "text":
                text_blocks.append(block.text)

        # Append the assistant message
        messages.append({"role": "assistant", "content": assistant_content})

        # If there are tool calls, execute them
        if tool_use_blocks:
            tool_results_content = []
            for tool_block in tool_use_blocks:
                tool_name = tool_block.name
                tool_input = tool_block.input

                _status(f"🔧 Calling Tool", f"{tool_name}...")

                result = _execute_tool(tool_name, tool_input, df)
                tool_results[tool_name] = result

                steps.append({
                    "tool": tool_name,
                    "input": tool_input,
                    "output_preview": result[:500] + "..." if len(result) > 500 else result,
                })

                tool_results_content.append({
                    "type": "tool_result",
                    "tool_use_id": tool_block.id,
                    "content": result,
                })

            messages.append({"role": "user", "content": tool_results_content})
        else:
            # No more tool calls — agent has finished
            break

        # Check stop reason
        if response.stop_reason == "end_turn" and not tool_use_blocks:
            break

    # Extract the final narrative
    narrative = "\n\n".join(text_blocks) if text_blocks else "Agent did not produce a final narrative."

    _status("✅ Analysis Complete", "Executive memo ready.")

    return {
        "steps": steps,
        "narrative": narrative,
        "metrics_json": tool_results.get("analyze_unit_economics", "{}"),
        "risks_json": tool_results.get("identify_risks", "{}"),
        "recommendations_json": tool_results.get("generate_recommendations", "{}"),
        "scenarios_json": tool_results.get("build_scenario_model", "{}"),
    }


def chat_with_data(
    df: pd.DataFrame,
    user_question: str,
    conversation_history: list[dict[str, str]],
) -> str:
    """Answer a user's question about their GTM data using Claude.

    Args:
        df: Raw GTM dataset.
        user_question: The user's natural language question.
        conversation_history: List of prior messages [{role, content}, ...].

    Returns:
        Claude's response text.
    """
    client = _get_client()

    # Build data context
    from models.financial_model import compute_gtm_metrics, get_latest_metrics_summary
    metrics_summary = get_latest_metrics_summary(df)
    metrics_df = compute_gtm_metrics(df)

    # Regional summary
    regional_summary = (
        df.groupby("region")
        .agg(
            total_revenue=("revenue", "sum"),
            avg_monthly_revenue=("revenue", "mean"),
            total_customers=("new_customers", "sum"),
            total_churn=("churned_customers", "sum"),
        )
        .round(0)
        .to_dict()
    )

    # Product summary
    product_summary = (
        df.groupby("product")
        .agg(
            total_revenue=("revenue", "sum"),
            avg_monthly_revenue=("revenue", "mean"),
            total_customers=("new_customers", "sum"),
        )
        .round(0)
        .to_dict()
    )

    data_context = f"""Here is the current GTM financial data context:

LATEST METRICS (most recent month):
{json.dumps(metrics_summary, indent=2, default=str)}

REGIONAL BREAKDOWN:
{json.dumps(regional_summary, indent=2, default=str)}

PRODUCT BREAKDOWN:
{json.dumps(product_summary, indent=2, default=str)}

MONTHLY TREND (last 6 months - key metrics):
{metrics_df[['date', 'mrr', 'arr', 'cac', 'ltv_cac_ratio', 'nrr_pct', 'burn_multiple']].tail(6).to_string(index=False)}

DATA RANGE: {df['date'].min().strftime('%Y-%m-%d')} to {df['date'].max().strftime('%Y-%m-%d')}
TOTAL ROWS: {len(df)}
REGIONS: {', '.join(df['region'].unique())}
PRODUCTS: {', '.join(df['product'].unique())}"""

    system_prompt = f"""You are a GTM Finance Intelligence Agent — an AI finance analyst with deep expertise 
in SaaS Go-To-Market metrics and strategy. You have access to the company's GTM financial data.

{data_context}

Answer questions precisely using the actual data provided. Include specific numbers.
If asked about projections, use the current trends to extrapolate.
If asked about comparisons, be specific about which metrics differ and by how much.
Be concise but thorough. Format responses with bullet points and bold numbers where appropriate.
If you cannot answer from the available data, say so clearly."""

    # Build messages with conversation history
    messages = []
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_question})

    try:
        response = client.messages.create(
            model="claude-opus-4-20250514",
            max_tokens=2048,
            system=system_prompt,
            messages=messages,
        )
        return response.content[0].text
    except anthropic.APIError as e:
        return f"⚠️ API Error: {e}"
    except ValueError as e:
        return f"⚠️ Configuration Error: {e}"
