from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import json
import os
import logging
from datetime import datetime

from models.config import PartnerConfig, ConfigResponse
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/{partner_id}", response_model=ConfigResponse)
async def get_config(partner_id: str):
    """Get configuration for a partner"""
    config_file = os.path.join(settings.config_dir, f"{partner_id}_config.json")
    
    if not os.path.exists(config_file):
        # Return default config if doesn't exist
        default_config = PartnerConfig()
        return ConfigResponse(
            partner_id=partner_id,
            config=default_config,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    return ConfigResponse(
        partner_id=partner_id,
        config=PartnerConfig(**config_data),
        created_at=config_data.get("created_at", datetime.now().isoformat()),
        updated_at=config_data.get("updated_at", datetime.now().isoformat())
    )

@router.post("/{partner_id}", response_model=ConfigResponse)
async def save_config(partner_id: str, config: PartnerConfig):
    """Save configuration for a partner"""
    config_file = os.path.join(settings.config_dir, f"{partner_id}_config.json")
    
    config_data = config.dict()
    config_data["created_at"] = datetime.now().isoformat()
    config_data["updated_at"] = datetime.now().isoformat()
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Saved configuration for partner {partner_id}")
    
    return ConfigResponse(
        partner_id=partner_id,
        config=config,
        created_at=config_data["created_at"],
        updated_at=config_data["updated_at"]
    )

@router.delete("/{partner_id}")
async def delete_config(partner_id: str):
    """Delete configuration for a partner"""
    config_file = os.path.join(settings.config_dir, f"{partner_id}_config.json")
    
    if os.path.exists(config_file):
        os.remove(config_file)
        logger.info(f"Deleted configuration for partner {partner_id}")
    
    return {"message": "Configuration deleted successfully"}

@router.get("/")
async def list_configs():
    """List all partner configurations"""
    configs = []
    
    if os.path.exists(settings.config_dir):
        for filename in os.listdir(settings.config_dir):
            if filename.endswith("_config.json"):
                partner_id = filename.replace("_config.json", "")
                with open(os.path.join(settings.config_dir, filename), 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                configs.append({
                    "partner_id": partner_id,
                    "client_id": config_data.get("client_id"),
                    "region_name": config_data.get("region_name"),
                    "updated_at": config_data.get("updated_at")
                })
    
    return {"configs": configs}