#!/usr/bin/env python3
"""
Bulk product + variant creation script for the Thrillophilia Admin API.

WHAT THIS DOES
  1. Reads products_from_sheet.csv  -> creates each row as a new product.
  2. Reads variants_new_products.csv -> creates a variant on each product
     just created in step 1 (matched via product_row_id).
  3. Reads variants_existing_products.csv -> creates a variant on products
     that already exist (matched via existing_product_code, no creation needed).

SAFETY
  By default this script only PRINTS what it would send — it makes zero
  API calls that change data. Nothing is created until you pass --execute.

HOW TO RUN (if you've never run a Python script before)
  1. Install Python 3 if you don't have it: https://www.python.org/downloads/
  2. Open a terminal, go to this folder, and install the one dependency:
       pip3 install requests
  3. Copy batch_config.example.json to batch_config.json and fill in
     client_id (and anything else that's account-specific — see that file's
     comments). Put the Access-Token in its own file (never in this file or
     on the command line) and pass it via --token-file.
  4. Dry run first (safe, creates nothing):
       python3 create_products_and_variants.py --token-file /path/to/token.txt
  5. Check the printed output and the results log (see below). If it looks
     right, run it for real:
       python3 create_products_and_variants.py --token-file /path/to/token.txt --execute
  6. After it finishes, open results_log.csv in this folder — it lists
     every row with what happened (created / skipped / failed) and why.
"""

import argparse
import csv
import json
import sys
import io
import re
from datetime import date

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip3 install requests")
    sys.exit(1)

from batch_config import load_config, require

"""
WHERE TO GET ACCESS_TOKEN
  This is NOT your admin login password. It's the Access-Token header
  the admin website sends on every request after you log in (an HS256 JWT).
  Ask whoever manages your admin backend how to obtain one for scripting —
  do not attempt to construct one yourself from a signing secret.
"""

import argparse
import csv
import os
import sys
import io
import re
import time
from datetime import date

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip3 install requests")
    sys.exit(1)

from batch_config import DEFAULTS, load_config

# ============================== CONFIG ==============================
# base_url/client_id/the variant defaults below all come from --config
# (see batch_config.example.json) — only the token stays out of the config
# file, since it's a secret and expires every ~24h.
_config_arg = next((a.split("=", 1)[1] if "=" in a else sys.argv[i + 1]
                     for i, a in enumerate(sys.argv) if a == "--config" or a.startswith("--config=")),
                    "batch_config.json")
CFG = load_config(_config_arg) if os.path.exists(_config_arg) else DEFAULTS
BASE_URL = os.environ.get("THRILLO_BASE_URL", CFG["base_url"])
DEFAULT_CLIENT_ID = os.environ.get("THRILLO_CLIENT_ID", CFG["client_id"] or "")
ACCESS_TOKEN = os.environ.get("THRILLO_ACCESS_TOKEN", "PASTE_YOUR_ACCESS_TOKEN_HERE")

# Safer than putting the token on the command line (which lands in shell
# history / process listings): put it in a file and pass --token-file.
_token_file_arg = next((a.split("=", 1)[1] if "=" in a else sys.argv[i + 1]
                         for i, a in enumerate(sys.argv) if a == "--token-file" or a.startswith("--token-file=")), None)
if _token_file_arg:
    with open(_token_file_arg, encoding="utf-8") as _f:
        ACCESS_TOKEN = _f.read().strip()
    print(f"DEBUG: Token loaded from file: {_token_file_arg}")
    print(f"DEBUG: Token length: {len(ACCESS_TOKEN)}")
    print(f"DEBUG: Token preview: {ACCESS_TOKEN[:20]}...{ACCESS_TOKEN[-20:]}")
else:
    print(f"DEBUG: Using environment token, length: {len(ACCESS_TOKEN)}")
# ======================================================================

RESULTS_LOG_CSV = "results_log.csv"

session = requests.Session()
session.headers.update({
    "Access-Token": ACCESS_TOKEN,
    "Accept": "application/json",
    "Content-Type": "application/json",
})

results = []  # each entry: dict(type, source_name, status, detail, url)
CLIENT_ID = DEFAULT_CLIENT_ID  # overwritten in main() from --client-id if passed


def log_result(row_type, name, status, detail="", url=""):
    results.append({"type": row_type, "name": name, "status": status, "detail": detail, "url": url})


def api_url(path):
    return f"{BASE_URL}/admin/api/p/{CLIENT_ID}{path}"


def admin_product_url(code):
    """Basic-details page for a product in the admin UI. Confirmed live: the frontend
    route needs BOTH '/edit' and '/basic-details' segments — neither alone resolves."""
    return f"{BASE_URL}/admin/{CLIENT_ID}/products/{code}/edit/basic-details"


def split_list(value):
    """'a;b;c' -> ['a', 'b', 'c']. Blank/missing -> []."""
    value = (value or "").strip()
    if not value:
        return []
    return [v.strip() for v in value.split(";") if v.strip()]


def to_bool(value):
    return (value or "").strip().upper() == "TRUE"


def to_int_or_none(value):
    value = (value or "").strip()
    return int(value) if value else None


# ------------------- name -> id lookups (autocomplete endpoints) -------------------
# Cache so we don't repeat the same lookup for every row.
_destination_cache = {}
_amenity_cache = {}


def find_destination_id(name):
    name = (name or "").strip()
    if not name:
        return None
    if name in _destination_cache:
        return _destination_cache[name]

    # Try to use config mappings first with numeric IDs
    try:
        from batch_config import load_config
        import sys
        config_path = "batch_config.json"
        if "--config" in sys.argv:
            config_idx = sys.argv.index("--config")
            if config_idx + 1 < len(sys.argv):
                config_path = sys.argv[config_idx + 1]
        
        config = load_config(config_path)
        if "destination_mappings" in config:
            # Case-insensitive matching with substring support
            for key, value in config["destination_mappings"].items():
                if (key.lower() in name.lower() or 
                    name.lower() in key.lower() or
                    key.lower().replace(" ", "") == name.lower().replace(" ", "")):
                    dest_id = value.get("destination_id")
                    if dest_id:
                        print(f"    Using mapped destination: '{name}' -> '{key}' -> {dest_id}")
                        _destination_cache[name] = dest_id
                        return dest_id
    except Exception as e:
        print(f"    !! Error loading destination mappings: {e}")

    # Fallback to API lookup
    resp = session.get(api_url("/destinations"), params={"filters[search_query]": name})
    resp.raise_for_status()
    matches = resp.json().get("destinations", [])
    if not matches:
        print(f"    !! No destination found matching '{name}'")
        _destination_cache[name] = None
        return None
    if len(matches) > 1:
        print(f"    !! Multiple destinations match '{name}': "
              f"{[d.get('name') for d in matches]} -> using '{matches[0].get('name')}'")
    dest_id = matches[0]["id"]
    _destination_cache[name] = dest_id
    return dest_id


def find_amenity_ids(names):
    """Resolve a list of amenity/inclusion names to their ids. Names that
    don't match anything are skipped (and printed) rather than blocking the row."""
    ids = []
    for name in names:
        if name in _amenity_cache:
            amenity_id = _amenity_cache[name]
        else:
            resp = session.get(api_url("/amenities"), params={"filters[search_query]": name})
            resp.raise_for_status()
            matches = resp.json().get("amenities", [])
            amenity_id = matches[0]["id"] if matches else None
            _amenity_cache[name] = amenity_id
            if amenity_id is None:
                print(f"    !! No amenity found matching '{name}' (inclusion skipped — "
                      f"create it in the admin panel first if you need it)")
        if amenity_id is not None:
            ids.append(amenity_id)
    return ids


# ------------------------------- product creation -------------------------------

def build_product_payload(row):
    # Try multiple possible column names for destination
    dest_name = row.get("primary_destination_name") or row.get("location") or row.get("destination")
    dest_id = find_destination_id(dest_name)
    if dest_id is None:
        return None, "no matching destination"

    # Clean up product name (remove trailing spaces, special characters)
    clean_name = re.sub(r'[^\w\s-]', '', row["name"]).strip()
    
    # Check if product already exists by searching for it
    resp = session.get(api_url("/products"), params={"filters[search_query]": clean_name})
    if resp.status_code == 200:
        existing_products = resp.json().get("products", [])
        for product in existing_products:
            if product.get("name") == clean_name:
                return {"existing_product_code": product.get("code")}, "existing_product"

    # Generate slug if not provided
    if not row.get("slug"):
        slug = re.sub(r'[^\w\s-]', '', row["name"]).strip().lower()
        slug = re.sub(r'[-\s]+', '-', slug)
        # Add timestamp to ensure uniqueness
        timestamp = int(time.time())
        row_id = row.get("row_id", "0")
        slug = f"{slug}-{row_id}-{timestamp}"
    else:
        slug = row["slug"]
    
    # Add default overview and description if not provided
    default_overview = f"Experience {clean_name} with our expert guides and premium service."
    default_description = f"Join us for an unforgettable {clean_name} experience. Our professional team ensures you get the most out of your visit with carefully curated itineraries, expert local knowledge, and top-notch service."
    
    payload = {
        "product_type": row.get("product_type") or "activity",  # Default to activity if not specified
        "name": clean_name,
        "slug": slug,
        "primary_destination_id": dest_id,
        "overview": row.get("overview") or default_overview,  # Use default if not provided
        "long_description": row.get("long_description") or default_description,  # Use default if not provided
        "currency": row.get("currency") or "INR",  # Default to INR if not provided
        "trip_difficulty": to_int_or_none(row.get("trip_difficulty")),
        "custom_highlights": split_list(row.get("custom_highlights")),
        "know_before_you_go": split_list(row.get("know_before_you_go")),
        "is_flight_only": to_bool(row.get("is_flight_only")),
        "tour_filter_custom_property_id": to_int_or_none(row.get("tour_filter_custom_property_id")),
        "bookable_period_starts_at": row.get("bookable_period_starts_at") or None,
        "bookable_period_ends_at": row.get("bookable_period_ends_at") or None,
    }
    # accessibility_ids / highlight_ids / things_to_carry / meal_type_ids need their own
    # name->id lookups. Not wired up here since the shipped CSVs don't populate them —
    # if you fill those columns in, resolve them the same way find_destination_id() does
    # (check the actual lookup endpoint for each before assuming the shape).
    for col in ("accessibility_names", "highlight_names", "things_to_carry_names", "meal_type_names"):
        if row.get(col, "").strip():
            print(f"    !! '{col}' has data ({row[col]!r}) but this script doesn't resolve it yet — "
                  f"add a lookup before relying on this field")

    return {k: v for k, v in payload.items() if v not in (None, [])}, None


def create_product(row, dry_run):
    payload, error = build_product_payload(row)
    if error:
        if error == "existing_product":
            existing_code = payload.get("existing_product_code")
            print(f"     Product already exists: {existing_code}")
            return existing_code
        print(f"    SKIPPED: {error}")
        log_result("product", row["name"], "skipped", error)
        return None

    print(f"  -> POST /products   {payload}")
    if dry_run:
        log_result("product", row["name"], "dry-run", "")
        return "DRY-RUN-CODE"

    resp = session.post(api_url("/products"), json=payload)
    if resp.status_code != 200:
        print(f"     FAILED ({resp.status_code}): {resp.text[:400]}")
        log_result("product", row["name"], "failed", f"{resp.status_code}: {resp.text[:300]}")
        return None

    code = resp.json()["product"]["code"]
    url = admin_product_url(code)
    print(f"     OK -> product code = {code}  ({url})")
    log_result("product", row["name"], "created", code, url)
    return code


# ------------------------------- variant creation -------------------------------

def availability_source_wire_values(names):
    """The API request must send the FRIENDLY keys 'partner'/'channel_manager' —
    NOT the model-persisted class-name strings 'Thrillo::Common::Partner'/'Thrillo::Common::Vendor'.
    CreateVariant#variant_params (app/commands/admin/api/create_variant.rb:91-98) does this
    translation server-side:
        availability_sources << 'Thrillo::Common::Partner' if form.availability_sources.include?('partner')
        availability_sources << 'Thrillo::Common::Vendor'  if form.availability_sources.include?('channel_manager')
    Confirmed live: sending the class-name strings directly gets silently translated to an
    empty array and then rejected with "availability_sources must be present."
    """
    wire = []
    for n in names:
        n = n.strip()
        if n in ("partner", "Thrillo::Common::Partner"):
            wire.append("partner")
        elif n in ("channel_manager", "vendor", "Thrillo::Common::Vendor"):
            wire.append("channel_manager")
        else:
            wire.append(n)  # pass through, let the API reject anything truly invalid
    return wire


def build_variant_payload(row):
    # lead_time: the model requires EXACTLY 3 values whenever the variant is created —
    # there's no "omit it" option in practice (confirmed live: omitting it entirely still
    # gets validated against the model's default [] and fails "exactly three values").
    # Default to [0, 0, 0] rather than leaving it out.
    lead_time_cols = ("lead_time_days", "lead_time_hours", "lead_time_minutes")
    lead_time = [to_int_or_none(row.get(c)) or 0 for c in lead_time_cols]

    inclusion_ids = find_amenity_ids(split_list(row.get("inclusion_names")))
    exclusion_ids = find_amenity_ids(split_list(row.get("exclusion_names")))
    amenity_ids = find_amenity_ids(split_list(row.get("amenity_names")))

    # booking_type and inventory_type are optional on the FORM but required by the
    # underlying Variant model for non-occupancy (activity/tour) products — confirmed
    # live via a 400 ("booking_type can't be blank", "inventory_type is not included
    # in the list") when left out. Default sensibly (from config) rather than omitting.
    dv = CFG["default_variant"]
    # Use CSV values if available, otherwise use defaults
    booking_type = row.get("booking_type") if row.get("booking_type") else dv.get("booking_type", "group")
    inventory_type = row.get("inventory_type") if row.get("inventory_type") else dv.get("inventory_type", "pax")
    # min_passenger_count is NOT NULL at the DB level — omitting it doesn't even get a clean
    # 400, it 500s with a raw PG::NotNullViolation. Always send something.
    min_passenger_count = to_int_or_none(row.get("min_passenger_count")) or dv.get("min_passenger_count", 1)
    # availability_sources is required - use default from config if not provided
    availability_sources = availability_source_wire_values(split_list(row.get("availability_sources"))) or availability_source_wire_values(dv.get("availability_sources", []))
    # duration fields - ensure we have at least duration_days set
    duration_days = to_int_or_none(row.get("duration_days")) or dv.get("duration_days", 1)
    duration_type = row.get("duration_type") if row.get("duration_type") else dv.get("duration_type", "days_hours_minutes")
    duration_hours = to_int_or_none(row.get("duration_hours")) or dv.get("duration_hours", 0)
    duration_minutes = to_int_or_none(row.get("duration_minutes")) or dv.get("duration_minutes", 0)

    payload = {
        "name": row["variant_name"],
        "overview": row.get("overview") or f"Premium {row['variant_name']} experience",
        "duration_type": duration_type,
        "duration_days": duration_days,
        "duration_hours": duration_hours,
        "duration_minutes": duration_minutes,
        "duration_nights": to_int_or_none(row.get("duration_nights")),
        "availability_sources": availability_sources,
        "inclusions": [{"id": i} for i in inclusion_ids],
        "exclusions": [{"id": i} for i in exclusion_ids],
        "amenities": [{"id": a} for a in amenity_ids],
        "inventory_type": inventory_type,
        "has_time_slots": to_bool(row.get("has_time_slots")),
        "min_passenger_count": min_passenger_count,
        "max_passenger_count": to_int_or_none(row.get("max_passenger_count")),
        "lead_time": lead_time,
        "booking_type": booking_type,
        "custom_inclusions": split_list(row.get("custom_inclusions")),
        "custom_highlights": split_list(row.get("custom_highlights")),
        "least_priced_inventory": row.get("least_priced_inventory") or None,
        "markup_on_vendor_pricing": to_bool(row.get("markup_on_vendor_pricing")),
        "markup_percentage": to_int_or_none(row.get("markup_percentage")),
        "transfers_included": to_bool(row.get("transfers_included")),
        # Based on existing variant analysis, API expects these field names
        "ticket_type": row.get("ticket_inclusion") or dv["ticket_inclusion"],
        "transfer_type": row.get("transfer_inclusion") or dv["transfer_inclusion"],
        "gallery_media_source": row.get("gallery_media_source") or None,
        "visibility_scopes": split_list(row.get("visibility_scopes")),
        "customer_notes": row.get("customer_notes") or None,
        "internal_notes": row.get("internal_notes") or None,
        # Additional required fields based on API validation
        "visible": True,
        "is_active": True,
    }
    return {k: v for k, v in payload.items() if v not in (None,)}


def create_variant(product_code, row, dry_run):
    payload = build_variant_payload(row)
    label = f"{row['variant_name']} (product {product_code})"

    print(f"  -> POST /products/{product_code}/variants   {payload}")
    if dry_run:
        log_result("variant", label, "dry-run", "")
        return

    resp = session.post(api_url(f"/products/{product_code}/variants"), json=payload)
    if resp.status_code != 200:
        error_data = resp.json()
        error_msg = error_data.get("messages", {}).get("errors", {})
        
        # Skip if variant name already exists (we already created it with correct values)
        if "name" in error_msg and "already present for product" in error_msg["name"]:
            print(f"     SKIPPED: variant with this name already exists")
            log_result("variant", label, "skipped", "variant name already exists")
            return
        
        print(f"     FAILED ({resp.status_code}): {resp.text[:400]}")
        log_result("variant", label, "failed", f"{resp.status_code}: {resp.text[:300]}")
        return

    variant_id = resp.json()["variant"]["id"]
    url = admin_product_url(product_code)
    print(f"     OK -> variant id = {variant_id}  ({url})")
    log_result("variant", label, "created", str(variant_id), url)


# ------------------------------------- main -------------------------------------

def main():
    global CLIENT_ID

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true",
                         help="Actually create things. Without this flag, nothing is created — "
                              "the script only prints what it WOULD send.")
    parser.add_argument("--config", default="batch_config.json",
                         help="Path to a JSON config file — see batch_config.example.json. "
                              "Already loaded once above to set BASE_URL/DEFAULT_CLIENT_ID/defaults; "
                              "listed here only so --help shows it and --client-id below can override it.")
    parser.add_argument("--client-id", default=DEFAULT_CLIENT_ID,
                         help="Partner id, from /admin/<this>/... in the admin URL.")
    parser.add_argument("--token-file", default=None,
                         help="Path to a file containing just the Access-Token. Safer than "
                              "putting the token directly on the command line.")
    parser.add_argument("--products-csv", default="products_from_sheet.csv")
    parser.add_argument("--variants-new-csv", default="variants_new_products.csv")
    parser.add_argument("--variants-existing-csv", default="variants_existing_products.csv")
    args = parser.parse_args()
    dry_run = not args.execute
    CLIENT_ID = args.client_id

    if ACCESS_TOKEN == "PASTE_YOUR_ACCESS_TOKEN_HERE":
        print("Set THRILLO_ACCESS_TOKEN in your environment (or ACCESS_TOKEN in this file) before running.")
        sys.exit(1)

    if dry_run:
        print("=== DRY RUN — nothing will be created. Re-run with --execute when ready. ===\n")
    else:
        print("=== LIVE RUN — this WILL create real products and variants. ===\n")
    print(f"Using client_id={CLIENT_ID}\n")

    row_id_to_code = {}

    print("### Step 1: creating products ###")
    with open(args.products_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(f"\nRow {row['row_id']}: {row['name']}")
            code = create_product(row, dry_run)
            if code:
                row_id_to_code[row["row_id"]] = code

    print("\n### Step 2: creating variants for products just created ###")
    with open(args.variants_new_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(f"\nVariant: {row['variant_name']} (for product_row_id {row['product_row_id']})")
            code = row_id_to_code.get(row["product_row_id"])
            if not code:
                print(f"    SKIPPED: no product was created for row_id {row['product_row_id']}")
                log_result("variant", row["variant_name"], "skipped",
                           f"no product created for row_id {row['product_row_id']}")
                continue
            create_variant(code, row, dry_run)

    print("\n### Step 3: creating variants for already-existing products ###")
    with open(args.variants_existing_csv, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            print(f"\nVariant: {row['variant_name']} (for existing product {row['existing_product_code']})")
            create_variant(row["existing_product_code"], row, dry_run)

    # write results log
    try:
        with open(RESULTS_LOG_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["type", "name", "status", "detail", "url"])
            writer.writeheader()
            writer.writerows(results)
    except Exception as e:
        sys.stderr.write(f"Error writing results log: {e}\n")

    created = sum(1 for r in results if r["status"] == "created")
    failed = sum(1 for r in results if r["status"] == "failed")
    skipped = sum(1 for r in results if r["status"] == "skipped")

    # Summary block for chat/Slack sharing: every successfully created product/variant,
    # name + admin basic-details URL. Not just logged to CSV — printed so whatever ran
    # this (a human or an agent) can paste it straight into a message.
    created_rows = [r for r in results if r["status"] == "created"]
    if created_rows:
        print("\n=== Created this run ===")
        for r in created_rows:
            label = "Product" if r["type"] == "product" else "Variant"
            print(f"  [{label}] {r['name']} -> {r['url']}")


if __name__ == "__main__":
    main()
