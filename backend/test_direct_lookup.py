from batch_config import load_config

config = load_config('../config/batch_config.json')
destination_mappings = config.get('destination_mappings', {})

# Test matching logic
test_locations = ['Cochin', 'Munnar', 'Thekkady', 'Alleppey', 'Varkala', 'Kovalam', 'Kanniyakumari ', 'Rameshwaram', 'Madurai', 'Vagamon', 'Kumarakom']

print("Testing destination matching logic:")
for location in test_locations:
    location_clean = location.strip()
    matched = False
    for key, value in destination_mappings.items():
        if (key.lower() in location_clean.lower() or 
            location_clean.lower() in key.lower() or
            key.lower().replace(" ", "") == location_clean.lower().replace(" ", "")):
            dest_id = value.get("destination_id")
            print(f"  '{location}' -> '{key}' -> {dest_id}")
            matched = True
            break
    if not matched:
        print(f"  '{location}' -> NO MATCH")