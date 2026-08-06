from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    # Thrillophilia API
    thrillo_base_url: str = "https://admin.thrillophilia.com"
    thrillo_client_id: str = "1"
    thrillo_access_token: str = ""
    
    # Claude API
    anthropic_api_key: str = ""
    
    # Groq API (Alternative to Claude)
    groq_api_key: str = ""
    
    # Application
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    cors_origins: str = "http://localhost:3000,http://localhost:3001,https://product-creation-frontend.onrender.com,https://product-creation-ou2z.onrender.com"
    
    # Directories
    upload_dir: str = "uploads"
    config_dir: str = "config"
    log_dir: str = "logs"
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string"""
        if isinstance(self.cors_origins, list):
            return self.cors_origins
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()

# Ensure directories exist
os.makedirs(settings.upload_dir, exist_ok=True)
os.makedirs(settings.config_dir, exist_ok=True)
os.makedirs(settings.log_dir, exist_ok=True)