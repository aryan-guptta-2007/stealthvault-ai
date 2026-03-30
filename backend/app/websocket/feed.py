"""
StealthVault AI - WebSocket Feed
Real-time alert streaming for the dashboard.
"""

import json
import asyncio
import redis.asyncio as redis
from typing import List
from fastapi import WebSocket
from datetime import datetime
from app.models.alert import ThreatAlert


from collections import defaultdict

class WebSocketManager:
    """Manages WebSocket connections and Redis-based localized broadcasting."""

    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = defaultdict(list)
        try:
            self.redis = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
            # We don't ping here as it's async, but we'll handle it in the listener
        except Exception:
            self.redis = None
        self._listener_task = None

    async def connect(self, websocket: WebSocket, tenant_id: str = "default"):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[tenant_id].append(websocket)
        print(f"🔌 Client connected to tenant {tenant_id}. Total for tenant: {len(self.active_connections[tenant_id])}")

    def disconnect(self, websocket: WebSocket, tenant_id: str = "default"):
        """Remove a disconnected client."""
        if tenant_id in self.active_connections and websocket in self.active_connections[tenant_id]:
            self.active_connections[tenant_id].remove(websocket)
            print(f"🔌 Client disconnected from tenant {tenant_id}. Total for tenant: {len(self.active_connections[tenant_id])}")

    async def _redis_listener(self):
        """Background task that listens for tenant-specific Redis broadcasts and pushes to local WebSocket clients."""
        if not self.redis:
            return
            
        pubsub = self.redis.pubsub()
        await pubsub.psubscribe("ws_broadcast:*")
        
        try:
            async for message in pubsub.listen():
                if message['type'] == 'pmessage':
                    channel = message['channel']
                    tenant_id = channel.split("ws_broadcast:")[-1]
                    alert_json = message['data']
                    await self._broadcast_raw(alert_json, tenant_id)
        except asyncio.CancelledError:
            await pubsub.punsubscribe()

    async def _broadcast_raw(self, message: str, tenant_id: str):
        """Internal helper to broadcast raw string data to local connections for a tenant."""
        if not self.active_connections.get(tenant_id):
            return
            
        disconnected = []
        for connection in self.active_connections[tenant_id]:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
                
        for dead_conn in disconnected:
            self.disconnect(dead_conn, tenant_id)

    async def publish_alert_globally(self, alert: ThreatAlert, tenant_id: str = "default"):
        """
        Publishes the alert to Redis so ALL horizontally-scaled FastAPI nodes
        can broadcast it to their respective connected clients for this tenant.
        """
        data = {
            "type": "ALERT",
            "timestamp": datetime.utcnow().isoformat(),
            "data": json.loads(alert.model_dump_json()),
        }
        if self.redis:
            await self.redis.publish(f"ws_broadcast:{tenant_id}", json.dumps(data))
        else:
            await self._broadcast_raw(json.dumps(data), tenant_id)
        
    async def broadcast_alert(self, alert: ThreatAlert):
        """Wrapper for old broadcast API."""
        tenant_id = getattr(alert.packet, "tenant_id", "default")
        await self.publish_alert_globally(alert, tenant_id)

    async def broadcast_stats(self, stats: dict, tenant_id: str = "default"):
        """Broadcast updated statistics to a specific tenant."""
        data = {
            "type": "STATS_UPDATE",
            "timestamp": datetime.utcnow().isoformat(),
            "data": stats,
        }
        if self.redis:
            await self.redis.publish(f"ws_broadcast:{tenant_id}", json.dumps(data))
        else:
            await self._broadcast_raw(json.dumps(data), tenant_id)

    async def start(self):
        if self._listener_task is None:
            self._listener_task = asyncio.create_task(self._redis_listener())

# Singleton
ws_manager = WebSocketManager()
