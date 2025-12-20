import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Use DB_ prefix to match app.py
    DB_HOST = os.getenv("DB_HOST", "172.17.0.1")
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    DB_NAME = os.getenv("DB_NAME", "booking_db")
    
    SECRET_KEY = os.getenv("SECRET_KEY", "campus-services-secret-key")
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
    USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://localhost:5001")
