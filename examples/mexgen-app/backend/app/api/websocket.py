"""WebSocket endpoint for real-time job progress."""

from __future__ import annotations

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.jobs import job_manager
from app.schemas.types import JobStatus

logger = logging.getLogger(__name__)
ws_router = APIRouter()


@ws_router.websocket("/ws/jobs/{job_id}")
async def job_progress(websocket: WebSocket, job_id: str) -> None:
    """Stream job state changes to the client as JSON messages.

    The client connects, and we push updates whenever the job's status
    or progress changes. The connection closes once the job reaches a
    terminal state (complete / failed).
    """
    await websocket.accept()

    job = job_manager.get(job_id)
    if job is None:
        await websocket.send_json({"error": "Job not found"})
        await websocket.close()
        return

    try:
        last_sent = None
        while True:
            payload = job.to_response().model_dump(mode="json")
            payload_key = (job.status, round(job.progress, 2))

            # Only send when something changed
            if payload_key != last_sent:
                await websocket.send_json(payload)
                last_sent = payload_key

            if job.status in (JobStatus.complete, JobStatus.failed):
                break

            # Wait for next state change (with timeout to keep connection alive)
            await job.wait_for_change(timeout=5.0)

    except WebSocketDisconnect:
        logger.debug("WS client disconnected for job %s", job_id)
    finally:
        await websocket.close()
