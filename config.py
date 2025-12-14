from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import Optional, Union
import os

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "sqlite:///./linkedin_insights.db"
    
    # Application Configuration
    secret_key: str = "your-secret-key-change-in-production"
    debug: Union[bool, str] = True
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # LinkedIn Scraper Configuration
    linkedin_base_url: str = "https://www.linkedin.com"
    scraper_timeout: int = 60000
    scraper_headless: Union[bool, str] = True
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # Solana/Phantom Wallet Configuration
    solana_network: str = "mainnet-beta"  # Options: mainnet-beta, testnet, devnet
    jwt_expiration_days: int = 30
    
    @field_validator('debug', 'scraper_headless', mode='before')
    @classmethod
    def parse_bool(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return bool(v)
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        env_file_encoding = 'utf-8'

settings = Settings()

if settings.database_url.startswith("sqlite"):
    from sqlalchemy.pool import StaticPool
    engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool
    }
else:
    # For PostgreSQL (including cloud databases like Supabase)
    # Use connection pooling for better performance
    engine_kwargs = {
        "pool_size": 5,
        "max_overflow": 10,
        "pool_pre_ping": True,  # Verify connections before using
        "pool_recycle": 3600,  # Recycle connections after 1 hour
    }

