import csv
import sys
import io

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Read the CSV exactly as the script does
with open('../uploads/products_from_sheet.csv', newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    print("CSV columns:", reader.fieldnames)
    print("\nFirst 5 rows:")
    for i, row in enumerate(reader):
        if i >= 5:
            break
        print(f"\nRow {i+1}:")
        for key, value in row.items():
            print(f"  {key}: '{value}' (type: {type(value).__name__})")