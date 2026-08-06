import sys
import io

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Test the create_products_and_variants script directly
import subprocess

result = subprocess.run([
    "python", "create_products_and_variants.py",
    "--config", "../config/batch_config.json",
    "--token-file", "../config/access_token.txt",
    "--products-csv", "../uploads/products_from_sheet.csv",
    "--variants-new-csv", "../uploads/variants_new_products.csv",
    "--variants-existing-csv", "../uploads/variants_existing_products.csv",
    "--execute"
], capture_output=True, text=True)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)