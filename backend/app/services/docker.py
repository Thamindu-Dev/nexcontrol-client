
from docker import from_env
from docker.errors import DockerException
import logging
from app.core.config import settings, logger
from app.core.security import SecurityManager

class DockerManager:
    """
    Manage Docker containers
    Supports listing, starting, stopping, restarting containers
    """

    def __init__(self):
        """Initialize Docker client"""
        self.client = None
        self.available = False
        self._init_docker()

    def _init_docker(self):
        """Initialize Docker connection"""
        try:
            logger.info("Attempting to connect to Docker...")
            self.client = from_env()
            self.client.ping()
            self.available = True
            logger.info("Docker connection established successfully")
        except DockerException as e:
            logger.warning(f"Docker not available: {type(e).__name__} - {str(e)}")
            self.available = False
        except Exception as e:
            logger.error(f"Docker initialization error: {type(e).__name__} - {str(e)}")
            self.available = False

    def list_containers(self, all: bool = True) -> dict:
        """List all Docker containers"""
        if not self.available:
            logger.warning("Docker is not available, returning empty container list")
            return {"containers": []}

        try:
            logger.info(f"Listing Docker containers (all={all})")
            containers = self.client.containers.list(all=all)
            logger.info(f"Found {len(containers)} containers")
            result = []
            for idx, container in enumerate(containers):
                try:
                    # Get container status safely
                    status = "unknown"
                    try:
                        status = container.status
                    except Exception as status_err:
                        logger.warning(f"Error getting status for container {idx}: {status_err}")
                        status = "unable to get status"

                    # Get container name safely
                    container_name = "unknown"
                    try:
                        container_name = container.name
                    except Exception as name_err:
                        logger.warning(f"Error getting name for container {idx}: {name_err}")
                        container_name = f"container_{idx}"

                    # Get image name safely
                    image_name = "unknown"
                    try:
                        if container.image.tags:
                            image_name = container.image.tags[0]
                        else:
                            image_name = container.image.id[:12]
                    except Exception as img_err:
                        logger.warning(f"Error getting image for container {idx}: {img_err}")
                        image_name = "unknown"

                    result.append({
                        "id": container.short_id,
                        "name": SecurityManager.sanitize_input(container_name, max_length=256),
                        "image": SecurityManager.sanitize_input(image_name, max_length=256),
                        "status": SecurityManager.sanitize_input(status, max_length=64),
                        "state": "running" if status.lower().startswith("running") or status.lower().startswith("up") else "stopped"
                    })
                    logger.info(f"Container: {container_name} - {status}")
                except Exception as e:
                    logger.warning(f"Error reading container info for container {idx}: {type(e).__name__}: {str(e)}")
                    import traceback
                    logger.warning(traceback.format_exc())
                    continue
            logger.info(f"Returning {len(result)} containers")
            return {"containers": result}
        except Exception as e:
            logger.error(f"Error listing containers: {type(e).__name__}: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return {"containers": []}

    def start_container(self, container_id: str) -> dict:
        """Start a Docker container"""
        if not self.available:
            return {"success": False, "message": "Docker is not available"}

        if not SecurityManager.validate_container_id(container_id):
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
        """Stop a Docker container"""
        if not self.available:
            return {"success": False, "message": "Docker is not available"}

        if not SecurityManager.validate_container_id(container_id):
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
        """Restart a Docker container"""
        if not self.available:
            return {"success": False, "message": "Docker is not available"}

        if not SecurityManager.validate_container_id(container_id):
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
        """Get logs from a Docker container"""
        if not self.available:
            return {"success": False, "message": "Docker is not available"}

        if not SecurityManager.validate_container_id(container_id):
            return {"success": False, "message": "Invalid container ID format"}

        try:
            tail = max(1, min(10000, int(tail)))
        except (ValueError, TypeError):
            tail = 100

        try:
            container = self.client.containers.get(container_id)
            logs = container.logs(tail=tail).decode('utf-8', errors='replace')

            max_log_size = 10 * 1024 * 1024  # 10MB
            if len(logs) > max_log_size:
                logs = logs[-max_log_size:]
                logs = "... (truncated) ...\n" + logs

            return {"success": True, "logs": logs}
        except Exception as e:
            logger.error(f"Error getting logs: {type(e).__name__}")
            return {"success": False, "message": "Failed to get logs"}

    def get_status(self) -> dict:
        """Check if Docker is available"""
        if self.available:
            return {"available": True, "message": "Docker is available"}
        else:
            return {"available": False, "message": "Docker is not installed or not running"}
