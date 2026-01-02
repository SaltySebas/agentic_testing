"""
WebSocket handler for real-time progress updates.
"""

from fastapi import WebSocket, WebSocketDisconnect, APIRouter
from typing import Dict, Optional
import json
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, WebSocket] = {}


@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time progress updates.
    
    Args:
        websocket: WebSocket connection
        client_id: Unique client identifier
    """
    await websocket.accept()
    active_connections[client_id] = websocket
    logger.info(f"WebSocket client connected: {client_id}")
    
    try:
        # Send connection confirmation
        await websocket.send_json({
            "type": "status",
            "step": "CONNECTED",
            "message": "Connected to Agentic Test Generator",
            "data": {}
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back or handle commands if needed
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "message": "pong"
                    })
            except json.JSONDecodeError:
                # Ignore invalid JSON
                pass
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected: {client_id}")
        if client_id in active_connections:
            del active_connections[client_id]
    except Exception as e:
        logger.error(f"WebSocket error for client {client_id}: {e}")
        if client_id in active_connections:
            del active_connections[client_id]


async def send_progress(
    client_id: str,
    step: str,
    message: str,
    data: Optional[Dict] = None
) -> bool:
    """
    Send progress update to specific client.
    
    Args:
        client_id: Client identifier
        step: Step identifier (e.g., "STEP 1", "STEP 2")
        message: Progress message
        data: Optional additional data
    
    Returns:
        True if message was sent, False if client not connected
    """
    if client_id not in active_connections:
        return False
    
    try:
        await active_connections[client_id].send_json({
            "type": "progress",
            "step": step,
            "message": message,
            "data": data or {}
        })
        return True
    except Exception as e:
        logger.error(f"Failed to send progress to client {client_id}: {e}")
        # Remove disconnected client
        if client_id in active_connections:
            del active_connections[client_id]
        return False


async def send_result(
    client_id: str,
    result: Dict,
    status: str = "result"
) -> bool:
    """
    Send final result to specific client.
    
    Args:
        client_id: Client identifier
        result: Result dictionary
        status: Result type (default: "result")
    
    Returns:
        True if message was sent, False if client not connected
    """
    if client_id not in active_connections:
        return False
    
    try:
        await active_connections[client_id].send_json({
            "type": status,
            "step": "COMPLETE",
            "message": result.get("message", "Operation completed"),
            "data": result
        })
        return True
    except Exception as e:
        logger.error(f"Failed to send result to client {client_id}: {e}")
        if client_id in active_connections:
            del active_connections[client_id]
        return False


async def send_error(
    client_id: str,
    error_message: str,
    error_details: Optional[Dict] = None
) -> bool:
    """
    Send error message to specific client.
    
    Args:
        client_id: Client identifier
        error_message: Error message
        error_details: Optional error details
    
    Returns:
        True if message was sent, False if client not connected
    """
    if client_id not in active_connections:
        return False
    
    try:
        await active_connections[client_id].send_json({
            "type": "error",
            "step": "ERROR",
            "message": error_message,
            "data": error_details or {}
        })
        return True
    except Exception as e:
        logger.error(f"Failed to send error to client {client_id}: {e}")
        if client_id in active_connections:
            del active_connections[client_id]
        return False


def is_client_connected(client_id: str) -> bool:
    """
    Check if a client is connected.
    
    Args:
        client_id: Client identifier
    
    Returns:
        True if client is connected
    """
    return client_id in active_connections

