"""
Test script for Groq AI integration
Run this to verify that Groq API is working correctly
"""
import asyncio
import os
from services.claude_service import ClaudeService
from config import settings

async def test_groq_integration():
    print("Testing Groq AI Integration...")
    print(f"Groq API Key configured: {bool(settings.groq_api_key)}")
    print(f"Claude API Key configured: {bool(settings.anthropic_api_key)}")
    
    # Initialize service
    service = ClaudeService()
    print(f"Service available: {service.is_available()}")
    
    if not service.is_available():
        print("\n[X] No AI API configured. Please set either:")
        print("   - GROQ_API_KEY in .env file (Recommended - Free)")
        print("   - ANTHROPIC_API_KEY in .env file (Paid)")
        print("\nGet a free Groq API key at: https://console.groq.com/keys")
        return
    
    # Test product description generation
    print("\n[TEST] Testing product description generation...")
    result = await service.generate_product_description(
        product_name="Kerala Backwaters Houseboat Experience",
        destination="Kerala, India",
        activity_type="Houseboat Stay",
        duration="3 days",
        special_features=["Sunset cruise", "Traditional Kerala cuisine", "Village visits"]
    )
    
    if result.get("success"):
        print("[OK] Product description generation successful!")
        print(f"   Provider: {result.get('provider')}")
        print(f"   Model: {result.get('model')}")
        print(f"   Tokens used: {result.get('tokens_used')}")
        print(f"\n   Generated content:")
        content = result.get('content', {})
        print(f"   Overview: {content.get('overview', 'N/A')}")
        print(f"   Highlights: {content.get('highlights', [])}")
    else:
        print(f"[FAIL] Product description generation failed: {result.get('error')}")
    
    # Test variant name generation
    print("\n[TEST] Testing variant name generation...")
    variant_result = await service.generate_variant_name(
        product_name="Kerala Backwaters Houseboat Experience",
        variant_details={
            "duration_type": "overnight",
            "duration_days": 2,
            "duration_hours": 0,
            "booking_type": "private",
            "availability_sources": "instant_booking"
        }
    )
    
    if variant_result.get("success"):
        print("[OK] Variant name generation successful!")
        print(f"   Provider: {variant_result.get('provider')}")
        content = variant_result.get('content', {})
        print(f"   Variant name: {content.get('variant_name', 'N/A')}")
        print(f"   Overview: {content.get('overview', 'N/A')}")
    else:
        print(f"[FAIL] Variant name generation failed: {variant_result.get('error')}")
    
    # Test SEO content generation
    print("\n[TEST] Testing SEO content generation...")
    seo_result = await service.generate_seo_content(
        product_name="Kerala Backwaters Houseboat Experience",
        destination="Kerala, India",
        activity_type="Houseboat Stay"
    )
    
    if seo_result.get("success"):
        print("[OK] SEO content generation successful!")
        print(f"   Provider: {seo_result.get('provider')}")
        content = seo_result.get('content', {})
        print(f"   Meta title: {content.get('meta_title', 'N/A')}")
        print(f"   Meta description: {content.get('meta_description', 'N/A')}")
    else:
        print(f"[FAIL] SEO content generation failed: {seo_result.get('error')}")
    
    print("\n[SUCCESS] Groq integration test completed!")

if __name__ == "__main__":
    asyncio.run(test_groq_integration())