#!/usr/bin/env python3
"""
RCA Support Requests - Exploratory Data Analysis

This script analyzes patterns in support requests to identify:
- Common issue categories
- Frequent root causes
- Time patterns (when issues occur)
- Customer/carrier patterns
- Tracking ID patterns

Usage:
    python notebooks/rca_eda.py --input slack_messages.json
    python notebooks/rca_eda.py --input jira_issues.json
"""

import os
import sys
import json
import re
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd


def load_slack_data(filepath: str) -> pd.DataFrame:
    """Load Slack messages JSON into DataFrame"""
    with open(filepath) as f:
        data = json.load(f)

    messages = data.get("messages", [])
    return pd.DataFrame(messages)


def load_jira_data(filepath: str) -> pd.DataFrame:
    """Load JIRA issues JSON into DataFrame"""
    with open(filepath) as f:
        data = json.load(f)

    if isinstance(data, list):
        return pd.DataFrame(data)
    return pd.DataFrame(data.get("issues", []))


def extract_identifiers(text: str) -> dict:
    """Extract tracking IDs, load numbers, containers from text"""
    if not isinstance(text, str):
        return {}

    result = {
        "tracking_ids": [],
        "load_numbers": [],
        "containers": [],
        "customers": [],
    }

    # Tracking IDs (9-12 digit numbers)
    result["tracking_ids"] = re.findall(r'\b(\d{9,12})\b', text)

    # Container numbers (4 letters + 7 digits)
    result["containers"] = re.findall(r'\b([A-Z]{4}\d{7})\b', text, re.IGNORECASE)

    # Load numbers (various patterns)
    load_patterns = [
        r'load[:\s#]*([A-Z0-9-]+)',
        r'load[_\s]?number[:\s]*([A-Z0-9-]+)',
    ]
    for pattern in load_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        result["load_numbers"].extend(matches)

    # Customer names (after "Customer:" pattern)
    customer_match = re.search(r'customer[:\s]+([A-Za-z0-9\s]+?)(?:\n|$|,|\.)', text, re.IGNORECASE)
    if customer_match:
        result["customers"].append(customer_match.group(1).strip())

    return result


def categorize_issue(text: str) -> list:
    """Categorize issue based on keywords"""
    if not isinstance(text, str):
        return ["unknown"]

    text_lower = text.lower()
    categories = []

    # Issue type patterns
    patterns = {
        "tracking_not_updating": ["not tracking", "no updates", "stale", "not updating", "stopped tracking"],
        "load_not_found": ["load not found", "not found", "missing load", "doesn't exist"],
        "callback_failure": ["callback", "webhook", "notification failed", "not receiving"],
        "wrong_eta": ["wrong eta", "eta issue", "incorrect eta", "eta not", "eta is wrong"],
        "wrong_location": ["wrong location", "incorrect location", "location issue"],
        "carrier_issue": ["carrier", "scac", "carrier file"],
        "validation_error": ["validation", "invalid", "failed to create", "error creating"],
        "network_issue": ["network", "relationship", "not configured"],
        "ocean_tracking": ["ocean", "container", "vessel", "port"],
        "file_processing": ["file", "integration", "processing error", "file not"],
        "api_error": ["api", "timeout", "connection", "500", "error response"],
        "duplicate": ["duplicate", "already exists", "created twice"],
    }

    for category, keywords in patterns.items():
        if any(kw in text_lower for kw in keywords):
            categories.append(category)

    return categories if categories else ["other"]


def analyze_time_patterns(df: pd.DataFrame, time_column: str) -> dict:
    """Analyze when issues occur"""
    if time_column not in df.columns:
        return {}

    # Convert to datetime
    df["parsed_time"] = pd.to_datetime(df[time_column], errors="coerce")
    valid_times = df[df["parsed_time"].notna()]

    if len(valid_times) == 0:
        return {}

    return {
        "by_hour": valid_times["parsed_time"].dt.hour.value_counts().sort_index().to_dict(),
        "by_day_of_week": valid_times["parsed_time"].dt.day_name().value_counts().to_dict(),
        "by_month": valid_times["parsed_time"].dt.month_name().value_counts().to_dict(),
    }


def run_eda(df: pd.DataFrame, text_column: str = "text") -> dict:
    """Run full EDA on the data"""
    results = {
        "total_records": len(df),
        "columns": list(df.columns),
    }

    if text_column not in df.columns:
        print(f"Warning: '{text_column}' column not found. Available: {df.columns.tolist()}")
        return results

    # Extract identifiers from all messages
    print("Extracting identifiers...")
    df["identifiers"] = df[text_column].apply(extract_identifiers)

    all_tracking_ids = []
    all_containers = []
    all_customers = []

    for ids in df["identifiers"]:
        all_tracking_ids.extend(ids.get("tracking_ids", []))
        all_containers.extend(ids.get("containers", []))
        all_customers.extend(ids.get("customers", []))

    results["unique_tracking_ids"] = len(set(all_tracking_ids))
    results["unique_containers"] = len(set(all_containers))
    results["top_customers"] = Counter(all_customers).most_common(20)

    # Categorize issues
    print("Categorizing issues...")
    df["categories"] = df[text_column].apply(categorize_issue)

    all_categories = []
    for cats in df["categories"]:
        all_categories.extend(cats)

    results["issue_categories"] = Counter(all_categories).most_common(20)

    # Time patterns
    time_columns = ["timestamp", "ts", "created", "created_at", "date"]
    for tc in time_columns:
        if tc in df.columns:
            print(f"Analyzing time patterns using '{tc}'...")
            results["time_patterns"] = analyze_time_patterns(df, tc)
            break

    # Text analysis
    print("Analyzing text patterns...")
    all_text = " ".join(df[text_column].dropna().astype(str))
    words = re.findall(r'\b[a-zA-Z]{4,}\b', all_text.lower())

    # Filter out common words
    stop_words = {"this", "that", "with", "have", "from", "they", "been", "were", "said",
                  "each", "which", "their", "there", "about", "would", "could", "should",
                  "customer", "issue", "load", "tracking", "please", "hello", "thanks"}
    filtered_words = [w for w in words if w not in stop_words]

    results["top_words"] = Counter(filtered_words).most_common(30)

    # Sample messages per category
    results["samples_by_category"] = {}
    for cat in [c[0] for c in results["issue_categories"][:5]]:
        samples = df[df["categories"].apply(lambda x: cat in x)][text_column].head(3).tolist()
        results["samples_by_category"][cat] = [s[:200] + "..." if len(s) > 200 else s for s in samples]

    return results


def print_report(results: dict):
    """Print EDA report"""
    print("\n" + "="*60)
    print("RCA SUPPORT REQUESTS - EDA REPORT")
    print("="*60)

    print(f"\n📊 OVERVIEW")
    print(f"   Total Records: {results.get('total_records', 0)}")
    print(f"   Unique Tracking IDs: {results.get('unique_tracking_ids', 0)}")
    print(f"   Unique Containers: {results.get('unique_containers', 0)}")

    print(f"\n📋 ISSUE CATEGORIES")
    for cat, count in results.get("issue_categories", []):
        pct = (count / results.get("total_records", 1)) * 100
        bar = "█" * int(pct / 5)
        print(f"   {cat:25} {count:4} ({pct:5.1f}%) {bar}")

    print(f"\n👥 TOP CUSTOMERS")
    for customer, count in results.get("top_customers", [])[:10]:
        print(f"   {customer:30} {count:4} issues")

    if "time_patterns" in results:
        print(f"\n🕐 TIME PATTERNS")
        by_dow = results["time_patterns"].get("by_day_of_week", {})
        if by_dow:
            print("   By Day of Week:")
            for day, count in sorted(by_dow.items(), key=lambda x: -x[1])[:5]:
                print(f"      {day:12} {count:4}")

    print(f"\n🔤 TOP KEYWORDS")
    for word, count in results.get("top_words", [])[:15]:
        print(f"   {word:20} {count:4}")

    print(f"\n📝 SAMPLE MESSAGES BY CATEGORY")
    for cat, samples in results.get("samples_by_category", {}).items():
        print(f"\n   [{cat.upper()}]")
        for i, sample in enumerate(samples, 1):
            print(f"   {i}. {sample}")

    print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="RCA Support Requests EDA")
    parser.add_argument("--input", "-i", required=True, help="Input JSON file")
    parser.add_argument("--text-column", "-t", default="text", help="Column containing issue text")
    parser.add_argument("--output", "-o", help="Output JSON file for results")
    parser.add_argument("--format", choices=["slack", "jira", "auto"], default="auto")

    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: File not found: {args.input}")
        sys.exit(1)

    print(f"Loading data from {args.input}...")

    # Detect format
    if args.format == "auto":
        with open(args.input) as f:
            data = json.load(f)
        if "messages" in data:
            args.format = "slack"
        elif "issues" in data or (isinstance(data, list) and len(data) > 0 and "key" in data[0]):
            args.format = "jira"
        else:
            args.format = "slack"  # default

    # Load data
    if args.format == "slack":
        df = load_slack_data(args.input)
    else:
        df = load_jira_data(args.input)
        args.text_column = "summary" if "summary" in df.columns else args.text_column

    print(f"Loaded {len(df)} records")
    print(f"Columns: {df.columns.tolist()}")

    # Run EDA
    results = run_eda(df, text_column=args.text_column)

    # Print report
    print_report(results)

    # Save results
    if args.output:
        with open(args.output, "w") as f:
            # Convert non-serializable items
            serializable = {k: v for k, v in results.items() if k != "samples_by_category"}
            serializable["samples_by_category"] = results.get("samples_by_category", {})
            json.dump(serializable, f, indent=2, default=str)
        print(f"\nResults saved to {args.output}")


if __name__ == "__main__":
    main()
