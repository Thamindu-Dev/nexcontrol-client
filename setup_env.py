#!/usr/bin/env python3
"""
 =============================================================================
 NexControl - Secure Environment Setup Script
 =============================================================================
 This script generates secure credentials for NexControl and updates the .env file.

 Features:
 - Generates secure AES_KEY (32-byte) for payload encryption
 - Hashes admin password using Argon2id (OWASP/NIST recommended)
 - Preserves existing .env configuration
 - Displays AES_KEY clearly for mobile app setup
 - Optional self-deletion after use

 Usage:
     python setup_env.py

 Security:
 - Uses secrets.token_urlsafe() for cryptographically secure key generation
 - Uses passlib.context.CryptContext with Argon2id for password hashing
 - Argon2id provides GPU/ASIC resistance and side-channel attack protection
 - Never logs sensitive data to files
 =============================================================================
"""

import os
import sys
import secrets
import getpass
from pathlib import Path

# Add backend directory to path for imports
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from passlib.context import CryptContext
except ImportError:
    print("❌ ERROR: passlib not installed. Run: pip install 'passlib' 'argon2-cffi'")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================
ENV_FILE = Path(__file__).parent / "backend" / ".env"
AES_KEY_LENGTH = 32  # bytes

# Password hashing context - Using Argon2id (OWASP/NIST recommended)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto",
    argon2__time_cost=3,        # Number of iterations
    argon2__memory_cost=65536,  # 64 MB memory cost (in KiB)
    argon2__parallelism=4,      # Number of parallel threads
    argon2__hash_len=32,        # Hash length in bytes
    argon2__salt_len=16         # Salt length in bytes
)


# =============================================================================
# UTILITIES
# =============================================================================
def generate_aes_key() -> str:
    """Generate a secure 32-byte AES key (URL-safe base64 encoded)."""
    return secrets.token_urlsafe(AES_KEY_LENGTH)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id (OWASP/NIST recommended)."""
    return pwd_context.hash(password)


def read_env_file(env_path: Path) -> dict:
    """
    Read .env file and return key-value pairs.
    Preserves comments and empty lines by storing them separately.
    """
    config = {}
    comments = []
    other_lines = []

    if not env_path.exists():
        return {"config": config, "comments": comments, "other_lines": other_lines}

    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            stripped = line.strip()

            # Skip empty lines (preserve in other_lines)
            if not stripped:
                other_lines.append(line)
                continue

            # Store comments
            if stripped.startswith('#'):
                comments.append(stripped)
                continue

            # Parse KEY=VALUE lines
            if '=' in stripped:
                key, value = stripped.split('=', 1)
                config[key.strip()] = value.strip()
            else:
                # Preserve other non-empty lines
                other_lines.append(line)

    return {"config": config, "comments": comments, "other_lines": other_lines}


def write_env_file(env_path: Path, data: dict, comments: list, other_lines: list):
    """Write configuration to .env file, preserving comments and formatting."""
    with open(env_path, 'w', encoding='utf-8') as f:
        # Write comments first
        for comment in comments:
            f.write(f"{comment}\n")

        # Write a separator
        f.write("\n")

        # Write other lines (empty lines, etc.)
        for line in other_lines:
            f.write(line)

        # Write configuration
        for key, value in data.items():
            f.write(f"{key}={value}\n")


def get_password_with_confirmation() -> str:
    """
    Securely prompt for password with confirmation.
    Uses getpass to avoid echoing to terminal.
    """
    print("\n" + "=" * 60)
    print("🔐 Admin Password Setup")
    print("=" * 60)
    print("This password will be used to login to the NexControl backend.")
    print("Choose a strong password (12+ characters recommended).\n")

    while True:
        try:
            password = getpass.getpass("Enter new admin password: ")

            if not password:
                print("❌ Password cannot be empty. Please try again.\n")
                continue

            if len(password) < 8:
                print("⚠️  Warning: Password is short. Recommended: 12+ characters.")

            confirm = getpass.getpass("Confirm password: ")

            if password == confirm:
                return password
            else:
                print("❌ Passwords do not match. Please try again.\n")

        except (EOFError, KeyboardInterrupt):
            print("\n\n❌ Cancelled by user.")
            sys.exit(0)


# =============================================================================
# MAIN SETUP
# =============================================================================
def main():
    print("\n" + "=" * 60)
    print("🔧 NexControl Environment Setup")
    print("=" * 60)
    print(f"Target: {ENV_FILE}")
    print()

    # Check if .env exists
    if ENV_FILE.exists():
        print("📄 Existing .env file found.")
        response = input("Do you want to update it? (y/n): ").strip().lower()
        if response != 'y':
            print("❌ Cancelled.")
            sys.exit(0)

    # Step 1: Get admin password
    print("\n" + "-" * 60)
    print("Step 1/2: Admin Password")
    print("-" * 60)
    admin_password = get_password_with_confirmation()

    # Step 2: Generate credentials
    print("\n" + "-" * 60)
    print("Step 2/2: Generate Credentials")
    print("-" * 60)
    print("🔄 Generating secure AES_KEY...")
    aes_key = generate_aes_key()
    print(f"✅ Generated {AES_KEY_LENGTH}-byte AES key")

    print("🔄 Hashing admin password...")
    password_hash = hash_password(admin_password)
    print("✅ Password hashed (Argon2id - OWASP/NIST recommended)")

    # Step 3: Read existing .env
    print("\n" + "-" * 60)
    print("Step 3/3: Update .env File")
    print("-" * 60)
    env_data = read_env_file(ENV_FILE)

    # Update only the target keys
    env_data["config"]["AES_KEY"] = aes_key
    env_data["config"]["APP_PASSWORD_HASH"] = password_hash

    # Write back to file
    write_env_file(
        ENV_FILE,
        env_data["config"],
        env_data["comments"],
        env_data["other_lines"]
    )
    print(f"✅ Updated: {ENV_FILE}")

    # Step 4: Display AES_KEY for mobile app
    print("\n" + "=" * 60)
    print("📱 Copy This Key to Your Mobile App")
    print("=" * 60)
    print()
    print("⚠️  IMPORTANT: Copy this key and enter it in the NexControl")
    print("   mobile app Settings → Encryption Key")
    print()
    print("   ┌─────────────────────────────────────────────────────┐")
    print("   │ " + aes_key + " │")
    print("   └─────────────────────────────────────────────────────┘")
    print()
    print("💡 Tip: You can also find this key in backend/.env file")
    print("   under the 'AES_KEY' variable.")

    # Step 5: Self-deletion
    print("\n" + "=" * 60)
    print("🧹 Cleanup")
    print("=" * 60)
    print("⚠️  For security, it's recommended to delete this setup script")
    print("   after use to prevent accidental credential resets.\n")

    response = input("Do you want to delete this setup script now? (y/n): ").strip().lower()

    if response == 'y':
        script_path = Path(__file__).absolute()
        try:
            os.remove(script_path)
            print(f"✅ Deleted: {script_path}")
        except Exception as e:
            print(f"❌ Failed to delete script: {e}")
            print("   You can delete it manually: rm setup_env.py")
    else:
        print("ℹ️  Script kept. You can delete it later: rm setup_env.py")

    print("\n" + "=" * 60)
    print("✅ Setup Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start the backend: cd backend && python main.py")
    print("2. Open the mobile app and enter the AES_KEY in Settings")
    print("3. Login with the admin password you just set")
    print()


if __name__ == "__main__":
    main()
