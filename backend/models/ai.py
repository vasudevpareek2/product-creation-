from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class AIContentRequest(BaseModel):
    content_type: str = Field(..., description="Type of content to generate: product_description, variant_name, seo_meta, etc.")
    input_data: Dict[str, Any] = Field(..., description="Input data for content generation")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for generation")

class AIContentResponse(BaseModel):
    content_type: str
    generated_content: Any
    raw_response: Optional[str] = None
    tokens_used: Optional[int] = None
    ai_model_used: str = "claude-3-5-sonnet-20241022"

class ProductSuggestionRequest(BaseModel):
    destination: str = Field(..., description="Product destination")
    activity_type: str = Field(..., description="Type of activity")
    duration: Optional[str] = Field(None, description="Duration of the activity")
    target_audience: Optional[str] = Field(None, description="Target audience")
    special_features: Optional[List[str]] = Field(None, description="Special features to highlight")

class ProductSuggestionResponse(BaseModel):
    suggested_name: str
    suggested_overview: str
    suggested_description: str
    suggested_highlights: List[str]
    suggested_variants: List[Dict[str, Any]]
    pricing_suggestions: Dict[str, Any]