
import logging
import platform
import time
import psutil
from app.core.config import settings, logger

# PyAutoGUI for Global Media Keys
try:
    import pyautogui
    # Fail-safe to prevent uncontrollable mouse logic
    pyautogui.FAILSAFE = True
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    logger.warning("pyautogui not installed - Screenshot Service and Global Media Keys disabled")
except Exception as e:
    PYAUTOGUI_AVAILABLE = False
    logger.warning(f"pyautogui initialization failed (headless?): {e}")


# Supported media applications and their process names
MEDIA_APPS = {
    "spotify": ["Spotify.exe", "spotify.exe"],
    "vlc": ["vlc.exe", "VLC.exe"],
    "chrome": ["chrome.exe", "Chrome.exe"],
    "firefox": ["firefox.exe", "Firefox.exe"],
    "edge": ["msedge.exe", "MicrosoftEdge.exe"],
    "youtube_music": ["Chrome.exe"],  # Web app
    "windows_media_player": ["wmplayer.exe"],
    "groove": ["GrooveMusic.exe", "Microsoft.ZuneMusic.exe"],
    "itunes": ["iTunes.exe"],
    "potplayer": ["PotPlayerMini.exe", "PotPlayer.exe"],
    "kmplayer": ["KMPlayer.exe"],
}

class MediaController:
    """
    Media playback controller supporting both global and targeted window control
    """

    @staticmethod
    def get_media_apps():
        """Scan running processes and return list of supported media apps"""
        available_apps = ["Default (Global)"]

        try:
            for proc in psutil.process_iter(['name']):
                try:
                    proc_name = proc.info['name']
                    if not proc_name:
                        continue

                    for app_name, process_names in MEDIA_APPS.items():
                        if proc_name in process_names:
                            display_name = app_name.replace("_", " ").title()
                            if display_name not in available_apps:
                                available_apps.append(display_name)
                            break
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logger.error(f"Error scanning media apps: {e}")

        return available_apps

    @staticmethod
    def send_media_command(app_name: str, action: str):
        """Send media command to specified app"""
        try:
            logger.info(f"MediaController.send_media_command() called with app='{app_name}', action='{action}'")

            app_key = app_name.lower().replace(" ", "_")
            logger.info(f"Normalized app_key: {app_key}")

            if app_name == "Default (Global)" or app_key not in MEDIA_APPS:
                logger.info("Using GLOBAL media keys (affects active window)")
                return MediaController._send_global_command(action)
            else:
                logger.info(f"Using TARGETED media keys for app: {app_key}")
                return MediaController._send_targeted_command(app_key, action)

        except Exception as e:
            logger.error(f"Media control error: {e}")
            return {
                "success": False,
                "message": f"Failed to send command: {str(e)}"
            }

    @staticmethod
    def _send_global_command(action: str):
        """Send global media key command using pyautogui"""
        try:
            if not PYAUTOGUI_AVAILABLE:
                logger.error("pyautogui is not available - cannot send media keys")
                return {
                    "success": False,
                    "message": "Media control not available (pyautogui not installed or headless system)"
                }

            key_map = {
                "playpause": "playpause",
                "next": "nexttrack",
                "prev": "prevtrack",
                "volumeup": "volumeup",
                "volumedown": "volumedown",
                "volumemute": "volumemute"
            }

            if action not in key_map:
                logger.error(f"Unknown action: {action}")
                return {
                    "success": False,
                    "message": f"Unknown action: {action}"
                }

            original_failsafe = pyautogui.FAILSAFE
            pyautogui.FAILSAFE = False

            try:
                presses = 5 if action in ["volumeup", "volumedown"] else 1
                pyautogui.press(key_map[action], presses=presses, interval=0.05)
            finally:
                pyautogui.FAILSAFE = original_failsafe

            logger.info(f"Sent global media command: {action}")
            return {
                "success": True,
                "message": f"Global {action} command sent"
            }

        except Exception as e:
            logger.error(f"Global command error: {type(e).__name__}: {e}")
            return {
                "success": False,
                "message": f"Failed to send global command: {str(e)}"
            }

    @staticmethod
    def _send_targeted_command(app_key: str, action: str):
        """Send media command to specific application window"""
        try:
            if settings.OS_TYPE != "Windows":
                return {
                    "success": False,
                    "message": "Targeted control only available on Windows"
                }

            import win32gui
            import win32process
            import win32con
            from ctypes import windll

            target_hwnd = None
            process_names = MEDIA_APPS.get(app_key, [])

            def callback(hwnd, windows):
                nonlocal target_hwnd
                if target_hwnd is not None:
                    return

                if win32gui.IsWindowVisible(hwnd):
                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                    try:
                        proc = psutil.Process(pid)
                        if proc.name() in process_names:
                            target_hwnd = hwnd
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                return True

            win32gui.EnumWindows(callback, [])

            if not target_hwnd:
                return {
                    "success": False,
                    "message": f"Could not find window for {app_key}"
                }

            chrome_shortcuts = {
                "playpause": 0x4B,   # VK_K
                "next": 0x4C,        # VK_L
                "prev": 0x4A,        # VK_J
            }

            app_commands = {
                "playpause": 0xE0000,
                "next": 0xE0001,
                "prev": 0xE0002,
                "volumeup": 0xE0005,
                "volumedown": 0xE0006,
                "volumemute": 0xE0007
            }

            if action not in app_commands:
                return {
                    "success": False,
                    "message": f"Unknown action: {action}"
                }

            try:
                windll.user32.ShowWindow(target_hwnd, win32con.SW_RESTORE)
                windll.user32.SetForegroundWindow(target_hwnd)
                time.sleep(0.05)
            except:
                pass

            if app_key == "chrome" and action in chrome_shortcuts:
                import win32api
                VK_KEY = chrome_shortcuts[action]
                scan_code = win32api.MapVirtualKey(VK_KEY, 0)

                windll.user32.PostMessageW(
                    target_hwnd,
                    win32con.WM_KEYDOWN,
                    VK_KEY,
                    scan_code | (0 << 16)
                )

                windll.user32.PostMessageW(
                    target_hwnd,
                    win32con.WM_KEYUP,
                    VK_KEY,
                    scan_code | (1 << 31)
                )

                return {
                    "success": True,
                    "message": f"Sent {action} to Chrome (keyboard shortcut)"
                }

            WM_APPCOMMAND = 0x0319
            win32gui.PostMessage(
                target_hwnd,
                WM_APPCOMMAND,
                0,
                app_commands[action] * 65536
            )

            logger.info(f"Sent targeted {action} command to {app_key}")
            return {
                "success": True,
                "message": f"Sent {action} to {app_key.replace('_', ' ').title()}"
            }

        except ImportError:
            return {
                "success": False,
                "message": "pywin32 required for targeted control"
            }
        except Exception as e:
            logger.error(f"Targeted command error: {e}")
            return {
                "success": False,
                "message": f"Failed to send targeted command: {str(e)}"
            }
