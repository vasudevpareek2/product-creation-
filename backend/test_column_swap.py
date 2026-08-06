import pandas as pd

df = pd.read_excel('../uploads/20260805_184621_kerala_batch_input_and_output.xlsx', header=1)
df.columns = df.columns.str.strip()
df.insert(0, 'row_id', range(1, len(df) + 1))

column_mapping = {
    'Unnamed: 0': 'name',
    'Unnamed: 1': 'variant_name',
    'Unnamed: 13': 'location',
    'Unnamed: 12': 'duration'
}
df = df.rename(columns=column_mapping)

print("Before swap:")
print(df[['row_id', 'name', 'location', 'duration']].head(10))

# Swap columns if needed
if 'location' in df.columns and 'duration' in df.columns:
    sample_duration = df['duration'].dropna().iloc[0] if len(df['duration'].dropna()) > 0 else None
    if sample_duration and isinstance(sample_duration, str):
        known_destinations = ['Cochin', 'Munnar', 'Thekkady', 'Alleppey', 'Varkala', 'Kovalam', 'Kanniyakumari', 'Rameshwaram', 'Madurai', 'Vagamon', 'Kumarakom']
        if any(dest.lower() in sample_duration.lower() for dest in known_destinations):
            print('Swapping columns')
            df['location'] = df['duration']
            df['duration'] = None

df = df[df['name'].notna() & (df['name'] != '')]

print("\nAfter swap:")
print(df[['row_id', 'name', 'location', 'duration']].head(10))