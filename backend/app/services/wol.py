
import socket
import json
import os
import logging
import ipaddress
from typing import Dict, Optional

from app.core.config import settings, logger
from app.core.security import SecurityManager

class WoLManager:
    """
    Wake-on-LAN functionality
    """

    # Storage file for registered devices
    _storage_file = "wol_devices.json"
    # In-memory cache for registered devices
    registered_macs: Dict[str, str] = {}

    @staticmethod
    def _load_devices():
        """Load devices from persistent storage"""
        try:
            if os.path.exists(WoLManager._storage_file):
                with open(WoLManager._storage_file, 'r') as f:
                    WoLManager.registered_macs = json.load(f)
                logger.info(f"Loaded {len(WoLManager.registered_macs)} WoL devices from storage")
        except Exception as e:
            logger.error(f"Error loading WoL devices: {e}")
            WoLManager.registered_macs = {}

    @staticmethod
    def _save_devices():
        """Save devices to persistent storage"""
        try:
            with open(WoLManager._storage_file, 'w') as f:
                json.dump(WoLManager.registered_macs, f, indent=2)
            logger.debug(f"Saved {len(WoLManager.registered_macs)} WoL devices to storage")
        except Exception as e:
            logger.error(f"Error saving WoL devices: {e}")

    @staticmethod
    def register_device(device_name: str, mac_address: str, broadcast_ip: Optional[str] = None, port: Optional[int] = None) -> dict:
        """Register a device for WoL"""
        mac_address = mac_address.strip() if mac_address else ""
        device_name = SecurityManager.sanitize_input(device_name, max_length=64)

        if not device_name:
            return {"success": False, "message": "Device name is required"}

        if not SecurityManager.validate_mac_address(mac_address):
            return {"success": False, "message": "Invalid MAC address format"}

        # Store device info as a dict to include broadcast_ip and port
        WoLManager.registered_macs[device_name] = {
            "mac_address": mac_address,
            "broadcast_ip": broadcast_ip or "255.255.255.255",
            "port": port or 9
        }
        WoLManager._save_devices()
        logger.info(f"Registered WoL device: {device_name}")

        return {"success": True, "message": f"Device '{device_name}' registered"}

    @staticmethod
    def get_devices() -> dict:
        """Get all registered devices"""
        return {"devices": WoLManager.registered_macs}

    @staticmethod
    def send_magic_packet(mac_address: str, broadcast_ip: str = "255.255.255.255", port: int = 9) -> dict:
        """Send WoL magic packet"""
        mac_address = mac_address.strip() if mac_address else ""
        if not SecurityManager.validate_mac_address(mac_address):
            raise ValueError("Invalid MAC address format")

        try:
            ip = ipaddress.ip_address(broadcast_ip)
            if not ip.is_private and broadcast_ip != "255.255.255.255":
                logger.warning(f"Sending WoL to non-private IP: {broadcast_ip}")
        except ValueError:
            raise ValueError("Invalid broadcast IP address")

        if not (1 <= port <= 65535):
            raise ValueError("Port must be between 1 and 65535")

        try:
            mac_clean = mac_address.replace(":", "").replace("-", "")
            magic_packet = b'\xff' * 6 + bytes.fromhex(mac_clean) * 16

            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                sock.sendto(magic_packet, (broadcast_ip, port))

            logger.info(f"Sent WoL magic packet to {mac_address} at {broadcast_ip}:{port}")

            return {
                "success": True,
                "message": f"Magic packet sent to {mac_address}",
                "mac_address": mac_address,
                "broadcast_ip": broadcast_ip,
                "port": port
            }

        except Exception as e:
            logger.error(f"Failed to send WoL packet: {str(e)}")
            raise e

    @staticmethod
    def delete_device(device_name: str) -> dict:
        """Delete a registered WoL device"""
        if device_name in WoLManager.registered_macs:
            del WoLManager.registered_macs[device_name]
            WoLManager._save_devices()
            logger.info(f"Deleted WoL device: {device_name}")
            return {"success": True, "message": f"Device '{device_name}' deleted"}
        return {"success": False, "message": "Device not found"}

    @staticmethod
    def get_device(device_name: str) -> Optional[dict]:
        """Get a specific device by name"""
        return WoLManager.registered_macs.get(device_name)

# Initialize: load devices on module import
WoLManager._load_devices()
