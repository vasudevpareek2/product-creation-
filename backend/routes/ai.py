from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

from models.ai import AIContentRequest, AIContentResponse, ProductSuggestionRequest, ProductSuggestionResponse
from services.claude_service import ClaudeService
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

claude_service = ClaudeService()

@router.post("/generate-content", response_model=AIContentResponse)
async def generate_content(request: AIContentRequest):
    """Generate content using Claude AI"""
    
    if not claude_service.is_available():
        raise HTTPException(status_code=503, detail="Claude API not configured")
    
    try:
        if request.content_type == "product_description":
            result = await claude_service.generate_product_description(
                product_name=request.input_data.get("product_name", ""),
                destination=request.input_data.get("destination", ""),
                activity_type=request.input_data.get("activity_type", ""),
                duration=request.input_data.get("duration"),
                special_features=request.input_data.get("special_features")
            )
        elif request.content_type == "variant_name":
            result = await claude_service.generate_variant_name(
                product_name=request.input_data.get("product_name", ""),
                variant_details=request.input_data.get("variant_details", {})
            )
        elif request.content_type == "seo_meta":
            result = await claude_service.generate_seo_content(
                product_name=request.input_data.get("product_name", ""),
                destination=request.input_data.get("destination", ""),
                activity_type=request.input_data.get("activity_type", "")
            )
        else:
            raise HTTPException(status_code=400, detail=f"Unknown content type: {request.content_type}")
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return AIContentResponse(
            content_type=request.content_type,
            generated_content=result["content"],
            raw_response=None,
            tokens_used=result.get("tokens_used"),
            ai_model_used=result.get("model", "claude-3-5-sonnet-20241022")
        )
        
    except Exception as e:
        logger.error(f"Error generating content: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/suggest-product", response_model=ProductSuggestionResponse)
async def suggest_product(request: ProductSuggestionRequest):
    """Suggest complete product structure using Claude AI"""
    
    if not claude_service.is_available():
        raise HTTPException(status_code=503, detail="Claude API not configured")
    
    try:
        result = await claude_service.suggest_product_structure(
            destination=request.destination,
            activity_type=request.activity_type,
            target_audience=request.target_audience
        )
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        content = result["content"]
        
        return ProductSuggestionResponse(
            suggested_name=content["name_suggestions"][0] if content["name_suggestions"] else "",
            suggested_overview=f"Recommended product type: {content['product_type']}",
            suggested_description=f"Suggested for {request.target_audience or 'general travelers'}",
            suggested_highlights=content.get("key_highlights", []),
            suggested_variants=content.get("variant_suggestions", []),
            pricing_suggestions={"strategy": content.get("pricing_strategy", "mid-range")}
        )
        
    except Exception as e:
        logger.error(f"Error suggesting product: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_ai_status():
    """Check if Claude API is configured and available"""
    return {
        "available": claude_service.is_available(),
        "configured": bool(settings.anthropic_api_key),
        "ai_model": "claude-3-5-sonnet-20241022"
    }