#!/usr/bin/env python3
"""
 =============================================================================
 NexControl Portable Setup Wizard
 =============================================================================
 First-run setup wizard for portable server distribution.

 Features:
 - GUI setup wizard using customtkinter
 - Generates unique AES_KEY and SECRET_KEY per installation
 - Stores config encrypted with Windows DPAPI in AppData
 - Exports AES key in multiple formats (text, QR, instructions)
 - No .env file exposed in portable folder

 Security:
 - Uses Windows DPAPI for machine-specific encryption
 - Argon2id password hashing
 - Unique keys per installation
 =============================================================================
"""

import os
import sys
import secrets
import json
import platform
from pathlib import Path

# Fix console encoding for Windows (handles emojis)
if platform.system() == "Windows":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except:
        pass

def safe_print(*args, **kwargs):
    """Print function that handles encoding errors gracefully."""
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        ascii_args = []
        for arg in args:
            if isinstance(arg, str):
                ascii_args.append(arg.encode('ascii', 'ignore').decode('ascii'))
            else:
                ascii_args.append(arg)
        print(*ascii_args, **kwargs)

# Try to import required dependencies
try:
    import customtkinter as ctk
except ImportError:
    safe_print("[!] ERROR: customtkinter not installed.")
    safe_print("   Run: pip install customtkinter")
    sys.exit(1)

try:
    from passlib.context import CryptContext
except ImportError:
    safe_print("[!] ERROR: passlib not installed.")
    safe_print("   Run: pip install 'passlib' 'argon2-cffi'")
    sys.exit(1)

try:
    import win32crypt
except ImportError:
    safe_print("[!] ERROR: pywin32 not installed.")
    safe_print("   Run: pip install pywin32")
    sys.exit(1)

try:
    import qrcode
except ImportError:
    safe_print("[!] WARNING: qrcode not installed. QR code generation disabled.")
    safe_print("   Run: pip install 'qrcode[pil]'")
    qrcode = None


# =============================================================================
# CONFIGURATION
# =============================================================================
CONFIG_DIR = Path(os.getenv('LOCALAPPDATA', '~')) / 'NexControl'
CONFIG_FILE = CONFIG_DIR / 'config.dat'
AES_KEY_LENGTH = 32
SECRET_KEY_LENGTH = 32


# =============================================================================
# PASSWORD HASHING
# =============================================================================
# Simple CryptContext initialization for better PyInstaller compatibility
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


# =============================================================================
# DPAPI ENCRYPTION FUNCTIONS
# =============================================================================
def encrypt_config_with_dpapi(data: dict) -> bytes:
    """
    Encrypt configuration data using Windows DPAPI.
    Data is tied to the current user's Windows credentials.
    """
    # Convert to JSON bytes
    json_str = json.dumps(data, separators=(',', ':'))
    json_data = bytes(json_str, 'utf-8')

    # Encrypt using DPAPI
    # CryptProtectData returns bytes directly when called with 2 arguments
    encrypted = win32crypt.CryptProtectData(json_data, 'NexControl Config')

    return encrypted


def decrypt_config_from_dpapi(encrypted_data: bytes) -> dict:
    """
    Decrypt configuration data using Windows DPAPI.
    """
    # Decrypt using DPAPI
    # CryptUnprotectData returns (description, data) tuple
    decrypted = win32crypt.CryptUnprotectData(encrypted_data)

    # Parse JSON from decrypted bytes (second element)
    return json.loads(decrypted[1].decode('utf-8'))


def load_config() -> dict | None:
    """Load configuration from AppData, returns None if not found."""
    try:
        if not CONFIG_FILE.exists():
            return None
        encrypted_data = CONFIG_FILE.read_bytes()
        return decrypt_config_from_dpapi(encrypted_data)
    except Exception as e:
        print(f"[!] Error loading config: {e}")
        return None


def save_config(aes_key: str, secret_key: str, password_hash: str) -> bool:
    """Save configuration encrypted with DPAPI to AppData."""
    try:
        config = {
            'AES_KEY': aes_key,
            'SECRET_KEY': secret_key,
            'APP_PASSWORD_HASH': password_hash
        }

        encrypted_data = encrypt_config_with_dpapi(config)

        # Ensure directory exists
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Write encrypted config
        CONFIG_FILE.write_bytes(encrypted_data)

        return True
    except Exception as e:
        safe_print(f"[!] Error saving config: {e}")
        return False


# =============================================================================
# KEY GENERATION
# =============================================================================
def generate_aes_key() -> str:
    """Generate a secure 32-byte AES key (URL-safe base64 encoded)."""
    return secrets.token_urlsafe(AES_KEY_LENGTH)


def generate_secret_key() -> str:
    """Generate a secure 32-byte secret key (URL-safe base64 encoded)."""
    return secrets.token_urlsafe(SECRET_KEY_LENGTH)


def hash_password(password: str) -> str:
    """Hash a password using Argon2id."""
    return pwd_context.hash(password)


# =============================================================================
# MOBILE APP EXPORT FUNCTIONS
# =============================================================================
def export_aes_key_text(aes_key: str, output_dir: Path) -> Path:
    """Export AES key to a text file."""
    output_file = output_dir / 'AES_KEY.txt'
    content = f"""================================================================
           NexControl Mobile App Encryption Key
================================================================

WARNING: KEEP THIS KEY SECURE - Do not share with others

Your Encryption Key:
{aes_key}

================================================================

How to use in Mobile App:

Method 1 - Manual Entry:
  1. Open NexControl mobile app
  2. Go to Settings -> Encryption Key
  3. Copy and paste the key above

Method 2 - Scan QR Code:
  1. Open AES_KEY_QR.png on this computer
  2. In mobile app, tap "Scan QR Code"
  3. Point camera at the QR code image

================================================================

Tip: You can also find this key later in the server
     system tray menu -> "Show Encryption Key"
"""
    output_file.write_text(content, encoding='utf-8')
    return output_file


def export_aes_key_qr(aes_key: str, output_dir: Path) -> Path | None:
    """Export AES key as a QR code image."""
    if qrcode is None:
        return None

    try:
        output_file = output_dir / 'AES_KEY_QR.png'

        # Create QR code - use make() without arguments
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(aes_key)
        qr.make()

        # Create simple image without text overlay
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(output_file)
        return output_file

    except Exception as e:
        # QR code generation is optional, fail silently
        return None


def export_setup_instructions(output_dir: Path) -> Path:
    """Export setup instructions to a text file."""
    output_file = output_dir / 'SETUP_INSTRUCTIONS.txt'
    content = """╔════════════════════════════════════════════════════════════╗
║              NexControl Portable Server Setup                ║
╚════════════════════════════════════════════════════════════╝

✅ Setup completed successfully!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📱 STEP 1: Configure Mobile App
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Open the NexControl mobile app and set up the encryption key:

Method A - Scan QR Code (Recommended):
  1. Open AES_KEY_QR.png on this computer
  2. In mobile app: Settings → Encryption Key → Scan QR Code
  3. Point your camera at the QR code image

Method B - Manual Entry:
  1. Open AES_KEY.txt on this computer
  2. Copy the encryption key
  3. In mobile app: Settings → Encryption Key
  4. Paste the key

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🚀 STEP 2: Start the Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Double-click: NexControl.exe

The server will start in a console window.
You can minimize it - it will run in the background.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 STEP 3: Login
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Use the admin password you just created during setup.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
💡 TIPS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• System Tray: Look for NexControl icon in your system tray
  for quick access to features.

• Show Encryption Key: Right-click tray icon → "Show Encryption Key"
  if you need to set up the mobile app on another device.

• Server URL: The mobile app will need your computer's IP address.
  Find it in: Settings → Server Info

• Firewall: Make sure Windows Firewall allows NexControl on port 8000.

━━━━━━━━━━━━━━━━══════════════════════════════════════════════

📚 Need Help? Visit: github.com/yourusername/nexcontrol
"""
    output_file.write_text(content, encoding='utf-8')
    return output_file


# =============================================================================
# GUI SETUP WIZARD
# =============================================================================
class SetupWizard(ctk.CTk):
    """First-run setup wizard GUI."""

    def __init__(self, on_complete_callback):
        super().__init__()

        self.on_complete_callback = on_complete_callback
        self.aes_key = None
        self.secret_key = None
        self.password_hash = None
        self.output_dir = Path.cwd()

        # Configure window
        self.title("NexControl Setup Wizard")
        self.geometry("650x650")
        self.resizable(False, False)

        # Set appearance
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.setup_ui()

    def setup_ui(self):
        """Build the setup wizard UI."""
        # Header
        header_frame = ctk.CTkFrame(self, height=80)
        header_frame.pack(fill="x", padx=20, pady=20)
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame,
            text="🔧 NexControl Setup Wizard",
            font=ctk.CTkFont(size=28, weight="bold")
        ).pack(pady=10)

        ctk.CTkLabel(
            header_frame,
            text="Securely configure your portable server",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        ).pack()

        # Scrollable content area
        self.scroll_frame = ctk.CTkScrollableFrame(self, height=450)
        self.scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # Step 1: Password Setup
        self.create_password_section()

        # Step 2: Progress info (initially hidden)
        self.progress_section = ctk.CTkFrame(self.scroll_frame)
        self.setup_complete_section = ctk.CTkFrame(self.scroll_frame)

        # Bottom button
        self.button_frame = ctk.CTkFrame(self, height=60)
        self.button_frame.pack(fill="x", padx=20, pady=10)
        self.button_frame.pack_propagate(False)

        self.setup_button = ctk.CTkButton(
            self.button_frame,
            text="✅ Complete Setup",
            command=self.complete_setup,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.setup_button.pack(pady=10)

    def create_password_section(self):
        """Create password setup section."""
        # Section title
        ctk.CTkLabel(
            self.scroll_frame,
            text="📝 Step 1: Create Admin Password",
            font=ctk.CTkFont(size=20, weight="bold")
        ).pack(pady=(0, 10), anchor="w")

        ctk.CTkLabel(
            self.scroll_frame,
            text="Create a strong password (12+ characters recommended)",
            text_color="gray"
        ).pack(pady=(0, 15), anchor="w")

        # Password frame
        password_frame = ctk.CTkFrame(self.scroll_frame)
        password_frame.pack(fill="x", pady=10)

        # Password field
        ctk.CTkLabel(password_frame, text="Password:").pack(anchor="w", padx=15, pady=(15, 5))
        self.password_entry = ctk.CTkEntry(password_frame, show="•", width=400, height=35)
        self.password_entry.pack(padx=15, pady=(0, 10))
        self.password_entry.focus()

        # Confirm password field
        ctk.CTkLabel(password_frame, text="Confirm Password:").pack(anchor="w", padx=15)
        self.confirm_entry = ctk.CTkEntry(password_frame, show="•", width=400, height=35)
        self.confirm_entry.pack(padx=15, pady=(0, 15))

        # Password strength indicator
        self.strength_label = ctk.CTkLabel(password_frame, text="", text_color="gray")
        self.strength_label.pack(anchor="w", padx=15, pady=(0, 10))

        # Info box
        info_frame = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", border_color="gray", border_width=1)
        info_frame.pack(fill="x", pady=15)

        info_text = """What happens next:

  1. Unique AES key and secret key will be generated
  2. Keys stored securely in Windows AppData (encrypted)
  3. AES key exported for mobile app setup (AES_KEY.txt, QR code)
  4. No sensitive files in portable folder"""

        ctk.CTkLabel(info_frame, text=info_text, justify="left").pack(padx=15, pady=10)

    def update_strength_indicator(self, value=None):
        """Update password strength indicator."""
        password = self.password_entry.get()
        if not password:
            self.strength_label.configure(text="")
            return

        length = len(password)
        if length < 8:
            text = "⚠️  Weak - Use 12+ characters for better security"
            color = "red"
        elif length < 12:
            text = "🟡 Medium - 12+ characters recommended"
            color = "yellow"
        else:
            text = "✅ Strong"
            color = "green"

        self.strength_label.configure(text=text, text_color=color)

    def complete_setup(self):
        """Complete the setup process."""
        # Validate password
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()

        if not password:
            self.show_error("Password cannot be empty")
            return

        if password != confirm:
            self.show_error("Passwords do not match")
            return

        if len(password) < 8:
            if not self.confirm_weak_password():
                return

        # Disable button and show progress
        self.setup_button.configure(state="disabled", text="⏳ Setting up...")

        # Generate keys
        try:
            self.aes_key = generate_aes_key()
            self.secret_key = generate_secret_key()
            self.password_hash = hash_password(password)

            # Save encrypted config to AppData
            if not save_config(self.aes_key, self.secret_key, self.password_hash):
                self.show_error("Failed to save configuration")
                self.setup_button.configure(state="normal", text="✅ Complete Setup")
                return

            # Export files for mobile app
            export_aes_key_text(self.aes_key, self.output_dir)
            export_aes_key_qr(self.aes_key, self.output_dir)
            export_setup_instructions(self.output_dir)

            # Show success screen
            self.show_success()

        except Exception as e:
            self.show_error(f"Setup failed: {str(e)}")
            self.setup_button.configure(state="normal", text="✅ Complete Setup")

    def confirm_weak_password(self) -> bool:
        """Show dialog to confirm weak password."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Warning")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        result = [False]

        ctk.CTkLabel(
            dialog,
            text="⚠️  Weak Password Warning",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="yellow"
        ).pack(pady=20)

        ctk.CTkLabel(
            dialog,
            text="Your password is less than 8 characters.\nContinue anyway?",
            text_color="gray"
        ).pack(pady=10)

        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(pady=20)

        def yes():
            result[0] = True
            dialog.destroy()

        def no():
            dialog.destroy()

        ctk.CTkButton(btn_frame, text="Yes, Continue", command=yes, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="No, Change It", command=no, width=120).pack(side="left", padx=5)

        dialog.wait_window()
        return result[0]

    def show_success(self):
        """Show success screen with AES key."""
        # Hide password section, show complete section
        for widget in self.scroll_frame.winfo_children():
            if widget not in [self.progress_section, self.setup_complete_section]:
                widget.pack_forget()

        # Create success UI
        ctk.CTkLabel(
            self.scroll_frame,
            text="✅ Setup Complete!",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="green"
        ).pack(pady=20)

        ctk.CTkLabel(
            self.scroll_frame,
            text="Your server has been configured securely",
            text_color="gray"
        ).pack(pady=(0, 20))

        # AES Key section
        key_frame = ctk.CTkFrame(self.scroll_frame)
        key_frame.pack(fill="x", pady=15)

        ctk.CTkLabel(
            key_frame,
            text="📱 Mobile App Encryption Key",
            font=ctk.CTkFont(size=18, weight="bold")
        ).pack(pady=(15, 10))

        ctk.CTkLabel(
            key_frame,
            text="Copy this key to your mobile app or scan AES_KEY_QR.png",
            text_color="gray"
        ).pack(pady=(0, 10))

        # Key entry (readonly)
        key_entry = ctk.CTkEntry(key_frame, width=450, height=35)
        key_entry.insert(0, self.aes_key)
        key_entry.configure(state="readonly")
        key_entry.pack(padx=15, pady=(0, 10))

        # Copy button
        ctk.CTkButton(
            key_frame,
            text="📋 Copy to Clipboard",
            command=self.copy_key_to_clipboard,
            width=200
        ).pack(pady=(0, 15))

        # Files created info
        files_frame = ctk.CTkFrame(self.scroll_frame)
        files_frame.pack(fill="x", pady=15)

        ctk.CTkLabel(
            files_frame,
            text="📁 Files Created",
            font=ctk.CTkFont(size=16, weight="bold")
        ).pack(pady=(15, 10))

        files_info = """• AES_KEY.txt - Copy key from here
• AES_KEY_QR.png - Scan with mobile app
• SETUP_INSTRUCTIONS.txt - Setup guide"""

        ctk.CTkLabel(files_frame, text=files_info, justify="left").pack(padx=15, pady=(0, 15))

        # Update button
        self.setup_button.configure(
            text="🚀 Launch Server",
            command=self.launch_server,
            fg_color="green",
            hover_color="darkgreen"
        )

    def copy_key_to_clipboard(self):
        """Copy AES key to clipboard."""
        self.clipboard_clear()
        self.clipboard_append(self.aes_key)
        self.update()  # Required for clipboard

    def launch_server(self):
        """Launch the server and close wizard."""
        self.destroy()
        if self.on_complete_callback:
            self.on_complete_callback()

    def show_error(self, message: str):
        """Show error message."""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Error")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="❌ Error",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="red"
        ).pack(pady=20)

        ctk.CTkLabel(dialog, text=message, text_color="gray").pack(pady=10)

        ctk.CTkButton(
            dialog,
            text="OK",
            command=dialog.destroy,
            width=100
        ).pack(pady=20)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
def run_setup_wizard(on_complete_callback=None):
    """
    Run the setup wizard.
    Returns True if setup completed successfully, False otherwise.
    """
    app = SetupWizard(on_complete_callback)
    app.mainloop()
    return True


def check_first_run() -> bool:
    """Check if this is the first run (no config exists)."""
    return load_config() is None


if __name__ == "__main__":
    # Test run
    if check_first_run():
        print("First run detected - launching setup wizard...")
        run_setup_wizard(lambda: print("Setup complete! Server can now start."))
    else:
        print("Config already exists. Server is ready to start.")
