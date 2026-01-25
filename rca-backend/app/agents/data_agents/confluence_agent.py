"""
Confluence Documentation Agent
Searches wiki for troubleshooting guides, service docs, and known issues
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any, List
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, AgentDiscussion, AgentMessage, AgentStatus
from app.services.confluence_client import ConfluenceClient


class ConfluenceAgent(BaseAgent):
    """
    Searches Confluence for relevant documentation with verbose output.

    Role: Documentation Researcher
    I search our knowledge base for relevant documentation and past solutions.
    """

    def __init__(self):
        super().__init__("Confluence Agent")
        self.client = ConfluenceClient()

    def _merge_updates(self, updates: Dict, new_update: Dict) -> Dict:
        """Helper to merge updates, handling list accumulation"""
        for key, value in new_update.items():
            if key in updates and isinstance(updates[key], list) and isinstance(value, list):
                updates[key] = updates[key] + value
            else:
                updates[key] = value
        return updates

    async def execute(self, state: InvestigationState) -> Dict[str, Any]:
        """
        Search Confluence for troubleshooting docs based on investigation context
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        # Extract context for search
        issue_text = state.get("issue_text", "")
        transport_mode = state.get("transport_mode", "unknown")

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Preparing to search Confluence documentation.\n" +
                    f"  • Issue context: {issue_text[:100] + '...' if len(issue_text) > 100 else issue_text}\n" +
                    f"  • Transport mode: {transport_mode}",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        # Get error patterns from hypotheses or validation data
        error_keywords = self._extract_keywords(state)

        if not error_keywords:
            think = AgentDiscussion(
                agent=self.name,
                message="[Thinking] No meaningful keywords to search. Need error messages or specific issue context.",
                message_type="proposal",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(think)

            return {
                **updates,
                "confluence_data": {"skipped": True, "reason": "No keywords to search"},
                "_message": "Skipped Confluence: no search keywords"
            }

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message=f"[Plan] Will search Confluence for:\n" +
                    f"  • Keywords: {', '.join(error_keywords[:5])}\n" +
                    f"  • Service: {self._get_service_name(transport_mode)}\n" +
                    f"  • Looking for: troubleshooting guides, runbooks, known issues",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        # Executing action
        action_msg = AgentMessage(
            agent=self.name,
            message=f"[Executing] CQL: type=page AND text~'{' '.join(error_keywords[:3])}'",
            status=AgentStatus.RUNNING,
            metadata={"type": "search", "source": "confluence"}
        )
        updates["agent_messages"].append(action_msg)

        try:
            # Search for troubleshooting documentation
            results = await self.client.search_troubleshooting(
                service_name=self._get_service_name(transport_mode),
                issue_keywords=error_keywords,
                limit=5
            )

            duration_ms = int((time.time() - start_time) * 1000)

            # Log the query
            query_desc = f"CQL: type=page AND text~'{' '.join(error_keywords[:3])}'"
            query_log = self.log_query(
                state,
                "Confluence",
                query_desc,
                result_count=len(results),
                raw_result=results,
                duration_ms=duration_ms
            )
            self._merge_updates(updates, query_log)

            confluence_data = {
                "found": len(results) > 0,
                "count": len(results),
                "pages": results,
                "search_keywords": error_keywords
            }

            if results:
                # Report findings
                pages_summary = "\n".join([f"  • {r['title'][:50]}" for r in results[:3]])
                finding = AgentDiscussion(
                    agent=self.name,
                    message=f"[Finding] Found {len(results)} relevant documentation pages!\n" +
                            f"{pages_summary}\n\n" +
                            f"These pages may contain troubleshooting steps or known issue information.",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = f"Found {len(results)} relevant docs: {', '.join([r['title'][:30] for r in results[:3]])}"
            else:
                finding = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] No relevant documentation found in Confluence.\n" +
                            f"  • Searched keywords: {', '.join(error_keywords[:5])}\n" +
                            "  • This may be a new/undocumented issue",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = "No relevant documentation found in Confluence"

            return {
                **updates,
                "confluence_data": confluence_data,
                "_message": message
            }

        except Exception as e:
            self.logger.error(f"Confluence search error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to search Confluence: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "confluence_data": {"error": str(e)},
                "_message": f"Confluence error: {str(e)}"
            }

    def _extract_keywords(self, state: InvestigationState) -> List[str]:
        """Extract search keywords from investigation state"""
        keywords = []

        # From issue text (first few significant words)
        issue_text = state.get("issue_text", "")
        if issue_text:
            # Extract meaningful words (skip common ones)
            stopwords = {"the", "a", "an", "is", "are", "not", "for", "and", "or", "but", "with", "load", "tracking"}
            words = [w.lower() for w in issue_text.split() if len(w) > 3 and w.lower() not in stopwords]
            keywords.extend(words[:5])

        # From validation errors
        redshift_data = state.get("redshift_data", {})
        latest_error = redshift_data.get("latest_error", "")
        if latest_error:
            # Extract key phrases from error
            error_words = [w for w in latest_error.split() if len(w) > 4][:3]
            keywords.extend(error_words)

        # From transport mode
        transport_mode = state.get("transport_mode")
        if transport_mode and transport_mode != "unknown":
            keywords.append(transport_mode.lower())

        return list(set(keywords))[:8]  # Dedupe and limit

    def _get_service_name(self, transport_mode: str) -> str:
        """Map transport mode to service name for documentation search"""
        mode_services = {
            "ocean": "ocean tracking",
            "otr": "truckload tracking",
            "ltl": "ltl tracking",
            "air": "air freight",
            "rail": "rail tracking",
            "parcel": "parcel tracking"
        }
        return mode_services.get(transport_mode.lower(), "tracking")
