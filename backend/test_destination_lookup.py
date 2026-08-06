import sys
import io

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Import the destination lookup function
from create_products_and_variants import find_destination_id

# Test with some location names from our Excel
test_locations = ['Cochin', 'Munnar', 'Thekkady', 'Alleppey', 'Varkala', 'Kovalam', 'Kanniyakumari ', 'Rameshwaram', 'Madurai', 'Vagamon', 'Kumarakom']

print("Testing destination lookup:")
for location in test_locations:
    dest_id = find_destination_id(location)
    print(f"  '{location}' -> {dest_id}")