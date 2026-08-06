"""
Direct test of token capture service without going through the API
"""
import asyncio
import sys
sys.path.append('.')

# Fix for Python 3.13 on Windows - set event loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from services.token_capture import TokenCaptureService

async def test_token_capture():
    print("Testing token capture service directly...")
    
    service = TokenCaptureService()
    
    try:
        print("Starting interactive token capture...")
        print("A browser window should open for you to log in.")
        
        result = await service.capture_token_interactive(
            admin_url="https://admin.thrillophilia.com",
            client_id="1"
        )
        
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
    asyncio.run(test_token_capture())