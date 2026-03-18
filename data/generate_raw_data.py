"""
Generate raw data for KPI Dashboard project.
Creates sales_raw.csv and targets_raw.csv with realistic retail data.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

np.random.seed(42)

# Create directories if they don't exist
os.makedirs('data/raw', exist_ok=True)

# Configuration
REGIONS = ['North', 'South', 'East', 'West']
STORES_PER_REGION = 8
CATEGORIES = ['Electronics', 'Apparel', 'Food', 'Home']
START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2024, 12, 31)

# Generate all weeks in 2024
weeks = []
current = START_DATE
while current <= END_DATE:
    weeks.append(current)
    current += timedelta(days=7)

print(f"Generating data for {len(weeks)} weeks...")

# Generate sales data
sales_records = []
store_id = 0

for region in REGIONS:
    for store_num in range(STORES_PER_REGION):
        store_id += 1
        store_name = f"{region}_STORE_{store_num+1:02d}"
        
        # Base performance varies by region
        base_revenue = {'North': 50000, 'South': 45000, 'East': 48000, 'West': 52000}[region]
        
        for week_idx, week_start in enumerate(weeks):
            quarter = (week_start.month - 1) // 3 + 1
            
            # Seasonality: higher in Q4, lower in Q2
            seasonality = 1.0
            if quarter == 4:
                seasonality = 1.3
            elif quarter == 2:
                seasonality = 0.85
            
            # South underperforms by ~15% starting Q3 (week 27+)
            region_factor = 1.0
            if region == 'South' and week_idx >= 26:
                region_factor = 0.85
            
            # Random weekly variation
            weekly_var = np.random.normal(1.0, 0.1)
            
            # Calculate revenue for this store/week
            revenue = base_revenue * seasonality * region_factor * weekly_var / STORES_PER_REGION
            
            # Units based on revenue (avg price ~500)
            avg_price = np.random.uniform(400, 600)
            units_sold = int(revenue / avg_price)
            
            # Returns ~3-5% of units
            returns = int(units_sold * np.random.uniform(0.03, 0.05))
            
            # Staff hours based on store size and seasonality
            base_hours = 320
            staff_hours = base_hours * seasonality * np.random.uniform(0.9, 1.1)
            
            # Occasional missing staff_hours (to test ETL filling)
            if np.random.random() < 0.02:
                staff_hours = np.nan
            
            # Occasionally negative revenue (to test ETL cleaning)
            if np.random.random() < 0.001:
                revenue = -revenue
            
            # Product category for this record (stores sell all categories)
            category = np.random.choice(CATEGORIES)
            
            sales_records.append({
                'date': week_start.strftime('%Y-%m-%d'),
                'store_id': store_name,
                'region': region,
                'product_category': category,
                'units_sold': units_sold,
                'revenue': round(revenue, 2),
                'returns': returns,
                'staff_hours': round(staff_hours, 1) if not np.isnan(staff_hours) else None
            })

# Create 3 anomalous weeks with revenue spikes
anomaly_weeks = [12, 28, 45]  # Week indices for anomalies
for idx in anomaly_weeks:
    week_start = weeks[idx]
    # Add spike to random stores in random regions
    for _ in range(5):
        random_record = np.random.randint(0, len(sales_records))
        if sales_records[random_record]['date'] == week_start.strftime('%Y-%m-%d'):
            sales_records[random_record]['revenue'] *= 2.5
            sales_records[random_record]['units_sold'] = int(sales_records[random_record]['units_sold'] * 2.5)

sales_df = pd.DataFrame(sales_records)
print(f"Generated {len(sales_df)} sales records")

# Generate targets data
target_records = []

for week_start in weeks:
    quarter = (week_start.month - 1) // 3 + 1
    week_num = (week_start - START_DATE).days // 7
    
    for region in REGIONS:
        # Base target
        base_target = {'North': 400000, 'South': 360000, 'East': 384000, 'West': 416000}[region]
        
        # Targets increase slightly each quarter
        quarter_lift = 1 + (quarter - 1) * 0.03
        
        revenue_target = base_target * quarter_lift
        
        # Units target based on avg price of 500
        units_target = int(revenue_target / 500)
        
        target_records.append({
            'week': week_start.strftime('%Y-%m-%d'),
            'region': region,
            'revenue_target': round(revenue_target, 2),
            'units_target': units_target
        })

targets_df = pd.DataFrame(target_records)
print(f"Generated {len(targets_df)} target records")

# Save to CSV
sales_df.to_csv('data/raw/sales_raw.csv', index=False)
targets_df.to_csv('data/raw/targets_raw.csv', index=False)

print("\nData generation complete!")
print(f"  - data/raw/sales_raw.csv: {len(sales_df)} rows")
print(f"  - data/raw/targets_raw.csv: {len(targets_df)} rows")
