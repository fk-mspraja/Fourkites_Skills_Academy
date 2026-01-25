"""Investigation endpoint with SSE streaming"""

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Any, Dict, AsyncGenerator, Optional
from pydantic import BaseModel

from api.models.requests import InvestigateRequest
from api.utils.tracing import trace_request
from modes.ocean.agent import OceanDebuggingAgent
from core.clients.clickhouse_client import ClickHouseClient
from core.utils.llm_client import LLMClient

router = APIRouter()
logger = logging.getLogger(__name__)


class LogQueryRequest(BaseModel):
    service: str
    message_type: str
    identifier: str
    days_back: int = 7


class AIChatRequest(BaseModel):
    message: str
    load_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


def serialize_evidence(evidence_list):
    """Convert evidence to JSON-safe format"""
    result = []
    for e in evidence_list:
        ev_dict = {
            "id": getattr(e, 'id', None),
            "finding": getattr(e, 'finding', ''),
            "source": e.source.value if hasattr(e.source, 'value') else str(getattr(e, 'source', '')),
            "relevance": getattr(e, 'relevance', 0.5),
        }
        if hasattr(e, 'timestamp') and e.timestamp:
            ev_dict["timestamp"] = e.timestamp.isoformat() if hasattr(e.timestamp, 'isoformat') else str(e.timestamp)
        result.append(ev_dict)
    return result


def format_sse(event: str, data: dict) -> bytes:
    """Format as SSE message - return bytes for immediate flush"""
    msg = f"event: {event}\ndata: {json.dumps(data)}\n\n"
    return msg.encode('utf-8')


@router.post("/investigate")
async def investigate(request: InvestigateRequest):
    """Start RCA investigation with SSE streaming"""

    logger.info(f"Investigation request: {request.dict()}")

    async def event_stream():
        """Generate SSE events - yields bytes for immediate streaming"""

        # Send connection acknowledgment immediately
        yield b": ok\n\n"

        investigation_id = f"inv_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        with trace_request() as trace_id:
            # Initial events - sent immediately
            yield format_sse("log", {
                "message": f"Starting {request.mode} investigation",
                "level": "info",
                "trace_id": trace_id
            })

            yield format_sse("step", {
                "step": 1,
                "title": "Initializing",
                "description": "Setting up investigation agent",
                "status": "active"
            })

            # Allow event loop to send above events
            await asyncio.sleep(0)

            # Determine case_number
            case_number = request.case_number
            if not case_number:
                if request.load_id:
                    case_number = f"LOAD_{request.load_id}"
                elif request.load_number:
                    case_number = f"LOADNUM_{request.load_number}"
                else:
                    case_number = "DIRECT_INQUIRY"

            if request.mode != "ocean":
                yield format_sse("error", {"message": f"Mode '{request.mode}' not implemented"})
                yield format_sse("complete", {"investigation_id": investigation_id, "status": "error"})
                return

            try:
                agent = OceanDebuggingAgent()

                yield format_sse("step", {"step": 1, "status": "completed"})
                yield format_sse("step", {
                    "step": 2,
                    "title": "Forming Hypotheses",
                    "description": "LLM analyzing problem space",
                    "status": "active"
                })
                await asyncio.sleep(0)

                # Event queue for callbacks
                event_queue: asyncio.Queue = asyncio.Queue()
                step_2_done = False
                step_3_done = False

                async def event_callback(event_type: str, data: Dict[str, Any]):
                    nonlocal step_2_done, step_3_done
                    await event_queue.put((event_type, data))

                    if event_type == "hypothesis" and not step_2_done:
                        step_2_done = True
                        await event_queue.put(("step", {"step": 2, "status": "completed"}))
                        await event_queue.put(("step", {
                            "step": 3,
                            "title": "Running Sub-Agents",
                            "description": "Parallel investigation",
                            "status": "active"
                        }))
                    elif event_type == "synthesis" and not step_3_done:
                        step_3_done = True
                        await event_queue.put(("step", {"step": 3, "status": "completed"}))
                        await event_queue.put(("step", {
                            "step": 4,
                            "title": "Synthesizing Results",
                            "description": "Determining root cause",
                            "status": "active"
                        }))

                # Start investigation in background
                investigation_done = asyncio.Event()
                result_holder = {"result": None, "error": None}

                async def run_investigation():
                    try:
                        result = await agent.investigate(
                            case_number=case_number,
                            progress_callback=lambda p: asyncio.create_task(
                                event_queue.put(("progress", {"percent": p}))
                            ),
                            event_callback=event_callback
                        )
                        result_holder["result"] = result
                    except Exception as e:
                        logger.error(f"Investigation error: {e}", exc_info=True)
                        result_holder["error"] = str(e)
                    finally:
                        investigation_done.set()

                task = asyncio.create_task(run_investigation())

                # Stream events as they arrive
                while not investigation_done.is_set() or not event_queue.empty():
                    try:
                        event_type, data = await asyncio.wait_for(event_queue.get(), timeout=0.3)
                        yield format_sse(event_type, data)
                    except asyncio.TimeoutError:
                        # Heartbeat to keep connection alive
                        yield b": ping\n\n"

                # Drain remaining events
                while not event_queue.empty():
                    try:
                        event_type, data = event_queue.get_nowait()
                        yield format_sse(event_type, data)
                    except asyncio.QueueEmpty:
                        break

                await task

                # Final results
                yield format_sse("step", {"step": 4, "status": "completed"})

                if result_holder["error"]:
                    yield format_sse("error", {"message": result_holder["error"]})
                elif result_holder["result"]:
                    result = result_holder["result"]
                    yield format_sse("result", {
                        "root_cause": result.root_cause,
                        "category": result.root_cause_category.value if result.root_cause_category else None,
                        "confidence": result.confidence,
                        "evidence_count": len(result.evidence),
                        "evidence": serialize_evidence(result.evidence[:10]),
                        "action": result.recommended_action.action if result.recommended_action else None,
                        "priority": result.recommended_action.priority.value if result.recommended_action else None,
                        "duration": result.investigation_time,
                        "needs_human": result.needs_human,
                        "human_question": result.human_question
                    })

                yield format_sse("complete", {"investigation_id": investigation_id, "status": "success"})

            except Exception as e:
                logger.error(f"Investigation error: {e}", exc_info=True)
                yield format_sse("error", {"message": str(e)})
                yield format_sse("complete", {"investigation_id": investigation_id, "status": "error"})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.post("/query-logs")
async def query_logs(request: LogQueryRequest):
    """Query SigNoz logs via ClickHouse"""

    logger.info(f"Log query request: service={request.service}, message_type={request.message_type}, identifier={request.identifier}")

    try:
        clickhouse_client = ClickHouseClient()

        if not clickhouse_client.is_configured:
            return {
                "logs": [],
                "count": 0,
                "message": "ClickHouse not configured"
            }

        # Calculate date range
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=request.days_back)).strftime("%Y-%m-%d")

        # Build search string with message type and identifier
        search_string = f"{request.message_type} AND {request.identifier}"

        # Query logs using manual search
        result = clickhouse_client.search_logs_manual(
            service_names=[request.service],
            start_date=start_date,
            end_date=end_date,
            search_string=search_string,
            limit=50
        )

        logs = result.get("logs", [])

        return {
            "logs": logs,
            "count": len(logs),
            "service": request.service,
            "message_type": request.message_type,
            "identifier": request.identifier
        }

    except Exception as e:
        logger.error(f"Log query error: {e}", exc_info=True)
        return {
            "logs": [],
            "count": 0,
            "error": str(e)
        }


@router.post("/ai-chat")
async def ai_chat(request: AIChatRequest):
    """AI-powered chat for RCA assistance"""

    logger.info(f"AI chat request: {request.message[:50]}...")

    try:
        llm_client = LLMClient()

        # Build context for the AI
        context_parts = []

        if request.load_id:
            context_parts.append(f"Current Load ID: {request.load_id}")

        if request.context:
            if request.context.get("hypotheses"):
                hypotheses = request.context["hypotheses"]
                context_parts.append(f"\nCurrent Hypotheses ({len(hypotheses)}):")
                for h in hypotheses[:5]:
                    context_parts.append(f"  - {h['description']} (confidence: {h['confidence']:.2f})")

            if request.context.get("evidence_count"):
                context_parts.append(f"\nEvidence collected: {request.context['evidence_count']} pieces")

            if request.context.get("result"):
                result = request.context["result"]
                if result.get("root_cause"):
                    context_parts.append(f"\nDetermined Root Cause: {result['root_cause']}")
                    context_parts.append(f"Confidence: {result.get('confidence', 0):.2f}")

        context = "\n".join(context_parts) if context_parts else "No investigation context available."

        # System prompt for RCA assistant
        system_prompt = """You are an expert RCA (Root Cause Analysis) assistant for FourKites shipment tracking.

You help support and operations teams understand investigation results, interpret logs, and recommend actions.

When answering questions:
1. Be specific and actionable
2. Reference TL/FTL processing stages when relevant (File Ingestion, Data Mapping, Asset Assignment, Location Processing, Location Validation, ELD Integration)
3. Suggest specific log queries using service names (carrier-files-worker, global-worker-ex, location-worker, cfw-eld-data)
4. Recommend concrete next steps
5. Explain technical concepts in ops-friendly language

Keep responses concise (2-3 paragraphs max) unless explaining complex issues."""

        # User prompt with context
        user_prompt = f"""INVESTIGATION CONTEXT:
{context}

USER QUESTION:
{request.message}

Provide a helpful, actionable response."""

        # Call LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = await llm_client._call_llm(messages)

        return {
            "response": response,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"AI chat error: {e}", exc_info=True)
        return {
            "response": f"Sorry, I encountered an error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat(),
            "error": True
        }
