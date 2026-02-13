#!/usr/bin/env python3
"""
 =============================================================================
 NexControl Update Checker Service
 =============================================================================
 Checks GitHub for new releases and notifies users about updates.
 =============================================================================
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
import aiohttp

logger = logging.getLogger("nexcontrol")


class UpdateChecker:
    """
    Checks for updates from GitHub releases.
    """
    
    def __init__(
        self,
        current_version: str,
        github_repo: str = "Thamindu-Dev/nexcontrol-client",
        check_interval_hours: int = 24
    ):
        """
        Initialize the update checker.
        
        Args:
            current_version: Current application version (e.g., "1.0.0")
            github_repo: GitHub repository in format "owner/repo"
            check_interval_hours: How often to check for updates
        """
        self.current_version = current_version
        self.github_repo = github_repo
        self.check_interval = timedelta(hours=check_interval_hours)
        
        self.last_check: Optional[datetime] = None
        self.latest_version: Optional[str] = None
        self.update_available: bool = False
        self.release_notes: Optional[str] = None
        self.download_url: Optional[str] = None
        
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def check_for_updates(self) -> Dict:
        """
        Check GitHub API for latest release.
        
        Returns:
            Dict with update information
        """
        try:
            api_url = f"https://api.github.com/repos/{self.github_repo}/releases/latest"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Extract version from tag_name (e.g., "v1.0.1" -> "1.0.1")
                        latest_version = data.get("tag_name", "").lstrip("v")
                        release_notes = data.get("body", "")
                        
                        # Find Windows exe download URL
                        download_url = None
                        for asset in data.get("assets", []):
                            if asset.get("name", "").endswith(".exe"):
                                download_url = asset.get("browser_download_url")
                                break
                        
                        # Update internal state
                        self.latest_version = latest_version
                        self.release_notes = release_notes
                        self.download_url = download_url
                        self.last_check = datetime.now()
                        
                        # Check if update is available
                        self.update_available = self._is_newer_version(
                            self.current_version,
                            latest_version
                        )
                        
                        logger.info(f"Update check: Current={self.current_version}, Latest={latest_version}, Available={self.update_available}")
                        
                        return {
                            "current_version": self.current_version,
                            "latest_version": latest_version,
                            "update_available": self.update_available,
                            "release_notes": release_notes,
                            "download_url": download_url,
                            "last_check": self.last_check.isoformat() if self.last_check else None
                        }
                    else:
                        logger.warning(f"GitHub API returned status {response.status}")
                        return self._get_cached_status()
                        
        except asyncio.TimeoutError:
            logger.warning("Update check timed out")
            return self._get_cached_status()
        except Exception as e:
            logger.error(f"Update check failed: {e}")
            return self._get_cached_status()
    
    def _get_cached_status(self) -> Dict:
        """Get cached update status."""
        return {
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "update_available": self.update_available,
            "release_notes": self.release_notes,
            "download_url": self.download_url,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "error": "Unable to check for updates"
        }
    
    @staticmethod
    def _is_newer_version(current: str, latest: str) -> bool:
        """
        Compare version strings.
        
        Args:
            current: Current version (e.g., "1.0.0")
            latest: Latest version (e.g., "1.0.1")
        
        Returns:
            True if latest is newer than current
        """
        try:
            # Parse version numbers
            current_parts = [int(x) for x in current.split(".")]
            latest_parts = [int(x) for x in latest.split(".")]
            
            # Pad shorter version with zeros
            max_len = max(len(current_parts), len(latest_parts))
            current_parts.extend([0] * (max_len - len(current_parts)))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            
            # Compare each part
            return latest_parts > current_parts
            
        except (ValueError, AttributeError):
            logger.warning(f"Invalid version format: current={current}, latest={latest}")
            return False
    
    async def _background_check_loop(self):
        """Background task that periodically checks for updates."""
        logger.info(f"Update checker started (checking every {self.check_interval.total_seconds() / 3600} hours)")
        
        while self._running:
            try:
                # Check for updates
                await self.check_for_updates()
                
                # Log if update is available
                if self.update_available:
                    logger.info(f"🆕 Update available: v{self.latest_version}")
                
                # Wait for next check
                await asyncio.sleep(self.check_interval.total_seconds())
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in update check loop: {e}")
                # Wait a bit before retrying
                await asyncio.sleep(3600)  # 1 hour
        
        logger.info("Update checker stopped")
    
    async def start(self):
        """Start the background update checker."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._background_check_loop())
        
        # Do an immediate check
        await self.check_for_updates()
    
    async def stop(self):
        """Stop the background update checker."""
        if not self._running:
            return
        
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
    
    def get_status(self) -> Dict:
        """Get current update status (cached)."""
        return {
            "current_version": self.current_version,
            "latest_version": self.latest_version,
            "update_available": self.update_available,
            "release_notes": self.release_notes,
            "download_url": self.download_url,
            "last_check": self.last_check.isoformat() if self.last_check else None
        }
