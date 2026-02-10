import os
import sys
import logging
import platform
from dotenv import load_dotenv

# Load key-value pairs from .env file
load_dotenv()

# ============================================================
# LOGGING CONFIGURATION
# ============================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] %(message)s',
    handlers=[
        logging.FileHandler('nexcontrol.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("nexcontrol")

# ============================================================
# APP CONFIGURATION
# ============================================================
class Settings:
    PROJECT_NAME = "NexControl API"
    VERSION = "1.0.0"
    
    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY", "NexControl-Secret-Key-Change-Me-12345678")
    AES_KEY = os.getenv("AES_KEY", "NexControl-AES-Key-32-Bytes-Change!!")
    
    # JWT Configuration
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    JWT_ISSUER = "nexcontrol-server"
    ALGORITHM = "HS256"
    
    # AES Configuration
    AES_NONCE_LENGTH = 12
    
    # App Password Configuration
    DEFAULT_APP_PASSWORD = "admin123" # CHANGE IN PRODUCTION!
    APP_PASSWORD_HASH = os.getenv("APP_PASSWORD_HASH")
    
    # Rate Limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 15
    TIMESTAMP_TOLERANCE = 30
    
    # OS Detection
    OS_TYPE = platform.system()
    
    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

settings = Settings()

# Validation
if len(settings.SECRET_KEY) < 32:
    logger.warning("SECRET_KEY is too short (min 32 chars). Using insecure default if not set!")

if len(settings.AES_KEY) < 32:
    logger.warning("AES_KEY is too short (min 32 chars). Using insecure default if not set!")
