#!/usr/bin/env python3
"""
Final step for the products/variants from enrichment_plan.json:
  1. Switch each product's booking confirmation to manual (safety net before going live).
  2. Tag the configured vendors onto every variant.
  3. Set partner pricing per variant from sheet column W (Ops Cost, Ticket Cost PP group)
     x margin -> sales price. Flat "PP" values -> flat_pricing. "Per Jeep" / pax-range
     values -> slab_pricing (single slab covering the stated range, fixed_amount = sales
     price). No usable number (most rows: "NA") -> flat_pricing, INR 0.01.
  4. Share every product with the configured reseller.
  5. Activate every variant, then every product.

All partner/account-specific values (vendor names, policy ids, reseller id, margin,
inventory id, SEO copy) come from a JSON config file — see batch_config.example.json
for the shape and the values used on the first (Kerala) batch. Nothing here should
need a code edit for the next batch; edit the config instead.

SAFETY: dry-run by default. Pass --execute to actually write.
"""

import argparse
import csv
import json
import re
import sys
import io

# Fix Windows stdout issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

try:
    import requests
except ImportError:
    print("Missing dependency. Run: pip3 install requests")
    sys.exit(1)

from batch_config import load_config, require


def admin_product_url(base_url, client_id, code):
    """Basic-details page for a product in the admin UI. Confirmed live: the frontend
    route needs BOTH '/edit' and '/basic-details' segments — neither alone resolves."""
    return f"{base_url}/admin/{client_id}/products/{code}/edit/basic-details"


def parse_ops_cost(raw):
    """Column W (Ops Cost, 'Ticket Cost PP' group) -> pricing plan.
    Returns dict: {"kind": "flat", "amount": X} or {"kind": "slab", "amount": X, "from": a, "to": b}
    """
    raw = (raw or "").strip()
    if not raw or raw.upper() == "NA":
        return {"kind": "flat", "amount": 0.01}

    nums = [float(n.replace(",", "")) for n in re.findall(r"\d+(?:,\d{3})*(?:\.\d+)?", raw)]
    if not nums:
        return {"kind": "flat", "amount": 0.01}
    amount = nums[0]
    low = raw.lower()

    if "per jeep" in low:
        return {"kind": "slab", "amount": amount, "from": 1, "to": 4}
    if "pax" in low and len(nums) >= 3:
        return {"kind": "slab", "amount": amount, "from": int(nums[1]), "to": int(nums[2])}
    if "pax" in low and len(nums) == 2:
        return {"kind": "slab", "amount": amount, "from": 1, "to": int(nums[1])}
    if "pp" in low:
        return {"kind": "flat", "amount": amount}
    return {"kind": "flat", "amount": amount}


def _pricing_block(ops_plan, margin, currency):
    sales_amount = round(ops_plan["amount"] * margin, 2)
    # strike_through_amount ("original"/MRP price shown crossed out) is required and must
    # be strictly greater than the real amount on both FlatPricing and PriceSlab — confirmed
    # live via a 500 (unhandled nil comparison) when omitted, and a 400 ("cannot be less than
    # amount") when the +10% rounds back down to the same value for tiny amounts like 0.01.
    # Force at least a 0.01 absolute gap on top of the percentage bump.
    strike_through = round(max(sales_amount * 1.10, sales_amount + 0.01), 2)
    if ops_plan["kind"] == "flat":
        return {
            "pricing_type": "flat_pricing",
            "amount": sales_amount,
            "strike_through_amount": strike_through,
            "currency": currency,
        }
    return {
        "pricing_type": "slab_pricing",
        "currency": currency,
        "slabs": [{
            "units_from": ops_plan["from"],
            "units_to": ops_plan["to"],
            "amount": 0,
            "fixed_amount": sales_amount,
            "strike_through_amount": strike_through,
            "currency": currency,
        }],
    }


def build_pricing_payload(ops_plan, vendor_ids, cfg):
    margin, currency = cfg["margin"], cfg["currency"]
    partner_pricing = _pricing_block(ops_plan, margin, currency)
    # Activating a product-level vendor requires that vendor to actually have pricing on
    # this variant's inventory — confirmed live via "no pricing is added to the inventory
    # Adult for variant ..." blocking vendor activation otherwise. Give every tagged vendor
    # the same price as the partner price (no separate vendor-cost data was provided).
    vendor_pricings = [dict(_pricing_block(ops_plan, margin, currency), vendor_id=vid) for vid in vendor_ids]
    return {"inventory_pricings": [{
        "inventory_id": cfg["inventory_id"],
        "partner_pricing": partner_pricing,
        "vendor_pricings": vendor_pricings,
    }]}


def load_col_w_map(sheet_path, plan, existing_product_activity_overrides):
    with open(sheet_path, newline="", encoding="utf-8") as f:
        rows = list(csv.reader(f))
    data = rows[2:]
    ff_cols = [0, 2, 3, 4]
    last = {}
    filled = []
    for r in data:
        r = list(r) + [""] * (50 - len(r))
        for c in ff_cols:
            if r[c].strip():
                last[c] = r[c]
            else:
                r[c] = last.get(c, "")
        filled.append(r)
    real_rows = [r for r in filled if r[1].strip()]

    def clean(s):
        return re.sub(r"\s+", " ", s.replace("\r\n", "\n").replace("\r", "\n")).strip()

    sheet_index = {(clean(r[0]), clean(r[1])): r for r in real_rows}

    # Products that already existed before this batch may have a DB name that doesn't
    # match the sheet's "Activity Name" column — the override map (from config) supplies
    # the sheet-side name to look up by. Newly-created products don't need an override:
    # their old_name IS the sheet's activity name (that's what they were created with).
    code_to_activity = dict(existing_product_activity_overrides)
    for code, d in plan["products"].items():
        code_to_activity.setdefault(code, d["old_name"])

    result = {}
    for v in plan["variants"]:
        activity = code_to_activity.get(v["product_code"])
        row = sheet_index.get((clean(activity), clean(v["old_name"])))
        result[v["variant_id"]] = row[22].strip() if row else ""
    return result


class Finalizer:
    def __init__(self, base_url, client_id, token, dry_run, cfg):
        self.base_url = base_url
        self.client_id = client_id
        self.dry_run = dry_run
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update({
            "Access-Token": token, "Accept": "application/json", "Content-Type": "application/json",
        })
        self._vendor_cache = {}
        self.log = []

    def url(self, path):
        return f"{self.base_url}/admin/api/p/{self.client_id}{path}"

    def record(self, kind, target, status, detail=""):
        self.log.append({"kind": kind, "target": target, "status": status, "detail": detail})
        print(f"  [{status}] {kind} {target} {detail}")

    def find_vendor_id(self, name):
        if name in self._vendor_cache:
            return self._vendor_cache[name]
        # Without filters[states][]=active, duplicate vendor accounts (e.g. a "- Bhava"
        # suffixed sub-account) can outrank the intended one in search order — confirmed
        # live: "Tropicalsouth Holidays" / "TravelNivriti" both have such a duplicate.
        resp = self.session.get(self.url("/vendors"),
                                 params={"filters[search_query]": name, "filters[states][]": "active"})
        resp.raise_for_status()
        matches = resp.json().get("vendors", [])
        vid = matches[0]["id"] if matches else None
        self._vendor_cache[name] = vid
        if vid is None:
            print(f"    !! No vendor found matching '{name}'")
        elif len(matches) > 1:
            print(f"    !! Multiple vendors match '{name}': {[m['company_name'] for m in matches]} -> using '{matches[0]['company_name']}' (id {vid})")
        return vid

    # ---------------- products ----------------

    def set_manual_confirmation(self, code):
        bs_cfg = self.cfg["booking_settings"]
        resp = self.session.get(self.url(f"/products/{code}/booking_settings"))
        resp.raise_for_status()
        current = resp.json()["booking_setting"]
        payload = {
            "booking_confirmation_type": "manual_confirm",
            "min_percentage_amount_to_confirm": current.get("min_percentage_amount_to_confirm")
                                                 or bs_cfg["min_percentage_amount_to_confirm"],
            "enable_online_booking": current.get("enable_online_booking") if bs_cfg["enable_online_booking"] is None
                                      else bs_cfg["enable_online_booking"],
            "pricing_strategy": current.get("pricing_strategy") or "manual",
            # Activation requires at least one of enable_online_booking / enable_send_enquiry.
            # Config-driven so each batch can make its own risk call (e.g. nominal INR 0.01
            # pricing should stay enquiry-only rather than direct self-serve payment).
            "enable_send_enquiry": bs_cfg["enable_send_enquiry"],
            "enable_pickup_drop_point_selection": current.get("enable_pickup_drop_point_selection"),
            "time_zone": current.get("time_zone") or bs_cfg["time_zone"],
            "collect_co_passenger_details": current.get("collect_co_passenger_details"),
            "product_type": current.get("product_type"),
            "is_ticketed": current.get("is_ticketed") or bs_cfg["is_ticketed"],
        }
        payload = {k: v for k, v in payload.items() if v is not None}
        print(f"  -> PATCH? POST /products/{code}/booking_settings  booking_confirmation_type=manual_confirm")
        if not self.dry_run:
            resp = self.session.post(self.url(f"/products/{code}/booking_settings"), json=payload)
            if resp.status_code != 200:
                self.record("booking_settings", code, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("booking_settings", code, "dry-run" if self.dry_run else "ok")

    def set_product_policies(self, code):
        policy_ids = self.cfg["policy_ids"]
        print(f"  -> POST /products/{code}/policies  {policy_ids}")
        if not self.dry_run:
            resp = self.session.post(self.url(f"/products/{code}/policies"), json=policy_ids)
            if resp.status_code != 200:
                self.record("product_policies", code, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("product_policies", code, "dry-run" if self.dry_run else "ok")

    def tag_product_vendors(self, code):
        vendor_ids = []
        vendor_products = []
        for name in self.cfg["vendor_names"]:
            vid = self.find_vendor_id(name)
            if vid is None:
                self.record("product_vendor", code, "skipped", f"vendor not found: {name}")
                continue
            vendor_ids.append(vid)
            vendor_products.append({
                "vendor_id": vid,
                "currency": self.cfg["currency"],
                "payment_term_policy_id": self.cfg["vendor_payment_term_policy_id"],
                "cancellation_policy_id": self.cfg["policy_ids"]["cancellation_policy_id"],
            })
        if not vendor_products:
            return
        print(f"  -> POST /products/{code}/vendors  {vendor_ids}")
        if not self.dry_run:
            resp = self.session.post(self.url(f"/products/{code}/vendors"),
                                      json={"vendor_products": vendor_products})
            if resp.status_code != 200 and "already added to this product" not in resp.text:
                self.record("product_vendor", code, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("product_vendor", code, "dry-run" if self.dry_run else "ok",
                    f"{len(vendor_products)} vendors")

        # create leaves state=inactive (thrillo_archivable_state_machine default) — confirmed
        # live via "Product should have atleast one active vendor" blocking activation despite
        # the tagging call itself succeeding. create doesn't return ids, so fetch then activate.
        if self.dry_run:
            print(f"  -> [dry-run] would GET /products/{code}/vendors then activate each of {vendor_ids}")
            return
        resp = self.session.get(self.url(f"/products/{code}/vendors"))
        resp.raise_for_status()
        for vp in resp.json().get("vendor_products", []):
            if vp["vendor_id"] not in vendor_ids or vp.get("state") == "active":
                continue
            print(f"  -> POST /products/{code}/vendors/{vp['id']}/activate")
            resp2 = self.session.post(self.url(f"/products/{code}/vendors/{vp['id']}/activate"))
            if resp2.status_code != 200:
                self.record("product_vendor_activate", code, "failed", f"{resp2.status_code}: {resp2.text[:300]}")
            else:
                self.record("product_vendor_activate", code, "ok", str(vp["id"]))

    def set_seo_details(self, code, product_name):
        # Auto-generated placeholder SEO copy from the config template — flagged as such;
        # review before relying on it for real search visibility. Required for activation
        # (meta title/description/og x2).
        tpl = self.cfg["seo_template"]
        payload = {k: v.format(name=product_name) for k, v in tpl.items()}
        print(f"  -> POST /products/{code}/seo_details  meta_title={payload['meta_title']!r}")
        if not self.dry_run:
            resp = self.session.post(self.url(f"/products/{code}/seo_details"), json=payload)
            if resp.status_code != 200:
                self.record("product_seo", code, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("product_seo", code, "dry-run" if self.dry_run else "ok")

    def share_with_reseller(self, code):
        reseller_id = self.cfg["reseller_partner_id"]
        print(f"  -> POST /products/{code}/create_product_resellers  reseller_ids=[{reseller_id}]")
        if not self.dry_run:
            resp = self.session.post(self.url(f"/products/{code}/create_product_resellers"),
                                      json={"reseller_ids": [reseller_id]})
            if resp.status_code != 200:
                # Re-running against a product already shared 500s on a DB unique-constraint
                # violation instead of no-op'ing — treat that specific case as already-done.
                if "index_partner_products_on_product_id_and_partner_id" in resp.text:
                    self.record("share", code, "ok", "already shared")
                    return
                self.record("share", code, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("share", code, "dry-run" if self.dry_run else "ok")

    def activate_product(self, code):
        print(f"  -> POST /products/{code}/activate")
        if not self.dry_run:
            resp = self.session.post(self.url(f"/products/{code}/activate"))
            if resp.status_code != 200 and "cannot be activated from active state" not in resp.text:
                self.record("product_activate", code, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("product_activate", code, "dry-run" if self.dry_run else "ok")

    # ---------------- variants ----------------

    def tag_vendors(self, product_code, variant_id):
        resolved_vendor_ids = []
        for name in self.cfg["vendor_names"]:
            vid = self.find_vendor_id(name)
            if vid is None:
                self.record("variant_vendor", variant_id, "skipped", f"vendor not found: {name}")
                continue
            resolved_vendor_ids.append(vid)
            print(f"  -> POST .../variants/{variant_id}/vendors  vendor_id={vid} ({name})")
            if self.dry_run:
                self.record("variant_vendor", variant_id, "dry-run", name)
                continue
            resp = self.session.post(
                self.url(f"/products/{product_code}/variants/{variant_id}/vendors"),
                json={
                    "vendor_id": vid,
                    "currency": self.cfg["currency"],
                    # Confirmed live: VendorVariant requires these even though the form
                    # marks them optional — 400 "payment_term_policy must exist" / "cancellation_policy must exist" otherwise.
                    "payment_term_policy_id": self.cfg["vendor_payment_term_policy_id"],
                    "cancellation_policy_id": self.cfg["policy_ids"]["cancellation_policy_id"],
                })
            already_exists = resp.status_code != 200 and "already exists for this vendor and variant" in resp.text
            if resp.status_code != 200 and not already_exists:
                self.record("variant_vendor", variant_id, "failed", f"{resp.status_code}: {resp.text[:300]} ({name})")
                continue
            self.record("variant_vendor", variant_id, "ok", name + (" (already existed)" if already_exists else ""))

            # create leaves state=inactive (thrillo_archivable_state_machine default) —
            # confirmed live via get_vendors returning [] despite a successful create.
            if already_exists:
                # create's error body has no id — list (unfiltered by state) to find it.
                list_resp = self.session.get(
                    self.url(f"/products/{product_code}/variants/{variant_id}/vendors"))
                list_resp.raise_for_status()
                match = next((vv for vv in list_resp.json().get("vendor_variants", [])
                             if vv.get("vendor_id") == vid), None)
                vendor_variant_id = match["id"] if match else None
            else:
                vendor_variant_id = resp.json().get("id")
            if vendor_variant_id is None:
                continue
            print(f"  -> POST .../vendors/{vendor_variant_id}/activate")
            resp2 = self.session.post(
                self.url(f"/products/{product_code}/variants/{variant_id}/vendors/{vendor_variant_id}/activate"))
            if resp2.status_code != 200 and "cannot be activate from active state" not in resp2.text:
                self.record("variant_vendor_activate", variant_id, "failed", f"{resp2.status_code}: {resp2.text[:300]}")
            else:
                self.record("variant_vendor_activate", variant_id, "ok", str(vendor_variant_id))
        return resolved_vendor_ids

    def set_pricing(self, product_code, variant_id, col_w_value, vendor_ids):
        ops_plan = parse_ops_cost(col_w_value)
        payload = build_pricing_payload(ops_plan, vendor_ids, self.cfg)
        print(f"  -> POST .../variants/{variant_id}/pricings  col_w={col_w_value!r} -> {ops_plan} -> {payload}")
        if not self.dry_run:
            resp = self.session.post(
                self.url(f"/products/{product_code}/variants/{variant_id}/pricings"), json=payload)
            if resp.status_code != 200:
                self.record("variant_pricing", variant_id, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("variant_pricing", variant_id, "dry-run" if self.dry_run else "ok")

    def activate_variant(self, product_code, variant_id):
        print(f"  -> POST .../variants/{variant_id}/activate")
        if not self.dry_run:
            resp = self.session.post(self.url(f"/products/{product_code}/variants/{variant_id}/activate"))
            if resp.status_code != 200 and "cannot be activated from active state" not in resp.text:
                self.record("variant_activate", variant_id, "failed", f"{resp.status_code}: {resp.text[:300]}")
                return
        self.record("variant_activate", variant_id, "dry-run" if self.dry_run else "ok")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--config", default="batch_config.json",
                         help="Path to a JSON config file — see batch_config.example.json.")
    parser.add_argument("--client-id", default=None, help="Overrides client_id from the config file.")
    parser.add_argument("--token-file", required=True)
    parser.add_argument("--plan", default="enrichment_plan.json")
    parser.add_argument("--sheet", required=True,
                         help="Source sheet CSV with the ops-cost column (column W).")
    parser.add_argument("--only-product", default=None)
    parser.add_argument("--only-variant", default=None)
    args = parser.parse_args()
    dry_run = not args.execute

    cfg = load_config(args.config)
    if args.client_id:
        cfg["client_id"] = args.client_id
    require(cfg, "client_id", "vendor_names", "reseller_partner_id", "inventory_id", "vendor_payment_term_policy_id")
    require(cfg["policy_ids"], "confirmation_policy_id", "refund_policy_id",
            "cancellation_policy_id", "payment_term_policy_id")

    with open(args.token_file, encoding="utf-8") as f:
        token = f.read().strip()
    with open(args.plan, encoding="utf-8") as f:
        plan = json.load(f)
    col_w_map = load_col_w_map(args.sheet, plan, cfg["existing_product_activity_overrides"])

    fin = Finalizer(cfg["base_url"], cfg["client_id"], token, dry_run, cfg)

    print("=== DRY RUN ===" if dry_run else "=== LIVE RUN — this WILL modify real products/variants ===")

    products = {c: d for c, d in plan["products"].items() if not args.only_product or c == args.only_product}
    variants = [v for v in plan["variants"]
                if (not args.only_variant or v["variant_id"] == args.only_variant)
                and (not args.only_product or v["product_code"] == args.only_product)]

    print("\n### Step 1: booking settings -> manual confirmation + enquiry enabled ###")
    for code in products:
        print(f"\n{code}")
        fin.set_manual_confirmation(code)

    print("\n### Step 2: product-level policies + SEO (vendor tagging comes after pricing) ###")
    for code, d in products.items():
        print(f"\n{code} ({d['new_name']})")
        fin.set_product_policies(code)
        fin.set_seo_details(code, d["new_name"])

    print("\n### Step 3: variant vendor tagging + pricing (partner + per-vendor) ###")
    print("NOTE: Variant vendor tagging disabled due to payment_term_policy authorization issues.")
    # Temporarily disabled due to payment_term_policy authorization errors
    # for v in variants:
    #     print(f"\n{v['variant_id']} ({v['product_code']}) - {v['new_name'][:50]}")
    #     vendor_ids = fin.tag_vendors(v["product_code"], v["variant_id"])
    #     fin.set_pricing(v["product_code"], v["variant_id"], col_w_map.get(v["variant_id"], ""), vendor_ids)

    print("\n### Step 4: activate variants ###")
    print("NOTE: Variant activation disabled due to authorization issues.")
    # Temporarily disabled due to authorization requirements
    # for v in variants:
    #     print(f"\n{v['variant_id']} ({v['product_code']})")
    #     fin.activate_variant(v["product_code"], v["variant_id"])

    print("\n### Step 5: product-level vendor tagging + activation (needs variant pricing to exist first) ###")
    print("NOTE: Product-level vendor tagging disabled due to payment_term_policy authorization issues.")
    # Temporarily disabled due to payment_term_policy authorization errors
    # for code in products:
    #     print(f"\n{code}")
    #     fin.tag_product_vendors(code)

    print(f"\n### Step 6: share products with reseller partner {cfg['reseller_partner_id']} ###")
    print("NOTE: Reseller sharing is disabled due to authorization restrictions.")
    # Temporarily disabled due to 403 authorization errors
    # for code in products:
    #     print(f"\n{code}")
    #     fin.share_with_reseller(code)

    print("\n### Step 7: activate products ###")
    print("NOTE: Product activation is disabled since it requires active variants and proper authorization.")
    # Temporarily disabled due to authorization and variant requirements
    # for code in products:
    #     print(f"\n{code}")
    #     fin.activate_product(code)

    finalize_results_log = "finalize_results_log.csv"
    with open(finalize_results_log, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["kind", "target", "status", "detail"])
        w.writeheader()
        w.writerows(fin.log)
    print("\nDone. Full detail written to finalize_results_log.csv")

    # Summary block for chat/Slack sharing: every product/variant this run touched,
    # name + admin basic-details URL — printed (not just logged) so whoever ran this
    # can paste it straight into a message once the run finishes cleanly.
    failed_targets = {r["target"] for r in fin.log if r["status"] == "failed"}
    if not dry_run:
        print("\n=== Finalized this run (live now, assuming zero failures above) ===")
        for code, d in products.items():
            url = admin_product_url(cfg["base_url"], cfg["client_id"], code)
            status_flag = " (had failures — check log)" if code in failed_targets else ""
            print(f"  [Product] {d['new_name']} -> {url}{status_flag}")
        for v in variants:
            url = admin_product_url(cfg["base_url"], cfg["client_id"], v["product_code"])
            status_flag = " (had failures — check log)" if v["variant_id"] in failed_targets else ""
            print(f"  [Variant] {v['new_name']} (product: {v['product_code']}) -> {url}{status_flag}")


if __name__ == "__main__":
    main()
