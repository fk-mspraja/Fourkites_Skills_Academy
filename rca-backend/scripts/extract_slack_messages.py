#!/usr/bin/env python3
"""
Extract messages from a Slack channel for RCA analysis.

Usage:
    python scripts/extract_slack_messages.py --channel support-automation-rca-analysis --days 30

Requirements:
    - SLACK_BOT_TOKEN environment variable set
    - Bot must be added to the channel
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError


def get_channel_id(client: WebClient, channel_name: str) -> str:
    """Get channel ID from channel name"""
    # Remove # if present
    channel_name = channel_name.lstrip('#')

    try:
        # Try public channels first
        result = client.conversations_list(types="public_channel", limit=1000)
        for channel in result.get("channels", []):
            if channel["name"] == channel_name:
                return channel["id"]

        # Try private channels
        result = client.conversations_list(types="private_channel", limit=1000)
        for channel in result.get("channels", []):
            if channel["name"] == channel_name:
                return channel["id"]

        raise ValueError(f"Channel '{channel_name}' not found")

    except SlackApiError as e:
        print(f"Error listing channels: {e.response['error']}")
        raise


def get_channel_messages(
    client: WebClient,
    channel_id: str,
    days: int = 30,
    limit: int = 1000
) -> list:
    """Get messages from a channel"""
    messages = []

    # Calculate oldest timestamp
    oldest = (datetime.now() - timedelta(days=days)).timestamp()

    try:
        cursor = None
        while True:
            result = client.conversations_history(
                channel=channel_id,
                oldest=str(oldest),
                limit=200,
                cursor=cursor
            )

            for msg in result.get("messages", []):
                # Skip bot messages and channel join/leave messages
                if msg.get("subtype") in ["channel_join", "channel_leave", "bot_message"]:
                    continue

                message_data = {
                    "ts": msg.get("ts"),
                    "timestamp": datetime.fromtimestamp(float(msg.get("ts", 0))).isoformat(),
                    "user": msg.get("user"),
                    "text": msg.get("text", ""),
                    "thread_ts": msg.get("thread_ts"),
                    "reply_count": msg.get("reply_count", 0),
                    "files": [f.get("name") for f in msg.get("files", [])],
                }

                # If this is a thread parent with replies, get the replies
                if msg.get("reply_count", 0) > 0:
                    message_data["replies"] = get_thread_replies(
                        client, channel_id, msg["ts"]
                    )

                messages.append(message_data)

            # Check for pagination
            cursor = result.get("response_metadata", {}).get("next_cursor")
            if not cursor or len(messages) >= limit:
                break

        return messages

    except SlackApiError as e:
        print(f"Error fetching messages: {e.response['error']}")
        raise


def get_thread_replies(client: WebClient, channel_id: str, thread_ts: str) -> list:
    """Get replies to a thread"""
    replies = []

    try:
        result = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=100
        )

        for msg in result.get("messages", [])[1:]:  # Skip parent message
            replies.append({
                "ts": msg.get("ts"),
                "timestamp": datetime.fromtimestamp(float(msg.get("ts", 0))).isoformat(),
                "user": msg.get("user"),
                "text": msg.get("text", ""),
            })

        return replies

    except SlackApiError as e:
        print(f"Error fetching replies: {e.response['error']}")
        return []


def get_user_names(client: WebClient, user_ids: set) -> dict:
    """Get user display names from user IDs"""
    user_names = {}

    for user_id in user_ids:
        try:
            result = client.users_info(user=user_id)
            user = result.get("user", {})
            user_names[user_id] = user.get("real_name") or user.get("name", user_id)
        except SlackApiError:
            user_names[user_id] = user_id

    return user_names


def extract_tracking_ids(text: str) -> list:
    """Extract potential tracking IDs from message text"""
    import re

    # Common patterns for tracking IDs, load numbers, containers
    patterns = [
        r'\b(\d{9,12})\b',  # 9-12 digit numbers (tracking IDs)
        r'\b([A-Z]{4}\d{7})\b',  # Container numbers (ABCD1234567)
        r'\bload[:\s#]?(\d+)\b',  # load:123 or load #123
        r'\btracking[:\s#]?(\d+)\b',  # tracking:123
    ]

    found = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found.extend(matches)

    return list(set(found))


def main():
    parser = argparse.ArgumentParser(description="Extract Slack channel messages")
    parser.add_argument("--channel", "-c", required=True, help="Channel name (e.g., support-automation-rca-analysis)")
    parser.add_argument("--days", "-d", type=int, default=30, help="Days of history to fetch (default: 30)")
    parser.add_argument("--output", "-o", default="slack_messages.json", help="Output file (default: slack_messages.json)")
    parser.add_argument("--format", "-f", choices=["json", "markdown"], default="json", help="Output format")

    args = parser.parse_args()

    # Check for token
    token = os.getenv("SLACK_BOT_TOKEN")
    if not token:
        print("Error: SLACK_BOT_TOKEN environment variable not set")
        print("\nTo get a token:")
        print("1. Go to https://api.slack.com/apps")
        print("2. Create or select your app")
        print("3. Go to 'OAuth & Permissions'")
        print("4. Copy the 'Bot User OAuth Token'")
        print("5. Add to .env: SLACK_BOT_TOKEN=xoxb-...")
        print("\nRequired scopes: channels:history, channels:read, users:read, groups:read, groups:history")
        sys.exit(1)

    client = WebClient(token=token)

    print(f"Fetching messages from #{args.channel} (last {args.days} days)...")

    # Get channel ID
    try:
        channel_id = get_channel_id(client, args.channel)
        print(f"Found channel ID: {channel_id}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Get messages
    try:
        messages = get_channel_messages(client, channel_id, days=args.days)
        print(f"Found {len(messages)} messages")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    # Get user names
    user_ids = set()
    for msg in messages:
        if msg.get("user"):
            user_ids.add(msg["user"])
        for reply in msg.get("replies", []):
            if reply.get("user"):
                user_ids.add(reply["user"])

    print(f"Looking up {len(user_ids)} users...")
    user_names = get_user_names(client, user_ids)

    # Replace user IDs with names
    for msg in messages:
        msg["user_name"] = user_names.get(msg.get("user"), msg.get("user"))
        msg["tracking_ids"] = extract_tracking_ids(msg.get("text", ""))
        for reply in msg.get("replies", []):
            reply["user_name"] = user_names.get(reply.get("user"), reply.get("user"))

    # Output
    if args.format == "json":
        output_data = {
            "channel": args.channel,
            "extracted_at": datetime.now().isoformat(),
            "days": args.days,
            "message_count": len(messages),
            "messages": messages
        }

        with open(args.output, "w") as f:
            json.dump(output_data, f, indent=2)
        print(f"Saved to {args.output}")

    else:  # markdown
        output_file = args.output.replace(".json", ".md")
        with open(output_file, "w") as f:
            f.write(f"# Slack Messages from #{args.channel}\n\n")
            f.write(f"Extracted: {datetime.now().isoformat()}\n")
            f.write(f"Messages: {len(messages)}\n\n")
            f.write("---\n\n")

            for msg in sorted(messages, key=lambda x: x.get("ts", ""), reverse=True):
                f.write(f"## {msg.get('timestamp', 'Unknown time')}\n")
                f.write(f"**{msg.get('user_name', 'Unknown')}**\n\n")
                f.write(f"{msg.get('text', '')}\n\n")

                if msg.get("tracking_ids"):
                    f.write(f"*Tracking IDs: {', '.join(msg['tracking_ids'])}*\n\n")

                if msg.get("replies"):
                    f.write("### Replies:\n")
                    for reply in msg["replies"]:
                        f.write(f"- **{reply.get('user_name')}**: {reply.get('text', '')}\n")
                    f.write("\n")

                f.write("---\n\n")

        print(f"Saved to {output_file}")

    # Print summary of tracking IDs found
    all_tracking_ids = []
    for msg in messages:
        all_tracking_ids.extend(msg.get("tracking_ids", []))

    if all_tracking_ids:
        print(f"\nFound {len(set(all_tracking_ids))} unique tracking IDs in messages")
        print("Sample IDs:", list(set(all_tracking_ids))[:10])


if __name__ == "__main__":
    main()
