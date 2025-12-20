"""
Configuration for Notification Service
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # MySQL Configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST", "172.17.0.1")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "notification_db")
    
    # JWT Configuration (shared with other services)
    SECRET_KEY = os.getenv("SECRET_KEY", "campus-services-secret-key")
    
    # Email Configuration
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USER = os.getenv("EMAIL_USER", "")
    EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@campus.edu")
    
    # Application Configuration
    PORT = int(os.getenv("PORT", "5003"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Notification Service Specific Configuration
    DEFAULT_NOTIFICATION_TYPE = "general"
    VALID_NOTIFICATION_TYPES = ["general", "request_update", "booking_confirmed", 
                                "announcement", "urgent", "system"]
    
    VALID_PRIORITIES = ["low", "medium", "high"]
    VALID_TARGET_AUDIENCES = ["all", "students", "staff", "admin"]
    
    # Email settings
    SEND_EMAIL_ENABLED = EMAIL_USER and EMAIL_PASSWORD
    EMAIL_SUBJECT_PREFIX = "[Campus Services] "
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = ['MYSQL_HOST', 'MYSQL_USER', 'MYSQL_PASSWORD', 'MYSQL_DB']
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")