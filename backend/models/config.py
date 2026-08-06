from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class PartnerConfig(BaseModel):
    base_url: str = "https://admin.thrillophilia.com"
    client_id: str = "1"
    region_name: Optional[str] = None
    visibility_scopes: List[str] = ["ib_builder", "quotation"]
    open_slots_until: Optional[str] = None
    required_inclusion_id: Optional[int] = None
    vendor_names: List[str] = []
    reseller_partner_id: Optional[int] = None
    inventory_id: Optional[int] = None
    margin: float = 1.0
    currency: str = "INR"
    policy_ids: Dict[str, Optional[int]] = {
        "confirmation_policy_id": None,
        "refund_policy_id": None,
        "cancellation_policy_id": None,
        "payment_term_policy_id": None
    }
    vendor_payment_term_policy_id: Optional[int] = None
    default_variant: Dict[str, Any] = {
        "booking_type": "private",
        "inventory_type": "pax",
        "min_passenger_count": 1,
        "transfer_inclusion": "not_included",
        "ticket_inclusion": "Not Ticketed"
    }
    booking_settings: Dict[str, Any] = {
        "enable_send_enquiry": True,
        "enable_online_booking": None,
        "is_ticketed": "no",
        "time_zone": "Asia/Kolkata",
        "min_percentage_amount_to_confirm": 100
    }
    seo_template: Dict[str, str] = {
        "meta_title": "{name} | Book Now",
        "meta_description": "Book {name} today. Reserve your spot now.",
        "og_title": "{name}",
        "og_description": "Explore {name} with a guided tour of the top local attractions."
    }
    existing_product_activity_overrides: Dict[str, str] = {}

class ConfigResponse(BaseModel):
    partner_id: str
    config: PartnerConfig
    created_at: str
    updated_at: str