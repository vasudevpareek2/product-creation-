from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List
import os
import shutil
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None
from datetime import datetime
import logging

from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

class TokenUploadRequest(BaseModel):
    token: str

@router.post("/csv")
async def upload_csv(file: UploadFile = File(...)):
    """Upload a CSV file for processing"""
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate CSV structure if pandas is available
        if PANDAS_AVAILABLE:
            try:
                df = pd.read_csv(file_path)
                logger.info(f"Uploaded CSV file: {filename}, Shape: {df.shape}")
                
                # Convert NaN to None for JSON serialization
                df_clean = df.replace({float('nan'): None})
                
                return {
                    "message": "File uploaded successfully",
                    "filename": filename,
                    "file_path": file_path,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "preview": df_clean.head(3).to_dict(orient="records")
                }
            except Exception as e:
                # If CSV parsing fails, delete the file and return error
                os.remove(file_path)
                raise HTTPException(status_code=400, detail=f"Invalid CSV file: {str(e)}")
        else:
            # Without pandas, just confirm file upload
            logger.info(f"Uploaded CSV file (pandas not available): {filename}")
            return {
                "message": "File uploaded successfully (basic validation only)",
                "filename": filename,
                "file_path": file_path,
                "note": "Install pandas for full CSV validation"
            }
            
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/excel")
async def upload_excel(file: UploadFile = File(...)):
    """Upload an Excel file for processing"""
    
    if not (file.filename.endswith('.xlsx') or file.filename.endswith('.xls')):
        raise HTTPException(status_code=400, detail="Only Excel files are allowed")
    
    # Generate unique filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    file_path = os.path.join(settings.upload_dir, filename)
    
    # Save file
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Validate Excel structure if pandas is available
        if PANDAS_AVAILABLE:
            try:
                df = pd.read_excel(file_path)
                logger.info(f"Uploaded Excel file: {filename}, Shape: {df.shape}")
                
                # Convert NaN to None for JSON serialization
                df_clean = df.replace({float('nan'): None})
                
                return {
                    "message": "File uploaded successfully",
                    "filename": filename,
                    "file_path": file_path,
                    "rows": len(df),
                    "columns": list(df.columns),
                    "preview": df_clean.head(3).to_dict(orient="records")
                }
            except Exception as e:
                # If Excel parsing fails, delete the file and return error
                os.remove(file_path)
                raise HTTPException(status_code=400, detail=f"Invalid Excel file: {str(e)}")
        else:
            # Without pandas, just confirm file upload
            logger.info(f"Uploaded Excel file (pandas not available): {filename}")
            return {
                "message": "File uploaded successfully (basic validation only)",
                "filename": filename,
                "file_path": file_path,
                "note": "Install pandas for full Excel validation"
            }
            
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config")
async def upload_config(file: UploadFile = File(...)):
    """Upload a configuration file"""
    
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")
    
    # Save as batch_config.json
    file_path = os.path.join(settings.config_dir, "batch_config.json")
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"Uploaded config file: batch_config.json")
        
        return {
            "message": "Configuration file uploaded successfully",
            "file_path": file_path
        }
        
    except Exception as e:
        logger.error(f"Error uploading config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/token")
async def upload_token(request: TokenUploadRequest):
    """Upload access token (via POST body for security)"""
    
    token = request.token
    if not token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    token_file = os.path.join(settings.config_dir, "access_token.txt")
    
    try:
        with open(token_file, "w") as f:
            f.write(token.strip())
        
        logger.info("Access token saved successfully")
        
        return {
            "message": "Access token saved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error saving token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files")
async def list_uploaded_files():
    """List all uploaded files"""
    
    files = []
    
    if os.path.exists(settings.upload_dir):
        for filename in os.listdir(settings.upload_dir):
            file_path = os.path.join(settings.upload_dir, filename)
            files.append({
                "filename": filename,
                "size": os.path.getsize(file_path),
                "uploaded_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
    
    return {"files": files}

@router.delete("/{filename}")
async def delete_file(filename: str):
    """Delete an uploaded file"""
    
    file_path = os.path.join(settings.upload_dir, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        os.remove(file_path)
        logger.info(f"Deleted file: {filename}")
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))