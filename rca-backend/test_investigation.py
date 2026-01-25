"""
Quick test script for RCA investigation workflow
Run this to verify the backend is working
"""
import asyncio
import sys
from app.models import create_initial_state
from app.agents.workflow import create_rca_workflow


async def test_investigation(issue_text: str):
    """Run a test investigation"""
    print("=" * 80)
    print("MULTI-AGENT RCA INVESTIGATION TEST")
    print("=" * 80)
    print(f"\nIssue: {issue_text}\n")

    # Create initial state
    state = create_initial_state(
        issue_text=issue_text
    )

    print(f"Investigation ID: {state['investigation_id']}\n")
    print("-" * 80)

    # Create and run workflow
    workflow = create_rca_workflow()

    try:
        final_state = await workflow.run(state)

        # Print results
        print("\n" + "=" * 80)
        print("INVESTIGATION RESULTS")
        print("=" * 80)

        # Identifiers
        print("\n1. EXTRACTED IDENTIFIERS:")
        identifiers = final_state.get("identifiers", {})
        if identifiers:
            for key, value in identifiers.items():
                print(f"   - {key}: {value}")
        else:
            print("   (none)")

        print(f"\n2. TRANSPORT MODE: {final_state.get('transport_mode', 'UNKNOWN')}")
        print(f"   ISSUE CATEGORY: {final_state.get('issue_category', 'unknown')}")

        # Agent messages
        print("\n3. AGENT ACTIVITY:")
        for msg in final_state.get("agent_messages", []):
            status_icon = {
                "running": "⏳",
                "completed": "✅",
                "failed": "❌"
            }.get(msg.status.value if hasattr(msg.status, 'value') else msg.status, "•")
            print(f"   {status_icon} {msg.agent}: {msg.message}")

        # Hypotheses
        print("\n4. HYPOTHESES FORMED:")
        hypotheses = final_state.get("hypotheses", [])
        if hypotheses:
            for i, hyp in enumerate(hypotheses, 1):
                conf_pct = f"{hyp.confidence * 100:.0f}%"
                print(f"   {i}. [{conf_pct}] {hyp.description}")
                print(f"      Category: {hyp.category.value if hasattr(hyp.category, 'value') else hyp.category}")
                print(f"      Evidence for: {len(hyp.evidence_for)}, against: {len(hyp.evidence_against)}")
        else:
            print("   (none)")

        # Root cause
        print("\n5. ROOT CAUSE DETERMINATION:")
        root_cause = final_state.get("root_cause")
        if root_cause:
            print(f"   ✅ DETERMINED: {root_cause.description}")
            print(f"   Confidence: {root_cause.confidence * 100:.0f}%")
            print(f"   Category: {root_cause.category.value if hasattr(root_cause.category, 'value') else root_cause.category}")

            print(f"\n   Recommended Actions ({len(root_cause.recommended_actions)}):")
            for action in root_cause.recommended_actions:
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(action.priority, "•")
                print(f"   {priority_icon} [{action.priority.upper()}] {action.description}")
                if action.details:
                    print(f"      → {action.details}")
        elif final_state.get("needs_human"):
            print(f"   ⚠️  HUMAN INPUT REQUIRED")
            print(f"   Question: {final_state.get('human_question', 'N/A')}")
        else:
            print("   ❌ Unable to determine")

        # Data sources queried
        print("\n6. DATA SOURCES QUERIED:")
        queries = final_state.get("executed_queries", [])
        if queries:
            sources = {}
            for q in queries:
                if q.source not in sources:
                    sources[q.source] = []
                sources[q.source].append(q)

            for source, source_queries in sources.items():
                print(f"   • {source}: {len(source_queries)} queries")
                for q in source_queries:
                    duration = f"({q.duration_ms}ms)" if q.duration_ms else ""
                    print(f"     - {q.query[:80]}... {duration}")
        else:
            print("   (none)")

        print("\n" + "=" * 80)
        print("Investigation completed successfully!")
        print("=" * 80)

        return final_state

    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Main entry point"""
    # Test cases
    test_cases = [
        "Load U110123982 is not tracking, customer reports no updates",
        "Container MSCU1234567 missing updates, shipper: ABC Corp, carrier: XYZ Logistics",
        "Tracking ID 614258134 showing wrong ETA",
    ]

    if len(sys.argv) > 1:
        # Use command line argument
        issue_text = " ".join(sys.argv[1:])
        await test_investigation(issue_text)
    else:
        # Use first test case
        print("No issue provided, using test case.\n")
        print("Usage: python test_investigation.py \"Your issue description here\"\n")
        await test_investigation(test_cases[0])


if __name__ == "__main__":
    asyncio.run(main())
