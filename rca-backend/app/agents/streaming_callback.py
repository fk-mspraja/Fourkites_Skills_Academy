"""
Streaming callback for real-time SSE updates during workflow execution
"""
import asyncio
from typing import AsyncGenerator, Dict, Any
import json
from datetime import datetime


class StreamingCallback:
    """Callback that streams workflow events to SSE"""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.done = False

    async def on_agent_message(self, agent: str, message: str, status: str = "completed"):
        """Called when an agent completes"""
        event_data = {
            "agent": agent,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": status
        }
        await self.queue.put(("agent_message", event_data))

    async def on_query_executed(self, source: str, query: str, result_count: int, duration_ms: int):
        """Called when a query is executed"""
        event_data = {
            "source": source,
            "query": query,
            "result_count": result_count,
            "duration_ms": duration_ms,
            "error": None
        }
        await self.queue.put(("query_executed", event_data))

    async def on_hypothesis_update(self, hypotheses: list):
        """Called when hypotheses are formed/updated"""
        await self.queue.put(("hypothesis_update", hypotheses))

    async def on_root_cause(self, root_cause: Dict):
        """Called when root cause is determined"""
        await self.queue.put(("root_cause", root_cause))

    async def on_needs_human(self, question: str):
        """Called when human input is needed"""
        await self.queue.put(("needs_human", {"question": question}))

    async def on_complete(self, investigation_id: str):
        """Called when investigation completes"""
        self.done = True
        await self.queue.put(("complete", {"investigation_id": investigation_id, "timestamp": datetime.now().isoformat()}))

    async def on_error(self, error: str):
        """Called when an error occurs"""
        self.done = True
        await self.queue.put(("error", {"error": error}))

    async def stream_events(self) -> AsyncGenerator[str, None]:
        """Generate SSE events from the queue"""
        while not self.done or not self.queue.empty():
            try:
                # Wait for next event with timeout
                event_type, data = await asyncio.wait_for(self.queue.get(), timeout=0.5)

                # Format as SSE
                yield f"event: {event_type}\n"
                yield f"data: {json.dumps(data)}\n\n"

            except asyncio.TimeoutError:
                # No event available, continue waiting
                continue
            except Exception as e:
                # Error in streaming
                yield f"event: error\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
                break
