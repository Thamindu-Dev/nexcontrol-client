#!/usr/bin/env python3
"""
 =============================================================================
 NexControl System Tray Manager
 =============================================================================
 Provides system tray functionality for the portable server.

 Features:
 - Minimize to system tray
 - Show/Hide console window
 - Quick access to key features
 - Server status indicator
 - Clean exit option
 =============================================================================
"""

import os
import sys
import threading
import subprocess
from pathlib import Path

# Try to import system tray dependencies
try:
    import pystray
except ImportError as e:
    print(f"[!] System tray feature requires pystray: {e}")
    print("[!] Run: pip install pystray")
    sys.exit(1)

# PIL for icon generation (optional, will use fallback if not available)
try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    print("[!] Warning: PIL not installed. Icons will use fallback.")
    PIL_AVAILABLE = False


# =============================================================================
# CONFIGURATION
# =============================================================================
TRAY_ICON_WIDTH = 64
TRAY_ICON_HEIGHT = 64
BG_COLOR = "white"
ICON_COLOR = "#1a1a1a"  # Dark gray
ACCENT_COLOR = "#00d4ff"  # Cyan

SERVER_RUNNING = "Server: Running"
SERVER_STOPPED = "Server: Stopped"
SERVER_STARTING = "Server: Starting..."


# =============================================================================
# TRAY ICON GENERATION
# =============================================================================
def create_icon(text: str, width: int = 64, height: int = 64):
    """
    Create a system tray icon with custom text.

    Args:
        text: Text to display on the icon
        width: Icon width
        height: Icon height

    Returns:
        PIL Image object
    """
    if not PIL_AVAILABLE:
        # Fallback: create a simple colored image
        return create_simple_icon(text, width, height)

    # Create image with white background
    img = Image.new('RGB', (width, height), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Draw circle border
    margin = 2
    draw.ellipse([margin, margin, width - margin, height - margin],
                 outline=ACCENT_COLOR, width=3)

    # Draw text
    try:
        # Try to use a nice font
        font = ImageFont.truetype("arial.ttf", max(12, width // 4))
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Center text
    if text:
        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        position = ((width - text_width) // 2, (height - text_height) // 2)
        draw.text(position, text, fill=ICON_COLOR, font=font)

    return img


def create_simple_icon(text: str, width: int = 64, height: int = 64):
    """
    Create a simple icon without PIL (fallback).
    Returns a placeholder icon - in production, pystray needs PIL.
    """
    # This is a fallback - in real usage, PIL will be available
    # We return a small 1x1 PNG as placeholder
    import base64

    # Very small 1x1 PNG with blue pixel
    png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+HwAAAABJRU5ErkJggg=="
    return base64.b64decode(png_base64)


# =============================================================================
# SYSTEM TRAY MANAGER
# =============================================================================
class SystemTrayManager:
    """
    Manages the system tray icon and menu for NexControl.
    """

    def __init__(self, exe_path: Path = None):
        """
        Initialize the system tray manager.

        Args:
            exe_path: Path to the NexControl executable
        """
        self.exe_path = exe_path or Path(sys.executable)
        self.icon = None
        self.tray = None
        self.running = False
        self.server_process = None
        self.console_window = None

        # Menu state
        self.server_running = False
        self.console_visible = True

    def create_menu(self):
        """Create the context menu for the tray icon."""
        return pystray.Menu(
            pystray.MenuItem("NexControl Server", None, default=True),
            pystray.MenuItem("Server Status", self.toggle_status, checked=self._get_server_status),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Show Console", self.show_console, visible=lambda item: not self.console_visible),
            pystray.MenuItem("Hide Console", self.hide_console, visible=lambda item: self.console_visible),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Open Web Interface", self.open_web_interface),
            pystray.MenuItem("Show Encryption Key", self.show_encryption_key),
            pystray.MenuItem("Check for Updates", self.check_for_updates),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Stop Server", self.stop_server),
            pystray.MenuItem("Exit", self.exit_application),
        )

    def _get_server_status(self, *args):
        """Get current server status for menu."""
        return self.server_running

    def start(self):
        """Start the system tray icon."""
        if self.running:
            return

        try:
            # Set Title for easier finding
            try:
                import ctypes
                ctypes.windll.kernel32.SetConsoleTitleW("NexControl Server Console")
            except:
                pass

            # Create icon
            icon_image = create_icon("N")

            # Create menu
            menu = self.create_menu()

            # Create tray icon
            self.icon = pystray.Icon(
                "NexControl",
                icon_image,
                "NexControl Server",
                menu
            )

            # Start tray in background thread
            self.running = True
            self.tray = self.icon

            # Run in separate thread
            tray_thread = threading.Thread(target=self._run_tray, daemon=True)
            tray_thread.start()

            # Monitor console state (auto-hide on minimize)
            monitor_thread = threading.Thread(target=self.monitor_console, daemon=True)
            monitor_thread.start()

        except Exception as e:
            print(f"[!] Failed to start system tray: {e}")

    def _run_tray(self):
        """Run the system tray loop."""
        try:
            self.icon.run()
        except KeyboardInterrupt:
            self.stop()

    def monitor_console(self):
        """
        Monitor the console window state.
        If the user minimizes the window, automatically hide it to tray.
        """
        import time
        import ctypes
        
        while self.running:
            try:
                # Only check if we think it's visible
                if self.console_visible:
                    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
                    if hwnd:
                        # Check if minimized (IsIconic returns non-zero if minimized)
                        if ctypes.windll.user32.IsIconic(hwnd):
                            # Hide the window
                            ctypes.windll.user32.ShowWindow(hwnd, 0) # SW_HIDE
                            self.console_visible = False
                            
                            # Update menu to show 'Show Console'
                            if self.icon:
                                self.icon.update_menu()
                
                time.sleep(0.5)
            except Exception as e:
                # Don't log continuously if error persists
                pass
                time.sleep(2)

    def stop(self):
        """Stop the system tray icon."""
        if self.icon:
            self.icon.stop()
            self.running = False

    def update_status(self, running: bool):
        """
        Update the server status in the menu.

        Args:
            running: Whether the server is running
        """
        self.server_running = running
        self.console_visible = True

        # Update icon text
        try:
            status_text = "RUN" if running else "STOP"
            new_icon = create_icon(status_text)
            self.icon.icon = new_icon
        except:
            pass

    # ============================================================
    # MENU CALLBACKS
    # ============================================================

    def toggle_status(self):
        """Toggle server status (menu callback)."""
        if self.server_running:
            self.stop_server()
        else:
            self.start_server()

    def start_server(self):
        """Start the server."""
        if self.server_running:
            print("[*] Server is already running")
            return

        try:
            # Start the executable
            if self.exe_path.exists():
                self.server_process = subprocess.Popen(
                    [str(self.exe_path)],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,
                    close_fds=True
                )
                self.server_running = True
                self.update_status(True)
                print("[+] Server started from system tray")

        except Exception as e:
            print(f"[!] Failed to start server: {e}")

    def stop_server(self):
        """Stop the server."""
        if not self.server_running:
            print("[*] Server is not running")
            return

        try:
            if self.server_process:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.server_running = False
                self.update_status(False)
                print("[+] Server stopped from system tray")

        except Exception as e:
            print(f"[!] Failed to stop server: {e}")


    def toggle_console(self):
        """Show/hide console window (menu callback)."""
        try:
            import ctypes
            import time

            # Define Windows API constants
            SW_HIDE = 0
            SW_SHOW = 5
            SW_RESTORE = 9
            
            # Get console window handle
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()

            if hwnd:
                if self.console_visible:
                    # Hide the console
                    ctypes.windll.user32.ShowWindow(hwnd, SW_HIDE)
                    self.console_visible = False
                else:
                    # Show and restore the console
                    ctypes.windll.user32.ShowWindow(hwnd, SW_SHOW)
                    ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
                    ctypes.windll.user32.SetForegroundWindow(hwnd)
                    self.console_visible = True
            
            # Update the tray menu
            if self.icon:
                self.icon.update_menu()
                
        except Exception as e:
            print(f"Error toggling console: {e}")

    def minimize_to_tray(self):
        """Minimize console to tray (menu callback)."""
        # Always hide the console when this is called
        if self.console_visible:
            self.toggle_console()

    def show_console(self):
        """Show the console window (menu callback)."""
        if not self.console_visible:
            self.toggle_console()

    def hide_console(self):
        """Hide the console window (menu callback)."""
        if self.console_visible:
            self.toggle_console()

    def open_web_interface(self):
        """Open the web interface in browser (menu callback)."""
        import webbrowser
        try:
            webbrowser.open("http://localhost:8000")
            print("[+] Opening web interface...")
        except Exception as e:
            print(f"[!] Failed to open browser: {e}")

    def show_encryption_key(self):
        """Show the AES encryption key (menu callback)."""
        try:
            import win32crypt
            import json
            import pathlib

            # Load DPAPI config
            config_file = pathlib.Path(os.getenv('LOCALAPPDATA')) / 'NexControl' / 'config.dat'

            if config_file.exists():
                encrypted_data = config_file.read_bytes()
                decrypted = win32crypt.CryptUnprotectData(encrypted_data)
                config = json.loads(decrypted[1].decode('utf-8'))

                # Show key in dialog
                self._show_key_dialog(config.get('AES_KEY', 'Not found'))
            else:
                self._show_key_dialog("No config found. Run setup first.")
        except ImportError:
            self._show_key_dialog("System tray requires pywin32. Run: pip install pywin32")
        except Exception as e:
            self._show_key_dialog(f"Failed to load key: {e}")

    def _show_key_dialog(self, aes_key: str):
        """Show dialog with the encryption key."""
        try:
            import win32gui
            import win32con

            # Create a simple message box
            msg = f"NexControl Encryption Key:\n\n{aes_key}\n\n(This key has been copied to your clipboard)"

            # Copy to clipboard
            import win32clipboard
            win32clipboard.SetClipboardText(aes_key)

            # Show message box
            win32gui.MessageBoxW(
                0,
                msg,
                "NexControl Encryption Key",
                0  # MB_OK
            )
        except:
            # Fallback: print to console
            print(f"\n{'=' * 50}")
            print("NexControl Encryption Key:")
            print(f"{aes_key}")
            print(f"{'=' * 50}\n")

    def check_for_updates(self):
        """Check for application updates (menu callback)."""
        try:
            import requests
            
            # Call local API
            response = requests.get("http://localhost:8000/api/update/check", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                current = data.get("current_version", "Unknown")
                latest = data.get("latest_version", "Unknown")
                available = data.get("update_available", False)
                download_url = data.get("download_url", "")
                
                if available:
                    msg = (
                        f"🆕 Update Available!\n\n"
                        f"Current Version: v{current}\n"
                        f"Latest Version: v{latest}\n\n"
                        f"Download from GitHub:\n{download_url}\n\n"
                        f"Release Notes:\n{data.get('release_notes', 'N/A')[:200]}..."
                    )
                    title = "NexControl - Update Available"
                else:
                    msg = f"✅ You're up to date!\n\nCurrent Version: v{current}"
                    title = "NexControl - No Updates"
                
                # Show message box
                try:
                    import win32gui
                    win32gui.MessageBoxW(0, msg, title, 0)
                except:
                    print(f"\n{'=' * 50}")
                    print(msg)
                    print(f"{'=' * 50}\n")
            else:
                raise Exception(f"API returned status {response.status_code}")
                
        except Exception as e:
            error_msg = f"Failed to check for updates:\n{str(e)}\n\nPlease check your internet connection."
            try:
                import win32gui
                win32gui.MessageBoxW(0, error_msg, "NexControl - Update Check Failed", 0)
            except:
                print(f"\n[!] {error_msg}\n")

    def exit_application(self):
        """Exit the application (menu callback)."""
        if self.server_running:
            self.stop_server()

        self.stop()
        print("[+] Exiting NexControl...")
        sys.exit(0)


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================
if __name__ == "__main__":
    # Test the system tray
    tray = SystemTrayManager()
    tray.start()

    print("[+] System tray started. Press Ctrl+C to exit.")
    print("[+] Use the tray icon to control the server.")

    try:
        input()
    except KeyboardInterrupt:
        print("\n[+] Shutting down...")
        tray.stop()
