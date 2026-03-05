# 🚀 GTM Finance Intelligence Agent

**A multi-agent AI system that automates Go-To-Market financial analysis for SaaS/Tech companies.**

This application replicates the exact work done by a Senior Finance & Strategy GTM Manager at companies like Anthropic, Google, or Meta — powered by Claude Opus and built with Streamlit.

---

## ✨ Features

| Module | Description |
|--------|-------------|
| **GTM Data Ingestion** | Upload CSV or use built-in 24-month demo dataset |
| **Automated Financial Model** | MRR, ARR, CAC, LTV, LTV:CAC, NRR, Burn Multiple & more |
| **AI Strategy Agent** | Agentic loop with 4 tools → CFO-level executive memo |
| **Scenario Planner** | Interactive sliders for Bull/Base/Bear projections |
| **Board-Ready Export** | One-click Excel report with 4 professionally formatted tabs |
| **Chat With Your Data** | Ask natural language questions about your GTM metrics |

---

## 🛠️ Tech Stack

- **Python 3.11+**
- **Anthropic SDK** (Claude Opus) — AI brain
- **Streamlit** — Web dashboard UI
- **Pandas + NumPy** — Financial modelling
- **Plotly** — Interactive charts
- **openpyxl** — Excel report generation
- **python-dotenv** — API key management

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
cd gtm_finance_agent
pip install -r requirements.txt
```

### 2. Configure API Key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

### 3. Run

```bash
streamlit run app.py
```

The dashboard will open at `http://localhost:8501`

---

## 📸 Screenshots

> *Screenshots will be added here after first deployment.*

| Dashboard Overview | AI Agent Analysis |
|---|---|
| ![Overview](screenshots/overview.png) | ![AI Analysis](screenshots/ai_analysis.png) |

| Scenario Planner | Board Report Export |
|---|---|
| ![Scenarios](screenshots/scenarios.png) | ![Export](screenshots/export.png) |

---

## 📁 Project Structure

```
gtm_finance_agent/
├── app.py                 # Main Streamlit entry point
├── agents/
│   ├── __init__.py
│   ├── gtm_agent.py       # Claude Opus agentic loop + tools
│   └── tools.py           # All 4 tool functions
├── models/
│   ├── __init__.py
│   └── financial_model.py # All GTM metric calculations
├── ui/
│   ├── __init__.py
│   ├── dashboard.py       # Main dashboard layout
│   ├── charts.py          # All Plotly visualizations
│   └── chat.py            # Chat interface component
├── exports/
│   ├── __init__.py
│   └── excel_export.py    # Board report generator
├── data/
│   └── demo_data.py       # Synthetic 24-month dataset
├── requirements.txt
├── .env.example
└── README.md
```

---

## 📊 Key Metrics Calculated

| Metric | Formula | Healthy Benchmark |
|--------|---------|-------------------|
| MRR | Sum of monthly recurring revenue | Growing MoM |
| ARR | MRR × 12 | > $1M for Series A |
| CAC | Marketing Spend ÷ New Customers | < $500 for SMB SaaS |
| LTV | ARPU ÷ Churn Rate | > 3× CAC |
| LTV:CAC | LTV ÷ CAC | > 3.0× |
| Payback Period | CAC ÷ Monthly ARPU | < 12 months |
| NRR | (Start MRR + Expansion − Churn) ÷ Start MRR | > 110% |
| Burn Multiple | Net Burn ÷ Net New ARR | < 2.0× |
| Sales Productivity | Revenue ÷ Sales Headcount | Increasing trend |

---

## 🤖 AI Agent Architecture

The AI Strategy Agent uses an **agentic tool-use loop** powered by Claude Opus:

1. **`analyze_unit_economics`** → Computes all GTM metrics as structured JSON
2. **`identify_risks`** → Flags metrics below benchmark thresholds
3. **`generate_recommendations`** → Produces CFO-level strategic recommendations
4. **`build_scenario_model`** → Runs Bull/Base/Bear 12-month projections

The agent autonomously chains these tools and synthesizes results into a professional executive memo.

---

## 📝 License

MIT License — Use freely for commercial and personal projects.

---

**Built by Arif Hossain — Finance Technologist | AI-Driven Finance Leader**
