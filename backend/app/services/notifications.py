
import asyncio
import json
import os
import time
import logging
from datetime import datetime
from typing import List, Optional

from app.core.config import settings, logger
from app.models.schemas import ThresholdConfig, ThresholdAlert
from app.services.system_monitor import SystemMonitor

class ThresholdNotificationManager:
    """
    Manage threshold-based notifications
    Monitors system metrics and alerts when thresholds are exceeded
    Stores alert history and manages notification delivery
    """

    def __init__(self, storage_file: str = "threshold_alerts.json"):
        """Initialize threshold notification manager"""
        self.storage_file = storage_file
        self.config_file = "threshold_config.json"  # Config persistence file
        self.config = ThresholdConfig()
        self.alerts: List[ThresholdAlert] = []
        self._monitor_task = None
        self._running = False
        self._last_alert_time = {}  # Track last alert time to prevent spam
        self._alert_cooldown = 300  # 5 minutes cooldown between alerts for same metric
        self._load_config()  # Load config from disk
        self._load_alerts()
        self._cleanup_old_alerts()  # Remove very old alerts
        self._restore_cooldown_from_alerts()  # Restore cooldown from recent alerts
        logger.info("ThresholdNotificationManager initialized")

    def _load_config(self):
        """Load threshold configuration from persistent storage if available"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    self.config = ThresholdConfig(**config_data)
                logger.info(f"Loaded threshold config from disk: {self.config.dict()}")
            else:
                logger.info("No saved config found, using defaults")
        except Exception as e:
            logger.error(f"Error loading config from disk: {type(e).__name__}: {e}")
            logger.info("Using default threshold configuration")

    def _save_config(self):
        """Save threshold configuration to persistent storage"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config.dict(), f, indent=2)
            logger.info(f"Saved threshold config to disk: {self.config.dict()}")
        except Exception as e:
            logger.error(f"Error saving config to disk: {type(e).__name__}: {e}")

    def _load_alerts(self):
        """Load alert history from persistent storage if available"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r') as f:
                    data = json.load(f)
                    loaded_count = 0
                    for alert_data in data:
                        try:
                            # Migrate old field names if present
                            if 'current_value' in alert_data and 'value' not in alert_data:
                                alert_data['value'] = alert_data.pop('current_value')
                            if 'timestamp' in alert_data and 'triggered_at' not in alert_data:
                                alert_data['triggered_at'] = alert_data.pop('timestamp')
                            # Ensure unit field exists
                            if 'unit' not in alert_data:
                                alert_data['unit'] = '%'

                            alert = ThresholdAlert(**alert_data)
                            self.alerts.append(alert)
                            loaded_count += 1
                        except Exception as e:
                            logger.warning(f"Skipping invalid alert data: {e}")
                            continue
                    logger.info(f"Loaded {loaded_count} alerts from storage (total data: {len(data)})")
        except Exception as e:
            logger.error(f"Error loading alerts: {type(e).__name__}: {e}")

    def _restore_cooldown_from_alerts(self):
        """Restore cooldown timers from recent unacknowledged alerts to prevent spam on restart"""
        try:
            now = time.time()
            for alert in self.alerts:
                if not alert.acknowledged:
                    try:
                        # Parse ISO format timestamp
                        alert_time = datetime.fromisoformat(alert.triggered_at).timestamp()
                        time_since_alert = now - alert_time

                        # If the alert is recent (within cooldown period), restore the cooldown
                        if time_since_alert < self._alert_cooldown:
                            remaining_cooldown = self._alert_cooldown - time_since_alert
                            # Set last alert time to now minus remaining cooldown
                            # This effectively extends the cooldown from the existing alert
                            self._last_alert_time[alert.metric_type] = now - remaining_cooldown
                            logger.info(f"Restored cooldown for {alert.metric_type}: {remaining_cooldown:.0f}s remaining")
                    except Exception as e:
                        logger.warning(f"Could not parse alert timestamp for cooldown: {e}")
        except Exception as e:
            logger.warning(f"Error restoring cooldown from alerts: {e}")

    def _cleanup_old_alerts(self):
        """Remove old acknowledged alerts to prevent clutter"""
        try:
            now = time.time()
            one_day_ago = now - 86400  # 24 hours

            # Keep unacknowledged alerts and recent acknowledged alerts (within 24 hours)
            cleaned_alerts = []
            removed_count = 0

            for alert in self.alerts:
                if not alert.acknowledged:
                    cleaned_alerts.append(alert)
                else:
                    try:
                        alert_time = datetime.fromisoformat(alert.triggered_at).timestamp()
                        if alert_time > one_day_ago:
                            cleaned_alerts.append(alert)
                        else:
                            removed_count += 1
                    except:
                        # Keep if we can't parse the time
                        cleaned_alerts.append(alert)

            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old acknowledged alerts")

            self.alerts = cleaned_alerts
        except Exception as e:
            logger.warning(f"Error cleaning up old alerts: {e}")

    def _save_alerts(self):
        """Save alerts to persistent storage"""
        try:
            # Clean up old alerts: keep last 50 and remove old acknowledged ones
            now = time.time()

            # Separate unacknowledged and acknowledged alerts
            unacknowledged = [a for a in self.alerts if not a.acknowledged]
            acknowledged = [a for a in self.alerts if a.acknowledged]

            # Keep all unacknowledged, but only last 20 acknowledged
            self.alerts = unacknowledged + acknowledged[-20:]

            # Keep total of max 50 alerts
            if len(self.alerts) > 50:
                self.alerts = self.alerts[-50:]

            with open(self.storage_file, 'w') as f:
                alerts_data = [alert.dict() for alert in self.alerts]
                json.dump(alerts_data, f, indent=2)

            logger.debug(f"Saved {len(self.alerts)} alerts ({len(unacknowledged)} unacknowledged)")
        except Exception as e:
            logger.error(f"Error saving alerts: {type(e).__name__}")

    def get_config(self) -> ThresholdConfig:
        """Get current threshold configuration"""
        return self.config

    def update_config(self, **kwargs) -> ThresholdConfig:
        """Update threshold configuration"""
        for key, value in kwargs.items():
            if hasattr(self.config, key) and value is not None:
                setattr(self.config, key, value)
        logger.info(f"Threshold config updated: {kwargs}")

        # Persist to disk
        self._save_config()

        return self.config

    def get_alerts(self, limit: int = 50, unacknowledged_only: bool = False) -> List[ThresholdAlert]:
        """Get alert history"""
        alerts = self.alerts
        if unacknowledged_only:
            alerts = [a for a in alerts if not a.acknowledged]
        # Return most recent first
        return sorted(alerts, key=lambda x: x.triggered_at, reverse=True)[:limit]

    def acknowledge_alert(self, alert_id: str) -> bool:
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                self._save_alerts()
                return True
        return False

    def acknowledge_all_alerts(self) -> int:
        """Acknowledge all alerts"""
        count = 0
        for alert in self.alerts:
            if not alert.acknowledged:
                alert.acknowledged = True
                count += 1
        if count > 0:
            self._save_alerts()
        return count

    def _check_threshold(self, metric_type: str, current_value: float, threshold: int) -> Optional[ThresholdAlert]:
        """Check if threshold is exceeded and create alert if needed"""
        import uuid

        # Check if threshold exceeded
        if current_value < threshold:
            return None

        # Check if there's already a recent unacknowledged alert for this metric
        now = time.time()
        for alert in reversed(self.alerts):  # Check most recent first
            if (alert.metric_type == metric_type and
                not alert.acknowledged and
                alert.value >= threshold):  # Value is still above threshold
                try:
                    alert_time = datetime.fromisoformat(alert.triggered_at).timestamp()
                    # If alert is less than 10 minutes old, don't create a new one
                    if now - alert_time < 600:
                        logger.debug(f"Skipping {metric_type} alert - recent unacknowledged alert exists")
                        return None
                except:
                    pass

        # Check cooldown to prevent alert spam
        last_alert = self._last_alert_time.get(metric_type, 0)
        if now - last_alert < self._alert_cooldown:
            return None

        # Create alert
        alert = ThresholdAlert(
            id=str(uuid.uuid4()),
            metric_type=metric_type,
            threshold=threshold,
            value=current_value,
            triggered_at=datetime.now().isoformat(),
            acknowledged=False
        )

        self.alerts.append(alert)
        self._last_alert_time[metric_type] = now
        self._save_alerts()

        logger.warning(f"Threshold alert: {metric_type.upper()} at {current_value:.1f}% exceeds threshold {threshold}%")
        return alert

    def check_thresholds(self) -> List[ThresholdAlert]:
        """Check all thresholds against current system stats"""
        if not self.config.enabled:
            return []

        new_alerts = []

        try:
            # Get current stats from SystemMonitor
            stats = SystemMonitor.get_all_stats()

            # Check CPU threshold
            if self.config.cpu_threshold > 0:
                cpu_usage = stats.get('cpu', {}).get('cpu_percent', 0)
                alert = self._check_threshold('cpu', cpu_usage, self.config.cpu_threshold)
                if alert:
                    new_alerts.append(alert)

            # Check Memory threshold
            if self.config.memory_threshold > 0:
                memory_usage = stats.get('memory', {}).get('percent', 0)
                alert = self._check_threshold('memory', memory_usage, self.config.memory_threshold)
                if alert:
                    new_alerts.append(alert)

            # Check Disk threshold
            if self.config.disk_threshold > 0:
                disk_usage = stats.get('disk', {}).get('percent', 0)
                alert = self._check_threshold('disk', disk_usage, self.config.disk_threshold)
                if alert:
                    new_alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking thresholds: {type(e).__name__}: {e}")

        return new_alerts

    async def start_monitor(self, websocket_manager=None):
        """Start the background threshold monitor. Pass websocket_manager to enable broadcasting."""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop(websocket_manager))
        logger.info("Threshold notification manager started")

    async def stop_monitor(self):
        """Stop the background threshold monitor"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Threshold notification manager stopped")

    async def _monitor_loop(self, websocket_manager=None):
        """Background loop that periodically checks thresholds"""
        while self._running:
            try:
                # Check thresholds
                new_alerts = self.check_thresholds()

                # Send WebSocket notifications for new alerts if manager is provided
                if websocket_manager and new_alerts:
                    for alert in new_alerts:
                        await websocket_manager.broadcast({
                            'type': 'threshold_alert',
                            'data': alert.dict()
                        })

                # Check every 30 seconds
                await asyncio.sleep(30)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitor loop error: {type(e).__name__}")
                await asyncio.sleep(60)
