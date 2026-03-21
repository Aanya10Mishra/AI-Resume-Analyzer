"""
Configuration for Resume Analyzer Application
Environment-specific settings
"""
import os
from datetime import timedelta
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

class Config:
    """Base configuration class"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{BASE_DIR}/resume_analyzer.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Set to True for SQL debugging
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'backend', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
    
    # Embedding model settings
    EMBEDDING_MODEL = 'all-MiniLM-L6-v2'  # Fast, 384-dim, 22MB
    # Alternative models:
    # 'all-mpnet-base-v2'  # Better quality, 768-dim, 420MB
    # 'paraphrase-MiniLM-L6-v2'  # Good for paraphrasing
    
    # Session settings
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    
    # CORS settings
    CORS_HEADERS = 'Content-Type'
    
    # API Keys (for future features)
    GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
    ONET_API_KEY = os.environ.get('ONET_API_KEY', '')
    
    # Pagination
    ITEMS_PER_PAGE = 10
    
    # Logging
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'app.log'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Show SQL queries in development

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Override with environment variables in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config(config_name=None):
    """Get configuration based on environment"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
    return config.get(config_name, config['default'])