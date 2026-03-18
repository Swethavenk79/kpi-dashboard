# KPI Dashboard — Streamlit BI App

**Role this showcases:** BI Developer / Analytics Engineer / Data Analyst

---

## Purpose

A production-ready weekly KPI dashboard for a regional retail business. This project demonstrates the ability to build end-to-end BI solutions: from raw data generation through ETL pipeline to an interactive Streamlit dashboard that non-technical stakeholders can use.

The dashboard answers three key business questions:
1. **What are our weekly KPIs** — and are we hitting targets?
2. **Which region is underperforming** — and since when?
3. **Are any weeks anomalous** — spikes or crashes that need investigation?

---

## KPIs Tracked

| KPI | Description | Target |
|-----|-------------|--------|
| **Revenue** | Total weekly revenue across all regions | ₹400K-520K per region |
| **Revenue vs Target** | Percentage achievement of revenue targets | >100% |
| **Units Sold** | Total units sold per week | Varies by region |
| **Return Rate** | Returns as % of units sold | <5% |
| **Revenue per Staff Hour** | Efficiency metric | Track trend |
| **Anomaly Flags** | Statistical outliers (>2σ) | Investigate |

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Raw Data       │────▶│  ETL Pipeline   │────▶│  Streamlit App  │
│  (CSV Files)    │     │  scripts/etl.py │     │  dashboard/     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       │                         │                       │
       ▼                         ▼                       ▼
   • sales_raw.csv          • Data cleaning        • Interactive
   • targets_raw.csv        • Aggregation            filters
                            • Anomaly detection    • Visualizations
                            • Target comparison    • CSV export
```

**Key Design Decisions:**
- **ETL runs separately** from the dashboard — if raw data changes, just rerun ETL
- **Dashboard only reads** from clean summary CSV — fast load times
- **Logging at every step** — debuggable pipeline for production reliability
- **Anomaly detection** using statistical methods (>2 standard deviations)

---

## Features

### 📊 Interactive Dashboard
- **Region filter** — Multi-select to compare specific regions
- **Date range slider** — Focus on specific time periods
- **Target toggle** — Show/hide target lines on charts

### 📈 Visualizations
- **KPI tiles** — At-a-glance metrics with week-over-week deltas
- **Revenue trend line chart** — With anomaly highlighting
- **Stacked bar chart** — Revenue breakdown by region
- **Detail data table** — Sortable weekly records

### 🔔 Smart Alerts
- **Anomaly detection** — Automatic flagging of unusual weeks
- **Conditional formatting** — Color-coded performance indicators

### 💾 Data Export
- **Download as CSV** — Export filtered data for further analysis

---

## How to Run

### Prerequisites
```bash
# Python 3.9+ required
python --version
```

### Setup
```bash
# 1. Navigate to project directory
cd kpi-dashboard

# 2. Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

### Run the Pipeline
```bash
# Step 1: Generate raw data (creates data/raw/*.csv)
python data/generate_raw_data.py

# Step 2: Run ETL pipeline (creates dashboard/data/weekly_summary.csv)
python scripts/etl.py

# Step 3: Launch dashboard
streamlit run dashboard/streamlit_app.py
```

The dashboard will open in your browser at `http://localhost:8501`

---

## Skills Demonstrated

| Skill | Implementation |
|-------|----------------|
| **Python / Pandas** | ETL pipeline with groupby, merge, pivot operations |
| **ETL Design** | Multi-step pipeline with validation, cleaning, aggregation |
| **Streamlit** | Full dashboard with filters, charts, and interactivity |
| **Statistical Analysis** | Z-score anomaly detection, target variance analysis |
| **Data Visualization** | Plotly charts with conditional formatting |
| **Error Handling** | Try/except for missing files, data validation |
| **BI Thinking** | KPI design, stakeholder-focused UX, target vs actual |

---

## Project Structure

```
kpi-dashboard/
├── data/
│   ├── raw/
│   │   ├── sales_raw.csv         # Generated: Store-level sales data
│   │   └── targets_raw.csv       # Generated: Weekly targets by region
│   └── generate_raw_data.py      # Raw data generator script
├── scripts/
│   └── etl.py                    # ETL pipeline
├── dashboard/
│   ├── streamlit_app.py          # Main dashboard application
│   ├── data/
│   │   └── weekly_summary.csv    # Output from ETL
│   └── static/
│       └── weekly_revenue_trend.png  # Static chart output
├── README.md                     # This file
└── requirements.txt              # Python dependencies
```

---

## Data Story

The generated dataset includes intentional patterns for dashboard validation:

- **South Region Underperformance** — Starting Q3 2024, South region misses targets by ~15%. This creates a clear narrative for stakeholders to investigate.
- **Seasonal Patterns** — Q4 holiday season shows 30% revenue lift, Q2 shows typical slump.
- **Anomalous Weeks** — Three weeks with revenue spikes (>2σ) test the anomaly detection feature.
- **Data Quality Issues** — Some missing staff_hours and occasional negative revenues test ETL robustness.

---

## Customization

### Adding New Metrics
1. Add calculation in `scripts/etl.py` → `aggregate_weekly()`
2. Add display in `dashboard/streamlit_app.py` → KPI tiles or charts

### Changing Date Range
Modify `START_DATE` and `END_DATE` in `data/generate_raw_data.py`, then rerun the full pipeline.

### Theming
Edit `st.set_page_config()` and CSS in `dashboard/streamlit_app.py` to match brand colors.

---

## License

This project is created for portfolio demonstration purposes.
