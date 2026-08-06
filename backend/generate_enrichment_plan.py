#!/usr/bin/env python3
"""
Generate enrichment plan from Excel data for Stage 2 processing.
This script reads the Excel file and creates an enrichment_plan.json
that can be used by the enrich_batch.py script.
"""

import pandas as pd
import json
import sys
import io

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def generate_enrichment_plan(excel_file, output_file="enrichment_plan.json"):
    """Generate enrichment plan from Excel data"""
    
    try:
        # Read Excel with header=1 to skip the first row
        df = pd.read_excel(excel_file, header=1)
        
        # Clean up column names
        df.columns = df.columns.str.strip()
        
        # Filter rows with product names
        df = df[df.iloc[:, 0].notna() & (df.iloc[:, 0] != '')]
        
        # Create enrichment plan structure
        enrichment_plan = {
            "products": {},
            "variants": [],
            "batch_settings": {
                "process_all_rows": True,
                "skip_existing_enriched": False,
                "enrichment_delay_ms": 100
            },
            "products": {
                "enrichment_fields": [
                    "overview",
                    "long_description", 
                    "highlights",
                    "know_before_you_go",
                    "seo_meta_title",
                    "seo_meta_description",
                    "seo_og_title",
                    "seo_og_description"
                ],
                "ai_settings": {
                    "use_groq": True,
                    "model": "llama-3.1-8b-instant",
                    "max_tokens": 2048
                }
            }
        }
        
        # Process each unique product
        unique_products = df.iloc[:, 0].dropna().unique()
        
        for product_name in unique_products:
            # Create placeholder for product (will be filled with actual product codes after Stage 1)
            product_key = product_name.replace(" ", "_").lower()
            product_rows = df[df.iloc[:, 0] == product_name]
            
            # Get destination and duration from the first row of this product
            if len(product_rows) > 0:
                first_row = product_rows.iloc[0]
                destination = first_row.iloc[12] if pd.notna(first_row.iloc[12]) else "Unknown"
                duration = first_row.iloc[13] if pd.notna(first_row.iloc[13]) else "Not specified"
            else:
                destination = "Unknown"
                duration = "Not specified"
            
            enrichment_plan["products"][product_key] = {
                "old_name": product_name,
                "new_name": product_name,
                "destination": str(destination) if destination != "Unknown" else "Unknown",
                "duration": str(duration) if duration != "Not specified" else "Not specified"
            }
        
        # Process variants
        for _, row in df.iterrows():
            product_name = row.iloc[0]
            variant_name = row.iloc[1] if pd.notna(row.iloc[1]) else f"Standard - {product_name}"
            
            enrichment_plan["variants"].append({
                "product_name": product_name,
                "variant_name": variant_name,
                "old_name": variant_name,
                "new_name": variant_name,
                "enrichment_fields": [
                    "variant_overview",
                    "detailed_description"
                ]
            })
        
        # Write to file with NaN handling
        def default_converter(obj):
            if pd.isna(obj):
                return None
            return str(obj) if not isinstance(obj, (str, int, float, bool, list, dict)) else obj
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(enrichment_plan, f, indent=2, ensure_ascii=False, default=default_converter)
        
        print(f"Generated enrichment plan with {len(unique_products)} products and {len(enrichment_plan['variants'])} variants")
        print(f"Saved to: {output_file}")
        
        return enrichment_plan
        
    except Exception as e:
        print(f"Error generating enrichment plan: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python generate_enrichment_plan.py <excel_file> [output_file]")
        sys.exit(1)
    
    excel_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "enrichment_plan.json"
    
    generate_enrichment_plan(excel_file, output_file)