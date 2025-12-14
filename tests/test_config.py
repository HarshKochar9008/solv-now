import pytest
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import settings

def test_settings_loaded():
    """Test that settings are loaded correctly."""
    assert settings is not None
    assert hasattr(settings, 'database_url')
    assert hasattr(settings, 'secret_key')
    assert hasattr(settings, 'debug')
    assert hasattr(settings, 'host')
    assert hasattr(settings, 'port')

def test_database_url_default():
    """Test default database URL."""
    assert settings.database_url is not None
    assert isinstance(settings.database_url, str)

def test_server_config():
    """Test server configuration."""
    assert settings.host is not None
    assert settings.port is not None
    assert isinstance(settings.port, int)
    assert settings.port > 0

def test_scraper_config():
    """Test scraper configuration."""
    assert hasattr(settings, 'linkedin_base_url')
    assert hasattr(settings, 'scraper_timeout')
    assert hasattr(settings, 'scraper_headless')
    assert isinstance(settings.scraper_timeout, int)
    assert isinstance(settings.scraper_headless, bool)

