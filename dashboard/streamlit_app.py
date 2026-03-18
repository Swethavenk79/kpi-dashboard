# Run: streamlit run dashboard/streamlit_app.py
"""
KPI Dashboard - Streamlit BI App
Weekly retail KPI monitoring dashboard for non-technical stakeholders.
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os
import sys
import subprocess

# Page configuration
st.set_page_config(
    page_title="Weekly KPI Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1A56DB;
        margin-bottom: 0.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1A56DB;
    }
</style>
""", unsafe_allow_html=True)

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
DATA_PATH = os.path.join(SCRIPT_DIR, 'data', 'weekly_summary.csv')
ETL_PATH = os.path.join(PROJECT_DIR, 'scripts', 'etl.py')

@st.cache_data
def load_data():
    """Load weekly summary data."""
    if not os.path.exists(DATA_PATH):
        st.error(f"Data file not found: {DATA_PATH}")
        st.info("Please run: python scripts/etl.py")
        return None
    
    df = pd.read_csv(DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    return df

def run_etl():
    """Rerun ETL pipeline."""
    try:
        result = subprocess.run([sys.executable, ETL_PATH], 
                              capture_output=True, text=True, cwd=PROJECT_DIR)
        if result.returncode == 0:
            st.cache_data.clear()
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def calculate_delta(df, metric, region_filter=None):
    """Calculate week-over-week delta for a metric."""
    if region_filter and len(region_filter) > 0:
        filtered = df[df['region'].isin(region_filter)]
    else:
        filtered = df
    
    # Get last two weeks
    latest_week = filtered['date'].max()
    prev_week = filtered[filtered['date'] < latest_week]['date'].max()
    
    latest_val = filtered[filtered['date'] == latest_week][metric].sum()
    prev_val = filtered[filtered['date'] == prev_week][metric].sum()
    
    if prev_val == 0:
        return 0, 0
    
    delta = ((latest_val / prev_val) - 1) * 100
    return latest_val, delta

def main():
    """Main dashboard layout."""
    # Load data
    df = load_data()
    if df is None:
        return
    
    # Header
    st.markdown('<p class="main-header">📊 Weekly KPI Dashboard</p>', unsafe_allow_html=True)
    
    col_title, col_refresh = st.columns([4, 1])
    with col_title:
        st.markdown(f"**Last updated:** {df['date'].max().strftime('%Y-%m-%d')}")
    with col_refresh:
        if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
            with st.spinner("Running ETL pipeline..."):
                success, output = run_etl()
                if success:
                    st.success("Data refreshed!")
                    df = load_data()
                else:
                    st.error(f"ETL failed: {output}")
    
    st.divider()
    
    # Sidebar filters
    st.sidebar.header("📋 Filters")
    
    # Region filter
    all_regions = sorted(df['region'].unique())
    selected_regions = st.sidebar.multiselect(
        "Regions",
        options=all_regions,
        default=all_regions
    )
    
    # Date range slider
    min_date = df['date'].min()
    max_date = df['date'].max()
    
    # Convert to week numbers for slider
    df['week_num'] = ((df['date'] - min_date).dt.days // 7)
    max_week = df['week_num'].max()
    
    week_range = st.sidebar.slider(
        "Date Range (Weeks)",
        min_value=0,
        max_value=int(max_week),
        value=(0, int(max_week))
    )
    
    start_date = min_date + pd.Timedelta(weeks=week_range[0])
    end_date = min_date + pd.Timedelta(weeks=week_range[1])
    st.sidebar.caption(f"From: {start_date.strftime('%Y-%m-%d')}  ")
    st.sidebar.caption(f"To: {end_date.strftime('%Y-%m-%d')}")
    
    # Show targets toggle
    show_targets = st.sidebar.toggle("Show Targets", value=True)
    
    # Filter data
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    if selected_regions:
        mask &= df['region'].isin(selected_regions)
    filtered_df = df[mask].copy()
    
    if len(filtered_df) == 0:
        st.warning("No data available for selected filters.")
        return
    
    # Row 1 - KPI Tiles
    st.subheader("📈 Key Performance Indicators")
    
    # Calculate metrics
    latest_week = filtered_df['date'].max()
    prev_week = filtered_df[filtered_df['date'] < latest_week]['date'].max()
    
    # Current week data
    curr_data = filtered_df[filtered_df['date'] == latest_week]
    prev_data = filtered_df[filtered_df['date'] == prev_week]
    
    # Aggregate metrics
    total_revenue = curr_data['revenue'].sum()
    prev_revenue = prev_data['revenue'].sum() if len(prev_data) > 0 else total_revenue
    revenue_delta = ((total_revenue / prev_revenue - 1) * 100) if prev_revenue > 0 else 0
    
    avg_vs_target = curr_data['revenue_vs_target'].mean()
    prev_vs_target = prev_data['revenue_vs_target'].mean() if len(prev_data) > 0 else avg_vs_target
    vs_target_delta = avg_vs_target - prev_vs_target
    
    total_units = curr_data['units_sold'].sum()
    prev_units = prev_data['units_sold'].sum() if len(prev_data) > 0 else total_units
    units_delta = ((total_units / prev_units - 1) * 100) if prev_units > 0 else 0
    
    avg_return_rate = curr_data['return_rate'].mean()
    prev_return_rate = prev_data['return_rate'].mean() if len(prev_data) > 0 else avg_return_rate
    return_delta = avg_return_rate - prev_return_rate
    
    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="💰 Total Revenue",
            value=f"₹{total_revenue:,.0f}",
            delta=f"{revenue_delta:+.1f}%"
        )
    
    with col2:
        st.metric(
            label="🎯 Revenue vs Target",
            value=f"{avg_vs_target:+.1f}%",
            delta=f"{vs_target_delta:+.1f}pp"
        )
    
    with col3:
        st.metric(
            label="📦 Units Sold",
            value=f"{total_units:,}",
            delta=f"{units_delta:+.1f}%"
        )
    
    with col4:
        st.metric(
            label="↩️ Return Rate",
            value=f"{avg_return_rate:.2f}%",
            delta=f"{return_delta:+.2f}pp",
            delta_color="inverse"
        )
    
    st.caption("Deltas show change vs previous week")
    st.divider()
    
    # Row 2 - Charts
    st.subheader("📊 Trends & Breakdown")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        # Weekly revenue line chart
        weekly_agg = filtered_df.groupby('date').agg({
            'revenue': 'sum',
            'revenue_target': 'sum',
            'is_anomaly': 'any'
        }).reset_index()
        
        fig1 = go.Figure()
        
        # Revenue line
        fig1.add_trace(go.Scatter(
            x=weekly_agg['date'],
            y=weekly_agg['revenue'],
            mode='lines+markers',
            name='Revenue',
            line=dict(color='#1A56DB', width=2),
            marker=dict(size=6)
        ))
        
        # Target line (if toggle on)
        if show_targets:
            fig1.add_trace(go.Scatter(
                x=weekly_agg['date'],
                y=weekly_agg['revenue_target'],
                mode='lines',
                name='Target',
                line=dict(color='#9CA3AF', width=2, dash='dash')
            ))
        
        # Anomaly highlights
        anomalies = weekly_agg[weekly_agg['is_anomaly']]
        if len(anomalies) > 0:
            fig1.add_trace(go.Scatter(
                x=anomalies['date'],
                y=anomalies['revenue'],
                mode='markers',
                name='Anomaly',
                marker=dict(color='#EF4444', size=12, symbol='x')
            ))
        
        fig1.update_layout(
            title="Weekly Revenue Trend",
            xaxis_title="Week",
            yaxis_title="Revenue (₹)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=80, b=40),
            height=350
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        st.caption("Red X markers indicate anomalous weeks (>2σ above mean)")
    
    with col_chart2:
        # Revenue by region stacked bar
        pivot_df = filtered_df.pivot_table(
            index='date',
            columns='region',
            values='revenue',
            aggfunc='sum'
        ).reset_index()
        
        fig2 = go.Figure()
        colors = {'North': '#1A56DB', 'South': '#3B82F6', 'East': '#60A5FA', 'West': '#93C5FD'}
        
        for region in pivot_df.columns[1:]:
            fig2.add_trace(go.Bar(
                x=pivot_df['date'],
                y=pivot_df[region],
                name=region,
                marker_color=colors.get(region, '#1A56DB')
            ))
        
        fig2.update_layout(
            title="Revenue by Region (Stacked)",
            xaxis_title="Week",
            yaxis_title="Revenue (₹)",
            barmode='stack',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=80, b=40),
            height=350
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        st.caption("South region underperformance visible in Q3 onwards")
    
    st.divider()
    
    # Row 3 - Detail Table
    st.subheader("📋 Weekly Detail Data")
    
    # Prepare display data
    display_df = filtered_df.copy()
    display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
    display_df['revenue'] = display_df['revenue'].apply(lambda x: f"₹{x:,.0f}")
    display_df['revenue_target'] = display_df['revenue_target'].apply(lambda x: f"₹{x:,.0f}")
    display_df['revenue_vs_target'] = display_df['revenue_vs_target'].apply(lambda x: f"{x:+.1f}%")
    display_df['units_vs_target'] = display_df['units_vs_target'].apply(lambda x: f"{x:+.1f}%")
    display_df['return_rate'] = display_df['return_rate'].apply(lambda x: f"{x:.2f}%")
    display_df['revenue_per_staff_hour'] = display_df['revenue_per_staff_hour'].apply(lambda x: f"₹{x:.0f}")
    
    # Rename columns
    display_df = display_df.rename(columns={
        'date': 'Week',
        'region': 'Region',
        'revenue': 'Revenue',
        'revenue_target': 'Target',
        'revenue_vs_target': 'vs Target',
        'units_sold': 'Units',
        'units_target': 'Units Target',
        'units_vs_target': 'Units vs Target',
        'returns': 'Returns',
        'return_rate': 'Return %',
        'staff_hours': 'Staff Hours',
        'revenue_per_staff_hour': 'Revenue/Hour',
        'is_anomaly': 'Anomaly'
    })
    
    # Select columns to show
    show_cols = ['Week', 'Region', 'Revenue', 'Target', 'vs Target', 
                 'Units', 'Units vs Target', 'Return %', 'Anomaly']
    
    st.dataframe(
        display_df[show_cols],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Anomaly": st.column_config.CheckboxColumn("Anomaly"),
        }
    )
    st.caption("Table shows all weekly records. Anomaly column indicates statistical outliers.")
    
    st.divider()
    
    # Row 4 - Export
    st.subheader("💾 Export Data")
    
    # Prepare CSV export
    export_df = filtered_df.copy()
    export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
    
    csv = export_df.to_csv(index=False)
    
    col_export1, col_export2 = st.columns([1, 3])
    with col_export1:
        st.download_button(
            label="📥 Download as CSV",
            data=csv,
            file_name=f"kpi_dashboard_export_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_export2:
        st.caption(f"Export includes {len(export_df)} rows matching current filters.")

if __name__ == '__main__':
    from datetime import datetime
    main()
