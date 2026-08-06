import requests
import json

# Load the access token
with open('../config/access_token.txt', 'r') as f:
    access_token = f.read().strip()

# Create session with authentication
session = requests.Session()
session.headers.update({
    'Access-Token': access_token,
    'Content-Type': 'application/json'
})

client_id = '1'
base_url = 'https://admin.thrillophilia.com/admin/api/p/1'

# Get a product that likely has variants
print('=== Getting products to find one with variants ===')
resp = session.get(f'{base_url}/products')
if resp.status_code == 200:
    products = resp.json()
    print(f'Found {len(products.get("products", []))} products')
    
    # Try to find a product with variants
    for product in products.get("products", [])[:5]:
        product_code = product.get("code")
        print(f'\nChecking product: {product.get("name")} (code: {product_code})')
        
        resp = session.get(f'{base_url}/products/{product_code}/variants')
        if resp.status_code == 200:
            variants_data = resp.json()
            variants = variants_data.get('variants', [])
            print(f'  Variants: {len(variants)}')
            
            if variants:
                first_variant = variants[0]
                print(f'  First variant structure:')
                print(json.dumps(first_variant, indent=2)[:1500])
                
                # Extract key fields
                print(f'\n  Key field values from existing variant:')
                print(f'    inventory_type: {first_variant.get("inventory_type")}')
                print(f'    duration_type: {first_variant.get("duration_type")}')
                print(f'    booking_type: {first_variant.get("booking_type")}')
                print(f'    availability_sources: {first_variant.get("availability_sources")}')
                print(f'    transfer_inclusion: {first_variant.get("transfer_inclusion")}')
                print(f'    ticket_inclusion: {first_variant.get("ticket_inclusion")}')
                break
else:
    print(f'Failed to get products: {resp.status_code}')