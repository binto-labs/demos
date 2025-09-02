"""
Configuration settings for Earthquake Claim Accelerator backend.
Manages environment variables, database settings, and application configuration.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, validator
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application settings
    APP_NAME: str = "Earthquake Claim Accelerator"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_VERSION: str = "v1"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"
    
    # Database settings
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/earthquake_claims"
    DATABASE_ECHO: bool = False
    DATABASE_POOL_SIZE: int = 5
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis settings (for caching and sessions)
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_EXPIRE_SECONDS: int = 3600
    
    # CORS settings
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # File upload settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    ALLOWED_FILE_TYPES: List[str] = [
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "application/pdf", "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain", "text/csv"
    ]
    UPLOAD_DIR: str = "uploads"
    
    # External API settings
    GOOGLE_MAPS_API_KEY: Optional[str] = None
    WEATHER_API_KEY: Optional[str] = None
    EARTHQUAKE_API_URL: str = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    # Email settings
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    EMAIL_FROM: Optional[str] = None
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    # AI/ML settings
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    MODEL_NAME: str = "gpt-3.5-turbo"
    MAX_TOKENS: int = 1000
    
    # Insurance company integration
    INSURANCE_API_ENDPOINTS: dict = {
        "state_farm": "https://api.statefarm.com",
        "allstate": "https://api.allstate.com",
        "farmers": "https://api.farmers.com"
    }
    
    @validator("CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("ALLOWED_HOSTS", pre=True)
    def assemble_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(",")]
        return v
    
    @validator("ALLOWED_FILE_TYPES", pre=True)
    def assemble_file_types(cls, v):
        if isinstance(v, str):
            return [file_type.strip() for file_type in v.split(",")]
        return v
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        if not v.startswith(("postgresql://", "sqlite:///")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL or SQLite URL")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Database configuration
class DatabaseConfig:
    """Database-specific configuration"""
    
    @staticmethod
    def get_database_url(settings: Settings) -> str:
        """Get formatted database URL"""
        return settings.DATABASE_URL
    
    @staticmethod
    def get_engine_config(settings: Settings) -> dict:
        """Get SQLAlchemy engine configuration"""
        return {
            "echo": settings.DATABASE_ECHO,
            "pool_size": settings.DATABASE_POOL_SIZE,
            "max_overflow": settings.DATABASE_MAX_OVERFLOW,
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }

# Cache configuration
class CacheConfig:
    """Redis/Cache configuration"""
    
    @staticmethod
    def get_redis_url(settings: Settings) -> str:
        """Get Redis connection URL"""
        return settings.REDIS_URL
    
    @staticmethod
    def get_cache_config(settings: Settings) -> dict:
        """Get cache configuration"""
        return {
            "expire": settings.REDIS_EXPIRE_SECONDS,
            "encoding": "utf-8",
            "decode_responses": True
        }

# JWT configuration
class JWTConfig:
    """JWT token configuration"""
    
    @staticmethod
    def get_jwt_config(settings: Settings) -> dict:
        """Get JWT configuration"""
        return {
            "secret_key": settings.SECRET_KEY,
            "algorithm": settings.ALGORITHM,
            "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": settings.REFRESH_TOKEN_EXPIRE_DAYS
        }

# File upload configuration
class FileConfig:
    """File upload configuration"""
    
    @staticmethod
    def get_upload_config(settings: Settings) -> dict:
        """Get file upload configuration"""
        return {
            "max_size": settings.MAX_FILE_SIZE,
            "allowed_types": settings.ALLOWED_FILE_TYPES,
            "upload_dir": settings.UPLOAD_DIR
        }

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Global settings instance
settings = get_settings()

# Export configuration classes
__all__ = [
    "Settings",
    "DatabaseConfig", 
    "CacheConfig",
    "JWTConfig",
    "FileConfig",
    "get_settings",
    "settings"
]