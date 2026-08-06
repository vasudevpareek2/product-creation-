"""Shared config loader for the product-creation batch scripts
(create_products_and_variants.py, enrich_batch.py, finalize_batch.py).

Every value in DEFAULTS was hardcoded in the scripts during the first
(Kerala) batch run and discovered live rather than from source alone
(vendor names, policy ids, margin, region, etc.). Centralizing them here
means a new batch only needs a new JSON config file — no code edits.

See batch_config.example.json for the config actually used for the Kerala
batch, as a starting template for the next one.
"""

import json

DEFAULTS = {
    "base_url": "https://admin.thrillophilia.com",
    "client_id": None,

    # enrich_batch.py
    "region_name": None,
    "visibility_scopes": ["ib_builder", "quotation"],
    "open_slots_until": None,
    # Amenity id required on every variant update for activity/tour products
    # (check_inclusions validation only fires on update, not create).
    "required_inclusion_id": None,

    # finalize_batch.py
    "vendor_names": [],
    "reseller_partner_id": None,
    "inventory_id": None,
    "margin": 1.0,
    "currency": "INR",
    "policy_ids": {
        "confirmation_policy_id": None,
        "refund_policy_id": None,
        "cancellation_policy_id": None,
        "payment_term_policy_id": None,
    },
    # VendorProduct/VendorVariant.payment_term_policy is a DIFFERENT model
    # class (Thrillo::Common::VendorPaymentTermPolicy) than the regular
    # payment_term_policy_id above — resolve separately via
    # filters[policy_types][]=vendor_payment_term_policy.
    "vendor_payment_term_policy_id": None,

    "default_variant": {
        "booking_type": "group",
        "inventory_type": "pax",
        "min_passenger_count": 1,
        "transfer_inclusion": "Not Included",
        "ticket_inclusion": "Not Ticketed",
        "availability_sources": ["partner"],
        "duration_type": "days_hours_minutes",
        "duration_days": 1,
        "duration_hours": 0,
        "duration_minutes": 0
    },
    "booking_settings": {
        "enable_send_enquiry": True,
        "enable_online_booking": None,
        "is_ticketed": "no",
        "time_zone": "Asia/Kolkata",
        "min_percentage_amount_to_confirm": 100,
    },
    "seo_template": {
        "meta_title": "{name} | Book Now",
        "meta_description": "Book {name} today. Reserve your spot now.",
        "og_title": "{name}",
        "og_description": "Explore {name} with a guided tour of the top local attractions.",
    },
    # product_code -> the exact "Activity Name" string used in the source
    # sheet's column A, for products that already existed before this batch
    # (so their sheet row can be found even though their DB name differs
    # from the sheet's activity name). Leave empty for a from-scratch batch
    # where every product is newly created by this same pipeline.
    "existing_product_activity_overrides": {},
}


def _merge(base, override):
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _merge(base[k], v)
        else:
            base[k] = v


def load_config(path):
    """Load a JSON config file and merge it over DEFAULTS (deep merge for
    nested dicts). Missing keys keep their default. Unknown keys are kept
    as-is so a config can carry extra notes without breaking anything."""
    with open(path, encoding="utf-8") as f:
        user_cfg = json.load(f)
    cfg = json.loads(json.dumps(DEFAULTS))
    _merge(cfg, user_cfg)
    return cfg


def require(cfg, *keys):
    """Fail loudly if required config keys were never filled in, instead of
    silently sending None/[] to the API and getting a confusing 400/500."""
    missing = [k for k in keys if not cfg.get(k)]
    if missing:
        raise SystemExit(
            f"Missing required config value(s) in your --config file: {', '.join(missing)}\n"
            f"See batch_config.example.json for the expected shape."
        )
