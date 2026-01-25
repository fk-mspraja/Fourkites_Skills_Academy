"""
Confluence Client
Search wiki documentation for troubleshooting guides and service docs
"""
import os
import logging
from typing import List, Dict, Optional
import httpx

logger = logging.getLogger(__name__)


class ConfluenceClient:
    """Client for Confluence wiki documentation search"""

    def __init__(self):
        self.base_url = os.getenv("CONFLUENCE_URL", "https://fourkites.atlassian.net/wiki")
        self.email = os.getenv("CONFLUENCE_EMAIL")
        self.api_token = os.getenv("CONFLUENCE_API_TOKEN")
        self.default_space = os.getenv("CONFLUENCE_SPACE_KEY", "EI")
        self.timeout = 30.0

        if not self.email or not self.api_token:
            logger.warning("Confluence credentials not configured")

    async def search(
        self,
        cql: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search Confluence using CQL (Confluence Query Language)

        Args:
            cql: Confluence Query Language query
                 Example: "type=page AND space=EI AND text~'ocean tracking'"
            limit: Maximum number of results

        Returns:
            List of:
            {
                "title": str,
                "url": str,
                "excerpt": str,
                "space": str,
                "last_modified": str (ISO)
            }
        """
        try:
            url = f"{self.base_url}/rest/api/content/search"
            params = {"cql": cql, "limit": limit, "expand": "space,history"}
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

                results = data.get("results", [])
                return [
                    {
                        "title": r["title"],
                        "url": f"{self.base_url}{r['_links']['webui']}",
                        "excerpt": r.get("excerpt", ""),
                        "space": r["space"]["name"],
                        "last_modified": r.get("history", {}).get("lastUpdated", {}).get("when")
                    }
                    for r in results
                ]

        except httpx.HTTPStatusError as e:
            logger.error(f"Confluence API HTTP error: {e.response.status_code}")
            return []
        except Exception as e:
            logger.error(f"Confluence API error: {str(e)}")
            return []

    async def search_by_keywords(
        self,
        keywords: List[str],
        space: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Search Confluence by keywords

        Args:
            keywords: List of keywords to search for
            space: Space key (default: EI)
            limit: Maximum results

        Returns:
            List of matching pages
        """
        space_key = space or self.default_space

        # Build CQL query
        keyword_query = " AND ".join([f"text~'{kw}'" for kw in keywords])
        cql = f"type=page AND space={space_key} AND ({keyword_query})"

        return await self.search(cql, limit)

    async def search_troubleshooting(
        self,
        service_name: str,
        issue_keywords: List[str],
        limit: int = 5
    ) -> List[Dict]:
        """
        Search for troubleshooting documentation

        Args:
            service_name: Service name (e.g., "ocean tracking", "callback worker")
            issue_keywords: Keywords describing the issue
            limit: Maximum results

        Returns:
            List of relevant troubleshooting pages
        """
        # Build comprehensive search query
        all_keywords = [service_name, "troubleshooting"] + issue_keywords
        cql_parts = [f"text~'{kw}'" for kw in all_keywords]

        # Search across multiple spaces (EI, PD, TI)
        spaces = ["EI", "PD", "TI"]
        space_query = " OR ".join([f"space={s}" for s in spaces])

        cql = f"type=page AND ({space_query}) AND ({' AND '.join(cql_parts)})"

        return await self.search(cql, limit)

    async def get_page_content(self, page_id: str) -> Optional[str]:
        """
        Get full content of a Confluence page

        Args:
            page_id: Confluence page ID

        Returns:
            Page content in markdown or None if not found
        """
        try:
            url = f"{self.base_url}/rest/api/content/{page_id}"
            params = {"expand": "body.storage"}
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

                # Return storage format (HTML-like)
                return data.get("body", {}).get("storage", {}).get("value")

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get page {page_id}: HTTP {e.response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Failed to get page {page_id}: {str(e)}")
            return None
