"""
API routes for the agentic test generator.
"""

import sys
import uuid
import asyncio
import queue
import threading
from pathlib import Path
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
import logging

# Add backend to path
backend_path = Path(__file__).parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

# Then your imports:
from core.orchestrator import Orchestrator
from api.websocket import send_progress, send_result, send_error, is_client_connected

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for request/response validation
class GenerateRequest(BaseModel):
    """Request model for generate endpoint."""
    requirements: str = Field(..., description="Requirements for code generation")
    max_iterations: int = Field(default=5, ge=1, le=20, description="Maximum iterations")


class TestRequest(BaseModel):
    """Request model for test endpoint."""
    code: str = Field(..., description="Code to generate tests for")
    max_iterations: int = Field(default=5, ge=1, le=20, description="Maximum iterations")


class ResumeRequest(BaseModel):
    """Request model for resume endpoint."""
    resume_state: Dict[str, Any] = Field(..., description="Resume state dictionary")
    code: str = Field(..., description="Updated code (if modified)")


# Store orchestrator instances per client (for progress tracking)
_orchestrators: Dict[str, Orchestrator] = {}


async def run_orchestrator_generate(
    client_id: str,
    requirements: str,
    max_iterations: int
) -> Dict[str, Any]:
    """
    Run orchestrator in GENERATE mode with progress updates.
    
    Args:
        client_id: Client identifier for WebSocket updates
        requirements: Requirements string
        max_iterations: Maximum iterations
    
    Returns:
        Result dictionary
    """
    # Create a queue for progress messages
    progress_queue = queue.Queue()
    
    # Background task to send progress updates
    async def progress_sender():
        """Send progress updates from queue."""
        while True:
            try:
                # Get message with timeout
                item = progress_queue.get(timeout=0.1)
                if item is None:  # Sentinel to stop
                    break
                step, message = item
                await send_progress(client_id, step, message)
            except queue.Empty:
                # Check if orchestrator is still running
                if client_id not in _orchestrators:
                    break
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error sending progress: {e}")
    
    try:
        # Send initial progress
        await send_progress(client_id, "START", "Starting code generation...")
        
        # Start progress sender task
        sender_task = asyncio.create_task(progress_sender())
        
        # Create orchestrator
        orchestrator = Orchestrator()
        _orchestrators[client_id] = orchestrator
        
        # Monkey-patch _log_step to queue progress updates
        original_log_step = orchestrator._log_step
        
        def log_step_with_ws(step: str, message: str):
            """Log step and queue WebSocket update."""
            original_log_step(step, message)
            try:
                progress_queue.put((step, message), block=False)
            except queue.Full:
                pass  # Skip if queue is full
        
        orchestrator._log_step = log_step_with_ws
        
        # Run orchestrator in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: orchestrator.run(
                mode="generate",
                input_code=requirements,
                max_iterations=max_iterations
            )
        )
        
        # Stop progress sender
        progress_queue.put(None)  # Sentinel
        await sender_task
        
        # Send final result
        await send_result(client_id, result, "result")
        
        # Clean up
        if client_id in _orchestrators:
            del _orchestrators[client_id]
        
        return result
        
    except Exception as e:
        logger.error(f"Error in generate mode: {e}", exc_info=True)
        await send_error(client_id, f"Generation failed: {str(e)}")
        if client_id in _orchestrators:
            del _orchestrators[client_id]
        raise


async def run_orchestrator_test(
    client_id: str,
    code: str,
    max_iterations: int
) -> Dict[str, Any]:
    """
    Run orchestrator in TEST mode with progress updates.
    
    Args:
        client_id: Client identifier for WebSocket updates
        code: Code to test
        max_iterations: Maximum iterations
    
    Returns:
        Result dictionary
    """
    # Create a queue for progress messages
    progress_queue = queue.Queue()
    
    # Background task to send progress updates
    async def progress_sender():
        """Send progress updates from queue."""
        while True:
            try:
                # Get message with timeout
                item = progress_queue.get(timeout=0.1)
                if item is None:  # Sentinel to stop
                    break
                step, message = item
                await send_progress(client_id, step, message)
            except queue.Empty:
                # Check if orchestrator is still running
                if client_id not in _orchestrators:
                    break
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error sending progress: {e}")
    
    try:
        # Send initial progress
        await send_progress(client_id, "START", "Starting test generation...")
        
        # Start progress sender task
        sender_task = asyncio.create_task(progress_sender())
        
        # Create orchestrator
        orchestrator = Orchestrator()
        _orchestrators[client_id] = orchestrator
        
        # Monkey-patch _log_step to queue progress updates
        original_log_step = orchestrator._log_step
        
        def log_step_with_ws(step: str, message: str):
            """Log step and queue WebSocket update."""
            original_log_step(step, message)
            try:
                progress_queue.put((step, message), block=False)
            except queue.Full:
                pass  # Skip if queue is full
        
        orchestrator._log_step = log_step_with_ws
        
        # Run orchestrator in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: orchestrator.run(
                mode="test",
                input_code=code,
                max_iterations=max_iterations
            )
        )
        
        # Stop progress sender
        progress_queue.put(None)  # Sentinel
        await sender_task
        
        # Send final result
        await send_result(client_id, result, "result")
        
        # Clean up
        if client_id in _orchestrators:
            del _orchestrators[client_id]
        
        return result
        
    except Exception as e:
        logger.error(f"Error in test mode: {e}", exc_info=True)
        await send_error(client_id, f"Test generation failed: {str(e)}")
        if client_id in _orchestrators:
            del _orchestrators[client_id]
        raise


async def run_orchestrator_resume(
    client_id: str,
    resume_state: Dict[str, Any],
    code: str
) -> Dict[str, Any]:
    """
    Resume orchestrator from saved state with progress updates.
    
    Args:
        client_id: Client identifier for WebSocket updates
        resume_state: Resume state dictionary
        code: Updated code
    
    Returns:
        Result dictionary
    """
    # Create a queue for progress messages
    progress_queue = queue.Queue()
    
    # Background task to send progress updates
    async def progress_sender():
        """Send progress updates from queue."""
        while True:
            try:
                # Get message with timeout
                item = progress_queue.get(timeout=0.1)
                if item is None:  # Sentinel to stop
                    break
                step, message = item
                await send_progress(client_id, step, message)
            except queue.Empty:
                # Check if orchestrator is still running
                if client_id not in _orchestrators:
                    break
                await asyncio.sleep(0.1)
            except Exception as e:
                logger.error(f"Error sending progress: {e}")
    
    try:
        # Send initial progress
        await send_progress(client_id, "RESUME", "Resuming from saved state...")
        
        # Start progress sender task
        sender_task = asyncio.create_task(progress_sender())
        
        # Create orchestrator
        orchestrator = Orchestrator()
        _orchestrators[client_id] = orchestrator
        
        # Monkey-patch _log_step to queue progress updates
        original_log_step = orchestrator._log_step
        
        def log_step_with_ws(step: str, message: str):
            """Log step and queue WebSocket update."""
            original_log_step(step, message)
            try:
                progress_queue.put((step, message), block=False)
            except queue.Full:
                pass  # Skip if queue is full
        
        orchestrator._log_step = log_step_with_ws
        
        # Determine mode from resume state
        mode = resume_state.get("mode", "test")
        
        # Run orchestrator in executor to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: orchestrator.run(
                mode=mode,
                input_code=code,
                max_iterations=resume_state.get("max_iterations", 5),
                resume_state=resume_state
            )
        )
        
        # Stop progress sender
        progress_queue.put(None)  # Sentinel
        await sender_task
        
        # Send final result
        await send_result(client_id, result, "result")
        
        # Clean up
        if client_id in _orchestrators:
            del _orchestrators[client_id]
        
        return result
        
    except Exception as e:
        logger.error(f"Error resuming: {e}", exc_info=True)
        await send_error(client_id, f"Resume failed: {str(e)}")
        if client_id in _orchestrators:
            del _orchestrators[client_id]
        raise


@router.post("/generate")
async def generate_endpoint(
    request: GenerateRequest,
    client_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate code and tests from requirements.
    
    Args:
        request: Generate request with requirements
        background_tasks: FastAPI background tasks
        client_id: Optional client ID for WebSocket updates
    
    Returns:
        Result dictionary
    """
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # Validate client connection if client_id provided
    if client_id and not is_client_connected(client_id):
        # Still allow the request, but warn
        logger.warning(f"Client {client_id} not connected via WebSocket")
    
    try:
        # Run in background task
        result = await run_orchestrator_generate(
            client_id,
            request.requirements,
            request.max_iterations
        )
        
        return {
            "status": result.get("status", "UNKNOWN"),
            "message": result.get("message", ""),
            "tests": result.get("tests", ""),
            "iterations": result.get("iterations", 0),
            "test_results": result.get("test_results"),
            "scenarios": result.get("scenarios"),
            "analysis": result.get("analysis"),
            "resume_state": result.get("resume_state"),
            "client_id": client_id
        }
    except Exception as e:
        logger.error(f"Generate endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Generation failed: {str(e)}"
        )


@router.post("/test")
async def test_endpoint(
    request: TestRequest,
    client_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate tests for existing code.
    
    Args:
        request: Test request with code
        background_tasks: FastAPI background tasks
        client_id: Optional client ID for WebSocket updates
    
    Returns:
        Result dictionary
    """
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # Validate client connection if client_id provided
    if client_id and not is_client_connected(client_id):
        logger.warning(f"Client {client_id} not connected via WebSocket")
    
    try:
        # Run in background task
        result = await run_orchestrator_test(
            client_id,
            request.code,
            request.max_iterations
        )
        
        return {
            "status": result.get("status", "UNKNOWN"),
            "message": result.get("message", ""),
            "tests": result.get("tests", ""),
            "iterations": result.get("iterations", 0),
            "test_results": result.get("test_results"),
            "scenarios": result.get("scenarios"),
            "analysis": result.get("analysis"),
            "resume_state": result.get("resume_state"),
            "client_id": client_id
        }
    except Exception as e:
        logger.error(f"Test endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Test generation failed: {str(e)}"
        )


@router.post("/resume")
async def resume_endpoint(
    request: ResumeRequest,
    client_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Resume test generation from saved state.
    
    Args:
        request: Resume request with state and code
        background_tasks: FastAPI background tasks
        client_id: Optional client ID for WebSocket updates
    
    Returns:
        Result dictionary
    """
    if not client_id:
        client_id = str(uuid.uuid4())
    
    # Validate client connection if client_id provided
    if client_id and not is_client_connected(client_id):
        logger.warning(f"Client {client_id} not connected via WebSocket")
    
    try:
        # Run in background task
        result = await run_orchestrator_resume(
            client_id,
            request.resume_state,
            request.code
        )
        
        return {
            "status": result.get("status", "UNKNOWN"),
            "message": result.get("message", ""),
            "tests": result.get("tests", ""),
            "iterations": result.get("iterations", 0),
            "test_results": result.get("test_results"),
            "scenarios": result.get("scenarios"),
            "analysis": result.get("analysis"),
            "resume_state": result.get("resume_state"),
            "client_id": client_id
        }
    except Exception as e:
        logger.error(f"Resume endpoint error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Resume failed: {str(e)}"
        )


@router.get("/status")
async def status_endpoint() -> Dict[str, Any]:
    """
    Get current system status.
    
    Returns:
        Status dictionary with system information
    """
    status = {
        "status": "operational",
        "version": "1.0.0",
        "docker_available": False,
        "docker_image": "agentic_test-runner:latest"
    }
    
    # Check Docker availability
    try:
        from agents.docker_execution_agent import DockerExecutorAgent
        executor = DockerExecutorAgent()
        status["docker_available"] = True
        status["docker_image"] = executor.image_name
    except Exception as e:
        status["docker_available"] = False
        status["docker_error"] = str(e)
    
    return status

