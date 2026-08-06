#!/usr/bin/env python3
"""
Retroactive enrichment for products/variants already created by
create_products_and_variants.py. Reads enrichment_plan.json and, for each
product: renames it and tags it with the configured region. For each
variant: renames it, sets the configured visibility_scopes, tags it with
Attraction records, and opens availability slots through the configured
date.

Renames use a fetch -> transform -> patch pattern: GET the current
basic_details (which reflects everything already persisted), overlay only
the field(s) being changed, then PATCH the full object back — because the
update endpoint overwrites every field with whatever's in the request body,
not just the ones you send (confirmed by reading UpdateVariant/update logic).

Region name, visibility scopes, availability window, and the required
inclusion id all come from a JSON config file — see
batch_config.example.json for the shape and the values used on the first
(Kerala) batch.

SAFETY: dry-run by default. Pass --execute to actually write.
"""

import argparse
import csv
import json
import sys
import io
from datetime import date
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip3 install requests")
    sys.exit(1)

from batch_config import load_config, require

# Import AI service for enrichment
try:
    from services.claude_service import ClaudeService
    AI_AVAILABLE = True
except ImportError:
    print("AI service not available - running without AI enrichment")
    AI_AVAILABLE = False

# Try to load API keys from environment or config
def get_api_keys():
    """Get API keys from environment or config"""
    import os
    from config import settings
    
    keys = {}
    if settings.groq_api_key:
        keys['groq'] = settings.groq_api_key
    if settings.anthropic_api_key:
        keys['anthropic'] = settings.anthropic_api_key
    
    # Also check environment variables
    if 'GROQ_API_KEY' in os.environ:
        keys['groq'] = os.environ['GROQ_API_KEY']
    if 'ANTHROPIC_API_KEY' in os.environ:
        keys['anthropic'] = os.environ['ANTHROPIC_API_KEY']
    
    # Exit if no keys are available
    if not keys:
        print("ERROR: No AI API keys configured. Please set GROQ_API_KEY or ANTHROPIC_API_KEY in .env file")
        sys.exit(1)
    
    return keys


def load_token(token_file):
    with open(token_file, encoding="utf-8") as f:
        return f.read().strip()


def api_url(base_url, client_id, path):
    return f"{base_url}/admin/api/p/{client_id}{path}"


class Enricher:
    def __init__(self, base_url, client_id, token, dry_run, cfg):
        self.base_url = base_url
        self.client_id = client_id
        self.dry_run = dry_run
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update({
            "Access-Token": token,
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        self._region_id = None
        self._attraction_cache = {}
        self.log = []
        
        # Initialize AI service if available
        self.ai_service = None
        if AI_AVAILABLE:
            try:
                # Get API keys
                api_keys = get_api_keys()
                
                # Initialize ClaudeService with explicit API keys
                anthropic_key = api_keys.get('anthropic')
                groq_key = api_keys.get('groq')
                
                if groq_key:
                    print(f"Groq API key configured")
                if anthropic_key:
                    print(f"Anthropic API key configured")
                
                self.ai_service = ClaudeService(
                    anthropic_api_key=anthropic_key,
                    groq_api_key=groq_key
                )
                if self.ai_service.is_available():
                    print("AI enrichment service initialized successfully")
                else:
                    print("AI service available but no API keys configured")
            except Exception as e:
                print(f"Failed to initialize AI service: {e}")

    def url(self, path):
        return api_url(self.base_url, self.client_id, path)

    def record(self, kind, target, status, detail=""):
        self.log.append({"kind": kind, "target": target, "status": status, "detail": detail})
        print(f"  [{status}] {kind} {target} {detail}")

    # ---------------- lookups ----------------

    def find_region_id(self, name):
        if self._region_id is not None:
            return self._region_id
        resp = self.session.get(self.url("/regions"), params={"filters[search_query]": name})
        resp.raise_for_status()
        matches = resp.json().get("regions", [])
        exact = next((r for r in matches if r.get("name") == name), None)
        chosen = exact or (matches[0] if matches else None)
        if chosen is None:
            print(f"    !! No region found matching '{name}'")
            return None
        self._region_id = chosen["id"]
        return self._region_id

    def find_attraction_id(self, name):
        if name in self._attraction_cache:
            return self._attraction_cache[name]
        resp = self.session.get(self.url("/attractions"), params={"filters[search_query]": name})
        resp.raise_for_status()
        matches = resp.json().get("attractions", [])
        attraction_id = matches[0]["id"] if matches else None
        self._attraction_cache[name] = attraction_id
        if attraction_id is None:
            print(f"    !! No attraction found matching '{name}' (skipped)")
        return attraction_id

    # ---------------- products ----------------

    def enrich_product_with_ai(self, code, product_name, destination, duration):
        """Use AI to generate rich content for the product"""
        if not self.ai_service or not self.ai_service.is_available():
            print(f"  -> AI enrichment skipped (no AI service available)")
            return None
        
        try:
            # Run the async AI function in a synchronous context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            result = loop.run_until_complete(
                self.ai_service.generate_product_description(
                    product_name=product_name,
                    destination=destination,
                    activity_type="Sightseeing Tour",
                    duration=duration,
                    special_features=["Customizable", "Professional Guide", "Safe Travel"]
                )
            )
            
            loop.close()
            
            if result.get("success"):
                print(f"  -> AI content generated successfully using {result.get('provider', 'unknown')}")
                return result.get("content")
            else:
                print(f"  -> AI generation failed: {result.get('error', 'Unknown error')}")
                return None
                
        except Exception as e:
            print(f"  -> AI enrichment error: {e}")
            return None

    def rename_and_tag_product(self, code, new_name, enrich_with_ai=False):
        resp = self.session.get(self.url(f"/products/{code}/basic_details"))
        resp.raise_for_status()
        current = resp.json()["product"]

        # Get AI-generated content if requested
        ai_content = None
        if enrich_with_ai:
            destination = current.get("primary_destination", {}).get("name", "Unknown")
            duration = current.get("duration", "Not specified")
            ai_content = self.enrich_product_with_ai(code, new_name, destination, duration)

        # Build payload with current data and AI enhancements
        payload = {
            "product_type": current["product_type"],
            "name": new_name,
            "slug": current["slug"],
            "primary_destination_id": current["primary_destination"]["id"],
            "overview": ai_content.get("overview") if ai_content else current["overview"],
            "long_description": ai_content.get("long_description") if ai_content else current["long_description"],
            "currency": current.get("currency"),
            "trip_difficulty": current.get("trip_difficulty"),
            "custom_highlights": ai_content.get("highlights") if ai_content else [h["name"] for h in current.get("custom_highlights", [])],
            "know_before_you_go": ai_content.get("know_before_you_go") if ai_content else [k["name"] for k in current.get("know_before_you_go", [])],
            "accessibility_ids": [a["id"] for a in current.get("accessibilities", [])],
            "highlight_ids": [h["id"] for h in current.get("highlights", [])],
            "things_to_carry": [{"id": t["id"]} for t in current.get("things_to_carry", [])],
            "meal_type_ids": [m["id"] for m in current.get("meal_types", [])],
        }
        tfcp = current.get("tour_filter_custom_property") or {}
        if tfcp.get("id"):
            payload["tour_filter_custom_property_id"] = tfcp["id"]
        payload = {k: v for k, v in payload.items() if v not in (None,)}

        print(f"  -> PATCH /products/{code}/basic_details  name={new_name!r}")
        if not self.dry_run:
            resp = self.session.patch(self.url(f"/products/{code}/basic_details"), json=payload)
            if resp.status_code != 200:
                self.record("product_rename", code, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("product_rename", code, "dry-run" if self.dry_run else "ok", "AI enriched" if ai_content else "")

        region_name = self.cfg["region_name"]
        region_id = self.find_region_id(region_name)
        if region_id is None:
            self.record("product_region", code, "skipped", "region not found")
            return
        print(f"  -> POST /products/{code}/regions  name={region_name!r} region_id={region_id}")
        if not self.dry_run:
            resp = self.session.post(self.url(f"/products/{code}/regions"),
                                      json={"name": region_name, "region_id": region_id})
            if resp.status_code != 200:
                self.record("product_region", code, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("product_region", code, "dry-run" if self.dry_run else "ok")

    # ---------------- variants ----------------

    def rename_and_retag_variant(self, product_code, variant_id, new_name, attraction_names):
        resp = self.session.get(self.url(f"/products/{product_code}/variants/{variant_id}/basic_details"))
        resp.raise_for_status()
        current = resp.json()  # flat response, no wrapper key (VariantsController#basic_details renders @variant directly)

        payload = {
            "name": new_name,
            "overview": current["overview"],
            "duration_type": current["duration_type"],
            "duration_days": current.get("duration_days"),
            "duration_hours": current.get("duration_hours"),
            "duration_minutes": current.get("duration_minutes"),
            "duration_nights": current.get("duration_nights"),
            "availability_sources": current.get("availability_sources", []),
            "inclusions": [{"id": i} for i in
                           ({inc["id"] for inc in current.get("inclusions", [])} | {self.cfg["required_inclusion_id"]})],
            "exclusions": [{"id": e["id"]} for e in current.get("exclusions", [])],
            "amenities": [{"id": a["id"]} for a in current.get("amenities", [])],
            "inventory_type": current.get("inventory_type"),
            "has_time_slots": current.get("has_time_slots"),
            "min_passenger_count": current.get("min_passenger_count"),
            "max_passenger_count": current.get("max_passenger_count"),
            "lead_time": current.get("lead_time"),
            "booking_type": current.get("booking_type"),
            "custom_inclusions": current.get("custom_inclusions", []),
            "custom_highlights": [h["name"] for h in current.get("custom_highlights", [])],
            "markup_on_vendor_pricing": current.get("markup_on_vendor_pricing"),
            "markup_percentage": current.get("markup_percentage"),
            "transfers_included": current.get("transfers_included"),
            "ticket_inclusion": current.get("ticket_inclusion"),
            "transfer_inclusion": current.get("transfer_inclusion"),
            "gallery_media_source": current.get("gallery_media_source"),
            "customer_notes": current.get("customer_notes"),
            "internal_notes": current.get("internal_notes"),
            # the actual change:
            "visibility_scopes": self.cfg["visibility_scopes"],
        }
        payload = {k: v for k, v in payload.items() if v is not None}

        print(f"  -> PATCH /products/{product_code}/variants/{variant_id}/basic_details  name={new_name!r}")
        if not self.dry_run:
            resp = self.session.patch(
                self.url(f"/products/{product_code}/variants/{variant_id}/basic_details"), json=payload)
            if resp.status_code != 200:
                self.record("variant_rename", variant_id, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("variant_rename", variant_id, "dry-run" if self.dry_run else "ok")

        # attraction tags
        attractions = []
        for i, name in enumerate(attraction_names):
            aid = self.find_attraction_id(name)
            if aid is not None:
                attractions.append({"id": aid, "name": name, "priority": i})
        if attractions:
            print(f"  -> POST .../variants/{variant_id}/attractions  "
                  f"{[a['name'] for a in attractions]}")
            if not self.dry_run:
                resp = self.session.post(
                    self.url(f"/products/{product_code}/variants/{variant_id}/attractions"),
                    json={"attractions": attractions})
                if resp.status_code != 200:
                    self.record("variant_attractions", variant_id, "failed", f"{resp.status_code}: {resp.text[:300]}")
                    return
            self.record("variant_attractions", variant_id, "dry-run" if self.dry_run else "ok",
                        f"{len(attractions)}/{len(attraction_names)} resolved")
        else:
            self.record("variant_attractions", variant_id, "skipped", "no attractions resolved")

        # open availability slots
        open_slots_until = self.cfg["open_slots_until"]
        open_slots_payload = {"open_slots": [{
            "starts_at": date.today().isoformat(),
            "ends_at": open_slots_until,
            # Thrillo::Common::DaysOfWeek expects exactly 7 booleans, in
            # [monday, tuesday, wednesday, thursday, friday, saturday, sunday] order —
            # NOT day-index integers (confirmed live via a 500 NotAnArrayOfBoolean).
            "days_of_week": [True] * 7,
            "exclusions": [],
        }]}
        print(f"  -> POST .../variants/{variant_id}/open_slots  until {open_slots_until}")
        if not self.dry_run:
            resp = self.session.post(
                self.url(f"/products/{product_code}/variants/{variant_id}/open_slots"),
                json=open_slots_payload)
            if resp.status_code != 200:
                self.record("variant_open_slots", variant_id, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("variant_open_slots", variant_id, "dry-run" if self.dry_run else "ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--config", default="batch_config.json",
                         help="Path to a JSON config file — see batch_config.example.json.")
    parser.add_argument("--client-id", default=None, help="Overrides client_id from the config file.")
    parser.add_argument("--token-file", required=True)
    parser.add_argument("--plan", default="enrichment_plan.json")
    parser.add_argument("--only-product", default=None, help="Limit to a single product code (for testing).")
    parser.add_argument("--only-variant", default=None, help="Limit to a single variant id (for testing).")
    parser.add_argument("--use-ai", action="store_true", help="Enable AI-powered content enrichment")
    args = parser.parse_args()
    dry_run = not args.execute

    cfg = load_config(args.config)
    if args.client_id:
        cfg["client_id"] = args.client_id
    require(cfg, "client_id", "region_name", "open_slots_until", "required_inclusion_id", "visibility_scopes")

    token = load_token(args.token_file)
    with open(args.plan, encoding="utf-8") as f:
        plan = json.load(f)

    enricher = Enricher(cfg["base_url"], cfg["client_id"], token, dry_run, cfg)
    
    # Check if AI enrichment is enabled in plan or command line
    use_ai = args.use_ai or plan.get("products", {}).get("ai_settings", {}).get("use_groq", False)
    if use_ai and not AI_AVAILABLE:
        print("Warning: AI enrichment requested but AI service not available")
        use_ai = False

    if dry_run:
        print("=== DRY RUN — nothing will be written ===\n")
    else:
        print("=== LIVE RUN — this WILL modify real products/variants ===\n")

    print("### Products: rename + region tag ###")
    for code, d in plan["products"].items():
        if args.only_product and code != args.only_product:
            continue
        print(f"\n{code}: {d['old_name']!r} -> {d['new_name']!r}")
        enricher.rename_and_tag_product(code, d["new_name"], enrich_with_ai=use_ai)

    print("\n### Variants: rename + visibility + attractions + availability ###")
    if plan.get("variants") and len(plan["variants"]) > 0:
        for v in plan["variants"]:
            if args.only_variant and v.get("variant_id") != args.only_variant:
                continue
            if args.only_product and v.get("product_code") != args.only_product:
                continue
            print(f"\n{v.get('variant_id', 'N/A')} ({v.get('product_code', 'N/A')}): {v.get('old_name', 'N/A')!r} -> {v.get('new_name', 'N/A')!r}")
            enricher.rename_and_retag_variant(v["product_code"], v["variant_id"], v["new_name"], v.get("attraction_names", []))
    else:
        print("No variants to process in enrichment plan.")

    enrichment_results_log = "enrichment_results_log.csv"
    with open(enrichment_results_log, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "target", "status", "detail"])
        w.writeheader()
        w.writerows(enricher.log)
    print("\nDone. Full detail written to enrichment_results_log.csv")


if __name__ == "__main__":
    main()
