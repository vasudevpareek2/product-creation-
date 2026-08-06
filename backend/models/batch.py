from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class BatchStatus(str, Enum):
    PENDING = "pending"
    STAGE1_COMPLETED = "stage1_completed"
    STAGE2_COMPLETED = "stage2_completed"
    STAGE3_COMPLETED = "stage3_completed"
    FAILED = "failed"
    COMPLETED = "completed"

class BatchCreate(BaseModel):
    name: str = Field(..., description="Batch name")
    description: Optional[str] = Field(None, description="Batch description")
    client_id: str = Field(..., description="Thrillophilia client ID")
    source_file: str = Field(..., description="Path to uploaded source file")

class BatchResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    client_id: str
    source_file: str
    status: BatchStatus
    created_at: datetime
    updated_at: Optional[datetime]
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class StageExecutionRequest(BaseModel):
    stage: int = Field(..., ge=1, le=3, description="Stage number (1-3)")
    dry_run: bool = Field(False, description="Perform dry run without making changes")
    config_overrides: Optional[Dict[str, Any]] = Field(None, description="Override config values")

class StageExecutionResponse(BaseModel):
    batch_id: str
    stage: int
    status: str
    dry_run: bool
    started_at: datetime
    completed_at: Optional[datetime]
    results: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None