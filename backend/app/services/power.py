
import os
import subprocess
import logging
import platform
import time

from app.core.config import settings, logger

class PowerManager:
    """
    Manage system power: Shutdown, Restart, Hibernate, Lock Screen
    """

    @staticmethod
    def shutdown(delay_seconds: int = 0) -> dict:
        """
        Shutdown the system
        
        Args:
            delay_seconds: Delay before shutdown (seconds)
        """
        try:
            logger.info(f"Shutdown requested with delay: {delay_seconds}s")
            
            if settings.OS_TYPE == "Windows":
                cmd = ["shutdown", "/s", "/t", str(delay_seconds)]
                # Use /f to force? Maybe safer not to unless requested.
                # Standard is /s /t
                result = subprocess.run(
                    cmd,
                    shell=False,  # Don't use shell for security
                    capture_output=True,
                    timeout=10
                )
            elif settings.OS_TYPE == "Linux":
                # Linux usually requires sudo or particular permissions
                # Using 'shutdown -h +minutes' or 'shutdown -h now'
                # Convert seconds to minutes roughly or sleep?
                # 'shutdown' command supports 'now' or '+m'
                time_arg = "now" if delay_seconds < 60 else f"+{delay_seconds//60}"
                cmd = ["shutdown", "-h", time_arg]
                
                # Check if running as root or has sudo
                # This might fail if not properly configured in sudoers
                if os.geteuid() != 0:
                    cmd.insert(0, "sudo")
                    
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            elif settings.OS_TYPE == "Darwin": # macOS
                time_arg = "now" if delay_seconds < 60 else f"+{delay_seconds//60}"
                cmd = ["shutdown", "-h", time_arg]
                if os.geteuid() != 0:
                    cmd.insert(0, "sudo")
                    
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            else:
                return {"success": False, "message": f"Unsupported OS: {settings.OS_TYPE}"}

            if result.returncode == 0:
                logger.info("Shutdown command received successfully")
                return {"success": True, "message": f"System shutting down in {delay_seconds} seconds"}
            else:
                error_msg = result.stderr.decode('utf-8').strip()
                logger.error(f"Shutdown failed: {error_msg}")
                return {"success": False, "message": f"Shutdown failed: {error_msg}"}
                
        except Exception as e:
            logger.error(f"Shutdown error: {type(e).__name__}")
            return {"success": False, "message": f"Shutdown failed: {str(e)}"}

    @staticmethod
    def restart(delay_seconds: int = 0) -> dict:
        """
        Restart the system
        
        Args:
            delay_seconds: Delay before restart (seconds)
        """
        try:
            logger.info(f"Restart requested with delay: {delay_seconds}s")
            
            if settings.OS_TYPE == "Windows":
                cmd = ["shutdown", "/r", "/t", str(delay_seconds)]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            elif settings.OS_TYPE == "Linux" or settings.OS_TYPE == "Darwin":
                time_arg = "now" if delay_seconds < 60 else f"+{delay_seconds//60}"
                cmd = ["shutdown", "-r", time_arg]
                
                if os.geteuid() != 0:
                    cmd.insert(0, "sudo")
                    
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            else:
                return {"success": False, "message": f"Unsupported OS: {settings.OS_TYPE}"}

            if result.returncode == 0:
                logger.info("Restart command received successfully")
                return {"success": True, "message": f"System restarting in {delay_seconds} seconds"}
            else:
                error_msg = result.stderr.decode('utf-8').strip()
                logger.error(f"Restart failed: {error_msg}")
                return {"success": False, "message": f"Restart failed: {error_msg}"}
                
        except Exception as e:
            logger.error(f"Restart error: {type(e).__name__}")
            return {"success": False, "message": f"Restart failed: {str(e)}"}

    @staticmethod
    def hibernate() -> dict:
        """Hibernate the system"""
        try:
            logger.info("Hibernate requested")
            
            if settings.OS_TYPE == "Windows":
                cmd = ["shutdown", "/h"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            elif settings.OS_TYPE == "Linux":
                # systemctl hibernate
                cmd = ["systemctl", "hibernate"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            elif settings.OS_TYPE == "Darwin":
                # macOS usually sleeps, hibernation is complex mode change (pmset)
                # Simulating sleep instead?
                cmd = ["pmset", "sleepnow"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            else:
                return {"success": False, "message": f"Unsupported OS: {settings.OS_TYPE}"}

            if result.returncode == 0:
                logger.info("Hibernate command successful")
                return {"success": True, "message": "System hibernating/sleeping"}
            else:
                error_msg = result.stderr.decode('utf-8').strip()
                logger.error(f"Hibernate failed: {error_msg}")
                return {"success": False, "message": f"Hibernate failed: {error_msg}"}
                
        except Exception as e:
            logger.error(f"Hibernate error: {type(e).__name__}")
            return {"success": False, "message": f"Hibernate failed: {str(e)}"}

    @staticmethod
    def lock_screen() -> dict:
        """Lock the screen"""
        try:
            logger.info("Lock screen requested")
            
            if settings.OS_TYPE == "Windows":
                cmd = ["rundll32.exe", "user32.dll,LockWorkStation"]
                # rundll32 returns immediately usually
                subprocess.Popen(cmd, shell=False)
            elif settings.OS_TYPE == "Linux":
                # Try common lock commands
                # Gnome
                try:
                    subprocess.run(["gnome-screensaver-command", "-l"], check=True)
                except:
                    try:
                        subprocess.run(["xdg-screensaver", "lock"], check=True)
                    except:
                        # Loginctl
                         subprocess.run(["loginctl", "lock-session"], check=True)
                         
            elif settings.OS_TYPE == "Darwin":
                cmd = ["pmset", "displaysleepnow"]
                result = subprocess.run(
                    cmd,
                    shell=False,
                    capture_output=True,
                    timeout=10
                )
            else:
                return {"success": False, "message": f"Unsupported OS: {settings.OS_TYPE}"}

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
            return {"success": False, "message": f"Lock screen failed: {str(e)}"}
