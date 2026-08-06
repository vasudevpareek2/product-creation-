"""
Quick test to verify Playwright works at all
"""
from playwright.sync_api import sync_playwright

print("Testing Playwright...")

try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://example.com')
        print("Browser opened successfully!")
        page.wait_for_timeout(2000)  # Wait 2 seconds
        browser.close()
        print("Test successful!")
except Exception as e:
    print(f"Test failed: {e}")