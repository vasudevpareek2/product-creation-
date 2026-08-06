"""
Test script to verify Playwright browser opens correctly
"""
import asyncio
import sys
from playwright.async_api import async_playwright

# Fix for Python 3.13 on Windows - set event loop policy
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

async def test_browser_open():
    print("Testing Playwright browser launch...")
    
    try:
        playwright = await async_playwright().start()
        print("Playwright started successfully")
        
        # Launch browser in non-headless mode (visible)
        browser = await playwright.chromium.launch(
            headless=False,
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        print("Browser launched successfully (should be visible)")
        
        # Create a new page
        page = await browser.new_page()
        print("New page created")
        
        # Navigate to a test page
        await page.goto('https://example.com')
        print("Navigated to example.com")
        
        # Wait for 5 seconds so you can see the browser
        print("Waiting 5 seconds for you to see the browser...")
        await asyncio.sleep(5)
        
        # Close browser
        await browser.close()
        await playwright.stop()
        print("Browser closed successfully")
        
        print("\n[SUCCESS] Browser test completed!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Browser test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_browser_open())
    if result:
        print("\n[OK] Playwright is working correctly")
    else:
        print("\n[FAIL] Playwright has issues - check the error above")