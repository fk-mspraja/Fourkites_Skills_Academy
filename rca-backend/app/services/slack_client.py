"""
Slack Client
Search channel history for past similar issues and resolutions
"""
import os
import logging
from typing import List, Dict, Optional
import asyncio
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)


class SlackClient:
    """Client for Slack channel history search"""

    def __init__(self):
        self.bot_token = os.getenv("SLACK_BOT_TOKEN")
        self.workspace = os.getenv("SLACK_WORKSPACE", "fourkites.slack.com")
        self.client = None

        if self.bot_token:
            self.client = WebClient(token=self.bot_token)
        else:
            logger.warning("Slack bot token not configured")

    async def search_messages(
        self,
        query: str,
        count: int = 20
    ) -> List[Dict]:
        """
        Search Slack messages across all channels

        Args:
            query: Search query (e.g., "ocean tracking not working")
            count: Maximum number of results

        Returns:
            List of:
            {
                "text": str,
                "user": str,
                "channel": str,
                "timestamp": str,
                "permalink": str
            }
        """
        if not self.client:
            logger.warning("Slack client not initialized")
            return []

        try:
            # Run blocking Slack SDK call in thread pool
            response = await asyncio.to_thread(
                self.client.search_messages,
                query=query,
                count=count,
                sort="timestamp",
                sort_dir="desc"
            )

            messages = response.get("messages", {}).get("matches", [])

            return [
                {
                    "text": m["text"],
                    "user": m.get("username", "Unknown"),
                    "channel": m.get("channel", {}).get("name", "Unknown"),
                    "timestamp": m["ts"],
                    "permalink": m.get("permalink", ""),
                    "reactions": self._extract_reactions(m)
                }
                for m in messages
            ]

        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return []
        except Exception as e:
            logger.error(f"Slack search error: {str(e)}")
            return []

    async def search_in_channels(
        self,
        query: str,
        channel_names: List[str],
        count: int = 10
    ) -> List[Dict]:
        """
        Search messages in specific channels

        Args:
            query: Search query
            channel_names: List of channel names (e.g., ["support-ocean", "eng-general"])
            count: Maximum results per channel

        Returns:
            List of matching messages
        """
        # Build channel filter
        channel_filter = " OR ".join([f"in:#{ch}" for ch in channel_names])
        full_query = f"{query} ({channel_filter})"

        return await self.search_messages(full_query, count)

    async def get_thread_context(
        self,
        channel_id: str,
        thread_ts: str
    ) -> List[Dict]:
        """
        Get all replies in a thread for context

        Args:
            channel_id: Channel ID
            thread_ts: Thread timestamp

        Returns:
            List of messages in the thread
        """
        if not self.client:
            return []

        try:
            response = await asyncio.to_thread(
                self.client.conversations_replies,
                channel=channel_id,
                ts=thread_ts
            )

            messages = response.get("messages", [])

            return [
                {
                    "text": m["text"],
                    "user": m.get("user", "Unknown"),
                    "timestamp": m["ts"],
                    "is_thread_parent": m.get("thread_ts") == m.get("ts")
                }
                for m in messages
            ]

        except SlackApiError as e:
            logger.error(f"Failed to get thread: {e.response['error']}")
            return []
        except Exception as e:
            logger.error(f"Thread retrieval error: {str(e)}")
            return []

    def _extract_reactions(self, message: Dict) -> List[Dict]:
        """Extract reactions from message"""
        reactions = message.get("reactions", [])
        return [
            {
                "name": r["name"],
                "count": r["count"]
            }
            for r in reactions
        ]

    async def search_similar_issues(
        self,
        issue_description: str,
        service_name: Optional[str] = None
    ) -> List[Dict]:
        """
        Search for similar past issues in support channels

        Args:
            issue_description: Description of the current issue
            service_name: Optional service name to filter by

        Returns:
            List of similar past discussions
        """
        # Common support channels for FourKites
        support_channels = [
            "support-ocean",
            "support-general",
            "eng-support",
            "ops-issues"
        ]

        # Build search query
        query_parts = [issue_description]
        if service_name:
            query_parts.append(service_name)

        query = " ".join(query_parts)

        return await self.search_in_channels(query, support_channels, count=15)
