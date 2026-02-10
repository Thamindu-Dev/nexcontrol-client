
import psutil
import logging
from app.core.config import settings, logger
from app.core.security import SecurityManager

class ProcessManager:
    """
    Manage system processes
    Supports listing processes sorted by resource usage
    and killing processes by PID
    """

    # List of critical PIDs that should not be killed
    PROTECTED_PIDS = {
        0,    # Idle process
        1,    # Init/systemd
        2,    # kthreadd
    }

    @staticmethod
    def list_processes(limit: int = 30, sort_by: str = "cpu") -> list:
        """List top resource-consuming processes"""
        try:
            limit = max(1, min(100, int(limit)))
            sort_by = sort_by.lower()
            if sort_by not in ["cpu", "memory"]:
                sort_by = "cpu"

            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'username']):
                try:
                    with proc.oneshot():
                        # Use cpu_percent without interval for cached/non-blocking value
                        # interval=None returns cached value immediately
                        cpu_pct = proc.cpu_percent(interval=None)

                        proc_info = {
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'username': proc.info['username'],
                            'cpu_percent': cpu_pct,
                            'memory_percent': proc.memory_percent()
                        }

                        # Sanitize
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

            # Sort
            if sort_by == "cpu":
                processes.sort(key=lambda x: x.get('cpu_percent', 0), reverse=True)
            elif sort_by == "memory":
                processes.sort(key=lambda x: x.get('memory_percent', 0), reverse=True)

            return processes[:limit]

        except Exception as e:
            logger.error(f"Error listing processes: {type(e).__name__}")
            return []

    @staticmethod
    def kill_process(pid: int, current_user: str = None) -> dict:
        """Kill a process by PID with ownership checking"""
        if not SecurityManager.validate_pid(pid):
            return {"success": False, "message": "Invalid PID"}

        if pid in ProcessManager.PROTECTED_PIDS:
            return {"success": False, "message": "Cannot kill critical system process"}

        try:
            proc = psutil.Process(pid)
            name = SecurityManager.sanitize_input(proc.name(), max_length=128)

            # Check ownership - only allow killing own processes
            try:
                proc_username = proc.username()
                if current_user:
                    # Normalize usernames for comparison (handles DOMAIN\user format on Windows)
                    current_normalized = current_user.split('\\')[-1].lower()
                    proc_normalized = proc_username.split('\\')[-1].lower()

                    if current_normalized != proc_normalized:
                        logger.warning(f"Attempt to kill process owned by another user: {name} (PID: {pid}, owner: {proc_username}, attempted by: {current_user})")
                        return {"success": False, "message": "Cannot kill processes owned by other users"}
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass

            # Additional protection: don't kill critical system processes
            if settings.OS_TYPE == "Linux":
                try:
                    cmdline = proc.cmdline()
                    if cmdline and any('kernel' in str(c).lower() or 'systemd' in str(c).lower() for c in cmdline):
                        return {"success": False, "message": "Cannot kill critical system process"}
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass
            elif settings.OS_TYPE == "Windows":
                try:
                    # Check if parent is services.exe or csrss.exe (system processes)
                    parent = proc.parent()
                    if parent:
                        parent_name = parent.name().lower()
                        if parent_name in ['services.exe', 'csrss.exe', 'wininit.exe', 'lsass.exe']:
                            return {"success": False, "message": "Cannot kill system service process"}
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    pass

            proc.kill()
            logger.info(f"Process killed: {name} (PID: {pid})")
            return {"success": True, "message": f"Process '{name}' (PID: {pid}) killed"}

        except psutil.NoSuchProcess:
            return {"success": False, "message": f"Process with PID {pid} not found"}
        except psutil.AccessDenied:
            return {"success": False, "message": f"Access denied to process {pid}"}
        except Exception as e:
            logger.error(f"Error killing process {pid}: {type(e).__name__}")
            return {"success": False, "message": "Failed to kill process"}

    @staticmethod
    def get_process_details(pid: int) -> dict:
        """Get detailed information about a process"""
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
                ][:32]
            except (psutil.AccessDenied, psutil.NoSuchProcess, Exception):
                details["cmdline"] = []

            return details

        except psutil.NoSuchProcess:
            return {"error": f"Process with PID {pid} not found"}
        except Exception as e:
            logger.error(f"Error getting process details: {type(e).__name__}")
            return {"error": "Failed to get process details"}
