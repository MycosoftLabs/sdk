"""
NatureOS Client - Main interface for interacting with NatureOS API.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class NatureOSClient:
    """
    Main client for interacting with the NatureOS API.
    
    This client provides methods for:
    - Device management
    - Sensor data access
    - Command execution
    - MycoBrain integration
    """
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        tenant_id: Optional[str] = None,
        timeout: int = 30,
        max_retries: int = 3,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the NatureOS client.
        
        Args:
            api_url: NatureOS API base URL
            api_key: API key for authentication
            tenant_id: Tenant/organization ID (optional)
            timeout: Request timeout in seconds
            max_retries: Maximum retry attempts
            config: Optional configuration dictionary
        """
        self.config = config or {}
        
        self.api_url = (api_url or os.getenv("NATUREOS_API_URL", "http://localhost:8002")).rstrip('/')
        self.api_key = api_key or os.getenv("NATUREOS_API_KEY", "")
        self.tenant_id = tenant_id or os.getenv("NATUREOS_TENANT_ID", "")
        self.timeout = timeout
        self.max_retries = max_retries
        
        self._http_client = None
        logger.info(f"NatureOS client initialized - API: {self.api_url}")
    
    async def _get_http_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            if self.tenant_id:
                headers["X-Tenant-ID"] = self.tenant_id
            
            self._http_client = httpx.AsyncClient(
                base_url=self.api_url,
                headers=headers,
                timeout=self.timeout,
                follow_redirects=True
            )
        
        return self._http_client
    
    async def list_devices(
        self,
        device_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        List all registered devices.
        
        Args:
            device_type: Filter by device type
            status: Filter by status
            limit: Maximum number of devices
        
        Returns:
            List of device dictionaries
        """
        try:
            client = await self._get_http_client()
            params = {"limit": limit}
            if device_type:
                params["device_type"] = device_type
            if status:
                params["status"] = status
            
            response = await client.get("/devices", params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("items", [])
        except httpx.HTTPError as e:
            logger.error(f"Error listing devices: {e}")
            raise
    
    async def get_device(self, device_id: str) -> Dict[str, Any]:
        """Get device details."""
        try:
            client = await self._get_http_client()
            response = await client.get(f"/devices/{device_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error getting device {device_id}: {e}")
            raise
    
    async def register_device(
        self,
        device_id: str,
        name: str,
        device_type: str,
        location: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register a new device."""
        try:
            client = await self._get_http_client()
            payload = {
                "device_id": device_id,
                "name": name,
                "device_type": device_type
            }
            if location:
                payload["location"] = location
            if metadata:
                payload["metadata"] = metadata
            
            response = await client.post("/devices/register", json=payload)
            response.raise_for_status()
            logger.info(f"Registered device: {device_id}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error registering device: {e}")
            raise
    
    async def get_sensor_data(
        self,
        device_id: str,
        sensor_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Get sensor data from a device."""
        try:
            client = await self._get_http_client()
            params = {"limit": limit}
            
            if sensor_type:
                params["sensor_type"] = sensor_type
            if start_time:
                params["start_time"] = start_time.isoformat()
            else:
                params["start_time"] = (datetime.utcnow() - timedelta(hours=24)).isoformat()
            if end_time:
                params["end_time"] = end_time.isoformat()
            else:
                params["end_time"] = datetime.utcnow().isoformat()
            
            response = await client.get(f"/devices/{device_id}/sensor-data", params=params)
            response.raise_for_status()
            data = response.json()
            
            return data.get("items", [])
        except httpx.HTTPError as e:
            logger.error(f"Error getting sensor data: {e}")
            raise
    
    async def send_command(
        self,
        device_id: str,
        command_type: str,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send a command to a device."""
        try:
            client = await self._get_http_client()
            payload = {
                "command_type": command_type,
                "parameters": parameters
            }
            
            response = await client.post(
                f"/devices/{device_id}/commands",
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Sent command {command_type} to device {device_id}")
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error sending command: {e}")
            raise
    
    async def register_mycobrain_device(
        self,
        device_id: str,
        serial_number: str,
        name: str,
        firmware_version: str,
        location: Optional[Dict[str, float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Register a MycoBrain device."""
        device_metadata = {
            "serial_number": serial_number,
            "firmware_version": firmware_version,
            "device_type": "mycobrain",
        }
        if metadata:
            device_metadata.update(metadata)
        
        return await self.register_device(
            device_id=device_id,
            name=name,
            device_type="mycobrain",
            location=location,
            metadata=device_metadata
        )
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

