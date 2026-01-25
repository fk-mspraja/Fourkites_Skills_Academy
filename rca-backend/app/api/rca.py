"""
RCA API Router
SSE streaming endpoints for real-time investigation updates
With heartbeat mechanism for connection keep-alive and progress visibility
"""
import json
import logging
import asyncio
from typing import Optional, Dict, Any, AsyncGenerator
from datetime import datetime
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.models import create_initial_state
from app.agents.workflow import create_rca_workflow
from app.agents.collaborative_workflow import create_collaborative_workflow

logger = logging.getLogger(__name__)


# Heartbeat configuration
HEARTBEAT_INTERVAL_SECONDS = 2.0  # Send heartbeat every 2 seconds


@dataclass
class InvestigationProgress:
    """Tracks investigation progress for heartbeat events"""
    phase: str = "initializing"
    progress_percent: int = 0
    current_activity: str = "Starting investigation..."
    agents_running: list = None
    data_sources_queried: int = 0
    data_sources_total: int = 10  # Total expected data sources (including logs)

    def __post_init__(self):
        if self.agents_running is None:
            self.agents_running = []

    def to_dict(self) -> dict:
        return {
            "phase": self.phase,
            "progress_percent": self.progress_percent,
            "current_activity": self.current_activity,
            "agents_running": self.agents_running,
            "data_sources_queried": self.data_sources_queried,
            "data_sources_total": self.data_sources_total
        }


def calculate_progress(state: dict) -> InvestigationProgress:
    """Calculate progress based on current investigation state"""
    progress = InvestigationProgress()

    # Determine phase and progress based on state
    iteration = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 10)
    phase = state.get("investigation_phase", "gathering")

    # Count data sources with data
    data_sources_with_data = 0
    data_source_keys = [
        "tracking_data", "redshift_data", "callbacks_data",
        "super_api_data", "jt_data", "network_data",
        "confluence_data", "slack_data", "jira_data", "logs_data"
    ]

    for key in data_source_keys:
        data = state.get(key, {})
        if data and not data.get("skipped") and not data.get("error"):
            data_sources_with_data += 1

    progress.data_sources_queried = data_sources_with_data

    # Calculate progress percentage based on phase
    if phase == "gathering":
        # 0-40%: Data gathering phase
        base_progress = 10
        data_progress = (data_sources_with_data / 10) * 30
        progress.progress_percent = int(base_progress + data_progress)
        progress.phase = "gathering"
        progress.current_activity = f"Collecting data from sources ({data_sources_with_data}/9 complete)"

    elif phase == "analyzing":
        # 40-70%: Analysis phase
        progress.progress_percent = 40 + int((iteration / max(max_iterations, 1)) * 30)
        progress.phase = "analyzing"
        progress.current_activity = "Analyzing collected evidence and forming hypotheses"

    elif phase == "synthesizing":
        # 70-90%: Synthesis phase
        progress.progress_percent = 70 + int((iteration / max(max_iterations, 1)) * 20)
        progress.phase = "synthesizing"
        progress.current_activity = "Determining root cause from hypotheses"

    elif phase == "complete":
        progress.progress_percent = 100
        progress.phase = "complete"
        progress.current_activity = "Investigation complete"

    else:
        # Default progress based on iteration
        progress.progress_percent = min(10 + (iteration * 10), 90)
        progress.phase = phase
        progress.current_activity = f"Processing iteration {iteration}"

    # Get running agents from recent messages
    recent_messages = state.get("agent_messages", [])[-5:]
    running_agents = list(set(
        msg.agent for msg in recent_messages
        if hasattr(msg, 'status') and str(msg.status).upper() == "RUNNING"
    ))
    progress.agents_running = running_agents if running_agents else []

    return progress


def serialize_for_json(obj: Any) -> Any:
    """
    Recursively convert datetime objects to ISO format strings for JSON serialization.

    Args:
        obj: Object to serialize (can be dict, list, datetime, or primitive)

    Returns:
        JSON-serializable version of the object
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {key: serialize_for_json(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [serialize_for_json(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(serialize_for_json(item) for item in obj)
    else:
        return obj

router = APIRouter(prefix="/api/rca", tags=["rca"])


class InvestigateRequest(BaseModel):
    """Request to start an investigation"""
    issue_text: str
    manual_identifiers: Optional[Dict[str, str]] = None


class InvestigateResponse(BaseModel):
    """Response with investigation ID"""
    investigation_id: str
    status: str


@router.post("/investigate/stream")
async def investigate_stream(request: InvestigateRequest):
    """
    Start an investigation with Server-Sent Events streaming

    SSE Events emitted:
    - agent_message: Agent conversation updates
    - timeline_event: Investigation timeline updates
    - hypothesis_update: Hypothesis scoring updates
    - query_executed: Data source query logs
    - root_cause: Final determination
    - needs_human: HITL request
    - error: Error events
    - complete: Investigation finished
    """

    async def event_generator():
        """Generate SSE events from investigation"""
        try:
            # Create initial state
            state = create_initial_state(
                issue_text=request.issue_text,
                manual_identifiers=request.manual_identifiers
            )

            investigation_id = state["investigation_id"]

            # Send initial event
            yield f"event: started\n"
            yield f"data: {json.dumps({'investigation_id': investigation_id, 'timestamp': datetime.now().isoformat()})}\n\n"

            # Create workflow
            workflow = create_rca_workflow()

            # Intercept workflow to stream events
            # We'll run the workflow and stream state updates
            prev_agent_messages = []
            prev_timeline_events = []
            prev_queries = []
            prev_hypotheses = []

            # Stream workflow execution in real-time
            # Track what we've already sent to avoid duplicates
            sent_message_count = 0
            sent_timeline_count = 0
            sent_query_count = 0

            try:
                # Use LangGraph's astream to get incremental state updates
                final_state = None
                async for state_update in workflow.workflow.astream(state):
                    # state_update is a dict with node name as key
                    for node_name, node_state in state_update.items():
                        # Merge this update into our tracking
                        if not final_state:
                            final_state = node_state
                        else:
                            final_state = {**final_state, **node_state}

                        # Stream new agent messages
                        current_messages = final_state.get("agent_messages", [])
                        for msg in current_messages[sent_message_count:]:
                            event_data = {
                                "agent": msg.agent,
                                "message": msg.message,
                                "timestamp": msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp),
                                "status": msg.status.value if hasattr(msg.status, 'value') else msg.status
                            }
                            yield f"event: agent_message\n"
                            yield f"data: {json.dumps(event_data)}\n\n"
                            sent_message_count += 1

                        # Stream new timeline events
                        current_timeline = final_state.get("timeline_events", [])
                        for event in current_timeline[sent_timeline_count:]:
                            event_data = {
                                "agent": event.agent,
                                "action": event.action,
                                "timestamp": event.timestamp.isoformat() if hasattr(event.timestamp, 'isoformat') else str(event.timestamp),
                                "duration_ms": event.duration_ms,
                                "result_summary": event.result_summary,
                                "status": event.status.value if hasattr(event.status, 'value') else event.status
                            }
                            yield f"event: timeline_event\n"
                            yield f"data: {json.dumps(event_data)}\n\n"
                            sent_timeline_count += 1

                        # Stream new queries
                        current_queries = final_state.get("executed_queries", [])
                        for query in current_queries[sent_query_count:]:
                            query_data = {
                                "source": query.source,
                                "query": query.query,
                                "result_count": query.result_count,
                                "duration_ms": query.duration_ms,
                                "error": query.error
                            }
                            yield f"event: query_executed\n"
                            yield f"data: {json.dumps(query_data)}\n\n"
                            sent_query_count += 1


                # After workflow completes, stream final results
                if not final_state:
                    raise Exception("Workflow did not produce any state")

                # Stream hypotheses (if not already sent)
                if final_state.get("hypotheses"):
                    hypotheses_data = []
                    for hyp in final_state["hypotheses"]:
                        hypotheses_data.append({
                            "id": hyp.id,
                            "description": hyp.description,
                            "category": hyp.category.value if hasattr(hyp.category, 'value') else hyp.category,
                            "confidence": hyp.confidence,
                            "evidence_for": [
                                {
                                    "source": e.source,
                                    "finding": e.finding,
                                    "weight": e.weight
                                }
                                for e in hyp.evidence_for
                            ],
                            "evidence_against": [
                                {
                                    "source": e.source,
                                    "finding": e.finding,
                                    "weight": e.weight
                                }
                                for e in hyp.evidence_against
                            ]
                        })
                    yield f"event: hypothesis_update\n"
                    yield f"data: {json.dumps(hypotheses_data)}\n\n"

                # Stream final result
                if final_state.get("root_cause"):
                    root_cause = final_state["root_cause"]
                    root_cause_data = {
                        "category": root_cause.category.value if hasattr(root_cause.category, 'value') else root_cause.category,
                        "description": root_cause.description,
                        "confidence": root_cause.confidence,
                        "recommended_actions": [
                            {
                                "description": action.description,
                                "priority": action.priority,
                                "category": action.category,
                                "details": action.details
                            }
                            for action in root_cause.recommended_actions
                        ]
                    }
                    yield f"event: root_cause\n"
                    yield f"data: {json.dumps(root_cause_data)}\n\n"

                # Check if human input needed
                if final_state.get("needs_human"):
                    hitl_data = {
                        "question": final_state.get("human_question", ""),
                        "investigation_id": investigation_id
                    }
                    yield f"event: needs_human\n"
                    yield f"data: {json.dumps(hitl_data)}\n\n"

                # Stream detailed data from each data source (for frontend tables)
                # Callbacks data
                if final_state.get("callbacks_data"):
                    callbacks = final_state["callbacks_data"]
                    if not callbacks.get("error") and not callbacks.get("skipped") and not callbacks.get("timeout"):
                        yield f"event: callbacks_data\n"
                        yield f"data: {json.dumps(serialize_for_json(callbacks))}\n\n"

                # Tracking API data
                if final_state.get("tracking_data"):
                    tracking = final_state["tracking_data"]
                    if tracking.get("exists"):
                        yield f"event: tracking_data\n"
                        yield f"data: {json.dumps(serialize_for_json(tracking))}\n\n"

                # Redshift validation errors
                if final_state.get("redshift_data"):
                    redshift = final_state["redshift_data"]
                    if not redshift.get("error") and not redshift.get("skipped") and not redshift.get("timeout"):
                        yield f"event: redshift_data\n"
                        yield f"data: {json.dumps(serialize_for_json(redshift))}\n\n"

                # Ocean events (ClickHouse logs)
                if final_state.get("ocean_events_data"):
                    ocean_events = final_state["ocean_events_data"]
                    if not ocean_events.get("error") and not ocean_events.get("skipped") and not ocean_events.get("timeout"):
                        yield f"event: ocean_events_data\n"
                        yield f"data: {json.dumps(serialize_for_json(ocean_events))}\n\n"

                # Ocean trace (DataHub subscription)
                if final_state.get("ocean_trace_data"):
                    ocean_trace = final_state["ocean_trace_data"]
                    if not ocean_trace.get("error") and not ocean_trace.get("skipped"):
                        yield f"event: ocean_trace_data\n"
                        yield f"data: {json.dumps(serialize_for_json(ocean_trace))}\n\n"

                # Confluence documentation
                if final_state.get("confluence_data"):
                    confluence = final_state["confluence_data"]
                    if not confluence.get("error") and not confluence.get("skipped"):
                        yield f"event: confluence_data\n"
                        yield f"data: {json.dumps(serialize_for_json(confluence))}\n\n"

                # Slack history
                if final_state.get("slack_data"):
                    slack = final_state["slack_data"]
                    if not slack.get("error") and not slack.get("skipped"):
                        yield f"event: slack_data\n"
                        yield f"data: {json.dumps(serialize_for_json(slack))}\n\n"

                # JIRA issues
                if final_state.get("jira_data"):
                    jira = final_state["jira_data"]
                    if not jira.get("error") and not jira.get("skipped"):
                        yield f"event: jira_data\n"
                        yield f"data: {json.dumps(serialize_for_json(jira))}\n\n"

                # Service logs
                if final_state.get("logs_data"):
                    logs = final_state["logs_data"]
                    if not logs.get("error") and not logs.get("skipped"):
                        yield f"event: logs_data\n"
                        yield f"data: {json.dumps(serialize_for_json(logs))}\n\n"

                # Send completion event
                yield f"event: complete\n"
                yield f"data: {json.dumps({'investigation_id': investigation_id, 'timestamp': datetime.now().isoformat()})}\n\n"

            except Exception as workflow_error:
                logger.error(f"Workflow error: {str(workflow_error)}", exc_info=True)
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(workflow_error)})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {str(e)}", exc_info=True)
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/investigate", response_model=InvestigateResponse)
async def investigate(request: InvestigateRequest):
    """
    Start an investigation (non-streaming version)

    Returns investigation ID immediately, investigation runs in background
    """
    # Create initial state
    state = create_initial_state(
        issue_text=request.issue_text,
        manual_identifiers=request.manual_identifiers
    )

    investigation_id = state["investigation_id"]

    # In production, you'd queue this or run in background task
    # For now, just return the ID
    return InvestigateResponse(
        investigation_id=investigation_id,
        status="started"
    )


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy", "service": "rca-backend"}


@router.post("/investigate/collaborative")
async def investigate_collaborative(request: InvestigateRequest):
    """
    Start a collaborative multi-agent investigation with SSE streaming.

    This endpoint uses the new collaborative workflow where agents:
    - Discuss findings with each other
    - Propose next investigation steps
    - Vote on priorities
    - Make decisions together
    - Show reasoning in real-time

    SSE Events emitted:
    - heartbeat: Periodic keep-alive with progress info (every 2s)
    - agent_spawn: Agent started executing
    - agent_discussion: Agent conversation/reasoning
    - agent_message: Agent status updates
    - decision: Collaborative decisions made
    - query_executed: API calls with full details (URL, params, response)
    - hypothesis_update: Hypothesis scoring
    - tracking_data/redshift_data/etc: Data source results
    - root_cause: Final determination
    - needs_human: HITL request
    - iteration: Current iteration count
    - error: Error events
    - complete: Investigation finished
    """

    async def event_generator():
        """Generate SSE events from collaborative investigation with heartbeat"""
        try:
            # Create initial state
            state = create_initial_state(
                issue_text=request.issue_text,
                manual_identifiers=request.manual_identifiers
            )

            investigation_id = state["investigation_id"]

            # Send initial event
            yield f"event: started\n"
            yield f"data: {json.dumps({'investigation_id': investigation_id, 'timestamp': datetime.now().isoformat(), 'mode': 'collaborative'})}\n\n"

            # Create collaborative workflow
            workflow = create_collaborative_workflow()

            # Track what we've sent
            sent_message_count = 0
            sent_discussion_count = 0
            sent_decision_count = 0
            sent_query_count = 0
            sent_timeline_count = 0
            last_iteration = 0

            # Event queue for interleaving heartbeats with workflow events
            event_queue: asyncio.Queue = asyncio.Queue()
            workflow_complete = asyncio.Event()
            final_state_holder = {"state": None}

            async def workflow_producer():
                """Run workflow and produce events to queue"""
                try:
                    async for state_update in workflow.workflow.astream(state):
                        for node_name, node_state in state_update.items():
                            await event_queue.put(("state_update", node_name, node_state))
                    await event_queue.put(("workflow_done", None, None))
                except Exception as e:
                    await event_queue.put(("workflow_error", str(e), None))
                finally:
                    workflow_complete.set()

            async def heartbeat_producer():
                """Produce heartbeat events periodically"""
                heartbeat_count = 0
                while not workflow_complete.is_set():
                    await asyncio.sleep(HEARTBEAT_INTERVAL_SECONDS)
                    if not workflow_complete.is_set():
                        heartbeat_count += 1
                        await event_queue.put(("heartbeat", heartbeat_count, None))

            # Start both producers
            workflow_task = asyncio.create_task(workflow_producer())
            heartbeat_task = asyncio.create_task(heartbeat_producer())

            try:
                # Process events from queue
                final_state = None
                while True:
                    try:
                        # Wait for next event with timeout
                        event_type, event_data, extra = await asyncio.wait_for(
                            event_queue.get(),
                            timeout=30.0  # 30 second timeout for safety
                        )

                        if event_type == "heartbeat":
                            # Send heartbeat with progress info
                            progress = calculate_progress(final_state or state)
                            heartbeat_data = {
                                "timestamp": datetime.now().isoformat(),
                                "heartbeat_count": event_data,
                                **progress.to_dict()
                            }
                            yield f"event: heartbeat\n"
                            yield f"data: {json.dumps(heartbeat_data)}\n\n"
                            continue

                        elif event_type == "workflow_done":
                            break

                        elif event_type == "workflow_error":
                            raise Exception(event_data)

                        elif event_type == "state_update":
                            node_name = event_data
                            node_state = extra

                            # Merge updates with proper list accumulation
                            # Lists like agent_messages need to be extended, not replaced
                            if not final_state:
                                final_state = node_state
                            else:
                                for key, value in node_state.items():
                                    if key in final_state and isinstance(final_state[key], list) and isinstance(value, list):
                                        # Extend lists (don't duplicate)
                                        existing_ids = {id(item) for item in final_state[key]}
                                        for item in value:
                                            if id(item) not in existing_ids:
                                                final_state[key].append(item)
                                    else:
                                        final_state[key] = value
                            final_state_holder["state"] = final_state

                            # Stream iteration updates
                            current_iteration = final_state.get("iteration_count", 0)
                            if current_iteration > last_iteration:
                                yield f"event: iteration\n"
                                yield f"data: {json.dumps({'count': current_iteration, 'max': final_state.get('max_iterations', 10), 'phase': final_state.get('investigation_phase', 'gathering')})}\n\n"
                                last_iteration = current_iteration

                            # Stream agent messages
                            current_messages = final_state.get("agent_messages", [])
                            for msg in current_messages[sent_message_count:]:
                                msg_event_data = {
                                    "agent": msg.agent,
                                    "message": msg.message,
                                    "timestamp": msg.timestamp.isoformat() if hasattr(msg.timestamp, 'isoformat') else str(msg.timestamp),
                                    "status": msg.status.value if hasattr(msg.status, 'value') else msg.status,
                                    "metadata": msg.metadata if hasattr(msg, 'metadata') else {}
                                }
                                yield f"event: agent_message\n"
                                yield f"data: {json.dumps(msg_event_data)}\n\n"
                                sent_message_count += 1

                            # Stream agent discussions
                            current_discussions = final_state.get("agent_discussions", [])
                            for disc in current_discussions[sent_discussion_count:]:
                                disc_data = {
                                    "agent": disc.agent,
                                    "message": disc.message,
                                    "type": disc.message_type,
                                    "timestamp": disc.timestamp.isoformat() if hasattr(disc.timestamp, 'isoformat') else str(disc.timestamp)
                                }
                                yield f"event: agent_discussion\n"
                                yield f"data: {json.dumps(disc_data)}\n\n"
                                sent_discussion_count += 1

                            # Stream decisions
                            current_decisions = final_state.get("decisions", [])
                            for dec in current_decisions[sent_decision_count:]:
                                dec_data = {
                                    "action": dec.selected_action.action,
                                    "target": dec.selected_action.target,
                                    "agent": dec.selected_action.agent,
                                    "reasoning": dec.selected_action.reasoning,
                                    "rationale": dec.rationale,
                                    "votes": dec.votes
                                }
                                yield f"event: decision\n"
                                yield f"data: {json.dumps(dec_data)}\n\n"
                                sent_decision_count += 1

                            # Stream queries as they execute (ops love seeing the API calls!)
                            current_queries = final_state.get("executed_queries", [])
                            for query in current_queries[sent_query_count:]:
                                query_data = {
                                    "source": query.source,
                                    "query": query.query,
                                    "result_count": query.result_count,
                                    "duration_ms": query.duration_ms,
                                    "error": query.error,
                                    "executed_at": query.executed_at.isoformat() if hasattr(query.executed_at, 'isoformat') else str(query.executed_at),
                                    "raw_result": serialize_for_json(query.raw_result) if query.raw_result else None
                                }
                                yield f"event: query_executed\n"
                                yield f"data: {json.dumps(query_data)}\n\n"
                                sent_query_count += 1

                            # Stream timeline events
                            current_timeline = final_state.get("timeline_events", [])
                            for tl_event in current_timeline[sent_timeline_count:]:
                                tl_event_data = {
                                    "agent": tl_event.agent,
                                    "action": tl_event.action,
                                    "timestamp": tl_event.timestamp.isoformat() if hasattr(tl_event.timestamp, 'isoformat') else str(tl_event.timestamp),
                                    "duration_ms": tl_event.duration_ms,
                                    "result_summary": tl_event.result_summary,
                                    "status": tl_event.status.value if hasattr(tl_event.status, 'value') else tl_event.status
                                }
                                yield f"event: timeline_event\n"
                                yield f"data: {json.dumps(tl_event_data)}\n\n"
                                sent_timeline_count += 1

                    except asyncio.TimeoutError:
                        # Queue timeout - send a keepalive and continue
                        yield f"event: heartbeat\n"
                        yield f"data: {json.dumps({'timestamp': datetime.now().isoformat(), 'type': 'keepalive'})}\n\n"
                        continue

                # Cancel heartbeat task now that workflow is done
                heartbeat_task.cancel()

                # After workflow completes, stream final results
                if not final_state:
                    raise Exception("Workflow did not produce any state")

                # Stream hypotheses
                if final_state.get("hypotheses"):
                    hypotheses_data = []
                    for hyp in final_state["hypotheses"]:
                        hypotheses_data.append({
                            "id": hyp.id,
                            "description": hyp.description,
                            "category": hyp.category.value if hasattr(hyp.category, 'value') else hyp.category,
                            "confidence": hyp.confidence,
                            "evidence_for": [
                                {"source": e.source, "finding": e.finding, "weight": e.weight}
                                for e in hyp.evidence_for
                            ],
                            "evidence_against": [
                                {"source": e.source, "finding": e.finding, "weight": e.weight}
                                for e in hyp.evidence_against
                            ]
                        })
                    yield f"event: hypothesis_update\n"
                    yield f"data: {json.dumps(hypotheses_data)}\n\n"

                # Stream root cause
                if final_state.get("root_cause"):
                    root_cause = final_state["root_cause"]
                    root_cause_data = {
                        "category": root_cause.category.value if hasattr(root_cause.category, 'value') else root_cause.category,
                        "description": root_cause.description,
                        "confidence": root_cause.confidence,
                        "recommended_actions": [
                            {
                                "description": action.description,
                                "priority": action.priority,
                                "category": action.category,
                                "details": action.details
                            }
                            for action in root_cause.recommended_actions
                        ]
                    }
                    yield f"event: root_cause\n"
                    yield f"data: {json.dumps(root_cause_data)}\n\n"

                # Check if human input needed
                if final_state.get("needs_human"):
                    hitl_data = {
                        "question": final_state.get("human_question", ""),
                        "investigation_id": investigation_id,
                        "phase": final_state.get("investigation_phase", "stuck")
                    }
                    yield f"event: needs_human\n"
                    yield f"data: {json.dumps(hitl_data)}\n\n"

                # Stream data source results with full raw data for ops visibility
                if final_state.get("tracking_data"):
                    tracking = final_state["tracking_data"]
                    yield f"event: tracking_data\n"
                    yield f"data: {json.dumps(serialize_for_json(tracking))}\n\n"

                if final_state.get("redshift_data"):
                    redshift = final_state["redshift_data"]
                    yield f"event: redshift_data\n"
                    yield f"data: {json.dumps(serialize_for_json(redshift))}\n\n"

                if final_state.get("callbacks_data"):
                    callbacks = final_state["callbacks_data"]
                    yield f"event: callbacks_data\n"
                    yield f"data: {json.dumps(serialize_for_json(callbacks))}\n\n"

                if final_state.get("super_api_data"):
                    super_api = final_state["super_api_data"]
                    yield f"event: super_api_data\n"
                    yield f"data: {json.dumps(serialize_for_json(super_api))}\n\n"

                if final_state.get("jt_data"):
                    jt = final_state["jt_data"]
                    yield f"event: jt_data\n"
                    yield f"data: {json.dumps(serialize_for_json(jt))}\n\n"

                if final_state.get("ocean_events_data"):
                    ocean_events = final_state["ocean_events_data"]
                    yield f"event: ocean_events_data\n"
                    yield f"data: {json.dumps(serialize_for_json(ocean_events))}\n\n"

                if final_state.get("ocean_trace_data"):
                    ocean_trace = final_state["ocean_trace_data"]
                    yield f"event: ocean_trace_data\n"
                    yield f"data: {json.dumps(serialize_for_json(ocean_trace))}\n\n"

                if final_state.get("confluence_data"):
                    confluence = final_state["confluence_data"]
                    yield f"event: confluence_data\n"
                    yield f"data: {json.dumps(serialize_for_json(confluence))}\n\n"

                if final_state.get("slack_data"):
                    slack = final_state["slack_data"]
                    yield f"event: slack_data\n"
                    yield f"data: {json.dumps(serialize_for_json(slack))}\n\n"

                if final_state.get("jira_data"):
                    jira = final_state["jira_data"]
                    yield f"event: jira_data\n"
                    yield f"data: {json.dumps(serialize_for_json(jira))}\n\n"

                if final_state.get("logs_data"):
                    logs = final_state["logs_data"]
                    yield f"event: logs_data\n"
                    yield f"data: {json.dumps(serialize_for_json(logs))}\n\n"

                # Send completion with summary stats
                summary = {
                    "investigation_id": investigation_id,
                    "timestamp": datetime.now().isoformat(),
                    "iterations": final_state.get("iteration_count", 0),
                    "total_queries": len(final_state.get("executed_queries", [])),
                    "total_messages": len(final_state.get("agent_messages", [])),
                    "hypotheses_count": len(final_state.get("hypotheses", [])),
                    "root_cause_found": final_state.get("root_cause") is not None,
                    "confidence": final_state.get("root_cause").confidence if final_state.get("root_cause") else 0
                }
                yield f"event: complete\n"
                yield f"data: {json.dumps(summary)}\n\n"

            except Exception as workflow_error:
                logger.error(f"Collaborative workflow error: {str(workflow_error)}", exc_info=True)
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(workflow_error)})}\n\n"

            finally:
                # Clean up tasks
                if not heartbeat_task.done():
                    heartbeat_task.cancel()
                if not workflow_task.done():
                    workflow_task.cancel()
                # Wait for cancellation to complete
                try:
                    await asyncio.gather(heartbeat_task, workflow_task, return_exceptions=True)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Stream error: {str(e)}", exc_info=True)
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
