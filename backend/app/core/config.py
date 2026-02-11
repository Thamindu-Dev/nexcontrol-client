import os
import sys
import logging
import platform
import re
import json
from pathlib import Path
from dotenv import load_dotenv

# Load key-value pairs from .env file (legacy mode)
load_dotenv()

# Try to import DPAPI for portable mode
DPAPI_AVAILABLE = False
if platform.system() == "Windows":
    try:
        import win32crypt
        DPAPI_AVAILABLE = True
    except ImportError:
        logger = logging.getLogger("nexcontrol")
        logger.warning("pywin32 not installed - DPAPI mode unavailable. Install with: pip install pywin32")

# ============================================================
# LOGGING CONFIGURATION
# ============================================================
# Create separate security audit logger
security_audit_handler = logging.FileHandler('security_audit.log')
security_audit_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

security_logger = logging.getLogger("security_audit")
security_logger.addHandler(security_audit_handler)
security_logger.setLevel(logging.INFO)

# Main application logger
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
# SECURITY VALIDATION FUNCTIONS
# ============================================================
def validate_aes_key(key: str) -> bool:
    """
    Validate AES key for strength and entropy.
    Prevents weak keys like 'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'
    """
    if not key or len(key) < 32:
        return False

    # Check entropy (must have variety of characters)
    unique_chars = len(set(key))
    if unique_chars < 16:  # At least 16 different characters
        return False

    # Must contain mix of character types
    has_upper = any(c.isupper() for c in key)
    has_lower = any(c.islower() for c in key)
    has_digit = any(c.isdigit() for c in key)
    has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in key)

    # Require at least 3 of the 4 character types
    char_types = sum([has_upper, has_lower, has_digit, has_special])
    if char_types < 3:
        return False

    # Reject repeating patterns
    if len(key) >= 8:
        # Check for same character repeated
        if all(c == key[0] for c in key):
            return False
        # Check for simple patterns (123, abc, etc.)
        pattern_score = 0
        for i in range(len(key) - 2):
            # Check sequential characters
            if (ord(key[i+1]) - ord(key[i]) == 1 and
                ord(key[i+2]) - ord(key[i+1]) == 1):
                pattern_score += 1
        if pattern_score > len(key) / 4:  # Too many sequential chars
            return False

    return True


# ============================================================
# PORTABLE MODE (DPAPI) CONFIG LOADING
# ============================================================
def load_dpapi_config() -> dict | None:
    """
    Load configuration from Windows AppData (DPAPI encrypted).
    Used for portable mode - keys are unique per installation.
    """
    if not DPAPI_AVAILABLE:
        return None

    try:
        import win32crypt
    except ImportError:
        return None

    config_dir = Path(os.getenv('LOCALAPPDATA', '~')) / 'NexControl'
    config_file = config_dir / 'config.dat'

    if not config_file.exists():
        return None

    try:
        encrypted_data = config_file.read_bytes()
        # Decrypt using DPAPI
        # CryptUnprotectData returns (description, data) tuple
        decrypted = win32crypt.CryptUnprotectData(encrypted_data)
        # Parse JSON from decrypted bytes (second element)
        return json.loads(decrypted[1].decode('utf-8'))
    except Exception as e:
        logger = logging.getLogger("nexcontrol")
        logger.warning(f"Failed to load DPAPI config: {e}")
        return None


# ============================================================
# APP CONFIGURATION
# ============================================================
class Settings:
    PROJECT_NAME = "NexControl API"
    VERSION = "1.0.0"

    # Security Configuration
    # Only use DPAPI (portable mode) - NO .env fallback for security
    _dpapi_config = load_dpapi_config()

    if _dpapi_config:
        # Portable mode - using DPAPI encrypted config
        SECRET_KEY = _dpapi_config.get("SECRET_KEY", "")
        AES_KEY = _dpapi_config.get("AES_KEY", "")
        APP_PASSWORD_HASH = _dpapi_config.get("APP_PASSWORD_HASH", "")
        _config_source = "DPAPI (portable mode)"
    else:
        # No config found - require setup wizard
        logger = logging.getLogger("nexcontrol")
        logger.critical("=" * 60)
        logger.critical("SECURITY ERROR: No configuration found!")
        logger.critical("-" * 60)
        logger.critical("The server requires secure configuration to start.")
        logger.critical("")
        logger.critical("Please run the setup wizard:")
        logger.critical("  1. Run: NexControl.exe (will launch setup automatically)")
        logger.critical("  2. Or run: python -m app.portable_setup")
        logger.critical("")
        logger.critical("The setup wizard will guide you through:")
        logger.critical("  - Creating an admin password")
        logger.critical("  - Generating unique AES keys")
        logger.critical("  - Exporting the AES key for your mobile app")
        logger.critical("=" * 60)
        raise RuntimeError(
            "No secure configuration found.\n\n"
            "Please run the setup wizard first:\n"
            "  1. Double-click NexControl.exe\n"
            "  2. Or run: python -m app.portable_setup\n\n"
            "The setup wizard will create a secure configuration with your own password."
        )

    # JWT Configuration - Reduced to 15 minutes for better security
    ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Reduced from 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7  # For future refresh token implementation
    JWT_ISSUER = "nexcontrol-server"
    ALGORITHM = "HS256"

    # AES Configuration
    AES_NONCE_LENGTH = 12

    # App Password Configuration
    # Loaded from DPAPI or .env above - no defaults

    # Rate Limiting
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_MINUTES = 15
    TIMESTAMP_TOLERANCE = 5  # Reduced from 30 to 5 seconds for better security

    # Power Action Rate Limiting (new)
    POWER_ACTION_LIMIT_PER_MINUTE = 5
    POWER_ACTION_WINDOW_SECONDS = 60

    # OS Detection
    OS_TYPE = platform.system()

    # CORS
    ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")  # production or development

settings = Settings()

# Validation with stronger checks
if len(settings.SECRET_KEY) < 32:
    logger.warning("SECRET_KEY is too short (min 32 chars). Using insecure default if not set!")

# Stronger AES key validation
if not validate_aes_key(settings.AES_KEY):
    logger.warning("AES_KEY is weak! Must be 32+ chars with mixed case, numbers, and symbols.")
    logger.warning("Example of strong key: 'MySecr3t-K3y!With$Mixed@Chars2026'")

# Log security configuration on startup
security_logger.info("=" * 60)
security_logger.info(f"NexControl Server v{settings.VERSION} starting")
security_logger.info(f"Config Source: {settings._config_source}")
security_logger.info(f"Environment: {settings.ENVIRONMENT}")
security_logger.info(f"Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")
security_logger.info(f"Timestamp Tolerance: {settings.TIMESTAMP_TOLERANCE} seconds")
security_logger.info("=" * 60)
