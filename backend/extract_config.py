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

# Get detailed policy information
print('=== Getting Policy Details ===')
resp = session.get(f'{base_url}/policies')
if resp.status_code == 200:
    data = resp.json()
    policies = data.get('policies', [])
    print(f'Total policies: {len(policies)}')
    
    # Filter for different policy types
    confirmation_policies = []
    refund_policies = []
    cancellation_policies = []
    payment_term_policies = []
    vendor_payment_term_policies = []
    
    for policy in policies:
        policy_name = policy.get('name', '').lower()
        policy_id = policy.get('id')
        
        if 'confirmation' in policy_name or 'dob' in policy_name:
            confirmation_policies.append({'id': policy_id, 'name': policy.get('name')})
        elif 'refund' in policy_name:
            refund_policies.append({'id': policy_id, 'name': policy.get('name')})
        elif 'cancellation' in policy_name:
            cancellation_policies.append({'id': policy_id, 'name': policy.get('name')})
        elif 'payment term' in policy_name:
            payment_term_policies.append({'id': policy_id, 'name': policy.get('name')})
        elif 'vendor payment' in policy_name:
            vendor_payment_term_policies.append({'id': policy_id, 'name': policy.get('name')})
    
    print(f'\nConfirmation Policies ({len(confirmation_policies)}):')
    for p in confirmation_policies[:5]:
        print(f"  ID: {p['id']}, Name: {p['name']}")
    
    print(f'\nRefund Policies ({len(refund_policies)}):')
    for p in refund_policies[:5]:
        print(f"  ID: {p['id']}, Name: {p['name']}")
    
    print(f'\nCancellation Policies ({len(cancellation_policies)}):')
    for p in cancellation_policies[:5]:
        print(f"  ID: {p['id']}, Name: {p['name']}")
    
    print(f'\nPayment Term Policies ({len(payment_term_policies)}):')
    for p in payment_term_policies[:5]:
        print(f"  ID: {p['id']}, Name: {p['name']}")
    
    print(f'\nVendor Payment Term Policies ({len(vendor_payment_term_policies)}):')
    for p in vendor_payment_term_policies[:5]:
        print(f"  ID: {p['id']}, Name: {p['name']}")

# Get active vendors
print('\n=== Getting Active Vendors ===')
resp = session.get(f'{base_url}/vendors')
if resp.status_code == 200:
    data = resp.json()
    vendors = data.get('vendors', [])
    active_vendors = [v for v in vendors if v.get('state') == 'active']
    print(f'Active vendors ({len(active_vendors)}):')
    for vendor in active_vendors:
        print(f"  ID: {vendor['id']}, Name: {vendor['company_name']}")

# Get recommended inventory (likely "Adult" for activities)
print('\n=== Getting Inventory Options ===')
resp = session.get(f'{base_url}/inventories')
if resp.status_code == 200:
    data = resp.json()
    inventories = data.get('inventories', [])
    print(f'Available inventories:')
    for inv in inventories:
        print(f"  ID: {inv['id']}, Name: {inv['name']}, Code: {inv['code']}, Type: {inv['inventory_type']}")

# Get reseller info (likely Thrillophilia main accounts)
print('\n=== Getting Reseller Info ===')
resp = session.get(f'{base_url}/resellers')
if resp.status_code == 200:
    data = resp.json()
    partners = data.get('partners', [])
    print(f'Thrillophilia-related resellers:')
    for partner in partners:
        if 'thrillophilia' in partner['company_name'].lower():
            print(f"  ID: {partner['id']}, Name: {partner['company_name']}")