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

from fastapi import FastAPI, HTTPException, Depends, status, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator, constr
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
from cryptography.hazmat.backends import default_backend
import jose.exceptions
from jose import jwt
from passlib.context import CryptContext

# ============================================================
# CONFIGURATION & CONSTANTS
# ============================================================

# Security Configuration - Load from environment with validation
def get_secret_key() -> bytes:
    """Get and validate SECRET_KEY from environment"""
    key = os.getenv("SECRET_KEY")
    if not key:
        logger.warning("SECRET_KEY not set, using insecure default! CHANGE THIS IN PRODUCTION!")
        key = "NexControl-Secret-Key-Change-Me-12345678"
    if len(key) < 32:
        raise ValueError("SECRET_KEY must be at least 32 characters long")
    return key.encode()[:32]

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
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# AES Encryption Configuration
AES_NONCE_LENGTH = 12  # 96-bit nonce for GCM

# App Password Configuration
# Default password: admin123
# Pre-computed bcrypt hash for compatibility
DEFAULT_APP_PASSWORD = "admin123"  # CHANGE IN PRODUCTION!
DEFAULT_PASSWORD_HASH = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5aqLkqVE1wkK6"
app_password_hash = os.getenv("APP_PASSWORD_HASH", DEFAULT_PASSWORD_HASH)

# Rate Limiting Configuration
MAX_LOGIN_ATTEMPTS = 5
LOGIN_LOCKOUT_MINUTES = 15

# Timestamp tolerance for replay attack prevention (seconds)
TIMESTAMP_TOLERANCE = 30

# OS Detection
OS_TYPE = platform.system()  # 'Windows', 'Linux', 'Darwin'
logger.info(f"Operating System detected: {OS_TYPE}")

# CORS Configuration - Allow all local network origins
# In production, you should restrict this to specific IPs
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ============================================================
# FASTAPI APP INITIALIZATION
# ============================================================

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(
    title="NexControl API",
    description="Secure Remote PC Controller Backend",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware - Configure based on environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

    @validator('password')
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

    @validator('timestamp')
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

    @validator('action')
    def validate_action(cls, v):
        """Validate action is allowed"""
        allowed = ['shutdown', 'hibernate', 'restart']
        if v.lower() not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v.lower()

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
        """Hash a password using bcrypt"""
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

        # Add unique token ID for revocation capability
        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16)  # JWT ID for potential revocation
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
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except jose.exceptions.ExpiredSignatureError:
            logger.warning("Expired token attempt detected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
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
            HTTPException: If decryption fails
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
        except Exception as e:
            logger.error(f"Decryption error: {str(e)[:100]}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
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
        try:
            # Use interval=0.1 for faster response
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()

            return {
                "cpu_percent": round(cpu_percent, 2),
                "cpu_count": cpu_count if cpu_count else 0,
                "cpu_freq_mhz": round(cpu_freq.current, 2) if cpu_freq else 0
            }
        except Exception as e:
            logger.error(f"Error getting CPU stats: {type(e).__name__}")
            return {"cpu_percent": 0, "error": "Failed to get CPU stats"}

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
        Get disk usage statistics

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
            "gpu": SystemMonitor.get_gpu_temperature(),
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
    def list_processes(limit: int = 20, sort_by: str = "cpu") -> list:
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
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    proc_info['cpu_percent'] = proc.cpu_percent()

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

            # Sort by specified metric
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

    For non-encrypted requests (GET, login):
    1. Pass through to route handler
    """
    # Track if request was encrypted
    was_encrypted = False

    # Check if request is encrypted (has encrypted data)
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            # Read request body
            body = await request.body()

            if body and len(body) < 10 * 1024 * 1024:  # Max 10MB
                import json
                data = json.loads(body)

                # Check if this is an encrypted payload
                if "data" in data and "timestamp" in data:
                    # Validate timestamp first (replay attack prevention)
                    if not SecurityManager.validate_timestamp(data["timestamp"]):
                        logger.warning(f"Invalid timestamp from {get_remote_address(request)}")
                        return JSONResponse(
                            status_code=status.HTTP_401_UNAUTHORIZED,
                            content={"detail": "Invalid timestamp"}
                        )

                    # Decrypt the payload
                    decrypted_data = SecurityManager.decrypt_data(data["data"])

                    # Store decrypted data in request state for route handlers
                    request.state.decrypted_data = decrypted_data
                    was_encrypted = True

        except json.JSONDecodeError:
            # Not valid JSON, let route handler deal with it
            pass
        except Exception as e:
            logger.error(f"Encryption middleware error: {type(e).__name__}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "Request processing failed"}
            )

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
            logger.error(f"Response encryption error: {type(e).__name__}")
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": "Response encryption failed"}
            )

    return response


# ============================================================
# API ROUTES: AUTHENTICATION
# ============================================================

@app.post("/api/auth/login", response_model=TokenResponse, tags=["Authentication"])
@limiter.limit("10 per minute")
async def login(request: LoginRequest, http_request: Request):
    """
    Authenticate with app password and receive JWT token

    Rate limited: 10 attempts per minute per IP
    Locks out after 5 failed attempts for 15 minutes

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


@app.options("/api/auth/login", tags=["Authentication"])
async def login_options():
    """
    Explicit OPTIONS handler for login endpoint
    iOS/Capacitor requires explicit CORS preflight response
    """
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Max-Age": "86400"
        }
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
    """Get GPU temperature statistics (no auth required)"""
    return SystemMonitor.get_gpu_temperature()


@app.get("/api/stats/network", tags=["System Stats (Public)"])
async def get_network_stats_public():
    """Get network I/O statistics (no auth required)"""
    return SystemMonitor.get_network_stats()


@app.get("/api/stats/all", tags=["System Stats (Public)"])
async def get_all_stats_public():
    """Get all system statistics in one call (no auth required)"""
    return SystemMonitor.get_all_stats()

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
    """Get GPU temperature statistics (authentication required)"""
    return SystemMonitor.get_gpu_temperature()


@app.get("/api/v1/stats/network", tags=["System Stats (Protected)"])
async def get_network_stats(current_user: dict = Depends(get_current_user)):
    """Get network I/O statistics (authentication required)"""
    return SystemMonitor.get_network_stats()


@app.get("/api/v1/stats/all", tags=["System Stats (Protected)"])
async def get_all_stats(current_user: dict = Depends(get_current_user)):
    """Get all system statistics in one call (authentication required)"""
    return SystemMonitor.get_all_stats()


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
    limit: int = 20,
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


@app.get("/api/test/connection", tags=["General"])
async def test_connection():
    """
    Simple connection test endpoint for debugging iOS network issues
    No authentication required, returns CORS headers
    """
    from fastapi.responses import JSONResponse
    return JSONResponse(
        content={
            "status": "connected",
            "message": "Connection successful! Your iOS device can reach the server.",
            "timestamp": time.time(),
            "server_time": datetime.now().isoformat()
        },
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )


@app.options("/api/test/connection", tags=["General"])
async def test_connection_options():
    """OPTIONS handler for test connection endpoint"""
    from fastapi.responses import Response
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "*"
        }
    )


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
