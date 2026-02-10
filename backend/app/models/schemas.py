from pydantic import BaseModel, Field, field_validator, constr
from typing import Optional, List, Dict, Any
from datetime import datetime
import time

class LoginRequest(BaseModel):
    """Login request schema with validation"""
    password: constr(min_length=4, max_length=128) = Field(
        ...,
        description="App password for authentication"
    )

    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        """Prevent common injection patterns"""
        if any(char in v for char in [';', '|', '&', '$', '`', '\n', '\r']):
            raise ValueError("Password contains invalid characters")
        return v

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenResponse(BaseModel):
    """JWT token response schema"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class EncryptedPayload(BaseModel):
    """Encrypted request payload schema"""
    data: str = Field(..., min_length=1, description="Base64-encoded encrypted data (includes nonce)")
    timestamp: float = Field(..., description="Unix timestamp for replay attack prevention")

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp_format(cls, v):
        """Validate timestamp is reasonable"""
        if v < 0 or v > (time.time() + 3600):
            raise ValueError("Invalid timestamp")
        return v

class CommandResponse(BaseModel):
    """Standard command response schema"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None

class PowerActionRequest(BaseModel):
    """Power action request schema with validation"""
    action: str = Field(..., description="Action: shutdown, hibernate, restart")
    delay_seconds: int = Field(0, ge=0, le=86400, description="Delay before execution (0-86400 seconds)")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is allowed"""
        allowed = ['shutdown', 'hibernate', 'restart']
        if v.lower() not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v.lower()


# Scheduled Task Models
class ScheduledTask(BaseModel):
    """Scheduled task model"""
    id: str = Field(..., description="Unique task ID")
    name: str = Field(..., min_length=1, max_length=100, description="Task name")
    action: str = Field(..., description="Action: shutdown, hibernate, restart, lock")
    scheduled_time: str = Field(..., description="Scheduled time in ISO format")
    enabled: bool = Field(True, description="Whether the task is enabled")
    created_at: str = Field(..., description="Creation timestamp in ISO format")
    last_run: Optional[str] = Field(None, description="Last execution timestamp (ISO format)")
    execution_result: Optional[dict] = Field(None, description="Result of last execution")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is allowed"""
        allowed = ['shutdown', 'hibernate', 'restart', 'lock']
        if v.lower() not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v.lower()


class CreateScheduledTaskRequest(BaseModel):
    """Create scheduled task request schema"""
    name: str = Field(..., min_length=1, max_length=100, description="Task name")
    action: str = Field(..., description="Action: shutdown, hibernate, restart, lock")
    scheduled_time: str = Field(..., description="Scheduled time in ISO format (YYYY-MM-DDTHH:MM:SS)")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is allowed"""
        allowed = ['shutdown', 'hibernate', 'restart', 'lock']
        if v.lower() not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v.lower()

    @field_validator('scheduled_time')
    @classmethod
    def validate_scheduled_time(cls, v):
        """Validate scheduled time is in the future"""
        try:
            scheduled_dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
            # datetime.now() needs to use the same timezone or lack thereof. 
            # Assuming naive if no tzinfo, or we can just compare. 
            # The original code used scheduled_dt.tzinfo
            if scheduled_dt <= datetime.now(scheduled_dt.tzinfo):
                raise ValueError("Scheduled time must be in the future")
        except ValueError as e:
            if "must be in the future" in str(e):
                raise
            raise ValueError("Invalid datetime format. Use ISO format: YYYY-MM-DDTHH:MM:SS")
        return v


class UpdateScheduledTaskRequest(BaseModel):
    """Update scheduled task request schema"""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Task name")
    action: Optional[str] = Field(None, description="Action: shutdown, hibernate, restart")
    scheduled_time: Optional[str] = Field(None, description="Scheduled time in ISO format")

    @field_validator('action')
    @classmethod
    def validate_action(cls, v):
        """Validate action is allowed"""
        if v is None:
            return v
        allowed = ['shutdown', 'hibernate', 'restart']
        if v.lower() not in allowed:
            raise ValueError(f"Action must be one of: {', '.join(allowed)}")
        return v.lower()


# Threshold Notification Models
class ThresholdConfig(BaseModel):
    """Threshold configuration model"""
    cpu_threshold: int = Field(80, ge=0, le=100, description="CPU usage threshold percentage")
    memory_threshold: int = Field(85, ge=0, le=100, description="Memory usage threshold percentage")
    disk_threshold: int = Field(90, ge=0, le=100, description="Disk usage threshold percentage")
    enabled: bool = Field(True, description="Whether threshold monitoring is enabled")

    class Config:
        json_schema_extra = {
            "example": {
                "cpu_threshold": 80,
                "memory_threshold": 85,
                "disk_threshold": 90,
                "enabled": True
            }
        }


class ThresholdAlert(BaseModel):
    """Threshold alert model"""
    id: str
    metric_type: str = Field(..., description="Type: cpu, memory, disk")
    threshold: int = Field(..., description="Threshold value that was exceeded")
    value: float = Field(..., description="Current value that exceeded threshold")
    triggered_at: str = Field(..., description="Alert timestamp")
    acknowledged: bool = Field(False, description="Whether alert was acknowledged")
    unit: str = Field("%", description="Unit of measurement (percentage)")

class AppLaunchRequest(BaseModel):
    """App launch request schema"""
    app_id: str = Field(..., description="Application ID to launch")
    args: Optional[str] = Field(None, description="Optional arguments")

class MediaControlRequest(BaseModel):
    """Media control request schema"""
    action: str = Field(..., description="Action: playpause, next, prev, volumeup, volumedown, volumemute")
    scope: str = Field("global", description="Scope: global, targeted")
    app_name: Optional[str] = Field(None, description="Target app name for targeted scope")

class WolRequest(BaseModel):
    """Wake-on-LAN request schema"""
    mac_address: str = Field(..., description="MAC address of target device")
    broadcast_ip: str = Field("255.255.255.255", description="Broadcast IP address")
    port: int = Field(9, description="WoL port")

class ScreenshotRequest(BaseModel):
    """Screenshot request schema"""
    quality: int = Field(75, ge=1, le=100, description="Image quality (1-100)")

