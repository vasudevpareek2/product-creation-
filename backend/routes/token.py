from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional
import logging
import asyncio
from services.token_capture import token_capture_service
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/capture-interactive")
async def capture_token_interactive(
    admin_url: str = "https://admin.thrillophilia.com",
    client_id: str = "1"
):
    """
    Start interactive token capture process.
    Opens a browser window for user to log in, then captures the token.
    """
    try:
        logger.info("Starting interactive token capture")
        
        # Run the capture process
        result = await token_capture_service.capture_token_interactive(
            admin_url=admin_url,
            client_id=client_id
        )
        
        if result["success"]:
            # Save the captured token
            import os
            token_file = os.path.join(settings.config_dir, "access_token.txt")
            with open(token_file, 'w') as f:
                f.write(result["token"])
            
            logger.info("Token saved successfully")
            return {
                "success": True,
                "message": "Token captured and saved successfully",
                "method": result.get("method"),
                "token_preview": result["token"][:20] + "..." if len(result["token"]) > 20 else result["token"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Token capture failed"))
            
    except Exception as e:
        logger.error(f"Error in interactive token capture: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/capture-from-storage")
async def capture_token_from_storage(
    cookies: list = [],
    localStorage: dict = {},
    admin_url: str = "https://admin.thrillophilia.com",
    client_id: str = "1"
):
    """
    Capture token using existing session data (cookies/localStorage).
    """
    try:
        logger.info("Starting token capture from storage")
        
        result = await token_capture_service.capture_token_from_storage(
            admin_url=admin_url,
            client_id=client_id,
            cookies=cookies,
            localStorage=localStorage
        )
        
        if result["success"]:
            # Save the captured token
            import os
            token_file = os.path.join(settings.config_dir, "access_token.txt")
            with open(token_file, 'w') as f:
                f.write(result["token"])
            
            logger.info("Token saved successfully")
            return {
                "success": True,
                "message": "Token captured and saved successfully",
                "method": result.get("method"),
                "token_preview": result["token"][:20] + "..." if len(result["token"]) > 20 else result["token"]
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("error", "Token capture failed"))
            
    except Exception as e:
        logger.error(f"Error capturing token from storage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validate")
async def validate_token(
    token: str,
    admin_url: str = "https://admin.thrillophilia.com"
):
    """
    Validate if a token is still valid by making a test API call.
    """
    try:
        result = await token_capture_service.validate_token(
            token=token,
            admin_url=admin_url
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error validating token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status")
async def get_token_status():
    """
    Check if a token file exists and is valid.
    """
    import os
    from datetime import datetime
    
    token_file = os.path.join(settings.config_dir, "access_token.txt")
    
    if not os.path.exists(token_file):
        return {
            "exists": False,
            "valid": False,
            "message": "No token file found"
        }
    
    # Check file age
    file_age = datetime.now().timestamp() - os.path.getmtime(token_file)
    hours_old = file_age / 3600
    
    # Read token
    with open(token_file, 'r') as f:
        token = f.read().strip()
    
    return {
        "exists": True,
        "valid": bool(token),
        "token_preview": token[:20] + "..." if len(token) > 20 else token,
        "hours_old": round(hours_old, 2),
        "message": f"Token file is {round(hours_old, 2)} hours old"
    }