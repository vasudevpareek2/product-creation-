#!/usr/bin/env python3
"""
Update enrichment plan with actual product codes from Stage 1 results.
This script reads the Stage 1 results and updates the enrichment plan with real product codes.
"""

import json
import sys
import io

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def update_enrichment_plan(stage1_results_file, enrichment_plan_file, output_file=None):
    """Update enrichment plan with actual product codes from Stage 1"""
    
    try:
        # Read Stage 1 results
        with open(stage1_results_file, 'r') as f:
            stage1_data = json.load(f)
        
        # Read enrichment plan
        with open(enrichment_plan_file, 'r') as f:
            enrichment_plan = json.load(f)
        
        # Create mapping from product names to actual codes
        name_to_code = {}
        for result in stage1_data.get('stage1_results', []):
            if result.get('type') == 'product':
                product_name = result.get('name', '').strip()
                product_code = result.get('detail', '').strip()
                if product_name and product_code:
                    name_to_code[product_name] = product_code
        
        print(f"Found {len(name_to_code)} product codes from Stage 1 results")
        
        # Update enrichment plan with actual codes
        updated_products = {}
        for key, product_data in enrichment_plan.get('products', {}).items():
            old_name = product_data.get('old_name', '').strip()
            
            # Try to find matching product code
            if old_name in name_to_code:
                actual_code = name_to_code[old_name]
                updated_products[actual_code] = product_data
                print(f"Updated {old_name} -> {actual_code}")
            else:
                # Keep the original key if no match found
                updated_products[key] = product_data
                print(f"No match found for {old_name}, keeping original key")
        
        # Update the enrichment plan
        enrichment_plan['products'] = updated_products
        
        # Write updated plan
        output_file = output_file or enrichment_plan_file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enrichment_plan, f, indent=2, ensure_ascii=False)
        
        print(f"Updated enrichment plan saved to: {output_file}")
        return enrichment_plan
        
    except Exception as e:
        print(f"Error updating enrichment plan: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python update_enrichment_plan.py <stage1_results.json> <enrichment_plan.json> [output_file]")
        sys.exit(1)
    
    stage1_results_file = sys.argv[1]
    enrichment_plan_file = sys.argv[2]
    output_file = sys.argv[3] if len(sys.argv) > 3 else None
    
    update_enrichment_plan(stage1_results_file, enrichment_plan_file, output_file)