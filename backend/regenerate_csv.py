import pandas as pd
import sys
import io

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Read Excel with header=1 to skip the first row
df = pd.read_excel('../uploads/20260805_184621_kerala_batch_input_and_output.xlsx', header=1)

# Clean up column names
df.columns = df.columns.str.strip()

# Add row_id column (required by the script)
df.insert(0, 'row_id', range(1, len(df) + 1))

# Map Excel columns to script expected columns
column_mapping = {
    'Unnamed: 0': 'name',
    'Unnamed: 1': 'variant_name',
    'Unnamed: 2': 'name_backend',
    'Unnamed: 3': 'activity_link',
    'Unnamed: 4': 'slug',
    'Unnamed: 13': 'location',  # Destination names are in column 13
    'Unnamed: 12': 'duration',  # Duration info is in column 12
    'Unnamed: 14': 'day_description',
    'Unnamed: 15': 'customer_notes',
    'Unnamed: 16': 'breakfast_included',
    'Unnamed: 17': 'lunch',
    'Unnamed: 18': 'dinner',
    'Unnamed: 19': 'priced_in_transfer',
    'Unnamed: 20': 'ticket_inclusion'
}

# Rename columns that exist in the mapping
df = df.rename(columns=column_mapping)

# Fix: swap location and duration if they're in wrong columns
if 'location' in df.columns and 'duration' in df.columns:
    # Check if duration column contains destination names
    sample_duration = df['duration'].dropna().iloc[0] if len(df['duration'].dropna()) > 0 else None
    if sample_duration and isinstance(sample_duration, str):
        # If duration looks like a destination name (e.g., "Cochin", "Munnar"), move it to location
        known_destinations = ['Cochin', 'Munnar', 'Thekkady', 'Alleppey', 'Varkala', 'Kovalam', 'Kanniyakumari', 'Rameshwaram', 'Madurai', 'Vagamon', 'Kumarakom']
        if any(dest.lower() in sample_duration.lower() for dest in known_destinations):
            print(f"Detected destination names in duration column, swapping with location")
            df['location'] = df['duration']
            df['duration'] = None  # Clear duration as it actually contained destinations

# Filter out rows without product names
df = df[df['name'].notna() & (df['name'] != '')]

# Reset row_id after filtering
df['row_id'] = range(1, len(df) + 1)

# Prepare products CSV with required columns
products_csv = '../uploads/products_from_sheet.csv'
products_df = df[['row_id', 'name', 'location', 'duration', 'day_description']].copy()
products_df.to_csv(products_csv, index=False)

print(f"Regenerated products CSV with {len(products_df)} rows")
print("Sample data:")
print(products_df.head(10))