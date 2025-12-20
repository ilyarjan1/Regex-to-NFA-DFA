"""
Configuration for Request Service
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # MySQL Configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "request_db")
    
    # JWT Configuration (same as user service)
    SECRET_KEY = os.getenv("SECRET_KEY", "campus-services-secret-key")
    
    # Service URLs for inter-service communication
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:5000")
    NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:5003")
    
    # Application Configuration
    PORT = int(os.getenv("PORT", "5002"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Request Service Specific Configuration
    DEFAULT_PRIORITY = "medium"
    DEFAULT_STATUS = "pending"
    AUTO_ASSIGN_ENABLED = True
    
    # Allowed values for validation
    VALID_CATEGORIES = ["maintenance", "cleaning", "it_support", "facilities", "other"]
    VALID_PRIORITIES = ["low", "medium", "high", "urgent"]
    VALID_STATUSES = ["pending", "in_progress", "completed", "cancelled"]
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DB']
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
