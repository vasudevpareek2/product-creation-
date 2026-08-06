import csv
import sys
import io

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Read the CSV exactly as the script does
with open('../uploads/products_from_sheet.csv', newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    print("CSV field names:", reader.fieldnames)
    print("\nFirst row raw data:")
    first_row = next(reader)
    for key, value in first_row.items():
        print(f"  '{key}': '{value}' (repr: {repr(value)})")
    
    # Check specifically for location
    print(f"\nLocation field value: '{first_row.get('location')}'")
    print(f"Location field repr: {repr(first_row.get('location'))}")
    print(f"Location field type: {type(first_row.get('location'))}")
    print(f"Location field length: {len(first_row.get('location', ''))}")