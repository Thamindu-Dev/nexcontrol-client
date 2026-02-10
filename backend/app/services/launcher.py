
import os
import subprocess
import logging
import json
import threading
from typing import Dict, List, Optional
from app.core.config import settings, logger

# Predefined applications list with platform-specific commands
AVAILABLE_APPS = {
    "windows": {
        "chrome": {"name": "Google Chrome","icon": "language","command": "chrome","args": ""},
        "edge": {"name": "Microsoft Edge","icon": "travel_explore","command": "msedge","args": ""},
        "firefox": {"name": "Mozilla Firefox","icon": "public","command": "firefox","args": ""},
        "notepad": {"name": "Notepad","icon": "edit_note","command": "notepad","args": ""},
        "calculator": {"name": "Calculator","icon": "calculate","command": "calc","args": ""},
        "spotify": {"name": "Spotify","icon": "music_note","command": "spotify","args": ""},
        "vscode": {"name": "VS Code","icon": "code","command": "code","args": ""},
        "explorer": {"name": "File Explorer","icon": "folder","command": "explorer","args": ""},
        "cmd": {"name": "Command Prompt","icon": "terminal","command": "cmd","args": "/c start cmd"},
        "powershell": {"name": "PowerShell","icon": "terminal","command": "powershell","args": "-NoExit"},
        "taskmgr": {"name": "Task Manager","icon": "analytics","command": "taskmgr","args": ""},
        "mspaint": {"name": "Paint","icon": "palette","command": "mspaint","args": ""}
    },
    "linux": {
        "chrome": {"name": "Google Chrome","icon": "language","command": "google-chrome","args": ""},
        "firefox": {"name": "Mozilla Firefox","icon": "public","command": "firefox","args": ""},
        "terminal": {"name": "Terminal","icon": "terminal","command": "gnome-terminal","args": ""},
        "files": {"name": "File Manager","icon": "folder","command": "nautilus","args": ""},
        "vscode": {"name": "VS Code","icon": "code","command": "code","args": ""},
        "spotify": {"name": "Spotify","icon": "music_note","command": "spotify","args": ""},
        "calculator": {"name": "Calculator","icon": "calculate","command": "gnome-calculator","args": ""},
        "gedit": {"name": "Text Editor","icon": "edit_note","command": "gedit","args": ""},
        "system_monitor": {"name": "System Monitor","icon": "analytics","command": "gnome-system-monitor","args": ""}
    },
    "darwin": {
        "chrome": {"name": "Google Chrome","icon": "language","command": "open","args": "-a 'Google Chrome'"},
        "firefox": {"name": "Mozilla Firefox","icon": "public","command": "open","args": "-a Firefox"},
        "safari": {"name": "Safari","icon": "public","command": "open","args": "-a Safari"},
        "finder": {"name": "Finder","icon": "folder","command": "open","args": "-a Finder"},
        "terminal": {"name": "Terminal","icon": "terminal","command": "open","args": "-a Terminal"},
        "vscode": {"name": "VS Code","icon": "code","command": "open","args": "-a 'Visual Studio Code'"},
        "spotify": {"name": "Spotify","icon": "music_note","command": "open","args": "-a Spotify"},
        "calculator": {"name": "Calculator","icon": "calculate","command": "open","args": "-a Calculator"},
        "notes": {"name": "Notes","icon": "edit_note","command": "open","args": "-a Notes"},
        "system_prefs": {"name": "System Preferences","icon": "settings","command": "open","args": "-a 'System Preferences'"}
    }
}

class AppLauncher:
    """
    App Launcher Service
    Manages custom apps and launching logic
    """

    def __init__(self):
        self.custom_apps: Dict[str, dict] = {}
        # Path for custom apps json, relative to backend root ideally
        self.config_file = os.path.join(os.getcwd(), "custom_apps.json")
        self._load_custom_apps()

    def _load_custom_apps(self):
        """Load custom apps from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    self.custom_apps = json.load(f)
                logger.info(f"Loaded {len(self.custom_apps)} custom apps")
            else:
                self.custom_apps = {}
        except Exception as e:
            logger.error(f"Failed to load custom apps: {e}")
            self.custom_apps = {}

    def save_custom_apps(self):
        """Save custom apps to file (async/threaded)"""
        try:
            def save_to_file():
                try:
                    with open(self.config_file, "w") as f:
                        json.dump(self.custom_apps, f, indent=2)
                    logger.info(f"Saved {len(self.custom_apps)} custom apps to file")
                except Exception as e:
                    logger.error(f"Failed to save custom apps: {e}")

            thread = threading.Thread(target=save_to_file, daemon=True)
            thread.start()

        except Exception as e:
            logger.error(f"Failed to initiate custom apps save: {e}")

    def get_platform_apps(self) -> dict:
        """Get available applications for current platform"""
        if settings.OS_TYPE == "Windows":
            return AVAILABLE_APPS.get("windows", {})
        elif settings.OS_TYPE == "Linux":
            return AVAILABLE_APPS.get("linux", {})
        elif settings.OS_TYPE == "Darwin":
            return AVAILABLE_APPS.get("darwin", {})
        else:
            return AVAILABLE_APPS.get("windows", {})

    def get_all_apps(self) -> list:
        """Get integrated list of all apps (predefined + custom)"""
        apps = self.get_platform_apps()
        app_list = []

        # Predefined
        for app_id, app_info in apps.items():
            app_list.append({
                "id": app_id,
                "name": app_info["name"],
                "icon": app_info["icon"],
                "command": app_info["command"],
                "args": app_info["args"],
                "type": "predefined"
            })

        # Custom
        for app_id, app_info in self.custom_apps.items():
            app_list.append({
                "id": app_id,
                "name": app_info["name"],
                "icon": app_info.get("icon", "apps"),
                "type": app_info.get("type", "local"),
                "path": app_info.get("path", ""),
                "url": app_info.get("url", ""),
                "is_custom": True
            })

        return app_list

    def add_custom_app(self, name: str, app_type: str, path: str = None, url: str = None, icon: str = "apps", user: str = "unknown") -> dict:
        """Add a custom app"""
        import uuid
        app_id = f"custom_{uuid.uuid4().hex[:8]}"
        
        self.custom_apps[app_id] = {
            "name": name,
            "type": app_type,
            "path": path or "",
            "url": url or "",
            "icon": icon,
            "created_by": user
        }
        self.save_custom_apps()
        return {"app_id": app_id, "app": self.custom_apps[app_id]}

    def delete_custom_app(self, app_id: str) -> bool:
        if app_id in self.custom_apps:
            del self.custom_apps[app_id]
            self.save_custom_apps()
            return True
        return False

    def launch_app(self, app_id: str, user: str = "unknown") -> dict:
        """Launch an application"""
        try:
            # Get user's home directory to use as working directory
            # This ensures apps open in the user's home folder instead of backend directory
            home_dir = os.path.expanduser("~")
            logger.info(f"Using home directory as cwd: {home_dir}")

            # Check custom apps
            if app_id in self.custom_apps:
                app_info = self.custom_apps[app_id]
                app_type = app_info.get("type", "local")

                if app_type == "web":
                    url = app_info.get("url", "")
                    import webbrowser
                    webbrowser.open(url)
                    logger.info(f"Launched web app: {app_info['name']} -> {url} by user {user}")
                    return {"success": True, "message": f"Opened {app_info['name']} in browser"}
                else:
                    app_path = app_info.get("path", "")
                    if settings.OS_TYPE == "Windows":
                        subprocess.Popen([app_path], shell=True, cwd=home_dir)
                    elif settings.OS_TYPE == "Darwin":
                        subprocess.Popen(["open", app_path], cwd=home_dir)
                    else:
                        subprocess.Popen([app_path], cwd=home_dir)

                    logger.info(f"Launched custom app: {app_info['name']} -> {app_path} by user {user}")
                    return {"success": True, "message": f"Launched {app_info['name']}"}

            # Predefined apps
            apps = self.get_platform_apps()
            if app_id not in apps:
                return {"success": False, "message": f"Unknown application: {app_id}"}

            app_info = apps[app_id]
            command = app_info["command"]
            args = app_info["args"]

            if settings.OS_TYPE == "Windows":
                # Use 'start /d' to set working directory for Windows
                full_command = f"start /d \"{home_dir}\" {command}"
                if args:
                    full_command += f" {args}"
                subprocess.Popen(full_command, shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
            elif settings.OS_TYPE == "Darwin":
                full_command = f"{command} {args}".strip()
                subprocess.Popen(full_command, shell=True, cwd=home_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                full_command = f"{command} {args}".strip()
                subprocess.Popen(full_command.split(), cwd=home_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            logger.info(f"Launched application: {app_info['name']} ({app_id}) by user {user}")
            return {"success": True, "message": f"Launched {app_info['name']}"}

        except FileNotFoundError:
            return {"success": False, "message": f"Application '{app_id}' is not installed"}
        except Exception as e:
            logger.error(f"Failed to launch: {e}")
            return {"success": False, "message": f"Failed to launch: {str(e)}"}
