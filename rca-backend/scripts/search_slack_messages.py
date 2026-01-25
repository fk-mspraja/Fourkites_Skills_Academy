#!/usr/bin/env python3
"""
Search Slack messages using the search API.
Only requires 'search:read' scope (User Token).

Usage:
    python scripts/search_slack_messages.py --query "tracking" --channel support-automation-rca-analysis
    python scripts/search_slack_messages.py --query "error callback" --days 30
"""

import os
import sys
import json
import argparse
import re
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def search_messages(client: WebClient, query: str, channel: str = None, days: int = 30, count: int = 100) -> list:
    """Search Slack messages using search.messages API"""

    # Build search query
    search_query = query
    if channel:
        search_query = f"in:#{channel} {query}"

    # Add date filter
    after_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
    search_query = f"{search_query} after:{after_date}"

    print(f"Search query: {search_query}")

    messages = []
    page = 1

    try:
        while len(messages) < count:
            result = client.search_messages(
                query=search_query,
                sort="timestamp",
                sort_dir="desc",
                count=min(100, count - len(messages)),
                page=page
            )

            matches = result.get("messages", {}).get("matches", [])
            if not matches:
                break

            for msg in matches:
                messages.append({
                    "ts": msg.get("ts"),
                    "timestamp": msg.get("ts"),
                    "text": msg.get("text", ""),
                    "user": msg.get("user", ""),
                    "username": msg.get("username", ""),
                    "channel": msg.get("channel", {}).get("name", ""),
                    "permalink": msg.get("permalink", ""),
                })

            # Check if more pages
            total = result.get("messages", {}).get("total", 0)
            if len(messages) >= total or len(messages) >= count:
                break
            page += 1

        return messages

    except SlackApiError as e:
        print(f"Error searching: {e.response['error']}")
        raise


def extract_tracking_ids(text: str) -> list:
    """Extract potential tracking IDs from message text"""
    patterns = [
        r'\b(\d{9,12})\b',  # 9-12 digit numbers (tracking IDs)
        r'\b([A-Z]{4}\d{7})\b',  # Container numbers (ABCD1234567)
        r'tracking[_\s]?id[:\s]*(\d+)',  # tracking_id: 123
        r'load[_\s]?(?:number|num|#)?[:\s]*([A-Z0-9]+)',  # load_number: ABC123
    ]

    found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)

    return list(set(found))


def main():
    parser = argparse.ArgumentParser(description="Search Slack messages")
    parser.add_argument("--query", "-q", default="tracking error", help="Search query")
    parser.add_argument("--channel", "-c", help="Channel name to search in")
    parser.add_argument("--days", "-d", type=int, default=30, help="Days of history (default: 30)")
    parser.add_argument("--count", "-n", type=int, default=100, help="Max results (default: 100)")
    parser.add_argument("--output", "-o", default="slack_search_results.json", help="Output file")

    args = parser.parse_args()

    # Check for token - can be bot token or user token
    token = os.getenv("SLACK_BOT_TOKEN") or os.getenv("SLACK_USER_TOKEN")
    if not token:
        print("Error: No Slack token found")
        print("Set SLACK_BOT_TOKEN or SLACK_USER_TOKEN in .env")
        sys.exit(1)

    client = WebClient(token=token)

    print(f"Searching for '{args.query}' in last {args.days} days...")
    if args.channel:
        print(f"Channel: #{args.channel}")

    try:
        messages = search_messages(
            client,
            args.query,
            channel=args.channel,
            days=args.days,
            count=args.count
        )
        print(f"Found {len(messages)} messages")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Extract tracking IDs
    all_tracking_ids = []
    for msg in messages:
        ids = extract_tracking_ids(msg.get("text", ""))
        msg["tracking_ids"] = ids
        all_tracking_ids.extend(ids)

    # Save results
    output_data = {
        "query": args.query,
        "channel": args.channel,
        "days": args.days,
        "extracted_at": datetime.now().isoformat(),
        "message_count": len(messages),
        "unique_tracking_ids": list(set(all_tracking_ids)),
        "messages": messages
    }

    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Saved to {args.output}")

    # Print summary
    if all_tracking_ids:
        unique_ids = list(set(all_tracking_ids))
        print(f"\nFound {len(unique_ids)} unique tracking IDs:")
        for tid in unique_ids[:20]:
            print(f"  - {tid}")
        if len(unique_ids) > 20:
            print(f"  ... and {len(unique_ids) - 20} more")

    # Print sample messages
    print(f"\nSample messages:")
    for msg in messages[:5]:
        text = msg.get("text", "")[:150]
        print(f"\n[{msg.get('channel')}] {msg.get('username')}:")
        print(f"  {text}...")
        if msg.get("tracking_ids"):
            print(f"  IDs: {msg['tracking_ids']}")


if __name__ == "__main__":
    main()
