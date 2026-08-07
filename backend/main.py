from fastapi import FastAPI, UploadFile, File, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os
import json
from datetime import datetime
from typing import List
import uuid
import asyncio

from config import settings
from routes import batch, config, ai, upload, token

# Global connection manager for WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting Product Creation Web App")

    # Ensure required directories exist
    os.makedirs(settings.upload_dir, exist_ok=True)
    os.makedirs(settings.config_dir, exist_ok=True)
    os.makedirs(settings.log_dir, exist_ok=True)

    print(f"✅ Upload directory: {settings.upload_dir}")
    print(f"✅ Config directory: {settings.config_dir}")
    print(f"✅ Log directory: {settings.log_dir}")

    yield
    # Shutdown
    print("👋 Shutting down Product Creation Web App")

app = FastAPI(
    title="Product Creation API",
    description="API for automating Thrillophilia product creation workflow",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(batch.router, prefix="/api/batch", tags=["batch"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(upload.router, prefix="/api/upload", tags=["upload"])
app.include_router(token.router, prefix="/api/token", tags=["token"])

# WebSocket endpoint for real-time log streaming
@app.websocket("/ws/logs/{batch_id}")
async def websocket_logs(websocket: WebSocket, batch_id: str):
    await manager.connect(websocket)
    try:
        while True:
            # In a real implementation, this would read from log files
            # and stream to connected clients
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
async def root():
    return {
        "message": "Product Creation API",
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "batches": "/api/batch",
            "config": "/api/config",
            "ai": "/api/ai",
            "upload": "/api/upload"
        }
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "settings": {
            "thrillo_base_url": settings.thrillo_base_url,
            "thrillo_client_id": settings.thrillo_client_id,
            "has_claude_api": bool(settings.anthropic_api_key),
            "cors_origins": settings.cors_origins_list
        },
        "directories": {
            "upload_dir": settings.upload_dir,
            "upload_dir_exists": os.path.exists(settings.upload_dir),
            "config_dir": settings.config_dir,
            "config_dir_exists": os.path.exists(settings.config_dir),
            "log_dir": settings.log_dir,
            "log_dir_exists": os.path.exists(settings.log_dir)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )