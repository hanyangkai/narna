"""WebSocket connection manager for mobile app real-time updates."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manage WebSocket connections for mobile clients."""

    def __init__(self) -> None:
        # bot_id -> list of (websocket, mobile_token, device_info)
        self.connections: dict[str, list[tuple[WebSocket, str, dict[str, Any]]]] = {}
        # session_id -> bot_id mapping
        self.session_to_bot: dict[str, str] = {}
    
    async def connect(
        self,
        websocket: WebSocket,
        bot_id: str,
        mobile_token: str,
        device_info: dict[str, Any] | None = None
    ) -> None:
        """Register a new WebSocket connection."""
        await websocket.accept()
        
        if bot_id not in self.connections:
            self.connections[bot_id] = []
        
        self.connections[bot_id].append((websocket, mobile_token, device_info or {}))
    
    def disconnect(self, websocket: WebSocket, bot_id: str) -> None:
        """Remove a WebSocket connection."""
        if bot_id in self.connections:
            self.connections[bot_id] = [
                (ws, token, info)
                for ws, token, info in self.connections[bot_id]
                if ws != websocket
            ]
            
            if not self.connections[bot_id]:
                del self.connections[bot_id]
    
    async def send_to_bot(self, bot_id: str, message: dict[str, Any]) -> int:
        """Send message to all connections for a bot."""
        if bot_id not in self.connections:
            return 0
        
        sent_count = 0
        dead_connections = []
        
        for websocket, token, info in self.connections[bot_id]:
            try:
                await websocket.send_json(message)
                sent_count += 1
            except Exception:
                dead_connections.append((websocket, token, info))
        
        # Clean up dead connections
        for dead_ws, _, _ in dead_connections:
            self.disconnect(dead_ws, bot_id)
        
        return sent_count
    
    async def send_to_session(self, session_id: str, message: dict[str, Any]) -> int:
        """Send message to all connections for a session."""
        bot_id = self.session_to_bot.get(session_id)
        if bot_id:
            return await self.send_to_bot(bot_id, message)
        return 0
    
    def register_session(self, session_id: str, bot_id: str) -> None:
        """Map session_id to bot_id for event forwarding."""
        self.session_to_bot[session_id] = bot_id
    
    def get_connection_count(self, bot_id: str) -> int:
        """Get number of active connections for a bot."""
        return len(self.connections.get(bot_id, []))
    
    async def broadcast(self, message: dict[str, Any]) -> int:
        """Broadcast message to all connected clients."""
        total_sent = 0
        for bot_id in list(self.connections.keys()):
            total_sent += await self.send_to_bot(bot_id, message)
        return total_sent


# Global singleton
_manager: ConnectionManager | None = None


def get_ws_manager() -> ConnectionManager:
    """Get singleton WebSocket manager."""
    global _manager
    if _manager is None:
        _manager = ConnectionManager()
    return _manager


# Event forwarding helpers

async def forward_agent_event(
    session_id: str,
    event_type: str,
    data: dict[str, Any]
) -> None:
    """Forward agent runtime event to mobile clients."""
    manager = get_ws_manager()
    
    message = {
        "type": event_type,
        "session_id": session_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "data": data
    }
    
    await manager.send_to_session(session_id, message)


async def notify_approval_required(
    bot_id: str,
    approval_id: str,
    action_type: str,
    description: str,
    details: dict[str, Any]
) -> None:
    """Notify mobile app that agent needs approval."""
    manager = get_ws_manager()
    
    await manager.send_to_bot(bot_id, {
        "type": "approval_required",
        "approval_id": approval_id,
        "action_type": action_type,
        "description": description,
        "details": details,
        "timestamp": datetime.now(timezone.utc).isoformat()
    })
