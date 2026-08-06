"""
Test the subprocess-based token capture
"""
import asyncio
import sys
import os

# Add the backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.token_capture import TokenCaptureService

async def test_subprocess_capture():
    print("Testing subprocess-based token capture...")
    
    service = TokenCaptureService()
    
    try:
        print("Starting token capture...")
        result = await service.capture_token_interactive(
            admin_url="https://admin.thrillophilia.com",
            client_id="1"
        )
        
        print(f"\nResult: {result}")
        
        if result["success"]:
            print(f"\n[SUCCESS] Token captured!")
            print(f"Method: {result.get('method')}")
            print(f"Token preview: {result['token'][:20]}...")
            
            # Save the token
            import os
            from config import settings
            token_file = os.path.join(settings.config_dir, "access_token.txt")
            with open(token_file, 'w') as f:
                f.write(result["token"])
            print(f"Token saved to: {token_file}")
        else:
            print(f"\n[FAILED] {result.get('error')}")
            
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_subprocess_capture())