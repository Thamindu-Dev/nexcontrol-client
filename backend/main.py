#!/usr/bin/env python3
"""
============================================================
NexControl Backend - FastAPI Server
============================================================
A secure, local network Remote PC Controller backend.
Supports system monitoring, power management, Docker control,
process management, and screenshot capture.

Architecture:
- FastAPI for REST API
- AES-256-GCM for payload encryption
- Argon2id for password hashing (OWASP/NIST recommended)
- JWT for authentication
- Replay attack prevention via timestamps
- Rate limiting for brute force protection
- Input validation for security

Author: NexControl Team
Target: Engineering Students & SysAdmins
============================================================
"""

import os
import sys
import platform
import subprocess
import base64
import time
import logging
import re
import secrets
import asyncio
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from functools import wraps

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# ============================================================
# LOGGING (must be configured before other imports)
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] %(message)s',
    handlers=[
        logging.FileHandler('nexcontrol.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================
# IMPORTS
# ============================================================

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator, constr
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

import psutil
# pyautogui is optional - only needed for screenshots
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except (ImportError, KeyError, Exception) as e:
    PYAUTOGUI_AVAILABLE = False
    logger.warning(f"pyautogui not available: screenshot feature disabled ({type(e).__name__})")

# Docker SDK imports
try:
    from docker.errors import DockerException
    from docker import from_env
    DOCKER_AVAILABLE = True
except ImportError:
    DOCKER_AVAILABLE = False
    DockerException = Exception
    from_env = None
    logger.warning("Docker SDK not installed")
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend
from cryptography.exceptions import InvalidTag
import jose.exceptions
from jose import jwt
from passlib.context import CryptContext

# Password hashing context (must be defined before use)
# Using Argon2id - OWASP recommended and NIST approved password hashing algorithm
# Argon2id provides the best balance between resistance to GPU/ASIC attacks and side-channel attacks
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=3,        # Number of iterations
    argon2__memory_cost=65536,  # 64 MB memory cost (in KiB)
    argon2__parallelism=4,      # Number of parallel threads
    argon2__hash_len=32,        # Hash length in bytes
    argon2__salt_len=16         # Salt length in bytes
)

# ============================================================
# CONFIGURATION & CONSTANTS
# ============================================================

# Security Configuration - Load from environment with validation
def get_secret_key() -> bytes:
    """
    Get and validate SECRET_KEY from environment.

    The key is hashed using SHA-256 to ensure consistent length and security.
    This prevents truncation issues while maintaining key entropy.
    """
    key = os.getenv("SECRET_KEY")
    if not key:
        logger.warning("SECRET_KEY not set, using insecure default! CHANGE THIS IN PRODUCTION!")
        key = "NexControl-Secret-Key-Change-Me-12345678"
    if len(key) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")
    # Hash the key to ensure consistent 32-byte length for HMAC
    import hashlib
    return hashlib.sha256(key.encode()).digest()

def get_aes_key() -> bytes:
    """Get and validate AES_KEY from environment"""
    key = os.getenv("AES_KEY")
    if not key:
        logger.warning("AES_KEY not set, using insecure default! CHANGE THIS IN PRODUCTION!")
        key = "NexControl-AES-Key-32-Bytes-Change!!"
    if len(key) < 32:
        raise ValueError("AES_KEY must be at least 32 characters long")
    return key.encode()[:32]

try:
    SECRET_KEY = get_secret_key()
    AES_KEY = get_aes_key()
except ValueError as e:
    logger.error(f"Security configuration error: {e}")
    sys.exit(1)

ALGORITHM = "HS256"

# JWT Configuration
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour (reduced from 24h for better security)
JWT_ISSUER = "nexcontrol-server"  # Issuer claim for token validation

# AES Encryption Configuration
AES_NONCE_LENGTH = 12  # 96-bit nonce for GCM

# App Password Configuration
# Default password: admin123
# Generate hash at startup to ensure it's correct
DEFAULT_APP_PASSWORD = "admin123"  # CHANGE IN PRODUCTION!

# Check if custom hash is provided in environment
custom_hash = os.getenv("APP_PASSWORD_HASH")
if custom_hash:
    app_password_hash = custom_hash
    logger.info("Using custom password hash from environment")
else:
    # Generate hash from default password
    app_password_hash = pwd_context.hash(DEFAULT_APP_PASSWORD)
    logger.info(f"Generated hash for default password '{DEFAULT_APP_PASSWORD}'")

# Rate Limiting Configuration
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

# Timestamp tolerance for replay attack prevention (seconds)
TIMESTAMP_TOLERANCE = 30

# OS Detection
OS_TYPE = platform.system()  # 'Windows', 'Linux', 'Darwin'
logger.info(f"Operating System detected: {OS_TYPE}")

# CORS Configuration - Allow all origins for local network access
# SECURITY: For production, set specific origins via environment variable
# Example: ALLOWED_ORIGINS=http://localhost:8080,https://app.example.com
# Note: When allow_credentials=False, we can use ["*"] to allow all origins
# For a local network app with JWT auth, we don't need credentials
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ============================================================
# FASTAPI APP INITIALIZATION
# ============================================================

# Lifespan context manager for background services
# Note: Managers are instantiated later in the file, but lifespan is called at runtime
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage lifespan events for background services"""
    # Startup
    logger.info("Starting scheduled task manager...")
    await scheduled_task_manager.start_scheduler()
    logger.info("Starting threshold notification manager...")
    await threshold_notification_manager.start_monitor()

    yield

    # Shutdown
    logger.info("Stopping scheduled task manager...")
    await scheduled_task_manager.stop_scheduler()
    logger.info("Stopping threshold notification manager...")
    await threshold_notification_manager.stop_monitor()
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage lifespan events for background services"""
    # Startup
    logger.info("Starting scheduled task manager...")
    await scheduled_task_manager.start_scheduler()
    logger.info("Starting threshold notification manager...")
    await threshold_notification_manager.start_monitor()

    yield

    # Shutdown
    logger.info("Stopping scheduled task manager...")
    await scheduled_task_manager.stop_scheduler()
    logger.info("Stopping threshold notification manager...")
    await threshold_notification_manager.stop_monitor()


# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="NexControl API",
    description="Secure Remote PC Controller Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware - Configure based on environment
# SECURITY: When allow_credentials=False, we can use ["*"] to allow all origins
# However, for production use, it's recommended to set specific origins via ALLOWED_ORIGINS env var
# Authentication is handled via JWT tokens in Authorization header, not cookies
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=False,  # Must be False when using wildcard origins
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],  # Explicitly allow common methods
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Encrypted",
        "X-Timestamp",
        "X-Request-ID"
    ],  # Explicitly allow required headers
    max_age=600,  # Cache preflight response for 10 minutes
    expose_headers=["X-Request-ID"]  # Expose custom headers to browser
)

# Login attempt tracking (in production, use Redis)
login_attempts = {}
locked_accounts = {}

# ============================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ============================================================

class LoginRequest(BaseModel):
    """Login request schema with validation"""
    password: constr(min_length=4, max_length=128) = Field(
        ...,
        description="App password for authentication"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Prevent common injection patterns"""
        if any(char in v for char in [';', '|', '&', '$', '`', '\n', '\r']):
            raise ValueError("Password contains invalid characters")
        return v

class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class EncryptedPayload(BaseModel):
    """Encrypted request payload schema"""
    data: str = Field(..., min_length=1, description="Base64-encoded encrypted data (includes nonce)")
    timestamp: float = Field(..., description="Unix timestamp for replay attack prevention")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp_format(cls, v):
        """Validate timestamp is reasonable"""
        if v < 0 or v > (time.time() + 3600):
            raise ValueError("Invalid timestamp")
        return v

class CommandResponse(BaseModel):
    """Standard command response schema"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PowerActionRequest(BaseModel):
    """Power action request schema with validation"""
    action: str = Field(..., description="Action: shutdown, hibernate, restart")
    delay_seconds: int = Field(0, ge=0, le=86400, description="Delay before execution (0-86400 seconds)")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is allowed"""
        allowed = ['shutdown', 'hibernate', 'restart']
        if v.lower() not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v.lower()


# Scheduled Task Models
class ScheduledTask(BaseModel):
    """Scheduled task model"""
    id: str = Field(..., description="Unique task ID")
    name: str = Field(..., min_length=1, max_length=100, description="Task name")
    action: str = Field(..., description="Action: shutdown, hibernate, restart")
    scheduled_time: str = Field(..., description="Scheduled time in ISO format")
    enabled: bool = Field(True, description="Whether the task is enabled")
    created_at: str = Field(..., description="Creation timestamp in ISO format")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is allowed"""
        allowed = ['shutdown', 'hibernate', 'restart']
        if v.lower() not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v.lower()


class CreateScheduledTaskRequest(BaseModel):
    """Create scheduled task request schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Task name")
    action: str = Field(..., description="Action: shutdown, hibernate, restart")
    scheduled_time: str = Field(..., description="Scheduled time in ISO format (YYYY-MM-DDTHH:MM:SS)")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is allowed"""
        allowed = ['shutdown', 'hibernate', 'restart']
        if v.lower() not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator('scheduled_time')
    @classmethod
    def validate_scheduled_time(cls, v):
        """Validate scheduled time is in the future"""
        try:
            scheduled_dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            if scheduled_dt <= datetime.now(scheduled_dt.tzinfo):
                raise ValueError("Scheduled time must be in the future")
        except ValueError as e:
            if "must be in the future" in str(e):
                raise
            raise ValueError("Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
        return v


class UpdateScheduledTaskRequest(BaseModel):
    """Update scheduled task request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Task name")
    action: Optional[str] = Field(None, description="Action: shutdown, hibernate, restart")
    scheduled_time: Optional[str] = Field(None, description="Scheduled time in ISO format")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is allowed"""
        if v is None:
            return v
        allowed = ['shutdown', 'hibernate', 'restart']
        if v.lower() not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v.lower()


# Threshold Notification Models
class ThresholdConfig(BaseModel):
    """Threshold configuration model"""
    cpu_threshold: int = Field(80, ge=0, le=100, description="CPU usage threshold percentage")
    memory_threshold: int = Field(85, ge=0, le=100, description="Memory usage threshold percentage")
    disk_threshold: int = Field(90, ge=0, le=100, description="Disk usage threshold percentage")
    enabled: bool = Field(True, description="Whether threshold monitoring is enabled")

    class Config:
        json_schema_extra = {
            "example": {
                "cpu_threshold": 80,
                "memory_threshold": 85,
                "disk_threshold": 90,
                "enabled": True
            }
        }


class ThresholdAlert(BaseModel):
    """Threshold alert model"""
    id: str
    metric_type: str = Field(..., description="Type: cpu, memory, disk")
    threshold: int = Field(..., description="Threshold value that was exceeded")
    current_value: float = Field(..., description="Current value that exceeded threshold")
    timestamp: str = Field(..., description="Alert timestamp")
    acknowledged: bool = Field(False, description="Whether alert was acknowledged")

# ============================================================
# SECURITY MANAGER CLASS
# ============================================================

class SecurityManager:
    """
    Handles all security-related operations:
    - AES-256-GCM encryption/decryption
    - JWT token generation/validation
    - Password hashing/verification
    - Timestamp validation for replay attack prevention
    - Input sanitization
    """

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using Argon2id (OWEF/NSA recommended)"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash using constant-time comparison"""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            # Use constant-time comparison for security
            return False

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token

        Args:
            data: Data to encode in token (typically user_id or similar)
            expires_delta: Token expiration time

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

        # Add standard JWT claims for security
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16),  # JWT ID for potential revocation
            "iss": JWT_ISSUER             # Issuer claim for validation
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        """
        Verify and decode a JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            HTTPException: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY,
                algorithms=[ALGORITHM],
                issuer=JWT_ISSUER
            )
            return payload
        except jose.exceptions.ExpiredSignatureError:
            logger.warning("Expired token attempt detected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jose.exceptions.InvalidIssuerError:
            logger.warning("Invalid token issuer detected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )
        except jose.exceptions.JWTError as e:
            logger.warning(f"Invalid token attempt: {str(e)[:100]}")  # Don't log full error
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    def encrypt_data(data: dict) -> str:
        """
        Encrypt data using AES-256-GCM

        Format: nonce (12 bytes) + ciphertext + tag (16 bytes)
        Returns: Base64-encoded string

        Args:
            data: Dictionary to encrypt

        Returns:
            Base64-encoded encrypted data (includes nonce)

        Raises:
            HTTPException: If encryption fails
        """
        try:
            import json

            # Validate data is dict
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")

            # Convert dict to JSON string
            json_data = json.dumps(data).encode('utf-8')

            # Generate random nonce (96-bit for GCM)
            nonce = os.urandom(AES_NONCE_LENGTH)

            # Create AESGCM cipher
            aesgcm = AESGCM(AES_KEY)

            # Encrypt data (GCM mode appends tag automatically)
            ciphertext = aesgcm.encrypt(nonce, json_data, None)

            # Combine nonce + ciphertext
            combined = nonce + ciphertext

            # Return as base64 string
            return base64.b64encode(combined).decode('utf-8')

        except Exception as e:
            logger.error(f"Encryption error: {str(e)[:100]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Encryption failed"
            )

    @staticmethod
    def decrypt_data(encrypted_data: str) -> dict:
        """
        Decrypt AES-256-GCM encrypted data

        Args:
            encrypted_data: Base64-encoded encrypted data (includes nonce)

        Returns:
            Decrypted dictionary

        Raises:
            HTTPException: If decryption fails (401 for key mismatch, 400 for bad format)
        """
        try:
            import json

            # Validate input
            if not encrypted_data or not isinstance(encrypted_data, str):
                raise ValueError("Invalid encrypted data format")

            # Decode base64
            try:
                combined = base64.b64decode(encrypted_data)
            except Exception:
                raise ValueError("Invalid base64 encoding")

            # Validate minimum length (nonce + minimum ciphertext + tag)
            if len(combined) < AES_NONCE_LENGTH + 16:
                raise ValueError("Encrypted data too short")

            # Split nonce and ciphertext
            nonce = combined[:AES_NONCE_LENGTH]
            ciphertext = combined[AES_NONCE_LENGTH:]

            # Create AESGCM cipher
            aesgcm = AESGCM(AES_KEY)

            # Decrypt data
            decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)

            # Convert to dict
            return json.loads(decrypted_data.decode('utf-8'))

        except ValueError as e:
            logger.warning(f"Decryption validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid encrypted data format"
            )
        except CryptoError as e:
            # THIS IS THE CRITICAL PART: Decryption failure = Wrong Key
            logger.warning(f"DECRYPTION FAILED (Invalid AES Key): {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Encryption Key"
            )
        except Exception as e:
            logger.error(f"Decryption error: {str(e)[:100]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Decryption failed"
            )

    @staticmethod
    def validate_timestamp(timestamp: float, tolerance: int = TIMESTAMP_TOLERANCE) -> bool:
        """
        Validate timestamp to prevent replay attacks

        Args:
            timestamp: Unix timestamp from request
            tolerance: Maximum allowed time difference in seconds

        Returns:
            True if timestamp is valid, False otherwise
        """
        current_time = time.time()
        time_diff = abs(current_time - timestamp)

        if time_diff > tolerance:
            logger.warning(f"Timestamp validation failed. Difference: {time_diff:.2f}s > {tolerance}s")
            return False

        return True

    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 256) -> str:
        """
        Sanitize string input to prevent injection attacks

        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized string
        """
        if not isinstance(input_str, str):
            raise ValueError("Input must be a string")

        # Truncate to max length
        input_str = input_str[:max_length]

        # Remove dangerous characters
        dangerous_chars = ['\x00', '\n', '\r', '\x1a', '\\', "'", '"', ';', '|', '&', '$', '`', '<', '>']
        for char in dangerous_chars:
            input_str = input_str.replace(char, '')

        # Remove any control characters except tab
        input_str = ''.join(char for char in input_str if char == '\t' or char.isprintable())

        return input_str.strip()

    @staticmethod
    def validate_pid(pid: int) -> bool:
        """
        Validate process ID is within reasonable range

        Args:
            pid: Process ID to validate

        Returns:
            True if valid, False otherwise
        """
        # PIDs are typically between 1 and 4,194,304 on most systems
        # Maximum PID on Linux is typically /proc/sys/kernel/pid_max (default 4194304)
        return isinstance(pid, int) and 1 <= pid <= 4194304

    @staticmethod
    def validate_container_id(container_id: str) -> bool:
        """
        Validate Docker container ID format

        Args:
            container_id: Container ID or name

        Returns:
            True if valid format, False otherwise
        """
        if not isinstance(container_id, str):
            return False

        # Container ID is 64 hex chars, or a shorter ID, or a name
        # Allow: hex string (up to 64 chars) or name (alphanumeric, _, -, .)
        sanitized = SecurityManager.sanitize_input(container_id, max_length=256)

        # Check if it's a hex ID or valid name
        hex_pattern = r'^[a-f0-9]{1,64}$'
        name_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$'

        return bool(re.match(hex_pattern, sanitized) or re.match(name_pattern, sanitized))

    @staticmethod
    def validate_mac_address(mac: str) -> bool:
        """
        Validate MAC address format

        Args:
            mac: MAC address string

        Returns:
            True if valid, False otherwise
        """
        if not isinstance(mac, str):
            return False

        mac = mac.strip()
        # Accept XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX format
        mac_pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(mac_pattern, mac))


# ============================================================
# RATE LIMITING & LOGIN TRACKING
# ============================================================

def check_login_attempts(client_ip: str) -> bool:
    """
    Check if client has exceeded login attempts

    Args:
        client_ip: Client IP address

    Returns:
        True if allowed, False if locked out
    """
    current_time = time.time()

    # Check if account is locked
    if client_ip in locked_accounts:
        lockout_expiry = locked_accounts[client_ip]
        if current_time < lockout_expiry:
            remaining = int((lockout_expiry - current_time) / 60)
            logger.warning(f"Locked login attempt from {client_ip}. {remaining} minutes remaining.")
            return False
        else:
            # Lockout expired, remove it
            del locked_accounts[client_ip]
            if client_ip in login_attempts:
                del login_attempts[client_ip]

    return True


def record_login_attempt(client_ip: str, success: bool):
    """
    Record login attempt for rate limiting

    Args:
        client_ip: Client IP address
        success: Whether login was successful
    """
    if success:
        # Clear attempts on successful login
        if client_ip in login_attempts:
            del login_attempts[client_ip]
    else:
        # Increment failed attempts
        login_attempts[client_ip] = login_attempts.get(client_ip, 0) + 1

        # Check if should lock out
        if login_attempts[client_ip] >= MAX_LOGIN_ATTEMPTS:
            lockout_until = time.time() + (LOGIN_LOCKOUT_MINUTES * 60)
            locked_accounts[client_ip] = lockout_until
            logger.warning(f"Account locked for {client_ip} after {MAX_LOGIN_ATTEMPTS} failed attempts")


# ============================================================
# SYSTEM MONITOR CLASS
# ============================================================

class SystemMonitor:
    """
    Monitor system resources using psutil
    Provides methods to get CPU, Memory, Disk, and GPU stats
    All methods have comprehensive error handling
    """

    @staticmethod
    def get_cpu_usage() -> dict:
        """
        Get CPU usage statistics

        Returns:
            Dict with CPU usage percentage and core counts
        """
        cpu_percent = 0  # Initialize with default value

        try:
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            # Method 1: Try per-CPU percentage first (more accurate)
            try:
                per_cpu_percent = psutil.cpu_percent(interval=0.5, percpu=True)
                if per_cpu_percent and len(per_cpu_percent) > 0:
                    # Calculate average, filtering any invalid values
                    valid_values = [p for p in per_cpu_percent if 0 <= p <= 100]
                    if valid_values:
                        cpu_percent = sum(valid_values) / len(valid_values)
            except Exception as e1:
                logger.debug(f"Method 1 failed: {e1}")
                # Method 2: Fallback to simple CPU percent
                try:
                    cpu_percent = psutil.cpu_percent(interval=1.0)
                except Exception as e2:
                    logger.debug(f"Method 2 failed: {e2}")
                    # Method 3: Calculate from CPU times
                    try:
                        cpu_times1 = psutil.cpu_times()
                        import time
                        time.sleep(0.2)
                        cpu_times2 = psutil.cpu_times()

                        # Calculate usage from CPU times
                        user_diff = cpu_times2.user - cpu_times1.user
                        system_diff = cpu_times2.system - cpu_times1.system
                        idle_diff = cpu_times2.idle - cpu_times1.idle
                        total_diff = user_diff + system_diff + idle_diff

                        if total_diff > 0:
                            cpu_percent = ((user_diff + system_diff) / total_diff) * 100
                    except Exception as e3:
                        logger.debug(f"Method 3 failed: {e3}")
                        cpu_percent = 0

            return {
                "cpu_percent": round(min(100, max(0, cpu_percent)), 2),
                "cpu_count": cpu_count if cpu_count else 0,
                "cpu_freq_mhz": round(cpu_freq.current, 2) if cpu_freq else 0
            }
        except Exception as e:
            logger.error(f"Error getting CPU stats: {type(e).__name__}: {str(e)}")
            return {"cpu_percent": 0, "cpu_count": 0, "cpu_freq_mhz": 0, "error": "Failed to get CPU stats"}

    @staticmethod
    def get_memory_usage() -> dict:
        """
        Get memory usage statistics

        Returns:
            Dict with memory usage in bytes and percentages
        """
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            return {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "free": mem.free,
                "percent": round(mem.percent, 2),
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": round(swap.percent, 2)
            }
        except Exception as e:
            logger.error(f"Error getting memory stats: {type(e).__name__}")
            return {"percent": 0, "error": "Failed to get memory stats"}

    @staticmethod
    def get_disk_usage(path: str = None) -> dict:
        """
        Get disk usage statistics (legacy - single disk)

        Args:
            path: Path to check (auto-detected if None)

        Returns:
            Dict with disk usage in bytes and percentages
        """
        try:
            # Auto-detect path based on OS
            if path is None:
                if OS_TYPE == "Windows":
                    path = "C:\\"
                elif OS_TYPE == "Darwin":  # macOS
                    path = "/"
                else:  # Linux
                    path = "/"

            # Sanitize path
            path = SecurityManager.sanitize_input(path, max_length=256)

            disk = psutil.disk_usage(path)

            return {
                "path": path,
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": round(disk.percent, 2)
            }
        except PermissionError:
            logger.error(f"Permission denied accessing disk: {path}")
            return {"percent": 0, "error": "Permission denied"}
        except FileNotFoundError:
            logger.error(f"Disk path not found: {path}")
            return {"percent": 0, "error": "Disk path not found"}
        except Exception as e:
            logger.error(f"Error getting disk stats: {type(e).__name__}")
            return {"percent": 0, "error": "Failed to get disk stats"}

    @staticmethod
    def get_all_disks() -> dict:
        """
        Get all attached storage devices (HDD, SSD, USB, partitions)

        Detects:
        - All disk partitions on Windows (C:, D:, etc.)
        - All mounted partitions on Linux/macOS
        - USB drives and external storage
        - Provides usage stats for each detected disk

        Returns:
            Dict with list of all disks/partitions
        """
        disks = []

        try:
            # Get all disk partitions
            partitions = psutil.disk_partitions(all=True)

            # Track unique devices to avoid duplicates
            seen_devices = set()

            for partition in partitions:
                try:
                    # Skip non-filesystem and special partitions
                    if partition.fstype == '' or partition.fstype == 'swap':
                        continue

                    # Skip common Linux special filesystems
                    if OS_TYPE == "Linux":
                        if any(partition.mountpoint.startswith(p) for p in ['/dev', '/proc', '/sys', '/run']):
                            continue

                    # Get device name for deduplication
                    device_key = f"{partition.device}:{partition.fstype}"
                    if device_key in seen_devices:
                        continue
                    seen_devices.add(device_key)

                    # Get disk usage if mountpoint is accessible
                    usage = None
                    try:
                        if partition.mountpoint and partition.mountpoint != '':
                            usage = psutil.disk_usage(partition.mountpoint)
                    except (PermissionError, FileNotFoundError):
                        # Can't access this partition, but still include it
                        pass

                    disk_info = {
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "opts": partition.opts
                    }

                    # Determine drive type from mount options
                    drive_type = "Unknown"
                    if partition.opts:
                        opts_lower = partition.opts.lower()
                        if 'fixed' in opts_lower:
                            drive_type = "Internal"
                        elif any(indicator in opts_lower for indicator in ['removable', 'usb', 'cdrom']):
                            drive_type = "External"
                    disk_info["drive_type"] = drive_type

                    # Add usage info if available
                    if usage:
                        disk_info.update({
                            "total": usage.total,
                            "used": usage.used,
                            "free": usage.free,
                            "percent": round(usage.percent, 2)
                        })
                    else:
                        disk_info["percent"] = None

                    # Determine if this is likely a removable/USB drive
                    # FIXED: Check for 'fixed' in opts to identify internal partitions
                    is_removable = False

                    if OS_TYPE == "Windows":
                        # On Windows, use win32api to check drive type if available
                        # Otherwise, be conservative - don't assume non-C: drives are removable
                        # Most Windows systems have multiple internal partitions (D:, E:, etc.)
                        is_removable = False  # Default to internal (fixed) on Windows
                        # TODO: Could use win32api.GetDriveType for accurate detection
                    else:  # Linux/macOS
                        # FIXED: Check opts for 'fixed' first - indicates internal partition
                        if partition.opts and 'fixed' in partition.opts.lower():
                            is_removable = False  # Internal partition
                        # Then check for removable indicators
                        elif partition.opts:
                            removable_indicators = ['removable', 'usb', 'cdrom']
                            if any(indicator in partition.opts.lower() for indicator in removable_indicators):
                                is_removable = True

                        # Check if mounted under /media or /mnt (common for USB)
                        if partition.mountpoint and not is_removable:
                            if any(partition.mountpoint.startswith(p) for p in ['/media/', '/mnt/']):
                                is_removable = True

                        # Additional check: /boot, /boot/efi, /home, /, /var, etc. are internal
                        if partition.mountpoint and not is_removable:
                            internal_mountpoints = ['/', '/boot', '/home', '/var', '/usr', '/opt', '/root']
                            if any(partition.mountpoint == p or partition.mountpoint.startswith(p + '/') for p in internal_mountpoints):
                                is_removable = False

                    disk_info["is_removable"] = is_removable
                    disks.append(disk_info)

                except PermissionError:
                    # Skip partitions we can't access
                    continue
                except Exception as e:
                    logger.warning(f"Error processing partition {partition.device}: {type(e).__name__}")
                    continue

            logger.info(f"Found {len(disks)} disk/partition(s)")

            return {
                "disks": disks,
                "count": len(disks)
            }

        except Exception as e:
            logger.error(f"Error getting all disks: {type(e).__name__}: {str(e)}")
            return {
                "disks": [],
                "count": 0,
                "error": str(e)
            }

    @staticmethod
    def get_gpu_temperature() -> dict:
        """
        Get GPU temperature (NVIDIA GPUs only)

        Returns:
            Dict with GPU temperature info
        """
        try:
            import pynvml

            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()

            gpu_data = []
            for i in range(device_count):
                try:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    name = pynvml.nvmlDeviceGetName(handle)
                    memory = pynvml.nvmlDeviceGetMemoryInfo(handle)

                    gpu_data.append({
                        "id": i,
                        "name": name.decode('utf-8') if isinstance(name, bytes) else name,
                        "temperature_c": temp,
                        "memory_total": memory.total,
                        "memory_used": memory.used,
                        "memory_percent": round((memory.used / memory.total) * 100, 2)
                    })
                except Exception as e:
                    logger.warning(f"Error reading GPU {i}: {type(e).__name__}")
                    continue

            pynvml.nvmlShutdown()

            if gpu_data:
                return {"gpus": gpu_data}
            else:
                return {"error": "No GPU data available"}

        except ImportError:
            logger.warning("pynvml not installed, GPU temp unavailable")
            return {"error": "GPU monitoring not available (pynvml not installed)"}
        except Exception as e:
            logger.error(f"Error getting GPU stats: {type(e).__name__}")
            return {"error": "Failed to get GPU stats"}

    @staticmethod
    def get_gpu_usage() -> dict:
        """
        Get GPU utilization percentage and memory usage
        Returns GPU stats in format expected by the frontend

        Returns:
            Dict with GPU utilization percentage, name, and memory info
        """
        try:
            import pynvml

            pynvml.nvmlInit()
            device_count = pynvml.nvmlDeviceGetCount()

            if device_count == 0:
                return None

            # Get first GPU data (for simplicity, returning primary GPU)
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)

            # Get GPU name
            name = pynvml.nvmlDeviceGetName(handle)
            gpu_name = name.decode('utf-8') if isinstance(name, bytes) else name

            # Get GPU utilization
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            gpu_percent = utilization.gpu  # GPU core utilization percentage

            # Get memory info
            memory = pynvml.nvmlDeviceGetMemoryInfo(handle)
            memory_percent = round((memory.used / memory.total) * 100, 2)

            pynvml.nvmlShutdown()

            return {
                "name": gpu_name,
                "usage_percent": gpu_percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "memory_free": memory.free,
                "memory_percent": memory_percent
            }

        except ImportError:
            logger.warning("pynvml not installed, GPU usage unavailable")
            return None
        except Exception as e:
            logger.error(f"Error getting GPU usage: {type(e).__name__}: {str(e)}")
            return None

    @staticmethod
    def get_network_stats() -> dict:
        """
        Get network I/O statistics

        Returns:
            Dict with network bytes sent/received
        """
        try:
            net_io = psutil.net_io_counters()
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errors_in": net_io.errin,
                "errors_out": net_io.errout
            }
        except Exception as e:
            logger.error(f"Error getting network stats: {type(e).__name__}")
            return {"error": "Failed to get network stats"}

    @staticmethod
    def get_all_stats() -> dict:
        """
        Get all system statistics in one call

        Returns:
            Combined dict of all system stats
        """
        return {
            "cpu": SystemMonitor.get_cpu_usage(),
            "memory": SystemMonitor.get_memory_usage(),
            "disk": SystemMonitor.get_disk_usage(),
            "gpu": SystemMonitor.get_gpu_usage(),
            "network": SystemMonitor.get_network_stats(),
            "timestamp": time.time()
        }


# ============================================================
# POWER MANAGER CLASS
# ============================================================

class PowerManager:
    """
    Handle power management operations
    Supports shutdown, hibernate, restart for Windows and Linux
    All commands are validated to prevent injection attacks
    """

    @staticmethod
    def shutdown(delay_seconds: int = 0) -> dict:
        """
        Shutdown the system

        Args:
            delay_seconds: Delay before shutdown (0 = immediate, max 86400)

        Returns:
            Dict with success status and message
        """
        try:
            # Validate delay
            if not isinstance(delay_seconds, int) or delay_seconds < 0 or delay_seconds > 86400:
                return {"success": False, "message": "Invalid delay (must be 0-86400 seconds)"}

            if OS_TYPE == "Windows":
                # Windows: shutdown /s /t <seconds>
                # Using list of args instead of shell=True for security
                cmd = ["shutdown", "/s", "/t", str(delay_seconds)]
                result = subprocess.run(
                    cmd,
                    shell=False,  # Don't use shell for security
                    capture_output=True,
                    timeout=10
                )
            elif OS_TYPE == "Linux":
                # Linux: shutdown -h now or shutdown -h +<minutes>
                if delay_seconds == 0:
                    cmd = ["shutdown", "-h", "now"]
                else:
                    minutes = max(1, delay_seconds // 60)  # At least 1 minute
                    cmd = ["shutdown", "-h", f"+{minutes}"]

                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            elif OS_TYPE == "Darwin":  # macOS
                cmd = ["shutdown", "-h", "now"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            else:
                return {"success": False, "message": f"Unsupported OS: {OS_TYPE}"}

            return {
                "success": True,
                "message": f"System shutdown initiated in {delay_seconds} seconds"
            }

        except subprocess.TimeoutExpired:
            logger.error("Shutdown command timed out")
            return {"success": False, "message": "Shutdown command timed out"}
        except PermissionError:
            logger.error("Permission denied for shutdown")
            return {"success": False, "message": "Insufficient permissions"}
        except FileNotFoundError:
            logger.error("Shutdown command not found")
            return {"success": False, "message": "Shutdown command not available"}
        except Exception as e:
            logger.error(f"Shutdown error: {type(e).__name__}")
            return {"success": False, "message": "Shutdown failed"}

    @staticmethod
    def hibernate() -> dict:
        """
        Hibernate the system

        Returns:
            Dict with success status and message
        """
        try:
            if OS_TYPE == "Windows":
                # Windows: shutdown /h
                cmd = ["shutdown", "/h"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            elif OS_TYPE == "Linux":
                # Linux: systemctl hibernate
                # Try systemctl first
                try:
                    cmd = ["systemctl", "hibernate"]
                    result = subprocess.run(
                        cmd,
                        shell=False,
                        capture_output=True,
                        timeout=10,
                        check=True
                    )
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fallback: write to sysfs (requires root)
                    logger.warning("systemctl hibernate failed, trying sysfs method")
                    return {
                        "success": False,
                        "message": "Hibernate requires root privileges (systemctl hibernate)"
                    }
            elif OS_TYPE == "Darwin":  # macOS
                # macOS: pmset sleepnow
                cmd = ["pmset", "sleepnow"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            else:
                return {"success": False, "message": f"Unsupported OS: {OS_TYPE}"}

            return {"success": True, "message": "System hibernation initiated"}

        except subprocess.TimeoutExpired:
            logger.error("Hibernate command timed out")
            return {"success": False, "message": "Hibernate command timed out"}
        except PermissionError:
            logger.error("Permission denied for hibernate")
            return {"success": False, "message": "Insufficient permissions for hibernate"}
        except FileNotFoundError:
            logger.error("Hibernate command not found")
            return {"success": False, "message": "Hibernate command not available"}
        except Exception as e:
            logger.error(f"Hibernate error: {type(e).__name__}")
            return {"success": False, "message": "Hibernate failed"}

    @staticmethod
    def restart(delay_seconds: int = 0) -> dict:
        """
        Restart the system

        Args:
            delay_seconds: Delay before restart (0 = immediate, max 86400)

        Returns:
            Dict with success status and message
        """
        try:
            # Validate delay
            if not isinstance(delay_seconds, int) or delay_seconds < 0 or delay_seconds > 86400:
                return {"success": False, "message": "Invalid delay (must be 0-86400 seconds)"}

            if OS_TYPE == "Windows":
                # Windows: shutdown /r /t <seconds>
                cmd = ["shutdown", "/r", "/t", str(delay_seconds)]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            elif OS_TYPE == "Linux":
                # Linux: shutdown -r now or shutdown -r +<minutes>
                if delay_seconds == 0:
                    cmd = ["shutdown", "-r", "now"]
                else:
                    minutes = max(1, delay_seconds // 60)  # At least 1 minute
                    cmd = ["shutdown", "-r", f"+{minutes}"]

                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            elif OS_TYPE == "Darwin":  # macOS
                cmd = ["shutdown", "-r", "now"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            else:
                return {"success": False, "message": f"Unsupported OS: {OS_TYPE}"}

            return {
                "success": True,
                "message": f"System restart initiated in {delay_seconds} seconds"
            }

        except subprocess.TimeoutExpired:
            logger.error("Restart command timed out")
            return {"success": False, "message": "Restart command timed out"}
        except PermissionError:
            logger.error("Permission denied for restart")
            return {"success": False, "message": "Insufficient permissions"}
        except FileNotFoundError:
            logger.error("Restart command not found")
            return {"success": False, "message": "Restart command not available"}
        except Exception as e:
            logger.error(f"Restart error: {type(e).__name__}")
            return {"success": False, "message": "Restart failed"}

    @staticmethod
    def lock_screen() -> dict:
        """
        Lock the screen (session lock)

        Returns:
            Dict with success status and message
        """
        try:
            if OS_TYPE == "Windows":
                # Windows: rundll32.exe user32.dll,LockWorkStation
                cmd = ["rundll32.exe", "user32.dll", "LockWorkStation"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            elif OS_TYPE == "Linux":
                # Linux: gnome-screensaver-command --lock or dbus
                # Try gnome-screensaver first (GNOME)
                try:
                    cmd = ["gnome-screensaver-command", "--lock"]
                    result = subprocess.run(
                        cmd,
                        shell=False,
                        capture_output=True,
                        timeout=10,
                        check=True
                    )
                except (subprocess.CalledProcessError, FileNotFoundError):
                    # Fallback: dbus for GNOME, KDE, etc.
                    cmd = [
                        "dbus-send",
                        "--session",
                        "--dest=org.gnome.ScreenSaver",
                        "/org/gnome/ScreenSaver",
                        "org.gnome.ScreenSaver.Lock"
                    ]
                    result = subprocess.run(
                        cmd,
                        shell=False,
                        capture_output=True,
                        timeout=10,
                        check=False
                    )
                    # If dbus fails, try loginctl (systemd)
                    if result.returncode != 0:
                        cmd = ["loginctl", "lock-session"]
                        result = subprocess.run(
                            cmd,
                            shell=False,
                            capture_output=True,
                            timeout=10,
                            check=False
                        )
            elif OS_TYPE == "Darwin":  # macOS
                # macOS: pmset displaysleepnow
                cmd = ["pmset", "displaysleepnow"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            else:
                return {"success": False, "message": f"Unsupported OS: {OS_TYPE}"}

            return {"success": True, "message": "Screen locked successfully"}

        except subprocess.TimeoutExpired:
            logger.error("Lock screen command timed out")
            return {"success": False, "message": "Lock screen command timed out"}
        except PermissionError:
            logger.error("Permission denied for lock screen")
            return {"success": False, "message": "Insufficient permissions"}
        except FileNotFoundError:
            logger.error("Lock screen command not found")
            return {"success": False, "message": "Lock screen command not available"}
        except Exception as e:
            logger.error(f"Lock screen error: {type(e).__name__}")
            return {"success": False, "message": "Lock screen failed"}


# ============================================================
# SCHEDULED TASK MANAGER CLASS
# ============================================================

class ScheduledTaskManager:
    """
    Manage scheduled power tasks
    Supports scheduling shutdown, restart, hibernate operations
    Uses in-memory storage with optional persistent file storage
    """

    def __init__(self, storage_file: str = "scheduled_tasks.json"):
        """
        Initialize scheduled task manager

        Args:
            storage_file: Optional file path for persistent storage
        """
        self.storage_file = storage_file
        self.tasks: Dict[str, ScheduledTask] = {}
        self._scheduler_task = None
        self._running = False
        self._load_tasks()
        logger.info("ScheduledTaskManager initialized")

    def _load_tasks(self):
        """Load tasks from persistent storage if available"""
        try:
            if os.path.exists(self.storage_file):
                import json
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = ScheduledTask(**task_data)
                        self.tasks[task.id] = task
                        # Clean up expired/disabled tasks on load
                        if not task.enabled:
                            self.tasks.pop(task.id, None)
                logger.info(f"Loaded {len(self.tasks)} scheduled tasks from storage")
        except Exception as e:
            logger.error(f"Error loading scheduled tasks: {type(e).__name__}")

    def _save_tasks(self):
        """Save tasks to persistent storage"""
        try:
            import json
            with open(self.storage_file, 'w') as f:
                tasks_data = [task.dict() for task in self.tasks.values()]
                json.dump(tasks_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving scheduled tasks: {type(e).__name__}")

    def create_task(self, name: str, action: str, scheduled_time: str) -> ScheduledTask:
        """
        Create a new scheduled task

        Args:
            name: Task name
            action: Power action (shutdown, hibernate, restart)
            scheduled_time: ISO format datetime string

        Returns:
            Created ScheduledTask object
        """
        import uuid
        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            id=task_id,
            name=name,
            action=action,
            scheduled_time=scheduled_time,
            enabled=True,
            created_at=datetime.now().isoformat()
        )
        self.tasks[task_id] = task
        self._save_tasks()
        logger.info(f"Created scheduled task: {name} ({action}) at {scheduled_time}")
        return task

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """
        Get a task by ID

        Args:
            task_id: Task ID

        Returns:
            ScheduledTask object or None
        """
        return self.tasks.get(task_id)

    def list_tasks(self) -> List[ScheduledTask]:
        """
        List all tasks

        Returns:
            List of ScheduledTask objects
        """
        return list(self.tasks.values())

    def update_task(self, task_id: str, **kwargs) -> Optional[ScheduledTask]:
        """
        Update a task

        Args:
            task_id: Task ID
            **kwargs: Fields to update

        Returns:
            Updated ScheduledTask or None if not found
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        for key, value in kwargs.items():
            if hasattr(task, key) and value is not None:
                setattr(task, key, value)

        self._save_tasks()
        logger.info(f"Updated scheduled task: {task_id}")
        return task

    def delete_task(self, task_id: str) -> bool:
        """
        Delete a task

        Args:
            task_id: Task ID

        Returns:
            True if deleted, False if not found
        """
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save_tasks()
            logger.info(f"Deleted scheduled task: {task_id}")
            return True
        return False

    def toggle_task(self, task_id: str) -> Optional[ScheduledTask]:
        """
        Toggle task enabled state

        Args:
            task_id: Task ID

        Returns:
            Updated ScheduledTask or None if not found
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        task.enabled = not task.enabled
        self._save_tasks()
        logger.info(f"Toggled scheduled task {task_id}: enabled={task.enabled}")
        return task

    async def start_scheduler(self):
        """Start the background task scheduler"""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())
        logger.info("Scheduled task manager started")

    async def stop_scheduler(self):
        """Stop the background task scheduler"""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass
        logger.info("Scheduled task manager stopped")

    async def _scheduler_loop(self):
        """Background loop that checks and executes scheduled tasks"""
        while self._running:
            try:
                now = datetime.now()
                for task_id, task in list(self.tasks.items()):
                    if not task.enabled:
                        continue

                    try:
                        scheduled_dt = datetime.fromisoformat(task.scheduled_time.replace('Z', '+00:00'))

                        # Execute task if time has arrived
                        if scheduled_dt <= now:
                            logger.info(f"Executing scheduled task: {task.name} ({task.action})")
                            await self._execute_task(task)

                            # Delete executed one-time tasks
                            self.delete_task(task_id)

                    except Exception as e:
                        logger.error(f"Error processing task {task_id}: {type(e).__name__}")

                # Check every second
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler loop error: {type(e).__name__}")
                await asyncio.sleep(5)

    async def _execute_task(self, task: ScheduledTask):
        """
        Execute a scheduled task

        Args:
            task: ScheduledTask to execute
        """
        try:
            if task.action == "shutdown":
                result = PowerManager.shutdown(0)
            elif task.action == "restart":
                result = PowerManager.restart(0)
            elif task.action == "hibernate":
                result = PowerManager.hibernate()
            else:
                logger.error(f"Unknown action: {task.action}")
                return

            if result.get("success"):
                logger.info(f"Task executed successfully: {task.name}")
            else:
                logger.error(f"Task execution failed: {task.name} - {result.get('message')}")

        except Exception as e:
            logger.error(f"Error executing task {task.name}: {type(e).__name__}")


# ============================================================
# THRESHOLD NOTIFICATION MANAGER CLASS
# ============================================================

class ThresholdNotificationManager:
    """
    Manage threshold-based notifications
    Monitors system metrics and alerts when thresholds are exceeded
    Stores alert history and manages notification delivery
    """

    def __init__(self, storage_file: str = "threshold_alerts.json"):
        """
        Initialize threshold notification manager

        Args:
            storage_file: Optional file path for alert history storage
        """
        self.storage_file = storage_file
        self.config_file = "threshold_config.json"  # Config persistence file
        self.config = ThresholdConfig()
        self.alerts: List[ThresholdAlert] = []
        self._monitor_task = None
        self._running = False
        self._last_alert_time = {}  # Track last alert time to prevent spam
        self._alert_cooldown = 300  # 5 minutes cooldown between alerts for same metric
        self._load_config()  # Load config from disk
        self._load_alerts()
        logger.info("ThresholdNotificationManager initialized")

    def _load_config(self):
        """Load threshold configuration from persistent storage if available"""
        try:
            if os.path.exists(self.config_file):
                import json
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    self.config = ThresholdConfig(**config_data)
                logger.info(f"Loaded threshold config from disk: {self.config.dict()}")
            else:
                logger.info("No saved config found, using defaults")
        except Exception as e:
            logger.error(f"Error loading config from disk: {type(e).__name__}: {e}")
            logger.info("Using default threshold configuration")

    def _save_config(self):
        """Save threshold configuration to persistent storage"""
        try:
            import json
            with open(self.config_file, 'w') as f:
                json.dump(self.config.dict(), f, indent=2)
            logger.info(f"Saved threshold config to disk: {self.config.dict()}")
        except Exception as e:
            logger.error(f"Error saving config to disk: {type(e).__name__}: {e}")

    def _load_alerts(self):
        """Load alert history from persistent storage if available"""
        try:
            if os.path.exists(self.storage_file):
                import json
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    for alert_data in data:
                        alert = ThresholdAlert(**alert_data)
                        self.alerts.append(alert)
                logger.info(f"Loaded {len(self.alerts)} alerts from storage")
        except Exception as e:
            logger.error(f"Error loading alerts: {type(e).__name__}")

    def _save_alerts(self):
        """Save alerts to persistent storage"""
        try:
            import json
            # Keep only last 100 alerts
            alerts_to_save = self.alerts[-100:] if len(self.alerts) > 100 else self.alerts
            with open(self.storage_file, 'w') as f:
                alerts_data = [alert.dict() for alert in alerts_to_save]
                json.dump(alerts_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving alerts: {type(e).__name__}")

    def get_config(self) -> ThresholdConfig:
        """Get current threshold configuration"""
        return self.config

    def update_config(self, **kwargs) -> ThresholdConfig:
        """
        Update threshold configuration

        Args:
            **kwargs: Fields to update (cpu_threshold, memory_threshold, disk_threshold, enabled)

        Returns:
            Updated ThresholdConfig
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key) and value is not None:
                setattr(self.config, key, value)
        logger.info(f"Threshold config updated: {kwargs}")

        # Persist to disk
        self._save_config()

        return self.config

    def get_alerts(self, limit: int = 50, unacknowledged_only: bool = False) -> List[ThresholdAlert]:
        """
        Get alert history

        Args:
            limit: Maximum number of alerts to return
            unacknowledged_only: If True, only return unacknowledged alerts

        Returns:
            List of ThresholdAlert objects
        """
        alerts = self.alerts
        if unacknowledged_only:
            alerts = [a for a in alerts if not a.acknowledged]
        # Return most recent first
        return sorted(alerts, key=lambda x: x.timestamp, reverse=True)[:limit]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """
        Acknowledge an alert

        Args:
            alert_id: Alert ID to acknowledge

        Returns:
            True if acknowledged, False if not found
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                self._save_alerts()
                return True
        return False

    def acknowledge_all_alerts(self) -> int:
        """
        Acknowledge all alerts

        Returns:
            Number of alerts acknowledged
        """
        count = 0
        for alert in self.alerts:
            if not alert.acknowledged:
                alert.acknowledged = True
                count += 1
        if count > 0:
            self._save_alerts()
        return count

    def _check_threshold(self, metric_type: str, current_value: float, threshold: int) -> Optional[ThresholdAlert]:
        """
        Check if threshold is exceeded and create alert if needed

        Args:
            metric_type: Type of metric (cpu, memory, disk)
            current_value: Current metric value
            threshold: Threshold value

        Returns:
            ThresholdAlert if threshold exceeded and cooldown passed, None otherwise
        """
        import uuid

        # Check if threshold exceeded
        if current_value < threshold:
            return None

        # Check cooldown to prevent alert spam
        now = time.time()
        last_alert = self._last_alert_time.get(metric_type, 0)
        if now - last_alert < self._alert_cooldown:
            return None

        # Create alert
        alert = ThresholdAlert(
            id=str(uuid.uuid4()),
            metric_type=metric_type,
            threshold=threshold,
            current_value=current_value,
            timestamp=datetime.now().isoformat(),
            acknowledged=False
        )

        self.alerts.append(alert)
        self._last_alert_time[metric_type] = now
        self._save_alerts()

        logger.warning(f"Threshold alert: {metric_type.upper()} at {current_value:.1f}% exceeds threshold {threshold}%")
        return alert

    def check_thresholds(self) -> List[ThresholdAlert]:
        """
        Check all thresholds against current system stats

        Returns:
            List of new alerts triggered
        """
        if not self.config.enabled:
            return []

        new_alerts = []

        try:
            # Get current stats
            stats = SystemMonitor.get_all_stats()

            # Check CPU threshold
            if self.config.cpu_threshold > 0:
                cpu_usage = stats.get('cpu', {}).get('usage_percent', 0)
                alert = self._check_threshold('cpu', cpu_usage, self.config.cpu_threshold)
                if alert:
                    new_alerts.append(alert)

            # Check Memory threshold
            if self.config.memory_threshold > 0:
                memory_usage = stats.get('memory', {}).get('usage_percent', 0)
                alert = self._check_threshold('memory', memory_usage, self.config.memory_threshold)
                if alert:
                    new_alerts.append(alert)

            # Check Disk threshold
            if self.config.disk_threshold > 0:
                disk_usage = stats.get('disk', {}).get('usage_percent', 0)
                alert = self._check_threshold('disk', disk_usage, self.config.disk_threshold)
                if alert:
                    new_alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking thresholds: {type(e).__name__}")

        return new_alerts

    async def start_monitor(self):
        """Start the background threshold monitor"""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Threshold notification manager started")

    async def stop_monitor(self):
        """Stop the background threshold monitor"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Threshold notification manager stopped")

    async def _monitor_loop(self):
        """Background loop that periodically checks thresholds"""
        while self._running:
            try:
                # Check thresholds
                new_alerts = self.check_thresholds()

                # Send WebSocket notifications for new alerts
                for alert in new_alerts:
                    await websocket_manager.broadcast({
                        'type': 'threshold_alert',
                        'data': alert.dict()
                    })

                # Check every 30 seconds
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {type(e).__name__}")
                await asyncio.sleep(60)


# ============================================================
# DOCKER MANAGER CLASS
# ============================================================

class DockerManager:
    """
    Manage Docker containers
    Supports listing, starting, stopping, restarting containers
    Gracefully handles when Docker is not installed/running
    """

    def __init__(self):
        """Initialize Docker client"""
        self.client = None
        self.available = False
        self._init_docker()

    def _init_docker(self):
        """Initialize Docker connection"""
        try:
            self.client = from_env()
            self.client.ping()
            self.available = True
            logger.info("Docker connection established")
        except DockerException as e:
            logger.warning(f"Docker not available: {type(e).__name__}")
            self.available = False
        except Exception as e:
            logger.error(f"Docker initialization error: {type(e).__name__}")
            self.available = False

    def list_containers(self, all: bool = True) -> list:
        """
        List all Docker containers

        Args:
            all: If True, include stopped containers

        Returns:
            List of container information dicts
        """
        if not self.available:
            return []

        try:
            containers = self.client.containers.list(all=all)
            result = []
            for container in containers:
                try:
                    result.append({
                        "id": container.short_id,
                        "name": SecurityManager.sanitize_input(container.name, max_length=256),
                        "image": SecurityManager.sanitize_input(
                            container.image.tags[0] if container.image.tags else container.image.id[:12],
                            max_length=256
                        ),
                        "status": SecurityManager.sanitize_input(container.status, max_length=64),
                        "state": "running" if container.status == "running" else "stopped"
                    })
                except Exception as e:
                    logger.warning(f"Error reading container info: {type(e).__name__}")
                    continue
            return result
        except Exception as e:
            logger.error(f"Error listing containers: {type(e).__name__}")
            return []

    def start_container(self, container_id: str) -> dict:
        """
        Start a Docker container

        Args:
            container_id: Container ID or name

        Returns:
            Dict with success status and message
        """
        if not self.available:
            return {"success": False, "message": "Docker is not available"}

        # Validate container ID
        if not SecurityManager.validate_container_id(container_id):
            logger.warning(f"Invalid container ID format: {container_id[:50]}")
            return {"success": False, "message": "Invalid container ID format"}

        try:
            container = self.client.containers.get(container_id)
            container.start(timeout=30)
            container_name = SecurityManager.sanitize_input(container.name, max_length=256)
            return {"success": True, "message": f"Container '{container_name}' started"}
        except Exception as e:
            logger.error(f"Error starting container: {type(e).__name__}")
            return {"success": False, "message": "Failed to start container"}

    def stop_container(self, container_id: str) -> dict:
        """
        Stop a Docker container

        Args:
            container_id: Container ID or name

        Returns:
            Dict with success status and message
        """
        if not self.available:
            return {"success": False, "message": "Docker is not available"}

        # Validate container ID
        if not SecurityManager.validate_container_id(container_id):
            logger.warning(f"Invalid container ID format: {container_id[:50]}")
            return {"success": False, "message": "Invalid container ID format"}

        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=30)
            container_name = SecurityManager.sanitize_input(container.name, max_length=256)
            return {"success": True, "message": f"Container '{container_name}' stopped"}
        except Exception as e:
            logger.error(f"Error stopping container: {type(e).__name__}")
            return {"success": False, "message": "Failed to stop container"}

    def restart_container(self, container_id: str) -> dict:
        """
        Restart a Docker container

        Args:
            container_id: Container ID or name

        Returns:
            Dict with success status and message
        """
        if not self.available:
            return {"success": False, "message": "Docker is not available"}

        # Validate container ID
        if not SecurityManager.validate_container_id(container_id):
            logger.warning(f"Invalid container ID format: {container_id[:50]}")
            return {"success": False, "message": "Invalid container ID format"}

        try:
            container = self.client.containers.get(container_id)
            container.restart(timeout=30)
            container_name = SecurityManager.sanitize_input(container.name, max_length=256)
            return {"success": True, "message": f"Container '{container_name}' restarted"}
        except Exception as e:
            logger.error(f"Error restarting container: {type(e).__name__}")
            return {"success": False, "message": "Failed to restart container"}

    def get_container_logs(self, container_id: str, tail: int = 100) -> dict:
        """
        Get logs from a Docker container

        Args:
            container_id: Container ID or name
            tail: Number of lines from the end of logs (max 10000)

        Returns:
            Dict with success status and logs
        """
        if not self.available:
            return {"success": False, "message": "Docker is not available"}

        # Validate container ID
        if not SecurityManager.validate_container_id(container_id):
            logger.warning(f"Invalid container ID format: {container_id[:50]}")
            return {"success": False, "message": "Invalid container ID format"}

        # Validate and limit tail parameter
        try:
            tail = max(1, min(10000, int(tail)))
        except (ValueError, TypeError):
            tail = 100

        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail).decode('utf-8', errors='replace')

            # Limit log size to prevent memory issues
            max_log_size = 10 * 1024 * 1024  # 10MB
            if len(logs) > max_log_size:
                logs = logs[-max_log_size:]
                logs = "... (truncated) ...\n" + logs

            return {"success": True, "logs": logs}
        except Exception as e:
            logger.error(f"Error getting logs: {type(e).__name__}")
            return {"success": False, "message": "Failed to get logs"}

    def get_status(self) -> dict:
        """
        Check if Docker is available

        Returns:
            Dict with Docker availability status
        """
        if self.available:
            return {"available": True, "message": "Docker is available"}
        else:
            return {"available": False, "message": "Docker is not installed or not running"}


# Initialize Docker Manager singleton
docker_manager = DockerManager()

# Initialize Scheduled Task Manager singleton
scheduled_task_manager = ScheduledTaskManager()

# Initialize Threshold Notification Manager singleton
threshold_notification_manager = ThresholdNotificationManager()
# ============================================================
# PROCESS MANAGER CLASS
# ============================================================

class ProcessManager:
    """
    Manage system processes
    Supports listing processes sorted by resource usage
    and killing processes by PID
    Includes protection for critical system processes
    """

    # List of critical PIDs that should not be killed
    PROTECTED_PIDS = {
        0,    # Idle process
        1,    # Init/systemd
        2,    # kthreadd
    }

    @staticmethod
    def list_processes(limit: int = 50, sort_by: str = "cpu") -> list:
        """
        List top resource-consuming processes

        Args:
            limit: Maximum number of processes to return (1-100)
            sort_by: Sort by 'cpu' or 'memory'

        Returns:
            List of process information dicts
        """
        try:
            # Validate and limit parameters
            limit = max(1, min(100, int(limit)))
            sort_by = sort_by.lower()
            if sort_by not in ["cpu", "memory"]:
                sort_by = "cpu"

            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    # Use oneshot() for more efficient and accurate readings
                    with proc.oneshot():
                        proc_info = {
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'username': proc.info['username'],
                            # Use interval=0.1 for accurate CPU reading
                            'cpu_percent': proc.cpu_percent(interval=0.1),
                            # Get accurate memory percentage
                            'memory_percent': proc.memory_percent()
                        }

                        # Sanitize process data
                        if proc_info.get('name'):
                            proc_info['name'] = SecurityManager.sanitize_input(
                                str(proc_info['name']), max_length=128
                            )
                        if proc_info.get('username'):
                            proc_info['username'] = SecurityManager.sanitize_input(
                                str(proc_info['username']), max_length=128
                            )

                        processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                except Exception:
                    continue

            # Sort by specified metric (descending - highest first)
            if sort_by == "cpu":
                processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)

            # Return top N processes
            return processes[:limit]

        except Exception as e:
            logger.error(f"Error listing processes: {type(e).__name__}")
            return []

    @staticmethod
    def kill_process(pid: int) -> dict:
        """
        Kill a process by PID

        Args:
            pid: Process ID to kill

        Returns:
            Dict with success status and message
        """
        # Validate PID
        if not SecurityManager.validate_pid(pid):
            logger.warning(f"Invalid PID: {pid}")
            return {"success": False, "message": "Invalid PID"}

        # Check if PID is protected
        if pid in ProcessManager.PROTECTED_PIDS:
            logger.warning(f"Attempt to kill protected PID: {pid}")
            return {"success": False, "message": "Cannot kill critical system process"}

        try:
            proc = psutil.Process(pid)
            name = SecurityManager.sanitize_input(proc.name(), max_length=128)

            # Additional protection: don't kill kernel processes
            if OS_TYPE == "Linux":
                try:
                    cmdline = proc.cmdline()
                    if cmdline and any('kernel' in str(c).lower() for c in cmdline):
                        logger.warning(f"Attempt to kill kernel process: {pid}")
                        return {"success": False, "message": "Cannot kill kernel process"}
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

            proc.kill()
            logger.info(f"Process killed: {name} (PID: {pid})")
            return {"success": True, "message": f"Process '{name}' (PID: {pid}) killed"}

        except psutil.NoSuchProcess:
            return {"success": False, "message": f"Process with PID {pid} not found"}
        except psutil.AccessDenied:
            logger.warning(f"Access denied to PID: {pid}")
            return {"success": False, "message": f"Access denied to process {pid}"}
        except Exception as e:
            logger.error(f"Error killing process {pid}: {type(e).__name__}")
            return {"success": False, "message": "Failed to kill process"}

    @staticmethod
    def get_process_details(pid: int) -> dict:
        """
        Get detailed information about a process

        Args:
            pid: Process ID

        Returns:
            Dict with process details
        """
        # Validate PID
        if not SecurityManager.validate_pid(pid):
            return {"error": "Invalid PID"}

        try:
            proc = psutil.Process(pid)

            details = {
                "pid": proc.pid,
                "name": SecurityManager.sanitize_input(proc.name(), max_length=128),
                "status": SecurityManager.sanitize_input(proc.status(), max_length=64),
                "cpu_percent": round(proc.cpu_percent(), 2),
                "memory_percent": round(proc.memory_percent(), 2),
                "create_time": proc.create_time()
            }

            # Add optional fields with error handling
            try:
                details["username"] = SecurityManager.sanitize_input(
                    str(proc.username()), max_length=128
                )
            except (psutil.AccessDenied, Exception):
                details["username"] = "N/A"

            try:
                details["exe"] = SecurityManager.sanitize_input(
                    str(proc.exe()), max_length=512
                )
            except (psutil.AccessDenied, psutil.NoSuchProcess, Exception):
                details["exe"] = "N/A"

            try:
                cmdline = proc.cmdline()
                details["cmdline"] = [
                    SecurityManager.sanitize_input(str(c), max_length=512) for c in cmdline
                ][:32]  # Limit to 32 args
            except (psutil.AccessDenied, psutil.NoSuchProcess, Exception):
                details["cmdline"] = []

            return details

        except psutil.NoSuchProcess:
            return {"error": f"Process with PID {pid} not found"}
        except Exception as e:
            logger.error(f"Error getting process details: {type(e).__name__}")
            return {"error": "Failed to get process details"}


# ============================================================
# SCREENSHOT SERVICE CLASS
# ============================================================

class ScreenshotService:
    """
    Capture screen screenshots using pyautogui
    Returns base64-encoded images
    """

    # Maximum screenshot size (10MB) to prevent memory issues
    MAX_SCREENSHOT_SIZE = 10 * 1024 * 1024

    @staticmethod
    def capture_screen(quality: int = 75) -> dict:
        """
        Capture the screen and return as base64 image

        Args:
            quality: JPEG quality (1-100, higher = better)

        Returns:
            Dict with success status and base64 image data
        """
        # Check if pyautogui is available
        if not PYAUTOGUI_AVAILABLE:
            return {
                "success": False,
                "message": "Screenshot feature not available (headless system or pyautogui not installed)"
            }

        try:
            # Validate quality range
            quality = max(1, min(100, int(quality)))

            # Check if display is available (not headless)
            if OS_TYPE != "Windows" and os.environ.get('DISPLAY') is None:
                logger.warning("Screenshot attempted on headless system")
                return {
                    "success": False,
                    "message": "No display available (headless system)"
                }

            # Take screenshot
            screenshot = pyautogui.screenshot()

            # Convert to bytes with specified quality
            from io import BytesIO
            buffer = BytesIO()
            screenshot.save(buffer, format="JPEG", quality=quality)
            image_bytes = buffer.getvalue()

            # Check size limits
            if len(image_bytes) > ScreenshotService.MAX_SCREENSHOT_SIZE:
                logger.warning(f"Screenshot too large: {len(image_bytes)} bytes")
                # Retry with lower quality
                for retry_quality in [50, 30, 10]:
                    buffer = BytesIO()
                    screenshot.save(buffer, format="JPEG", quality=retry_quality)
                    image_bytes = buffer.getvalue()
                    if len(image_bytes) <= ScreenshotService.MAX_SCREENSHOT_SIZE:
                        break

            # Encode to base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')

            return {
                "success": True,
                "image": image_b64,
                "format": "jpeg",
                "quality": quality,
                "size": len(image_bytes)
            }

        except Exception as e:
            logger.error(f"Screenshot error: {type(e).__name__}")
            return {
                "success": False,
                "message": "Screenshot failed"
            }


# ============================================================
# TOKEN DEPENDENCY FOR PROTECTED ROUTES
# ============================================================

async def get_token_from_header(request: Request) -> str:
    """
    Extract JWT token from Authorization header

    Args:
        request: FastAPI request object

    Returns:
        Token string

    Raises:
        HTTPException: If token is missing or invalid format
    """
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing"
        )

    # Validate Bearer format
    if not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    token = auth_header.split(" ", 1)[1].strip()

    # Validate token is not empty
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is empty"
        )

    # Validate token length (sanity check)
    if len(token) > 4096:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token too long"
        )

    return token


async def get_current_user(token: str = Depends(get_token_from_header)) -> dict:
    """
    Validate JWT token and return user payload

    Args:
        token: JWT token from header

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid
    """
    payload = SecurityManager.verify_token(token)
    return payload


# ============================================================
# MIDDLEWARE FOR ENCRYPTED REQUESTS
# ============================================================

@app.middleware("http")
async def encryption_middleware(request: Request, call_next):
    """
    Middleware to handle encryption/decryption of requests and responses

    For encrypted requests (POST/PUT/PATCH):
    1. Decrypt the request payload
    2. Forward to the route handler
    3. Encrypt the response

    For non-encrypted requests (GET, login, test endpoints):
    1. Pass through to route handler
    """
    # Skip encryption middleware for login and test endpoints
    # These endpoints use plain JSON, not encrypted payloads
    if request.url.path in ["/api/auth/login", "/api/test/echo", "/api/test/connection"]:
        return await call_next(request)

    # Track if request was encrypted
    was_encrypted = False

    # Check if request is encrypted (has encrypted data)
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            # Read request body
            body = await request.body()

            # Only process if body exists and looks like it might be encrypted
            # Encrypted payloads have "data" and "timestamp" fields
            if body and len(body) < 10 * 1024 * 1024:  # Max 10MB
                import json
                try:
                    data = json.loads(body)

                    # Check if this is an encrypted payload (has both data and timestamp)
                    if isinstance(data, dict) and "data" in data and "timestamp" in data:
                        # Validate timestamp first (replay attack prevention)
                        if not SecurityManager.validate_timestamp(data["timestamp"]):
                            logger.warning(f"Invalid timestamp from {get_remote_address(request)}")
                            return JSONResponse(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                content={"detail": "Invalid timestamp"}
                            )

                        # Decrypt the payload (CRITICAL: Catch decryption failures)
                        try:
                            decrypted_data = SecurityManager.decrypt_data(data["data"])
                        except HTTPException as http_ex:
                            # If decrypt_data raised HTTPException, pass it through
                            # This includes 401 for invalid key, 400 for bad format
                            logger.warning(f"Decryption blocked: {http_ex.detail}")
                            return JSONResponse(
                                status_code=http_ex.status_code,
                                content={"detail": http_ex.detail}
                            )

                        # Store decrypted data in request state for route handlers
                        request.state.decrypted_data = decrypted_data
                        was_encrypted = True
                except json.JSONDecodeError:
                    # Not valid JSON, let route handler deal with it
                    pass

        except HTTPException as http_ex:
            # Catch HTTPException from decrypt_data and return immediately
            logger.warning(f"Encryption middleware HTTP exception: {http_ex.detail}")
            return JSONResponse(
                status_code=http_ex.status_code,
                content={"detail": http_ex.detail}
            )
        except Exception as e:
            logger.error(f"Encryption middleware error: {type(e).__name__}: {e}")
            # Don't return error here - let route handler deal with it
            pass

    # Process the request
    response = await call_next(request)

    # Encrypt response if request was encrypted
    if was_encrypted:
        try:
            # Get response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Limit response size
            if len(response_body) > 50 * 1024 * 1024:  # 50MB limit
                logger.error(f"Response too large to encrypt: {len(response_body)} bytes")
                return JSONResponse(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    content={"detail": "Response too large"}
                )

            # Parse response body
            import json
            response_data = json.loads(response_body)

            # Encrypt response
            encrypted_response = SecurityManager.encrypt_data(response_data)

            # Return encrypted response
            return JSONResponse(
                content={"data": encrypted_response},
                status_code=response.status_code
            )

        except Exception as e:
            logger.error(f"Response encryption error: {type(e).__name__}: {e}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Response encryption failed"}
            )

    return response


# ============================================================
# API ROUTES: AUTHENTICATION
# ============================================================

@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
# Temporarily disabled rate limiter for iOS debugging
# @limiter.limit("10 per minute")
async def login(request: LoginRequest, http_request: Request):
    client_ip = get_remote_address(http_request)
    logger.info(f"[LOGIN ATTEMPT] Received login request from {client_ip}")

    # Check if account is locked
    """
    Authenticate with app password and receive JWT token

    Rate limited: 10 attempts per minute per IP (TEMPORARILY DISABLED)

    Args:
        request: Login request with password
        http_request: FastAPI request object

    Returns:
        JWT access token

    Raises:
        HTTPException: If password is invalid or account locked
    """
    client_ip = get_remote_address(http_request)

    # Check if account is locked
    if not check_login_attempts(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Account locked. Try again later."
        )

    # Verify password
    if SecurityManager.verify_password(request.password, app_password_hash):
        # Successful login - clear attempts
        record_login_attempt(client_ip, success=True)

        # Create token
        access_token = SecurityManager.create_access_token(
            data={"sub": "nexcontrol_user"}
        )

        logger.info(f"Successful login from {client_ip}")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    else:
        # Failed login - record attempt
        record_login_attempt(client_ip, success=False)

        logger.warning(f"Failed login attempt from {client_ip}")

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )


@app.get("/api/auth/verify", tags=["Authentication"])
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verify if a JWT token is valid

    Args:
        current_user: Current user from JWT token

    Returns:
        Token validation status
    """
    return {"valid": True, "user": current_user.get("sub")}


@app.post("/api/auth/verify-key", tags=["Authentication"])
async def verify_encryption_key(request: Request):
    """
    Verify if the client's AES encryption key matches the server's key.

    This endpoint is used by the Settings page to validate that the
    encryption key is correctly configured before allowing sensitive operations.

    Request Body:
    {
        "data": "<base64-encoded encrypted test string>"
    }

    Returns:
        {"status": "valid", "message": "Key matched"} (200) if key matches
        {"status": "invalid", "message": "Key mismatch"} (401) if key doesn't match
        {"status": "error", "message": "..."} (400) if request format is invalid
    """
    try:
        # Read request body
        body = await request.body()
        if not body:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Request body is required"
            )

        import json
        data = json.loads(body)

        # Check if this is an encrypted payload
        if not isinstance(data, dict) or "data" not in data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid request format. Expected {\"data\": \"<encrypted_string>\"}"
            )

        # Get client IP for logging
        client_ip = get_remote_address(request)

        # Try to decrypt using the server's AES key
        try:
            decrypted_data = SecurityManager.decrypt_data(data["data"])

            logger.info(f"[Key Verification] SUCCESS - Key matched from {client_ip}")

            return {
                "success": True,
                "status": "valid",
                "message": "Encryption key matched successfully"
            }

        except HTTPException as http_ex:
            # decrypt_data raised HTTPException (likely 401 for wrong key)
            logger.warning(f"[Key Verification] FAILED - Key mismatch from {client_ip}: {http_ex.detail}")

            return JSONResponse(
                status_code=http_ex.status_code,
                content={
                    "success": False,
                    "status": "invalid",
                    "message": "Encryption key does not match"
                }
            )

    except json.JSONDecodeError:
        logger.warning("[Key Verification] FAILED - Invalid JSON from request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON format"
        )
    except Exception as e:
        logger.error(f"[Key Verification] ERROR - Unexpected error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Verification failed"
        )


# ============================================================
# API ROUTES: SYSTEM MONITORING
# ============================================================

# Public endpoints (no auth required) - for testing and monitoring
@app.get("/api/stats/cpu", tags=["System Stats (Public)"])
async def get_cpu_stats_public():
    """Get CPU usage statistics (no auth required)"""
    return SystemMonitor.get_cpu_usage()


@app.get("/api/stats/memory", tags=["System Stats (Public)"])
async def get_memory_stats_public():
    """Get memory usage statistics (no auth required)"""
    return SystemMonitor.get_memory_usage()


@app.get("/api/stats/disk", tags=["System Stats (Public)"])
async def get_disk_stats_public():
    """Get disk usage statistics (no auth required)"""
    return SystemMonitor.get_disk_usage()


@app.get("/api/stats/gpu", tags=["System Stats (Public)"])
async def get_gpu_stats_public():
    """Get GPU usage and temperature statistics (no auth required)"""
    return {
        "usage": SystemMonitor.get_gpu_usage(),
        "temperature": SystemMonitor.get_gpu_temperature()
    }


@app.get("/api/stats/network", tags=["System Stats (Public)"])
async def get_network_stats_public():
    """Get network I/O statistics (no auth required)"""
    return SystemMonitor.get_network_stats()


@app.get("/api/stats/all", tags=["System Stats (Public)"])
async def get_all_stats_public():
    """Get all system statistics in one call (no auth required)"""
    return SystemMonitor.get_all_stats()


@app.get("/api/stats/disks", tags=["System Stats (Public)"])
async def get_all_disks_public():
    """Get all attached storage devices including USB drives, partitions (no auth required)"""
    return SystemMonitor.get_all_disks()


# Protected endpoints (auth required) - for frontend app
@app.get("/api/v1/stats/cpu", tags=["System Stats (Protected)"])
async def get_cpu_stats(current_user: dict = Depends(get_current_user)):
    """Get CPU usage statistics (authentication required)"""
    return SystemMonitor.get_cpu_usage()


@app.get("/api/v1/stats/memory", tags=["System Stats (Protected)"])
async def get_memory_stats(current_user: dict = Depends(get_current_user)):
    """Get memory usage statistics (authentication required)"""
    return SystemMonitor.get_memory_usage()


@app.get("/api/v1/stats/disk", tags=["System Stats (Protected)"])
async def get_disk_stats(current_user: dict = Depends(get_current_user)):
    """Get disk usage statistics (authentication required)"""
    return SystemMonitor.get_disk_usage()


@app.get("/api/v1/stats/gpu", tags=["System Stats (Protected)"])
async def get_gpu_stats(current_user: dict = Depends(get_current_user)):
    """Get GPU usage and temperature statistics (authentication required)"""
    return {
        "usage": SystemMonitor.get_gpu_usage(),
        "temperature": SystemMonitor.get_gpu_temperature()
    }


@app.get("/api/v1/stats/network", tags=["System Stats (Protected)"])
async def get_network_stats(current_user: dict = Depends(get_current_user)):
    """Get network I/O statistics (authentication required)"""
    return SystemMonitor.get_network_stats()


@app.get("/api/v1/stats/all", tags=["System Stats (Protected)"])
async def get_all_stats(current_user: dict = Depends(get_current_user)):
    """Get all system statistics in one call (authentication required)"""
    return SystemMonitor.get_all_stats()


@app.get("/api/v1/stats/disks", tags=["System Stats (Protected)"])
async def get_all_disks(current_user: dict = Depends(get_current_user)):
    """Get all attached storage devices including USB drives, partitions (authentication required)"""
    return SystemMonitor.get_all_disks()


# ============================================================
# API ROUTES: POWER MANAGEMENT
# ============================================================

@app.post("/api/power/shutdown", tags=["Power Management"])
async def shutdown(
    delay_seconds: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Shutdown the system

    Args:
        delay_seconds: Delay before shutdown (0-86400 seconds, default: 0)
        current_user: Authenticated user

    Returns:
        Shutdown status
    """
    # Validate delay
    delay_seconds = max(0, min(86400, int(delay_seconds)))
    return PowerManager.shutdown(delay_seconds)


@app.post("/api/power/hibernate", tags=["Power Management"])
async def hibernate(current_user: dict = Depends(get_current_user)):
    """
    Hibernate the system

    Args:
        current_user: Authenticated user

    Returns:
        Hibernate status
    """
    return PowerManager.hibernate()


@app.post("/api/power/lock", tags=["Power Management"])
async def lock_screen(current_user: dict = Depends(get_current_user)):
    """
    Lock the screen

    Args:
        current_user: Authenticated user

    Returns:
        Lock screen status
    """
    return PowerManager.lock_screen()


@app.post("/api/power/restart", tags=["Power Management"])
async def restart(
    delay_seconds: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Restart the system

    Args:
        delay_seconds: Delay before restart (0-86400 seconds, default: 0)
        current_user: Authenticated user

    Returns:
        Restart status
    """
    # Validate delay
    delay_seconds = max(0, min(86400, int(delay_seconds)))
    return PowerManager.restart(delay_seconds)


# ============================================================
# API ROUTES: SCHEDULED TASKS
# ============================================================

@app.post("/api/schedule", tags=["Scheduled Tasks"])
async def create_scheduled_task(
    request: CreateScheduledTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new scheduled power task

    Args:
        request: Task creation request with name, action, scheduled_time
        current_user: Authenticated user

    Returns:
        Created task details
    """
    task = scheduled_task_manager.create_task(
        name=request.name,
        action=request.action,
        scheduled_time=request.scheduled_time
    )
    return {
        "success": True,
        "message": "Task created successfully",
        "data": task.dict()
    }


@app.get("/api/schedule", tags=["Scheduled Tasks"])
async def list_scheduled_tasks(current_user: dict = Depends(get_current_user)):
    """
    List all scheduled tasks

    Args:
        current_user: Authenticated user

    Returns:
        List of all scheduled tasks
    """
    tasks = scheduled_task_manager.list_tasks()
    return {
        "success": True,
        "tasks": [task.dict() for task in tasks]
    }


@app.get("/api/schedule/{task_id}", tags=["Scheduled Tasks"])
async def get_scheduled_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get a specific scheduled task by ID

    Args:
        task_id: Task ID
        current_user: Authenticated user

    Returns:
        Task details or error if not found
    """
    task = scheduled_task_manager.get_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return {
        "success": True,
        "data": task.dict()
    }


@app.put("/api/schedule/{task_id}", tags=["Scheduled Tasks"])
async def update_scheduled_task(
    task_id: str,
    request: UpdateScheduledTaskRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Update a scheduled task

    Args:
        task_id: Task ID
        request: Update request with optional fields
        current_user: Authenticated user

    Returns:
        Updated task or error if not found
    """
    # Prepare update dict
    update_data = {}
    if request.name is not None:
        update_data['name'] = request.name
    if request.action is not None:
        update_data['action'] = request.action
    if request.scheduled_time is not None:
        update_data['scheduled_time'] = request.scheduled_time

    task = scheduled_task_manager.update_task(task_id, **update_data)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return {
        "success": True,
        "message": "Task updated successfully",
        "data": task.dict()
    }


@app.put("/api/schedule/{task_id}/toggle", tags=["Scheduled Tasks"])
async def toggle_scheduled_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Toggle a scheduled task enabled/disabled

    Args:
        task_id: Task ID
        current_user: Authenticated user

    Returns:
        Updated task or error if not found
    """
    task = scheduled_task_manager.toggle_task(task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return {
        "success": True,
        "message": f"Task {'enabled' if task.enabled else 'disabled'}",
        "data": task.dict()
    }


@app.delete("/api/schedule/{task_id}", tags=["Scheduled Tasks"])
async def delete_scheduled_task(
    task_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a scheduled task

    Args:
        task_id: Task ID
        current_user: Authenticated user

    Returns:
        Success message
    """
    if not scheduled_task_manager.delete_task(task_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return {
        "success": True,
        "message": "Task deleted successfully"
    }


# ============================================================
# API ROUTES: THRESHOLD NOTIFICATIONS
# ============================================================

@app.get("/api/threshold/config", tags=["Threshold Notifications"])
async def get_threshold_config(current_user: dict = Depends(get_current_user)):
    """
    Get current threshold configuration

    Args:
        current_user: Authenticated user

    Returns:
        Current threshold configuration
    """
    config = threshold_notification_manager.get_config()
    return {
        "success": True,
        "data": config.dict()
    }


@app.put("/api/threshold/config", tags=["Threshold Notifications"])
async def update_threshold_config(
    cpu_threshold: Optional[int] = None,
    memory_threshold: Optional[int] = None,
    disk_threshold: Optional[int] = None,
    enabled: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Update threshold configuration

    Args:
        cpu_threshold: CPU usage threshold (0-100)
        memory_threshold: Memory usage threshold (0-100)
        disk_threshold: Disk usage threshold (0-100)
        enabled: Whether monitoring is enabled
        current_user: Authenticated user

    Returns:
        Updated threshold configuration
    """
    # Build update dict with only provided values
    update_data = {}
    if cpu_threshold is not None:
        update_data['cpu_threshold'] = cpu_threshold
    if memory_threshold is not None:
        update_data['memory_threshold'] = memory_threshold
    if disk_threshold is not None:
        update_data['disk_threshold'] = disk_threshold
    if enabled is not None:
        update_data['enabled'] = enabled

    config = threshold_notification_manager.update_config(**update_data)
    return {
        "success": True,
        "message": "Threshold configuration updated",
        "data": config.dict()
    }


@app.get("/api/threshold/alerts", tags=["Threshold Notifications"])
async def get_threshold_alerts(
    limit: int = 50,
    unacknowledged_only: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """
    Get threshold alert history

    Args:
        limit: Maximum number of alerts to return
        unacknowledged_only: If True, only return unacknowledged alerts
        current_user: Authenticated user

    Returns:
        List of threshold alerts
    """
    alerts = threshold_notification_manager.get_alerts(limit=limit, unacknowledged_only=unacknowledged_only)
    return {
        "success": True,
        "alerts": [alert.dict() for alert in alerts]
    }


@app.put("/api/threshold/alerts/{alert_id}/acknowledge", tags=["Threshold Notifications"])
async def acknowledge_alert(
    alert_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Acknowledge a specific alert

    Args:
        alert_id: Alert ID to acknowledge
        current_user: Authenticated user

    Returns:
        Success message
    """
    if not threshold_notification_manager.acknowledge_alert(alert_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Alert not found"
        )
    return {
        "success": True,
        "message": "Alert acknowledged"
    }


@app.put("/api/threshold/alerts/acknowledge-all", tags=["Threshold Notifications"])
async def acknowledge_all_alerts(current_user: dict = Depends(get_current_user)):
    """
    Acknowledge all alerts

    Args:
        current_user: Authenticated user

    Returns:
        Success message with count
    """
    count = threshold_notification_manager.acknowledge_all_alerts()
    return {
        "success": True,
        "message": f"Acknowledged {count} alerts",
        "count": count
    }


@app.post("/api/threshold/check", tags=["Threshold Notifications"])
async def check_thresholds_now(current_user: dict = Depends(get_current_user)):
    """
    Manually trigger threshold check

    Args:
        current_user: Authenticated user

    Returns:
        List of any new alerts triggered
    """
    new_alerts = threshold_notification_manager.check_thresholds()
    return {
        "success": True,
        "alerts_triggered": len(new_alerts),
        "alerts": [alert.dict() for alert in new_alerts]
    }


# ============================================================
# API ROUTES: DOCKER MANAGEMENT
# ============================================================

@app.get("/api/docker/status", tags=["Docker"])
async def docker_status(current_user: dict = Depends(get_current_user)):
    """Check if Docker is available"""
    return docker_manager.get_status()


@app.get("/api/docker/containers", tags=["Docker"])
async def list_docker_containers(
    all: bool = True,
    current_user: dict = Depends(get_current_user)
):
    """
    List all Docker containers

    Args:
        all: Include stopped containers
        current_user: Authenticated user

    Returns:
        List of containers
    """
    containers = docker_manager.list_containers(all=all)
    return {"containers": containers}


@app.post("/api/docker/containers/{container_id}/start", tags=["Docker"])
async def start_docker_container(
    container_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Start a Docker container

    Args:
        container_id: Container ID or name
        current_user: Authenticated user

    Returns:
        Start status
    """
    return docker_manager.start_container(container_id)


@app.post("/api/docker/containers/{container_id}/stop", tags=["Docker"])
async def stop_docker_container(
    container_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Stop a Docker container

    Args:
        container_id: Container ID or name
        current_user: Authenticated user

    Returns:
        Stop status
    """
    return docker_manager.stop_container(container_id)


@app.post("/api/docker/containers/{container_id}/restart", tags=["Docker"])
async def restart_docker_container(
    container_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Restart a Docker container

    Args:
        container_id: Container ID or name
        current_user: Authenticated user

    Returns:
        Restart status
    """
    return docker_manager.restart_container(container_id)


@app.get("/api/docker/containers/{container_id}/logs", tags=["Docker"])
async def get_container_logs(
    container_id: str,
    tail: int = 100,
    current_user: dict = Depends(get_current_user)
):
    """
    Get logs from a Docker container

    Args:
        container_id: Container ID or name
        tail: Number of lines from end of logs (1-10000)
        current_user: Authenticated user

    Returns:
        Container logs
    """
    return docker_manager.get_container_logs(container_id, tail)


# ============================================================
# API ROUTES: PROCESS MANAGEMENT
# ============================================================

@app.get("/api/processes", tags=["Processes"])
async def list_processes(
    limit: int = 50,
    sort_by: str = "cpu",
    current_user: dict = Depends(get_current_user)
):
    """
    List system processes sorted by resource usage

    Args:
        limit: Maximum number of processes to return (1-100)
        sort_by: Sort by 'cpu' or 'memory'
        current_user: Authenticated user

    Returns:
        List of processes
    """
    # Validate and limit parameters
    limit = max(1, min(100, int(limit)))
    sort_by = sort_by.lower() if sort_by.lower() in ["cpu", "memory"] else "cpu"

    processes = ProcessManager.list_processes(limit=limit, sort_by=sort_by)
    return {"processes": processes}


@app.delete("/api/processes/{pid}", tags=["Processes"])
async def kill_process(
    pid: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Kill a process by PID

    Args:
        pid: Process ID to kill (must be valid PID)
        current_user: Authenticated user

    Returns:
        Kill status
    """
    # Validate PID
    try:
        pid = int(pid)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PID format"
        )

    return ProcessManager.kill_process(pid)


@app.get("/api/processes/{pid}", tags=["Processes"])
async def get_process_details(
    pid: int,
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a process

    Args:
        pid: Process ID
        current_user: Authenticated user

    Returns:
        Process details
    """
    # Validate PID
    try:
        pid = int(pid)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid PID format"
        )

    return ProcessManager.get_process_details(pid)


# ============================================================
# API ROUTES: SCREENSHOT
# ============================================================

@app.get("/api/screenshot/status", tags=["Screenshot"])
async def screenshot_status():
    """
    Check if screenshot functionality is available

    Returns:
        Availability status
    """
    return {
        "available": PYAUTOGUI_AVAILABLE
    }


@app.post("/api/screenshot/capture", tags=["Screenshot"])
async def capture_screenshot(
    quality: int = 75,
    current_user: dict = Depends(get_current_user)
):
    """
    Capture the screen and return as base64 image

    Args:
        quality: JPEG quality (1-100)
        current_user: Authenticated user

    Returns:
        Base64-encoded screenshot
    """
    # Validate quality range
    try:
        quality = int(quality)
        quality = max(1, min(100, quality))
    except (ValueError, TypeError):
        quality = 75

    return ScreenshotService.capture_screen(quality=quality)


# ============================================================
# API ROUTES: WAKE-ON-LAN PREPARATION
# ============================================================

# Simple in-memory storage for registered MAC addresses (in production, use a database)
registered_macs = {}


@app.post("/api/wol/register", tags=["Wake-on-LAN"])
async def register_wol_device(
    mac_address: str,
    device_name: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Register a device for Wake-on-LAN

    Args:
        mac_address: MAC address of the device (XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)
        device_name: Friendly name for the device (alphanumeric, max 64 chars)
        current_user: Authenticated user

    Returns:
        Registration status

    Raises:
        HTTPException: If MAC address or device name is invalid
    """
    # Validate and sanitize inputs
    mac_address = mac_address.strip() if mac_address else ""
    device_name = SecurityManager.sanitize_input(device_name, max_length=64)

    if not device_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Device name is required"
        )

    if not SecurityManager.validate_mac_address(mac_address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MAC address format (expected XX:XX:XX:XX:XX:XX or XX-XX-XX-XX-XX-XX)"
        )

    # Store the MAC address
    registered_macs[device_name] = mac_address

    logger.info(f"Registered WoL device: {device_name}")

    return {
        "success": True,
        "message": f"Device '{device_name}' registered"
    }


@app.get("/api/wol/devices", tags=["Wake-on-LAN"])
async def list_wol_devices(current_user: dict = Depends(get_current_user)):
    """
    List all registered Wake-on-LAN devices

    Args:
        current_user: Authenticated user

    Returns:
        List of registered devices
    """
    return {"devices": registered_macs}


@app.post("/api/wol/send", tags=["Wake-on-LAN"])
async def send_wol_packet(
    mac_address: str,
    broadcast_ip: str = "255.255.255.255",
    port: int = 9,
    current_user: dict = Depends(get_current_user)
):
    """
    Send Wake-on-LAN magic packet to wake a device

    Args:
        mac_address: MAC address of the target device
        broadcast_ip: Broadcast IP address (default: 255.255.255.255)
        port: UDP port to send to (default: 9)
        current_user: Authenticated user

    Returns:
        Sending status
    """
    import socket

    # Validate MAC address
    mac_address = mac_address.strip() if mac_address else ""

    if not SecurityManager.validate_mac_address(mac_address):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid MAC address format"
        )

    # Validate broadcast IP (basic check)
    import ipaddress
    try:
        ip = ipaddress.ip_address(broadcast_ip)
        if not ip.is_private and broadcast_ip != "255.255.255.255":
            logger.warning(f"Sending WoL to non-private IP: {broadcast_ip}")
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid broadcast IP address"
        )

    # Validate port
    if not (1 <= port <= 65535):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Port must be between 1 and 65535"
        )

    try:
        # Create magic packet
        # MAC address should be in format XX:XX:XX:XX:XX:XX
        mac_clean = mac_address.replace(":", "").replace("-", "")

        # Create the magic packet: 6 bytes of FF followed by MAC repeated 16 times
        magic_packet = b'\xff' * 6 + bytes.fromhex(mac_clean) * 16

        # Send via UDP socket
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.sendto(magic_packet, (broadcast_ip, port))

        logger.info(f"Sent WoL magic packet to {mac_address} at {broadcast_ip}:{port}")

        return {
            "success": True,
            "message": f"Magic packet sent to {mac_address}",
            "mac_address": mac_address,
            "broadcast_ip": broadcast_ip,
            "port": port
        }

    except Exception as e:
        logger.error(f"Failed to send WoL packet: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send magic packet"
        )


# ============================================================
# HEALTH CHECK & ROOT ENDPOINTS
# ============================================================

@app.get("/", tags=["General"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": "NexControl API",
        "version": "1.0.0",
        "status": "running",
        "os": OS_TYPE,
        "docs": "/docs",
        "endpoints": {
            "stats": "/api/stats/all",
            "health": "/health",
            "docs": "/docs"
        },
        "timestamp": time.time()
    }


@app.post("/api/test/echo", tags=["General"])
async def test_echo(request: Request):
    """
    Simple POST echo endpoint for testing iOS network issues
    Echos back whatever JSON is sent to it
    No authentication required
    """
    from fastapi.responses import JSONResponse
    import json

    # Try to read body
    body_bytes = await request.body()
    body_str = body_bytes.decode('utf-8')

    logger.info(f"[TEST ECHO] Received POST from {get_remote_address(request)}")
    logger.info(f"[TEST ECHO] Body: {body_str[:200]}")  # Log first 200 chars

    try:
        body_json = json.loads(body_str)
        return {
            "status": "success",
            "message": "POST request received successfully!",
            "received_data": body_json,
            "timestamp": time.time()
        }
    except json.JSONDecodeError:
        return {
            "status": "success",
            "message": "POST received (not valid JSON)",
            "raw_body": body_str,
            "timestamp": time.time()
        }


@app.get("/api/test/connection", tags=["General"])
async def test_connection():
    """
    Simple connection test endpoint for debugging iOS network issues
    No authentication required
    CORS is handled by CORSMiddleware
    """
    return {
        "status": "connected",
        "message": "Connection successful! Your iOS device can reach the server.",
        "timestamp": time.time(),
        "server_time": datetime.now().isoformat()
    }


@app.get("/stats", tags=["General"])
async def stats_redirect():
    """Convenient redirect to stats endpoint"""
    import json
    stats = SystemMonitor.get_all_stats()
    # Format for pretty display in browser
    return JSONResponse(
        content=stats,
        status_code=200
    )


@app.get("/health", tags=["General"])
async def health_check():
    """Health check endpoint - no authentication required"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "services": {
            "docker": docker_manager.available
        }
    }


# ============================================================
# WEBSOCKET SUPPORT - Real-time Stats Streaming
# ============================================================

class WebSocketConnectionManager:
    """Manages WebSocket connections for real-time stats broadcasting"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self._broadcast_task = None
        self._is_running = False

    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"[WebSocket] Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"[WebSocket] Client disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"[WebSocket] Error sending message: {e}")
            self.disconnect(websocket)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"[WebSocket] Failed to send to client: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def start_broadcasting(self, interval: float = 1.0):
        """Start background task to broadcast stats at regular intervals"""
        if self._is_running:
            return

        self._is_running = True
        logger.info(f"[WebSocket] Starting stats broadcast every {interval}s")

        while self._is_running:
            try:
                # Get current stats (including all disks)
                stats = SystemMonitor.get_all_stats()
                disks = SystemMonitor.get_all_disks()

                # Combine stats and disks
                broadcast_data = {
                    **stats,
                    "disks": disks
                }

                # Broadcast to all connected clients
                await self.broadcast({
                    "type": "stats_update",
                    "data": broadcast_data,
                    "timestamp": time.time()
                })

                await asyncio.sleep(interval)
            except Exception as e:
                logger.error(f"[WebSocket] Broadcast error: {e}")
                await asyncio.sleep(interval)

    def stop_broadcasting(self):
        """Stop the background broadcast task"""
        self._is_running = False
        logger.info("[WebSocket] Stopped stats broadcast")


# Global WebSocket manager
websocket_manager = WebSocketConnectionManager()

# Initialize manager singletons
docker_manager = DockerManager()
scheduled_task_manager = ScheduledTaskManager()
threshold_notification_manager = ThresholdNotificationManager()


@app.websocket("/ws/stats")
async def websocket_stats(websocket: WebSocket):
    """
    WebSocket endpoint for real-time system stats streaming.

    Connect to this endpoint to receive continuous updates of:
    - CPU usage
    - Memory usage
    - Disk usage
    - GPU temperature
    - Network stats

    No authentication required (for local network convenience)

    Example:
        ws = new WebSocket("ws://localhost:8000/ws/stats")
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data)
            console.log(data.data.cpu.cpu_percent)
        }
    """
    await websocket_manager.connect(websocket)

    # Start broadcasting if this is the first connection
    if len(websocket_manager.active_connections) == 1:
        # Note: In production, you'd want to run this in a proper background task
        # For now, we'll send initial stats and let clients poll as needed
        try:
            # Send initial stats immediately
            stats = SystemMonitor.get_all_stats()
            await websocket_manager.send_personal_message({
                "type": "stats_update",
                "data": stats,
                "timestamp": time.time()
            }, websocket)

            # Keep connection alive and handle incoming messages
            while True:
                try:
                    # Wait for client messages (ping/pong, control commands)
                    data = await websocket.receive_text()

                    # Handle client requests
                    if data == "ping":
                        await websocket_manager.send_personal_message({"type": "pong"}, websocket)
                    elif data == "get_stats":
                        stats = SystemMonitor.get_all_stats()
                        await websocket_manager.send_personal_message({
                            "type": "stats_update",
                            "data": stats,
                            "timestamp": time.time()
                        }, websocket)

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"[WebSocket] Error receiving message: {e}")
                    break

        finally:
            websocket_manager.disconnect(websocket)
    else:
        # Just keep the connection alive
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"[WebSocket] Connection error: {e}")
            websocket_manager.disconnect(websocket)


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom HTTP exception handler
    Sanitizes error messages to prevent information leakage
    """
    # Log the error
    logger.warning(f"HTTP {exc.status_code}: {exc.detail[:100]}")

    # Return sanitized error
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": str(exc.detail)}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    General exception handler
    Catches all unhandled exceptions
    """
    # Log the error with full details for debugging
    logger.error(f"Unhandled exception: {type(exc).__name__}: {str(exc)[:200]}")

    # Return generic error to client (don't expose internal details)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )


# ============================================================
# MAIN ENTRY POINT
# ============================================================

if __name__ == "__main__":
    import uvicorn

    logger.info("=" * 60)
    logger.info("Starting NexControl Backend Server...")
    logger.info("=" * 60)
    logger.info(f"Operating System: {OS_TYPE}")
    logger.info(f"Docker Available: {docker_manager.available}")
    logger.info(f"Rate Limiting: Enabled")
    logger.info(f"Security: AES-256-GCM + JWT")
    logger.info("=" * 60)

    # Get configuration from environment or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
