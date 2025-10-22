"""Cloud sync module for BizHive.cloud integration"""
import os
import httpx
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class CloudSyncManager:
    """
    Manages synchronization with BizHive.cloud

    Features:
    - Event-driven sync (leads, bookings, conversations)
    - Periodic analytics push
    - Bidirectional knowledge base updates
    - Optional - fully functional without cloud
    """

    def __init__(
        self,
        business_module: str,
        enabled: bool = None,
        api_key: Optional[str] = None,
        cloud_url: Optional[str] = None
    ):
        """
        Initialize cloud sync manager

        Args:
            business_module: Business module name (stayhive, techhive)
            enabled: Whether cloud sync is enabled (defaults to env var)
            api_key: BizHive Cloud API key (defaults to env var)
            cloud_url: BizHive Cloud URL (defaults to env var or production)
        """
        self.business_module = business_module

        # Check if cloud sync is enabled
        if enabled is None:
            enabled = os.getenv("BIZHIVE_CLOUD_ENABLED", "false").lower() == "true"

        self.enabled = enabled

        if self.enabled:
            self.api_key = api_key or os.getenv("BIZHIVE_CLOUD_API_KEY")
            self.cloud_url = cloud_url or os.getenv(
                "BIZHIVE_CLOUD_URL",
                "https://api.bizhive.cloud"
            )

            if not self.api_key:
                raise ValueError(
                    "Cloud sync enabled but BIZHIVE_CLOUD_API_KEY not set"
                )

            self.client = httpx.AsyncClient(
                base_url=self.cloud_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "X-Business-Module": business_module
                },
                timeout=30.0
            )
        else:
            self.client = None

    async def sync_lead(self, lead_data: Dict[str, Any]) -> bool:
        """
        Sync a new lead to BizHive Cloud

        Args:
            lead_data: Lead information

        Returns:
            True if sync successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            response = await self.client.post(
                "/v1/leads",
                json={
                    **lead_data,
                    "business_module": self.business_module,
                    "synced_at": datetime.utcnow().isoformat()
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            # Log but don't fail - local operation continues
            print(f"Cloud sync failed for lead: {e}")
            return False

    async def sync_reservation(self, reservation_data: Dict[str, Any]) -> bool:
        """Sync a new reservation to BizHive Cloud"""
        if not self.enabled:
            return False

        try:
            response = await self.client.post(
                "/v1/reservations",
                json={
                    **reservation_data,
                    "business_module": self.business_module,
                    "synced_at": datetime.utcnow().isoformat()
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Cloud sync failed for reservation: {e}")
            return False

    async def sync_conversation(
        self,
        session_id: str,
        messages: List[Dict],
        metadata: Dict
    ) -> bool:
        """Sync conversation history to BizHive Cloud for analytics"""
        if not self.enabled:
            return False

        try:
            response = await self.client.post(
                "/v1/conversations",
                json={
                    "session_id": session_id,
                    "messages": messages,
                    "metadata": metadata,
                    "business_module": self.business_module,
                    "synced_at": datetime.utcnow().isoformat()
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Cloud sync failed for conversation: {e}")
            return False

    async def fetch_knowledge_base_updates(self) -> Optional[Dict]:
        """
        Fetch knowledge base updates from BizHive Cloud

        Allows centralized management of policies, procedures, etc.
        """
        if not self.enabled:
            return None

        try:
            response = await self.client.get(
                f"/v1/knowledge-base/{self.business_module}/updates",
                params={"since": self._get_last_sync_time()}
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Failed to fetch KB updates: {e}")
            return None

    async def push_analytics(self, metrics: Dict[str, Any]) -> bool:
        """Push performance metrics and analytics to BizHive Cloud"""
        if not self.enabled:
            return False

        try:
            response = await self.client.post(
                "/v1/analytics",
                json={
                    "metrics": metrics,
                    "business_module": self.business_module,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to push analytics: {e}")
            return False

    def _get_last_sync_time(self) -> str:
        """Get last sync time from local storage"""
        # TODO: Implement local storage for sync timestamps
        return datetime.utcnow().isoformat()

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()


# Convenience function for quick sync operations
async def quick_sync(
    event_type: str,
    data: Dict[str, Any],
    business_module: str
) -> bool:
    """
    Quick one-off sync operation

    Args:
        event_type: Type of event (lead, reservation, conversation, etc.)
        data: Event data
        business_module: Business module name

    Returns:
        True if sync successful
    """
    if os.getenv("BIZHIVE_CLOUD_ENABLED", "false").lower() != "true":
        return False

    sync_manager = CloudSyncManager(business_module)

    try:
        if event_type == "lead":
            return await sync_manager.sync_lead(data)
        elif event_type == "reservation":
            return await sync_manager.sync_reservation(data)
        # Add more event types as needed

        return False
    finally:
        await sync_manager.close()
