import anthropic
import groq
from typing import Optional, Dict, Any, List
import logging
from config import settings

logger = logging.getLogger(__name__)

class ClaudeService:
    def __init__(self, anthropic_api_key=None, groq_api_key=None):
        # Use provided keys or fall back to settings
        anthropic_key = anthropic_api_key or settings.anthropic_api_key
        groq_key = groq_api_key or settings.groq_api_key
        
        # Try Claude first
        if anthropic_key:
            self.claude_client = anthropic.Anthropic(api_key=anthropic_key)
            logger.info("Claude API configured")
        else:
            self.claude_client = None
            logger.warning("Anthropic API key not configured")
        
        # Try Groq as alternative
        if groq_key:
            self.groq_client = groq.Groq(api_key=groq_key)
            logger.info("Groq API configured")
        else:
            self.groq_client = None
            logger.warning("Groq API key not configured")
        
        self.client = self.claude_client  # Default to Claude for backward compatibility
    
    def is_available(self) -> bool:
        return self.claude_client is not None or self.groq_client is not None
    
    def _get_available_client(self):
        """Get the first available client (prefer Claude, fallback to Groq)"""
        if self.claude_client:
            return self.claude_client, "claude"
        elif self.groq_client:
            return self.groq_client, "groq"
        else:
            return None, None
    
    async def generate_product_description(
        self,
        product_name: str,
        destination: str,
        activity_type: str,
        duration: Optional[str] = None,
        special_features: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate product overview and description using Claude or Groq"""
        
        client, provider = self._get_available_client()
        if not client:
            return {"error": "No AI API configured (Claude or Groq)"}
        
        prompt = f"""Generate a compelling product overview and detailed description for a travel product with the following details:

Product Name: {product_name}
Destination: {destination}
Activity Type: {activity_type}
Duration: {duration or 'Not specified'}
Special Features: {', '.join(special_features) if special_features else 'None'}

Please provide:
1. A compelling 2-3 sentence overview
2. A detailed 4-6 sentence description
3. 3-5 key highlights
4. Know-before-you-go tips (2-3 points)

Format the response as JSON with this structure:
{{
    "overview": "...",
    "long_description": "...",
    "highlights": ["...", "...", "..."],
    "know_before_you_go": ["...", "..."]
}}"""

        try:
            if provider == "claude":
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2048,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                content = message.content[0].text
                tokens_used = message.usage.input_tokens + message.usage.output_tokens
                model = message.model
            else:  # groq
                message = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=2048,
                    response_format={"type": "json_object"}
                )
                content = message.choices[0].message.content
                tokens_used = message.usage.total_tokens
                model = message.model
            
            # Parse JSON from the response
            import json
            result = json.loads(content)
            
            return {
                "success": True,
                "content": result,
                "tokens_used": tokens_used,
                "model": model,
                "provider": provider
            }
            
        except Exception as e:
            logger.error(f"Error generating product description: {str(e)}")
            return {"error": str(e)}
    
    async def generate_variant_name(
        self,
        product_name: str,
        variant_details: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate compelling variant name and overview using Claude or Groq"""
        
        client, provider = self._get_available_client()
        if not client:
            return {"error": "No AI API configured (Claude or Groq)"}
        
        prompt = f"""Generate a compelling name and overview for a product variant with these details:

Product Name: {product_name}
Duration Type: {variant_details.get('duration_type', 'Not specified')}
Duration: {variant_details.get('duration_days', 'N/A')} days, {variant_details.get('duration_hours', 'N/A')} hours
Booking Type: {variant_details.get('booking_type', 'Not specified')}
Availability: {variant_details.get('availability_sources', 'Not specified')}

Please provide:
1. A compelling variant name (2-6 words)
2. A 1-2 sentence overview

Format as JSON:
{{
    "variant_name": "...",
    "overview": "..."
}}"""

        try:
            if provider == "claude":
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=512,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                content = message.content[0].text
                tokens_used = message.usage.input_tokens + message.usage.output_tokens
            else:  # groq
                message = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=512,
                    response_format={"type": "json_object"}
                )
                content = message.choices[0].message.content
                tokens_used = message.usage.total_tokens
            
            import json
            result = json.loads(content)
            
            return {
                "success": True,
                "content": result,
                "tokens_used": tokens_used,
                "provider": provider
            }
            
        except Exception as e:
            logger.error(f"Error generating variant name: {str(e)}")
            return {"error": str(e)}
    
    async def generate_seo_content(
        self,
        product_name: str,
        destination: str,
        activity_type: str
    ) -> Dict[str, Any]:
        """Generate SEO metadata using Claude or Groq"""
        
        client, provider = self._get_available_client()
        if not client:
            return {"error": "No AI API configured (Claude or Groq)"}
        
        prompt = f"""Generate SEO metadata for a travel product:

Product Name: {product_name}
Destination: {destination}
Activity Type: {activity_type}

Please provide:
1. Meta title (50-60 characters, include destination)
2. Meta description (150-160 characters, compelling and keyword-rich)
3. OG title (similar to meta title)
4. OG description (150-200 characters, social media friendly)

Format as JSON:
{{
    "meta_title": "...",
    "meta_description": "...",
    "og_title": "...",
    "og_description": "..."
}}"""

        try:
            if provider == "claude":
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=512,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                content = message.content[0].text
                tokens_used = message.usage.input_tokens + message.usage.output_tokens
            else:  # groq
                message = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=512,
                    response_format={"type": "json_object"}
                )
                content = message.choices[0].message.content
                tokens_used = message.usage.total_tokens
            
            import json
            result = json.loads(content)
            
            return {
                "success": True,
                "content": result,
                "tokens_used": tokens_used,
                "provider": provider
            }
            
        except Exception as e:
            logger.error(f"Error generating SEO content: {str(e)}")
            return {"error": str(e)}
    
    async def suggest_product_structure(
        self,
        destination: str,
        activity_type: str,
        target_audience: Optional[str] = None
    ) -> Dict[str, Any]:
        """Suggest complete product structure using Claude or Groq"""
        
        client, provider = self._get_available_client()
        if not client:
            return {"error": "No AI API configured (Claude or Groq)"}
        
        prompt = f"""Suggest a complete product structure for a travel product:

Destination: {destination}
Activity Type: {activity_type}
Target Audience: {target_audience or 'General travelers'}

Please suggest:
1. 3-5 compelling product name options
2. Recommended product type (activity, tour, staycation, etc.)
3. Suggested duration options
4. Recommended pricing strategy (budget/mid-range/premium)
5. Key highlights to include
6. Suggested variant types (private/group, different durations)

Format as JSON:
{{
    "name_suggestions": ["...", "...", "..."],
    "product_type": "...",
    "duration_options": ["...", "..."],
    "pricing_strategy": "...",
    "key_highlights": ["...", "...", "..."],
    "variant_suggestions": [
        {{"name": "...", "type": "...", "duration": "..."}},
        {{"name": "...", "type": "...", "duration": "..."}}
    ]
}}"""

        try:
            if provider == "claude":
                message = client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=2048,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )
                content = message.content[0].text
                tokens_used = message.usage.input_tokens + message.usage.output_tokens
            else:  # groq
                message = client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    max_tokens=2048,
                    response_format={"type": "json_object"}
                )
                content = message.choices[0].message.content
                tokens_used = message.usage.total_tokens
            
            import json
            result = json.loads(content)
            
            return {
                "success": True,
                "content": result,
                "tokens_used": tokens_used,
                "provider": provider
            }
            
        except Exception as e:
            logger.error(f"Error suggesting product structure: {str(e)}")
            return {"error": str(e)}