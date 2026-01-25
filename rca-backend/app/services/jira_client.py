"""
JIRA Client
Search for related issues, past incidents, and known bugs
"""
import os
import logging
from typing import List, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class JIRAClient:
    """Client for JIRA issue search and retrieval"""

    def __init__(self):
        self.base_url = os.getenv("JIRA_SERVER", "https://fourkites.atlassian.net")
        self.email = os.getenv("JIRA_EMAIL")
        self.api_token = os.getenv("JIRA_API_TOKEN")
        self.timeout = 30.0

        if not self.email or not self.api_token:
            logger.warning("JIRA credentials not configured")

    async def search(
        self,
        jql: str,
        max_results: int = 20,
        fields: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Search JIRA using JQL (JIRA Query Language)

        Args:
            jql: JIRA Query Language query
                 Example: "project = SUPPORT AND text ~ 'ocean tracking'"
            max_results: Maximum number of results
            fields: Fields to return (default: key, summary, status, created, updated)

        Returns:
            List of issues with key fields
        """
        if fields is None:
            fields = ["key", "summary", "status", "created", "updated", "priority", "assignee", "reporter"]

        try:
            # Use the new /search/jql endpoint (GET with query params)
            url = f"{self.base_url}/rest/api/3/search/jql"
            params = {
                "jql": jql,
                "maxResults": max_results,
                "fields": ",".join(fields)  # Comma-separated for query param
            }
            auth = (self.email, self.api_token)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    auth=auth,
                    params=params,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()

                issues = data.get("issues", [])
                return [self._format_issue(issue) for issue in issues]

        except httpx.HTTPStatusError as e:
            logger.error(f"JIRA API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"JIRA API error: {str(e)}")
            return []

    def _format_issue(self, issue: Dict) -> Dict:
        """Format JIRA issue for consistent output"""
        fields = issue.get("fields", {})
        return {
            "key": issue.get("key"),
            "url": f"{self.base_url}/browse/{issue.get('key')}",
            "summary": fields.get("summary"),
            "status": fields.get("status", {}).get("name"),
            "priority": fields.get("priority", {}).get("name"),
            "created": fields.get("created"),
            "updated": fields.get("updated"),
            "assignee": fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            "reporter": fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
        }

    async def search_similar_issues(
        self,
        keywords: List[str],
        projects: Optional[List[str]] = None,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for similar issues by keywords

        Args:
            keywords: Keywords to search for
            projects: Project keys to search in (default: SUPPORT, EI, TI)
            max_results: Maximum results

        Returns:
            List of similar issues
        """
        # Build JQL - search across all accessible projects
        keyword_clause = " OR ".join([f'text ~ "{kw}"' for kw in keywords])

        # Optionally filter by specific projects
        if projects:
            project_clause = " OR ".join([f"project = {p}" for p in projects])
            jql = f"({project_clause}) AND ({keyword_clause}) ORDER BY updated DESC"
        else:
            jql = f"({keyword_clause}) ORDER BY updated DESC"

        return await self.search(jql, max_results)

    async def search_by_tracking_id(
        self,
        tracking_id: str,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for issues mentioning a tracking ID

        Args:
            tracking_id: FourKites tracking ID
            max_results: Maximum results

        Returns:
            List of related issues
        """
        jql = f'text ~ "{tracking_id}" ORDER BY updated DESC'
        return await self.search(jql, max_results)

    async def search_by_error_pattern(
        self,
        error_message: str,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for issues with similar error patterns

        Args:
            error_message: Error message to search for
            max_results: Maximum results

        Returns:
            List of issues with similar errors
        """
        # Extract key phrases from error message
        # Remove special characters that break JQL
        clean_error = error_message.replace('"', '\\"').replace("'", "")
        # Take first 100 chars to avoid query length issues
        clean_error = clean_error[:100]

        jql = f'text ~ "{clean_error}" ORDER BY updated DESC'
        return await self.search(jql, max_results)

    async def get_issue(self, issue_key: str) -> Optional[Dict]:
        """
        Get full details of a specific issue

        Args:
            issue_key: JIRA issue key (e.g., "SUPPORT-1234")

        Returns:
            Issue details or None if not found
        """
        try:
            url = f"{self.base_url}/rest/api/2/issue/{issue_key}"
            auth = (self.email, self.api_token)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    auth=auth,
                    timeout=self.timeout
                )
                response.raise_for_status()
                issue = response.json()

                result = self._format_issue(issue)
                # Add description for full issue view
                result["description"] = issue.get("fields", {}).get("description")
                return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Issue {issue_key} not found")
            else:
                logger.error(f"Failed to get issue {issue_key}: HTTP {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to get issue {issue_key}: {str(e)}")
            return None
