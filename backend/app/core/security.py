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
        """Verify a password. If no hash provided, uses the global app password hash."""
        if hashed_password is None:
            hashed_password = app_password_hash
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

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
        return isinstance(pid, int) and 1 <= pid <= 4194304

    @staticmethod
    def validate_container_id(container_id: str) -> bool:
        if not isinstance(container_id, str):
            return False
        sanitized = SecurityManager.sanitize_input(container_id, max_length=256)
        hex_pattern = r'^[a-f0-9]{1,64}$'
        name_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$'
        return bool(re.match(hex_pattern, sanitized) or re.match(name_pattern, sanitized))

    @staticmethod
    def validate_mac_address(mac_address: str) -> bool:
        if not isinstance(mac_address, str):
            return False
        pattern = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        return bool(re.match(pattern, mac_address))

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
            
        attempts = login_attempts.get(ip, [])
        return len(attempts) < settings.MAX_LOGIN_ATTEMPTS

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
