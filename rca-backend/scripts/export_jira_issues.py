#!/usr/bin/env python3
"""
Export JIRA issues for RCA analysis.
Uses existing JIRA credentials from .env

Usage:
    python scripts/export_jira_issues.py --project MM --days 90
    python scripts/export_jira_issues.py --jql "project = MM AND labels = rca"
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Try loading env manually
    import os
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    key, val = line.strip().split("=", 1)
                    os.environ.setdefault(key, val)

from jira import JIRA


def get_jira_client():
    """Initialize JIRA client"""
    server = os.getenv("JIRA_SERVER", "https://fourkites.atlassian.net")
    email = os.getenv("JIRA_EMAIL") or os.getenv("CONFLUENCE_EMAIL")
    token = os.getenv("JIRA_API_TOKEN") or os.getenv("CONFLUENCE_API_TOKEN")

    if not email or not token:
        print("Error: JIRA credentials not found")
        print("Set JIRA_EMAIL and JIRA_API_TOKEN in .env")
        print("Or CONFLUENCE_EMAIL and CONFLUENCE_API_TOKEN (same Atlassian token)")
        sys.exit(1)

    return JIRA(server=server, basic_auth=(email, token))


def export_issues(jira: JIRA, jql: str, max_results: int = 500) -> list:
    """Export issues matching JQL query"""
    issues = []
    start = 0
    batch_size = 100

    while start < max_results:
        # Use search_issues with use_post=True for JIRA Cloud compatibility
        try:
            batch = jira.search_issues(
                jql,
                startAt=start,
                maxResults=min(batch_size, max_results - start),
                fields="key,summary,description,status,priority,created,updated,assignee,reporter,labels,components",
                json_result=False
            )
        except Exception as e:
            if "deprecated" in str(e).lower():
                # Fallback for newer JIRA Cloud versions
                print(f"Using fallback search method...")
                batch = list(jira.search_issues(jql, startAt=start, maxResults=min(batch_size, max_results - start)))
            else:
                raise

        if not batch:
            break

        for issue in batch:
            issues.append({
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description or "",
                "status": str(issue.fields.status),
                "priority": str(issue.fields.priority) if issue.fields.priority else "None",
                "created": str(issue.fields.created),
                "updated": str(issue.fields.updated),
                "assignee": str(issue.fields.assignee) if issue.fields.assignee else "Unassigned",
                "reporter": str(issue.fields.reporter) if issue.fields.reporter else "Unknown",
                "labels": issue.fields.labels,
                "components": [str(c) for c in (issue.fields.components or [])],
                "url": f"https://fourkites.atlassian.net/browse/{issue.key}",
            })

        start += len(batch)
        print(f"Fetched {len(issues)} issues...")

        if len(batch) < batch_size:
            break

    return issues


def main():
    parser = argparse.ArgumentParser(description="Export JIRA issues for RCA analysis")
    parser.add_argument("--project", "-p", default="MM", help="JIRA project key (default: MM)")
    parser.add_argument("--jql", "-j", help="Custom JQL query")
    parser.add_argument("--days", "-d", type=int, default=90, help="Days of history (default: 90)")
    parser.add_argument("--max", "-m", type=int, default=500, help="Max issues to fetch (default: 500)")
    parser.add_argument("--output", "-o", default="jira_issues.json", help="Output file")

    args = parser.parse_args()

    jira = get_jira_client()

    # Build JQL
    if args.jql:
        jql = args.jql
    else:
        date_filter = (datetime.now() - timedelta(days=args.days)).strftime("%Y-%m-%d")
        jql = f'project = {args.project} AND created >= "{date_filter}" ORDER BY created DESC'

    print(f"JQL: {jql}")
    print(f"Fetching up to {args.max} issues...")

    issues = export_issues(jira, jql, max_results=args.max)
    print(f"\nTotal issues exported: {len(issues)}")

    # Save
    output_data = {
        "jql": jql,
        "exported_at": datetime.now().isoformat(),
        "count": len(issues),
        "issues": issues
    }

    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)
    print(f"Saved to {args.output}")

    # Quick stats
    statuses = {}
    priorities = {}
    for issue in issues:
        statuses[issue["status"]] = statuses.get(issue["status"], 0) + 1
        priorities[issue["priority"]] = priorities.get(issue["priority"], 0) + 1

    print(f"\nBy Status:")
    for s, c in sorted(statuses.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")

    print(f"\nBy Priority:")
    for p, c in sorted(priorities.items(), key=lambda x: -x[1]):
        print(f"  {p}: {c}")

    print(f"\nRun EDA:")
    print(f"  python notebooks/rca_eda.py --input {args.output} --format jira")


if __name__ == "__main__":
    main()
