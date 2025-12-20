"""
Configuration for API Gateway
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Application Configuration
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # JWT Configuration (shared secret with services)
    SECRET_KEY = os.getenv("SECRET_KEY", "campus-services-secret-key")
    
    # Service URLs
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:5000")
    REQUEST_SERVICE_URL = os.getenv("REQUEST_SERVICE_URL", "http://localhost:5002")
    BOOKING_SERVICE_URL = os.getenv("BOOKING_SERVICE_URL", "http://localhost:5001")
    NOTIFICATION_SERVICE_URL = os.getenv("NOTIFICATION_SERVICE_URL", "http://localhost:5003")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED = os.getenv("RATE_LIMIT_ENABLED", "True").lower() == "true"
    RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
    
    # Timeout Configuration
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
    
    @classmethod
    def validate_config(cls):
        """Validate required configuration"""
        required_vars = [
            'USER_SERVICE_URL', 
            'REQUEST_SERVICE_URL', 
            'BOOKING_SERVICE_URL', 
            'NOTIFICATION_SERVICE_URL'
        ]
        missing = [var for var in required_vars if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {missing}")
