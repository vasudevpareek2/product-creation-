import sys
import io

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Test the exact logic used in create_products_and_variants.py
import pandas as pd

# Read the CSV
df = pd.read_csv('../uploads/products_from_sheet.csv')

print("Testing destination matching with actual CSV data:")
print(f"CSV columns: {df.columns.tolist()}")
print(f"Number of rows: {len(df)}")

# Test a few rows
for idx, row in df.head(5).iterrows():
    location = row.get('location')
    name = row.get('name')
    print(f"\nRow {idx}: {name}")
    print(f"  Location value: '{location}'")
    print(f"  Location type: {type(location)}")
    print(f"  Is NaN: {pd.isna(location)}")
    
    # Test the matching logic
    if pd.isna(location) or location == '':
        print("  -> Would be skipped (no location)")
    else:
        print(f"  -> Would try to match destination: '{location}'")