"""
JIRA Issues Agent
Searches for related tickets, past incidents, and known bugs
With Claude Code-style verbose output
"""
import time
from typing import Dict, Any, List
from datetime import datetime

from app.agents.base import BaseAgent
from app.models import InvestigationState, AgentDiscussion, AgentMessage, AgentStatus
from app.services.jira_client import JIRAClient


class JIRAAgent(BaseAgent):
    """
    Searches JIRA for related issues and past incidents with verbose output.

    Role: Issue Tracker
    I search for related tickets and known issues in our tracking system.
    """

    def __init__(self):
        super().__init__("JIRA Agent")
        self.client = JIRAClient()

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
        Search JIRA for related issues
        """
        updates: Dict[str, Any] = {"agent_discussions": [], "agent_messages": []}

        tracking_id = self.extract_identifier(state, "tracking_id")

        # Observation
        obs = AgentDiscussion(
            agent=self.name,
            message=f"[Observation] Preparing to search JIRA for related issues.\n" +
                    f"  • tracking_id: {tracking_id or 'not available'}\n" +
                    "  • Will search: by tracking ID, error pattern, and keywords",
            message_type="observation",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(obs)

        # Plan
        plan = AgentDiscussion(
            agent=self.name,
            message="[Plan] Will use multi-strategy JIRA search:\n" +
                    "  1. Search by tracking ID (exact match)\n" +
                    "  2. Search by error pattern (from Redshift data)\n" +
                    "  3. Search by keywords (from issue text)\n" +
                    "  • Looking for: known bugs, past incidents, workarounds",
            message_type="proposal",
            timestamp=datetime.now()
        )
        updates["agent_discussions"].append(plan)

        start_time = time.time()

        # Executing action
        action_msg = AgentMessage(
            agent=self.name,
            message="[Executing] Multi-strategy JIRA search (tracking_id, error, keywords)",
            status=AgentStatus.RUNNING,
            metadata={"type": "search", "source": "jira"}
        )
        updates["agent_messages"].append(action_msg)

        try:
            all_issues = []

            # Strategy 1: Search by tracking ID
            if tracking_id:
                tracking_issues = await self.client.search_by_tracking_id(tracking_id, max_results=5)
                for issue in tracking_issues:
                    issue["search_type"] = "tracking_id"
                all_issues.extend(tracking_issues)

                if tracking_issues:
                    strategy_disc = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Found {len(tracking_issues)} issues matching tracking_id={tracking_id}",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(strategy_disc)

            # Strategy 2: Search by error pattern
            redshift_data = state.get("redshift_data", {})
            latest_error = redshift_data.get("latest_error", "")
            if latest_error:
                error_issues = await self.client.search_by_error_pattern(latest_error, max_results=5)
                for issue in error_issues:
                    issue["search_type"] = "error_pattern"
                # Avoid duplicates
                existing_keys = {i["key"] for i in all_issues}
                new_issues = [i for i in error_issues if i["key"] not in existing_keys]
                all_issues.extend(new_issues)

                if new_issues:
                    strategy_disc = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Found {len(new_issues)} issues matching error pattern",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(strategy_disc)

            # Strategy 3: Search by keywords
            keywords = self._extract_keywords(state)
            if keywords:
                keyword_issues = await self.client.search_similar_issues(keywords, max_results=5)
                for issue in keyword_issues:
                    issue["search_type"] = "keywords"
                existing_keys = {i["key"] for i in all_issues}
                new_issues = [i for i in keyword_issues if i["key"] not in existing_keys]
                all_issues.extend(new_issues)

                if new_issues:
                    strategy_disc = AgentDiscussion(
                        agent=self.name,
                        message=f"[Finding] Found {len(new_issues)} issues matching keywords: {', '.join(keywords[:3])}",
                        message_type="observation",
                        timestamp=datetime.now()
                    )
                    updates["agent_discussions"].append(strategy_disc)

            duration_ms = int((time.time() - start_time) * 1000)

            # Log the query
            query_log = self.log_query(
                state,
                "JIRA",
                f"Multi-strategy search (tracking_id, error, keywords)",
                result_count=len(all_issues),
                raw_result=all_issues[:5],
                duration_ms=duration_ms
            )
            self._merge_updates(updates, query_log)

            # Analyze issues
            analysis = self._analyze_issues(all_issues)

            jira_data = {
                "found": len(all_issues) > 0,
                "count": len(all_issues),
                "issues": all_issues[:10],
                "analysis": analysis
            }

            if all_issues:
                open_count = sum(1 for i in all_issues if i.get("status") not in ["Done", "Closed", "Resolved"])

                # Report summary findings
                finding = AgentDiscussion(
                    agent=self.name,
                    message=f"[Finding] JIRA search complete!\n" +
                            f"  • Total issues found: {len(all_issues)}\n" +
                            f"  • Open issues: {open_count}\n" +
                            f"  • Has open bugs: {'Yes' if analysis.get('has_open_issues') else 'No'}\n" +
                            (f"  • Top issue: {all_issues[0].get('key')} - {all_issues[0].get('summary', '')[:50]}" if all_issues else ""),
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = f"Found {len(all_issues)} related JIRA issues ({open_count} open)"
            else:
                finding = AgentDiscussion(
                    agent=self.name,
                    message="[Finding] No related JIRA issues found.\n" +
                            "  • This may be a new/unreported issue\n" +
                            "  • Consider creating a new ticket if investigation confirms a bug",
                    message_type="observation",
                    timestamp=datetime.now()
                )
                updates["agent_discussions"].append(finding)
                message = "No related JIRA issues found"

            return {
                **updates,
                "jira_data": jira_data,
                "_message": message
            }

        except Exception as e:
            self.logger.error(f"JIRA search error: {str(e)}", exc_info=True)

            error_disc = AgentDiscussion(
                agent=self.name,
                message=f"[Error] Failed to search JIRA: {str(e)}",
                message_type="observation",
                timestamp=datetime.now()
            )
            updates["agent_discussions"].append(error_disc)

            return {
                **updates,
                "jira_data": {"error": str(e)},
                "_message": f"JIRA error: {str(e)}"
            }

    def _extract_keywords(self, state: InvestigationState) -> List[str]:
        """Extract search keywords from state"""
        keywords = []

        # Transport mode
        transport_mode = state.get("transport_mode")
        if transport_mode and transport_mode != "unknown":
            keywords.append(transport_mode)

        # Issue text keywords
        issue_text = state.get("issue_text", "")
        stopwords = {"the", "a", "an", "is", "are", "not", "for", "and", "or", "load"}
        words = [w.lower() for w in issue_text.split() if len(w) > 3 and w.lower() not in stopwords]
        keywords.extend(words[:5])

        # Error keywords
        redshift_data = state.get("redshift_data", {})
        latest_error = redshift_data.get("latest_error", "")
        if latest_error:
            error_words = [w for w in latest_error.split() if len(w) > 4 and w.isalpha()][:3]
            keywords.extend(error_words)

        return list(set(keywords))[:8]

    def _analyze_issues(self, issues: List[Dict]) -> Dict:
        """Analyze found issues for patterns"""
        if not issues:
            return {"patterns": [], "has_known_bug": False}

        # Count statuses
        status_counts = {}
        for issue in issues:
            status = issue.get("status", "Unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        # Check for open bugs
        has_open_bug = any(
            issue.get("status") not in ["Done", "Closed", "Resolved"]
            for issue in issues
        )

        # Find most common priority
        priority_counts = {}
        for issue in issues:
            priority = issue.get("priority", "Unknown")
            if priority:
                priority_counts[priority] = priority_counts.get(priority, 0) + 1

        return {
            "status_breakdown": status_counts,
            "priority_breakdown": priority_counts,
            "has_open_issues": has_open_bug,
            "total_found": len(issues)
        }
