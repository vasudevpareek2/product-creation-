"""
Standalone script for token capture using Playwright with proper event loop handling.
This runs in a separate process to avoid Python 3.13 event loop issues.
"""
import sys
import json
import asyncio

# Set event loop policy BEFORE Playwright import
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from playwright.sync_api import sync_playwright

def capture_token_interactive(admin_url="https://admin.thrillophilia.com", client_id="1"):
    """Capture token using synchronous Playwright"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            context = browser.new_context(viewport={'width': 1280, 'height': 720})
            page = context.new_page()

            login_url = f"{admin_url}/admin/{client_id}"
            print(f"Navigating to {login_url}")
            page.goto(login_url, wait_until='networkidle')

            captured_token = None
            
            def handle_request(request):
                nonlocal captured_token
                headers = request.headers
                auth_token = headers.get('access-token') or headers.get('Access-Token')
                if auth_token and not captured_token:
                    captured_token = auth_token
                    print("Token captured from network request")

            page.on('request', handle_request)

            print("Browser opened. Please complete the login process...")
            print("Waiting for token capture...")

            max_wait_time = 300  # 5 minutes
            elapsed = 0
            check_interval = 2

            while elapsed < max_wait_time and not captured_token:
                page.wait_for_timeout(check_interval * 1000)
                elapsed += check_interval
                
                current_url = page.url
                if 'dashboard' in current_url.lower() or 'products' in current_url.lower():
                    print("Detected successful login, checking local storage...")
                    try:
                        local_storage = page.evaluate('() => window.localStorage')
                        for key, value in local_storage.items():
                            if 'token' in key.lower() or 'auth' in key.lower():
                                captured_token = value
                                print(f"Token captured from localStorage key: {key}")
                                break
                    except:
                        pass

            browser.close()

            if captured_token:
                print("Token successfully captured")
                result = {
                    "success": True,
                    "token": captured_token,
                    "method": "network_request" if 'request' in str(captured_token) else "local_storage"
                }
            else:
                print("Token capture timed out")
                result = {
                    "success": False,
                    "error": "Token capture timed out. Please try again."
                }
            
            print(json.dumps(result))
            return result

    except Exception as e:
        print(f"Error: {str(e)}")
        result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(result))
        return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        admin_url = sys.argv[1]
    else:
        admin_url = "https://admin.thrillophilia.com"
    
    if len(sys.argv) > 2:
        client_id = sys.argv[2]
    else:
        client_id = "1"
    
    capture_token_interactive(admin_url, client_id)