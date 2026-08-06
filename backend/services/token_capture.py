import asyncio
import logging
import sys
import multiprocessing
import json
import os
from typing import Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

def _selenium_capture_process(admin_url, client_id, result_queue):
    """Run Selenium in a separate process with its own event loop - using undetected-chromedriver"""
    try:
        import time
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        
        # Try undetected-chromedriver first (like the working automation)
        try:
            import undetected_chromedriver as uc
            chrome_options = uc.ChromeOptions()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            
            driver = uc.Chrome(options=chrome_options, version_main=150)
            print("Started browser with undetected-chromedriver")
        except Exception as uc_error:
            print(f"Undetected-chromedriver failed: {uc_error}, trying regular Selenium...")
            # Fallback to regular Selenium
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_argument("--disable-extensions")
            chrome_options.add_argument("--disable-infobars")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.binary_location = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
            
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                driver = webdriver.Chrome(service=service, options=chrome_options)
            except:
                driver = webdriver.Chrome(options=chrome_options)
            print("Started browser with regular Selenium")
        
        login_url = f"{admin_url}/admin/partners/"
        print(f"Navigating to {login_url}")
        driver.get(login_url)
        
        captured_token = None
        max_wait_time = 300  # 5 minutes
        elapsed = 0
        check_interval = 2
        
        print("Browser opened. Please complete the login process...")
        print("Waiting for token capture...")
        
        while elapsed < max_wait_time and not captured_token:
            time.sleep(check_interval)
            elapsed += check_interval
            
            # Try to get token from localStorage - check ALL keys
            try:
                # Properly read localStorage using JavaScript
                local_storage_dict = driver.execute_script("""
                    var items = {};
                    for (var i = 0; i < localStorage.length; i++) {
                        var key = localStorage.key(i);
                        items[key] = localStorage.getItem(key);
                    }
                    return items;
                """)
                print(f"LocalStorage items: {list(local_storage_dict.keys())}")
                for key, value in local_storage_dict.items():
                    # Check for any value that looks like a token (long string with dots, hyphens, etc)
                    if value and len(value) > 20 and ('.' in value or '-' in value or '_' in value):
                        captured_token = value
                        print(f"Token captured from localStorage key: {key}")
                        break
                    # Also check key names
                    if 'token' in key.lower() or 'auth' in key.lower() or 'access' in key.lower():
                        captured_token = value
                        print(f"Token captured from localStorage key: {key}")
                        break
            except Exception as e:
                print(f"Error reading localStorage: {e}")
            
            # Also check sessionStorage
            try:
                session_storage_dict = driver.execute_script("""
                    var items = {};
                    for (var i = 0; i < sessionStorage.length; i++) {
                        var key = sessionStorage.key(i);
                        items[key] = sessionStorage.getItem(key);
                    }
                    return items;
                """)
                print(f"SessionStorage items: {list(session_storage_dict.keys())}")
                for key, value in session_storage_dict.items():
                    if value and len(value) > 20 and ('.' in value or '-' in value or '_' in value):
                        captured_token = value
                        print(f"Token captured from sessionStorage key: {key}")
                        break
            except Exception as e:
                print(f"Error reading sessionStorage: {e}")
            
            # Check if we're on a dashboard page (user logged in)
            current_url = driver.current_url
            print(f"Current URL: {current_url}")
            if 'dashboard' in current_url.lower() or 'products' in current_url.lower() or 'partners' in current_url.lower():
                print("User appears to be logged in, checking all storage...")
                try:
                    # Make a request to get the actual JWT token from API response headers
                    try:
                        # Try to fetch API data to get the token from response headers
                        token = driver.execute_script("""
                            return new Promise((resolve) => {
                                fetch('/api/partners', {
                                    headers: {
                                        'Content-Type': 'application/json'
                                    }
                                })
                                .then(response => {
                                    const authHeader = response.headers.get('authorization') || response.headers.get('x-access-token');
                                    resolve(authHeader || null);
                                })
                                .catch(() => resolve(null));
                            });
                        """)
                        if token:
                            # Remove "Bearer " prefix if present
                            if token.startswith('Bearer '):
                                token = token[7:]
                            captured_token = token
                            print(f"Token captured from API response header")
                    except Exception as e:
                        print(f"Error getting token from API: {e}")
                    
                    # Fallback: Check all cookies
                    if not captured_token:
                        cookies = driver.get_cookies()
                        print(f"Cookies: {[c['name'] for c in cookies]}")
                        for cookie in cookies:
                            # Check cookie value for JWT-like patterns (2+ dots = header.payload.signature)
                            if cookie['value'] and len(cookie['value']) > 20 and cookie['value'].count('.') >= 2:
                                captured_token = cookie['value']
                                print(f"Token captured from cookie: {cookie['name']}")
                                break
                            # Check cookie names
                            if 'token' in cookie['name'].lower() or 'auth' in cookie['name'].lower():
                                captured_token = cookie['value']
                                print(f"Token captured from cookie: {cookie['name']}")
                                break
                except Exception as e:
                    print(f"Error reading cookies: {e}")
        
        driver.quit()
        
        if captured_token:
            print("Token successfully captured")
            result_queue.put({
                "success": True,
                "token": captured_token,
                "method": "local_storage"
            })
        else:
            print("Token capture timed out")
            result_queue.put({
                "success": False,
                "error": "Token capture timed out. Please try again."
            })
    except Exception as e:
        print(f"Error in capture process: {str(e)}")
        result_queue.put({
            "success": False,
            "error": str(e)
        })

class TokenCaptureService:
    def __init__(self):
        pass

    def is_available(self) -> bool:
        try:
            import selenium
            return True
        except ImportError:
            return False
    
    async def capture_token_interactive(
        self,
        admin_url: str = "https://admin.thrillophilia.com",
        client_id: str = "1"
    ) -> Dict[str, Any]:
        """
        Capture token using Selenium in a separate process.
        This completely isolates the browser automation from the main event loop.
        """
        try:
            import selenium
        except ImportError:
            return {
                "success": False,
                "error": "Selenium is not installed. Run: pip install selenium"
            }
        
        try:
            # Use multiprocessing to run in a completely separate process
            result_queue = multiprocessing.Queue()
            process = multiprocessing.Process(
                target=_selenium_capture_process,
                args=(admin_url, client_id, result_queue)
            )
            
            logger.info("Starting Selenium capture process...")
            process.start()
            
            # Wait for the process to complete
            process.join(timeout=310)  # 5 minutes + 10 seconds buffer
            
            if process.is_alive():
                process.terminate()
                process.join()
                return {
                    "success": False,
                    "error": "Token capture timed out"
                }
            
            # Get the result from the queue
            if not result_queue.empty():
                result = result_queue.get()
                logger.info(f"Capture result: {result}")
                return result
            else:
                return {
                    "success": False,
                    "error": "No result from capture process"
                }

        except Exception as e:
            logger.error(f"Error during token capture: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def capture_token_from_storage(
        self,
        admin_url: str = "https://admin.thrillophilia.com",
        client_id: str = "1",
        cookies: list = None,
        localStorage: dict = None
    ) -> Dict[str, Any]:
        """
        Token capture from storage - disabled for now.
        """
        return {
            "success": False,
            "error": "This feature is currently disabled. Please use interactive capture or manual entry."
        }

    async def validate_token(
        self,
        token: str,
        admin_url: str = "https://admin.thrillophilia.com"
    ) -> Dict[str, Any]:
        """
        Basic token validation.
        """
        if not token or not token.strip():
            return {
                "valid": False,
                "message": "Token is empty"
            }
        
        if len(token) < 10:
            return {
                "valid": False,
                "message": "Token is too short to be valid"
            }
        
        return {
            "valid": True,
            "message": "Token format appears valid"
        }

    async def cleanup(self):
        """No cleanup needed for multiprocessing approach"""
        pass

# Global service instance
token_capture_service = TokenCaptureService()