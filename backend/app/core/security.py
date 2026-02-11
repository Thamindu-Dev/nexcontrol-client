import os
import sys
import json
import base64
import time
import re
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import jwt, exceptions as jose_exceptions
from passlib.context import CryptContext
from fastapi import HTTPException, status

from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings, logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Rate limiting storage
login_attempts: Dict[str, list] = {}  # IP -> list of timestamps

# Power action rate limiting storage (new)
power_action_timestamps: Dict[str, list] = {}  # IP -> list of timestamps


# Password hashing context
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=3,
    argon2__memory_cost=65536,
    argon2__parallelism=4,
    argon2__hash_len=32,
    argon2__salt_len=16
)

# Initialize password hash
if settings.APP_PASSWORD_HASH:
    app_password_hash = settings.APP_PASSWORD_HASH
    logger.info("Using custom password hash from environment")
else:
    app_password_hash = pwd_context.hash(settings.DEFAULT_APP_PASSWORD)
    logger.info(f"Generated hash for default password")

def get_secret_key_bytes() -> bytes:
    """Ensure SECRET_KEY is valid bytes"""
    import hashlib
    return hashlib.sha256(settings.SECRET_KEY.encode()).digest()

def get_aes_key_bytes() -> bytes:
    """Ensure AES_KEY is valid bytes"""
    return settings.AES_KEY.encode()[:32]

SECRET_KEY_BYTES = get_secret_key_bytes()
AES_KEY_BYTES = get_aes_key_bytes()

class SecurityManager:
    """
    Handles all security-related operations:
    - AES-256-GCM encryption/decryption
    - JWT token generation/validation
    - Password hashing/verification
    - Timestamp validation
    - Input sanitization
    """

    @staticmethod
    def hash_password(password: str) -> str:
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str = None) -> bool:
        """
        Verify a password with constant-time comparison to prevent timing attacks.
        If no hash provided, uses the global app password hash.
        """
        if hashed_password is None:
            hashed_password = app_password_hash

        start_time = time.time()
        result = False

        try:
            result = pwd_context.verify(plain_password, hashed_password)
        except Exception:
            result = False

        # Constant-time delay to prevent timing attacks
        # argon2 already has constant-time properties, but we add
        # additional delay to further obfuscate the verification time
        elapsed = time.time() - start_time
        min_verification_time = 0.05  # 50ms minimum
        if elapsed < min_verification_time:
            time.sleep(min_verification_time - elapsed)

        return result

    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        to_encode.update({
            "exp": expire,
            "iat": datetime.utcnow(),
            "jti": secrets.token_hex(16),
            "iss": settings.JWT_ISSUER
        })
        encoded_jwt = jwt.encode(to_encode, SECRET_KEY_BYTES, algorithm=settings.ALGORITHM)
        return encoded_jwt

    @staticmethod
    def verify_token(token: str) -> dict:
        try:
            payload = jwt.decode(
                token,
                SECRET_KEY_BYTES,
                algorithms=[settings.ALGORITHM],
                issuer=settings.JWT_ISSUER
            )
            return payload
        except jose_exceptions.ExpiredSignatureError:
            logger.warning("Expired token attempt detected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jose_exceptions.InvalidIssuerError:
            logger.warning("Invalid token issuer detected")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token issuer"
            )
        except jose_exceptions.JWTError as e:
            logger.warning(f"Invalid token attempt: {str(e)[:100]}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    def encrypt_data(data: dict) -> str:
        try:
            if not isinstance(data, dict):
                raise ValueError("Data must be a dictionary")
            
            json_data = json.dumps(data).encode('utf-8')
            nonce = os.urandom(settings.AES_NONCE_LENGTH)
            aesgcm = AESGCM(AES_KEY_BYTES)
            ciphertext = aesgcm.encrypt(nonce, json_data, None)
            combined = nonce + ciphertext
            return base64.b64encode(combined).decode('utf-8')

        except Exception as e:
            logger.error(f"Encryption error: {str(e)[:100]}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Encryption failed"
            )

    @staticmethod
    def decrypt_data(encrypted_data: str) -> dict:
        try:
            if not encrypted_data or not isinstance(encrypted_data, str):
                raise ValueError("Invalid encrypted data format")

            try:
                combined = base64.b64decode(encrypted_data)
            except Exception:
                raise ValueError("Invalid base64 encoding")

            if len(combined) < settings.AES_NONCE_LENGTH + 16:
                raise ValueError("Encrypted data too short")

            nonce = combined[:settings.AES_NONCE_LENGTH]
            ciphertext = combined[settings.AES_NONCE_LENGTH:]
            aesgcm = AESGCM(AES_KEY_BYTES)
            decrypted_data = aesgcm.decrypt(nonce, ciphertext, None)
            
            return json.loads(decrypted_data.decode('utf-8'))

        except ValueError as e:
            logger.warning(f"Decryption validation error: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid encrypted data format"
            )
        except Exception as e:
            # Likely crypto error (wrong key)
            logger.warning(f"DECRYPTION FAILED: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Encryption Key or Decryption Failed"
            )

    @staticmethod
    def validate_timestamp(timestamp: float, tolerance: int = settings.TIMESTAMP_TOLERANCE) -> bool:
        current_time = time.time()
        time_diff = abs(current_time - timestamp)
        if time_diff > tolerance:
            logger.warning(f"Timestamp validation failed. Difference: {time_diff:.2f}s > {tolerance}s")
            return False
        return True

    @staticmethod
    def sanitize_input(input_str: str, max_length: int = 256) -> str:
        if not isinstance(input_str, str):
            raise ValueError("Input must be a string")
        
        input_str = input_str[:max_length]
        dangerous_chars = ['\x00', '\n', '\r', '\x1a', '\\', "'", '"', ';', '|', '&', '$', '`', '<', '>']
        for char in dangerous_chars:
            input_str = input_str.replace(char, '')
        
        input_str = ''.join(char for char in input_str if char == '\t' or char.isprintable())
        return input_str.strip()

    @staticmethod
    def validate_pid(pid: int) -> bool:
        """Validate PID is within valid system range"""
        if not isinstance(pid, int):
            return False

        # Platform-specific max PID values
        import platform
        if platform.system() == "Windows":
            max_pid = 4194304  # Windows max
        elif platform.system() == "Darwin":  # macOS
            max_pid = 99999
        else:  # Linux and others
            max_pid = 32768  # Linux default (can be higher but 32768 is safe default)

        return 1 <= pid <= max_pid

    @staticmethod
    def validate_container_id(container_id: str) -> bool:
        """Validate Docker container ID/name to prevent path traversal"""
        if not isinstance(container_id, str):
            return False

        # Check for path traversal attempts
        if '..' in container_id or '/' in container_id or '\\' in container_id:
            return False

        sanitized = SecurityManager.sanitize_input(container_id, max_length=256)
        hex_pattern = r'^[a-f0-9]{12,64}$'  # Docker IDs are minimum 12 chars
        name_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_-]{0,62}$'  # No leading ., max 63 chars

        return bool(re.match(hex_pattern, sanitized) or re.match(name_pattern, sanitized))

    @staticmethod
    def validate_mac_address(mac_address: str) -> bool:
        if not isinstance(mac_address, str):
            return False
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if not re.match(pattern, mac_address):
            return False

        # Reject broadcast MAC address
        clean_mac = mac_address.upper().replace(':', '').replace('-', '')
        if clean_mac == 'FFFFFFFFFFFF':
            return False

        # Reject multicast MAC addresses (LSB of first octet is 1)
        try:
            first_octet = int(mac_address[:2], 16)
            if first_octet & 1:  # If LSB is 1, it's multicast
                return False
        except (ValueError, IndexError):
            return False

        return True

    @staticmethod
    def validate_file_path(file_path: str) -> bool:
        """Validate file path to prevent path traversal and command injection"""
        import os

        if not isinstance(file_path, str):
            return False

        # Reject empty paths
        if not file_path or not file_path.strip():
            return False

        # Reject path traversal attempts
        if '..' in file_path or '~' in file_path:
            return False

        # Reject suspicious characters that could enable command injection
        # Only allow alphanumeric, spaces, and certain punctuation
        # Windows: allow : for drive letter, \ for path separator
        # Linux/macOS: allow / for path separator
        allowed_chars = set(r'a-zA-Z0-9\s\:\/\\._-')
        if not set(file_path).issubset(allowed_chars):
            # Check for shell metacharacters specifically
            shell_chars = set('&|<>$`!()[]{};\'"')
            if any(char in file_path for char in shell_chars):
                return False

        # Validate path format (basic check)
        try:
            # Normalize the path
            normalized = os.path.normpath(file_path)
            # Ensure it doesn't escape to parent directories
            if '..' in normalized:
                return False
        except:
            return False

        return True

    @staticmethod
    async def get_current_user(token: str = Depends(oauth2_scheme)):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = SecurityManager.verify_token(token)
            user = payload.get("sub")
            if user is None:
                raise credentials_exception
            return user
        except Exception:
            raise credentials_exception

    @staticmethod
    def check_rate_limit(ip: str) -> bool:
        """Check if IP has exceeded login attempts"""
        now = time.time()
        # Clean up old attempts for this IP first
        if ip in login_attempts:
            # Filter out attempts older than lockout period
            valid_window = now - (settings.LOGIN_LOCKOUT_MINUTES * 60)
            login_attempts[ip] = [t for t in login_attempts[ip] if t > valid_window]

            # Remove IP entry if no recent attempts
            if not login_attempts[ip]:
                del login_attempts[ip]

        attempts = login_attempts.get(ip, [])
        return len(attempts) < settings.MAX_LOGIN_ATTEMPTS

    @staticmethod
    def cleanup_old_login_attempts():
        """Clean up old login attempts to prevent memory leak"""
        now = time.time()
        cutoff = now - (settings.LOGIN_LOCKOUT_MINUTES * 60 * 2)  # 2x lockout period

        # Clean up IPs with only old attempts
        for ip in list(login_attempts.keys()):
            if not login_attempts[ip] or max(login_attempts[ip]) < cutoff:
                del login_attempts[ip]

    @staticmethod
    def record_login_attempt(ip: str, success: bool):
        """Record a login attempt"""
        if success:
            if ip in login_attempts:
                # Reset attempts on success?
                # Yes, usually.
                del login_attempts[ip]
        else:
            now = time.time()
            if ip not in login_attempts:
                login_attempts[ip] = []
            login_attempts[ip].append(now)

    @staticmethod
    def check_power_action_rate_limit(ip: str) -> tuple[bool, int]:
        """
        Check if IP has exceeded power action rate limit.
        Returns (allowed, remaining_requests)
        """
        now = time.time()
        window_start = now - settings.POWER_ACTION_WINDOW_SECONDS

        # Clean up old timestamps for this IP
        if ip in power_action_timestamps:
            power_action_timestamps[ip] = [
                t for t in power_action_timestamps[ip]
                if t > window_start
            ]

        # Get current count
        attempts = power_action_timestamps.get(ip, [])
        count = len(attempts)

        if count >= settings.POWER_ACTION_LIMIT_PER_MINUTE:
            remaining = 0
            return False, remaining

        remaining = settings.POWER_ACTION_LIMIT_PER_MINUTE - count
        return True, remaining

    @staticmethod
    def record_power_action(ip: str):
        """Record a power action for rate limiting"""
        now = time.time()
        if ip not in power_action_timestamps:
            power_action_timestamps[ip] = []
        power_action_timestamps[ip].append(now)

    @staticmethod
    def cleanup_old_power_action_attempts():
        """Clean up old power action timestamps to prevent memory leak"""
        now = time.time()
        cutoff = now - (settings.POWER_ACTION_WINDOW_SECONDS * 2)

        for ip in list(power_action_timestamps.keys()):
            # Remove IPs with only old timestamps
            if not power_action_timestamps[ip] or max(power_action_timestamps[ip]) < cutoff:
                del power_action_timestamps[ip]
