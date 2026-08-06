import pandas as pd

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
    'Unnamed: 13': 'location',  # Destination names are in column 13
    'Unnamed: 12': 'duration',  # Duration info is in column 12
}

# Rename columns that exist in the mapping
df = df.rename(columns=column_mapping)

print("Before swap:")
print(f"Location column sample: {df['location'].head(5).tolist()}")
print(f"Duration column sample: {df['duration'].head(5).tolist()}")

# Check if duration column contains destination names
sample_duration = df['duration'].dropna().iloc[0] if len(df['duration'].dropna()) > 0 else None
print(f"\nSample duration value: '{sample_duration}'")
print(f"Is string: {isinstance(sample_duration, str)}")

if sample_duration and isinstance(sample_duration, str):
    known_destinations = ['Cochin', 'Munnar', 'Thekkady', 'Alleppey', 'Varkala', 'Kovalam', 'Kanniyakumari', 'Rameshwaram', 'Madurai', 'Vagamon', 'Kumarakom']
    match_found = any(dest.lower() in sample_duration.lower() for dest in known_destinations)
    print(f"Match found: {match_found}")
    
    if match_found:
        print("Swapping columns")
        df['location'] = df['duration']
        df['duration'] = None

# Filter out rows without product names
df = df[df['name'].notna() & (df['name'] != '')]

print("\nAfter swap and filtering:")
print(df[['row_id', 'name', 'location', 'duration']].head(10))