
import time
import psutil
import platform
import logging

# Try to use NVIDIA's official NVML library (supports RTX 40-series)
try:
    import pynvml
    HAS_NVIDIA_GPU = True
except ImportError:
    HAS_NVIDIA_GPU = False
    try:
        # Fallback to GPUtil for older systems
        import GPUtil
        HAS_GPU_UTIL = True
    except ImportError:
        HAS_GPU_UTIL = False

from app.core.config import settings, logger

class SystemMonitor:
    """
    Monitor system resources: CPU, Memory, Disk, Network, GPU
    """

    @staticmethod
    def get_cpu_usage() -> dict:
        """Get CPU usage statistics"""
        try:
            # interval=0.1 ensures accurate reading, not 0
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_freq = psutil.cpu_freq()

            # Structure matching frontend expectations
            stats = {
                "cpu_percent": cpu_percent,
                "cpu_count": psutil.cpu_count(logical=True),
                "cpu_freq_mhz": round((cpu_freq.current if cpu_freq else 0) / 1000, 2) if cpu_freq else 0,
                "cpu_freq_current": round(cpu_freq.current, 2) if cpu_freq else 0,
                "temperature": SystemMonitor._get_cpu_temp()
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting CPU stats: {type(e).__name__}")
            return {"error": "Failed to get CPU stats"}

    @staticmethod
    def _get_cpu_temp() -> float:
        """Get CPU temperature (OS dependent implementation)"""
        try:
            if settings.OS_TYPE == "Linux":
                temps = psutil.sensors_temperatures()
                if "coretemp" in temps:
                    return temps["coretemp"][0].current
                elif "k10temp" in temps:  # AMD
                    return temps["k10temp"][0].current
            elif settings.OS_TYPE == "Windows":
                # Windows doesn't expose CPU temp via psutil directly without heavy wmi/admin rights usually
                # Need external library or more complex WMI query. 
                # For now returning 0 or placeholder.
                pass
            elif settings.OS_TYPE == "Darwin": # macOS
                 # macOS requires elevated privileges or specific tools
                 pass
                 
            return 0.0
        except Exception:
            return 0.0

    @staticmethod
    def get_memory_usage() -> dict:
        """Get Memory usage statistics"""
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()

            # Structure matching frontend expectations
            return {
                "total": mem.total,
                "available": mem.available,
                "used": mem.used,
                "free": mem.available,
                "percent": mem.percent,
                "swap_total": swap.total,
                "swap_used": swap.used,
                "swap_percent": swap.percent
            }
        except Exception as e:
            logger.error(f"Error getting Memory stats: {type(e).__name__}")
            return {"error": "Failed to get Memory stats"}

    @staticmethod
    def get_disk_usage() -> dict:
        """Get Disk usage statistics (primary partition)"""
        try:
            partitions = psutil.disk_partitions()

            # Get primary partition (C: on Windows, / on Linux)
            primary_partition = None
            if settings.OS_TYPE == "Windows":
                for partition in partitions:
                    if partition.device and partition.device.startswith(('C:', 'c:')):
                        primary_partition = partition
                        break
            else:
                for partition in partitions:
                    if partition.mountpoint == '/':
                        primary_partition = partition
                        break

            # Fallback to first partition if primary not found
            if not primary_partition and partitions:
                primary_partition = partitions[0]

            if primary_partition:
                usage = psutil.disk_usage(primary_partition.mountpoint)
                return {
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.percent,
                    "device": primary_partition.device,
                    "mountpoint": primary_partition.mountpoint,
                    "fstype": primary_partition.fstype
                }
            else:
                # No partitions found
                return {
                    "total": 0,
                    "used": 0,
                    "free": 0,
                    "percent": 0
                }
        except Exception as e:
            logger.error(f"Error getting Disk stats: {type(e).__name__}")
            return {"error": "Failed to get Disk stats"}

    @staticmethod
    def get_all_disks() -> dict:
        """Get all attached storage devices"""
        try:
            partitions = psutil.disk_partitions(all=True)
            disks = []

            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)

                    # Determine type (roughly)
                    is_removable = "removable" in partition.opts or "cdrom" in partition.opts
                    drive_type = "Internal"

                    # On Windows, try to determine drive type
                    if settings.OS_TYPE == "Windows":
                        if partition.device and len(partition.device) >= 2:
                            drive_letter = partition.device[0].upper()
                            # Try to get drive type using Windows API if possible
                            # For now, use simple heuristics
                            if is_removable:
                                drive_type = "External"

                    disks.append({
                        "device": partition.device,
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "opts": partition.opts,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": usage.percent,
                        "is_removable": is_removable,
                        "drive_type": drive_type
                    })
                except Exception:
                    continue

            return {"disks": disks}

        except Exception as e:
            logger.error(f"Error getting all disks: {type(e).__name__}")
            return {"disks": []}

    @staticmethod
    def get_gpu_usage() -> dict:
        """Get GPU usage statistics using NVML (preferred) or GPUtil (fallback)"""
        # Try NVML first (NVIDIA official library, supports RTX 40-series)
        if HAS_NVIDIA_GPU:
            try:
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()

                if device_count > 0:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)

                    # Get GPU name
                    name = pynvml.nvmlDeviceGetName(handle)
                    if isinstance(name, bytes):
                        name = name.decode('utf-8')

                    # Get utilization
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    gpu_percent = utilization.gpu

                    # Get memory info
                    mem_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    memory_total = mem_info.total
                    memory_used = mem_info.used
                    memory_percent = round((memory_used / memory_total) * 100, 1) if memory_total > 0 else 0

                    # Get temperature
                    try:
                        temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    except:
                        temperature = 0

                    pynvml.nvmlShutdown()

                    return {
                        "usage_percent": gpu_percent,
                        "name": name,
                        "temperature": temperature,
                        "memory_total": memory_total,
                        "memory_used": memory_used,
                        "memory_percent": memory_percent
                    }
            except Exception as e:
                logger.warning(f"Error reading GPU stats via NVML: {str(e)}")

        # Fallback to GPUtil
        if HAS_GPU_UTIL:
            try:
                available_gpus = GPUtil.getGPUs()
                if available_gpus:
                    gpu = available_gpus[0]  # Use first GPU
                    return {
                        "usage_percent": round(gpu.load * 100, 1),
                        "name": gpu.name,
                        "temperature": gpu.temperature,
                        "memory_total": gpu.memoryTotal,
                        "memory_used": gpu.memoryUsed,
                        "memory_percent": round((gpu.memoryUsed / gpu.memoryTotal) * 100, 1) if gpu.memoryTotal > 0 else 0
                    }
            except Exception as e:
                logger.warning(f"Error reading GPU stats via GPUtil: {str(e)}")
        return None

    @staticmethod
    def get_gpu_temperature() -> float:
        """Get primary GPU temperature using NVML (preferred) or GPUtil (fallback)"""
        # Try NVML first
        if HAS_NVIDIA_GPU:
            try:
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()

                if device_count > 0:
                    handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                    temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    pynvml.nvmlShutdown()
                    return temp
            except Exception:
                pass

        # Fallback to GPUtil
        if HAS_GPU_UTIL:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    return gpus[0].temperature
            except Exception:
                pass
        return 0.0

    @staticmethod
    def get_network_stats() -> dict:
        """Get Network statistics"""
        try:
            # Get IO stats
            net_io = psutil.net_io_counters()

            # Return raw bytes for frontend calculations
            return {
                "bytes_sent": net_io.bytes_sent,
                "bytes_recv": net_io.bytes_recv,
                "packets_sent": net_io.packets_sent,
                "packets_recv": net_io.packets_recv,
                "errin": net_io.errin,
                "errout": net_io.errout,
                "dropin": net_io.dropin,
                "dropout": net_io.dropout
            }
        except Exception as e:
            logger.error(f"Error getting Network stats: {type(e).__name__}")
            return {"error": "Failed to get Network stats"}
            
    @staticmethod
    def get_all_stats() -> dict:
        """Aggregate all stats for dashboard"""
        gpu_data = SystemMonitor.get_gpu_usage()

        return {
            "cpu": SystemMonitor.get_cpu_usage(),
            "memory": SystemMonitor.get_memory_usage(),
            "disk": SystemMonitor.get_disk_usage(),
            "gpu": gpu_data,
            "network": SystemMonitor.get_network_stats(),
            "temperature": SystemMonitor._get_cpu_temp(),
            "timestamp": time.time()
        }

    @staticmethod
    def _normalize_unit(bytes_val, suffix="B"):
        """
        Scale bytes to its proper format
        e.g:
            1253656 => '1.20 MB'
            1253656678 => '1.17 GB'
        """
        factor = 1024
        for unit in ["", "K", "M", "G", "T", "P"]:
            if bytes_val < factor:
                return f"{bytes_val:.2f} {unit}{suffix}"
            bytes_val /= factor
        return f"{bytes_val:.2f} E{suffix}"
