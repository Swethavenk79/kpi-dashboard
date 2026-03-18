"""
ETL Pipeline for KPI Dashboard.
Transforms raw sales and targets data into weekly summary for dashboard.
"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys
from datetime import datetime

# Set up paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
RAW_DATA_DIR = os.path.join(PROJECT_DIR, 'data', 'raw')
DASHBOARD_DATA_DIR = os.path.join(PROJECT_DIR, 'dashboard', 'data')
DASHBOARD_STATIC_DIR = os.path.join(PROJECT_DIR, 'dashboard', 'static')

# Ensure output directories exist
os.makedirs(DASHBOARD_DATA_DIR, exist_ok=True)
os.makedirs(DASHBOARD_STATIC_DIR, exist_ok=True)

def log_step(step_name, message):
    """Print formatted log message."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {step_name}: {message}")

def load_data():
    """Step 1: Load raw data with validation."""
    log_step("LOAD", "Reading raw data files...")
    
    sales_path = os.path.join(RAW_DATA_DIR, 'sales_raw.csv')
    targets_path = os.path.join(RAW_DATA_DIR, 'targets_raw.csv')
    
    # Check if files exist
    if not os.path.exists(sales_path):
        print(f"ERROR: Sales file not found: {sales_path}")
        sys.exit(1)
    
    if not os.path.exists(targets_path):
        print(f"ERROR: Targets file not found: {targets_path}")
        sys.exit(1)
    
    try:
        sales_df = pd.read_csv(sales_path)
        targets_df = pd.read_csv(targets_path)
        log_step("LOAD", f"✓ Loaded {len(sales_df)} sales rows, {len(targets_df)} target rows")
        return sales_df, targets_df
    except Exception as e:
        print(f"ERROR: Failed to load data: {str(e)}")
        sys.exit(1)

def clean_data(sales_df):
    """Step 2: Clean sales data."""
    log_step("CLEAN", "Cleaning sales data...")
    
    original_count = len(sales_df)
    
    # Fix date parsing
    sales_df['date'] = pd.to_datetime(sales_df['date'])
    
    # Drop rows where revenue is null or negative
    null_revenue = sales_df['revenue'].isnull().sum()
    negative_revenue = (sales_df['revenue'] < 0).sum()
    sales_df = sales_df[sales_df['revenue'].notna() & (sales_df['revenue'] >= 0)].copy()
    
    # Fill missing staff_hours with regional median
    missing_hours = sales_df['staff_hours'].isnull().sum()
    sales_df['staff_hours'] = sales_df.groupby('region')['staff_hours'].transform(
        lambda x: x.fillna(x.median())
    )
    
    dropped = original_count - len(sales_df)
    log_step("CLEAN", f"✓ Dropped {dropped} rows ({null_revenue} null, {negative_revenue} negative revenue)")
    log_step("CLEAN", f"✓ Filled {missing_hours} missing staff_hours with regional median")
    
    return sales_df

def aggregate_weekly(sales_df):
    """Step 3: Aggregate to weekly level per region."""
    log_step("AGGREGATE", "Aggregating to weekly level...")
    
    weekly_df = sales_df.groupby(['date', 'region']).agg({
        'revenue': 'sum',
        'units_sold': 'sum',
        'returns': 'sum',
        'staff_hours': 'sum'
    }).reset_index()
    
    # Calculate derived metrics
    weekly_df['return_rate'] = (weekly_df['returns'] / weekly_df['units_sold'] * 100).round(2)
    weekly_df['revenue_per_staff_hour'] = (weekly_df['revenue'] / weekly_df['staff_hours']).round(2)
    
    log_step("AGGREGATE", f"✓ Created {len(weekly_df)} weekly records")
    
    return weekly_df

def merge_targets(weekly_df, targets_df):
    """Step 4: Merge with targets and compute vs_target metrics."""
    log_step("MERGE", "Merging with targets...")
    
    # Prepare targets
    targets_df['week'] = pd.to_datetime(targets_df['week'])
    
    # Merge on date/week and region
    merged_df = weekly_df.merge(
        targets_df,
        left_on=['date', 'region'],
        right_on=['week', 'region'],
        how='left'
    ).drop('week', axis=1)
    
    # Calculate vs_target percentages
    merged_df['revenue_vs_target'] = ((merged_df['revenue'] / merged_df['revenue_target'] - 1) * 100).round(2)
    merged_df['units_vs_target'] = ((merged_df['units_sold'] / merged_df['units_target'] - 1) * 100).round(2)
    
    log_step("MERGE", f"✓ Merged targets for {merged_df['revenue_target'].notna().sum()} records")
    
    return merged_df

def detect_anomalies(merged_df):
    """Step 5: Flag anomalous weeks (>2 std dev above mean)."""
    log_step("ANOMALY", "Detecting anomalies...")
    
    # Calculate mean and std for each region
    region_stats = merged_df.groupby('region')['revenue'].agg(['mean', 'std']).reset_index()
    region_stats.columns = ['region', 'revenue_mean', 'revenue_std']
    
    # Merge stats back
    merged_df = merged_df.merge(region_stats, on='region')
    
    # Flag anomalies (revenue > mean + 2*std)
    merged_df['is_anomaly'] = merged_df['revenue'] > (merged_df['revenue_mean'] + 2 * merged_df['revenue_std'])
    
    anomaly_count = merged_df['is_anomaly'].sum()
    log_step("ANOMALY", f"✓ Flagged {anomaly_count} anomalous weeks")
    
    # Clean up temp columns
    merged_df = merged_df.drop(['revenue_mean', 'revenue_std'], axis=1)
    
    return merged_df

def save_outputs(merged_df):
    """Step 6: Save summary CSV and static chart."""
    log_step("SAVE", "Saving outputs...")
    
    # Save weekly summary CSV
    output_path = os.path.join(DASHBOARD_DATA_DIR, 'weekly_summary.csv')
    merged_df.to_csv(output_path, index=False)
    log_step("SAVE", f"✓ Saved {len(merged_df)} rows to dashboard/data/weekly_summary.csv")
    
    # Create static chart
    plt.figure(figsize=(12, 6))
    
    # Pivot for plotting
    pivot_df = merged_df.pivot(index='date', columns='region', values='revenue')
    
    # Plot lines for each region
    for region in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df[region], marker='o', markersize=3, label=region, alpha=0.8)
    
    # Highlight anomalies
    anomalies = merged_df[merged_df['is_anomaly']]
    if len(anomalies) > 0:
        plt.scatter(anomalies['date'], anomalies['revenue'], 
                   color='red', s=100, zorder=5, label='Anomaly', marker='X')
    
    plt.title('Weekly Revenue Trend by Region', fontsize=14, fontweight='bold')
    plt.xlabel('Week')
    plt.ylabel('Revenue (₹)')
    plt.legend(title='Region')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    
    chart_path = os.path.join(DASHBOARD_STATIC_DIR, 'weekly_revenue_trend.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    log_step("SAVE", f"✓ Saved chart to dashboard/static/weekly_revenue_trend.png")

def main():
    """Run the ETL pipeline."""
    print("=" * 60)
    print("KPI Dashboard ETL Pipeline")
    print("=" * 60)
    
    # Run all steps
    sales_df, targets_df = load_data()
    sales_df = clean_data(sales_df)
    weekly_df = aggregate_weekly(sales_df)
    merged_df = merge_targets(weekly_df, targets_df)
    merged_df = detect_anomalies(merged_df)
    save_outputs(merged_df)
    
    print("=" * 60)
    print("ETL Complete! Summary:")
    print(f"  - Raw sales rows: {len(sales_df)}")
    print(f"  - Weekly summary rows: {len(merged_df)}")
    print(f"  - Regions: {', '.join(merged_df['region'].unique())}")
    print(f"  - Date range: {merged_df['date'].min()} to {merged_df['date'].max()}")
    print(f"  - Anomalies detected: {merged_df['is_anomaly'].sum()}")
    print("=" * 60)

if __name__ == '__main__':
    main()
