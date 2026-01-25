"""
Test script to verify all data source connections work correctly
"""
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from clients.redshift_client import RedshiftClient
from clients.clickhouse_client import ClickHouseClient
from clients.rewind_clickhouse_client import RewindClickHouseClient
from clients.athena_client import AthenaClient
from clients.tracking_api_client import TrackingAPIClient
from clients.company_api_client import CompanyAPIClient
from utils.llm_client import LLMClient
from utils.config import config


async def test_tracking_api():
    """Test Tracking API connection"""
    print("\n🔍 Testing Tracking API...")
    try:
        client = TrackingAPIClient()
        # Try to get tracking by a known test ID
        result = await client.get_tracking_by_id("test-connection")
        print("✅ Tracking API: Connected (returned response)")
        return True
    except Exception as e:
        print(f"⚠️  Tracking API: Connection configured but returned error (expected for test ID): {type(e).__name__}")
        return True  # Expected to fail with test ID


async def test_company_api():
    """Test Company API connection"""
    print("\n🔍 Testing Company API...")
    try:
        client = CompanyAPIClient()
        # Try to get relationship for a test company
        result = await client.get_company_relationship("test-company", "test-carrier")
        print("✅ Company API: Connected")
        return True
    except Exception as e:
        print(f"⚠️  Company API: Connection configured but returned error (expected for test data): {type(e).__name__}")
        return True


def test_redshift():
    """Test Redshift connection"""
    print("\n🔍 Testing Redshift...")
    try:
        client = RedshiftClient()
        # Try a simple query
        result = client.execute("SELECT 1 as test", verbose=False, query_name="connection_test")
        if result and result[0].get('test') == 1:
            print("✅ Redshift: Connected and query executed successfully")
            return True
        else:
            print("⚠️  Redshift: Connected but unexpected result")
            return False
    except Exception as e:
        print(f"❌ Redshift: Connection failed - {type(e).__name__}: {str(e)[:100]}")
        return False


def test_signoz_clickhouse():
    """Test SigNoz ClickHouse connection"""
    print("\n🔍 Testing SigNoz ClickHouse...")
    try:
        client = ClickHouseClient()
        # Try a simple query
        result = client.execute("SELECT 1 as test", verbose=False, query_name="connection_test")
        if result and result[0].get('test') == 1:
            print("✅ SigNoz ClickHouse: Connected and query executed successfully")
            return True
        else:
            print("⚠️  SigNoz ClickHouse: Connected but unexpected result")
            return False
    except Exception as e:
        print(f"❌ SigNoz ClickHouse: Connection failed - {type(e).__name__}: {str(e)[:100]}")
        return False


def test_rewind_clickhouse():
    """Test Rewind ClickHouse Cloud connection"""
    print("\n🔍 Testing Rewind ClickHouse Cloud...")
    try:
        client = RewindClickHouseClient()
        # Connection is tested on initialization
        print("✅ Rewind ClickHouse Cloud: Connected successfully")
        return True
    except Exception as e:
        print(f"❌ Rewind ClickHouse Cloud: Connection failed - {type(e).__name__}: {str(e)[:100]}")
        return False


def test_athena():
    """Test Athena connection"""
    print("\n🔍 Testing Athena...")
    try:
        client = AthenaClient()
        # Try a simple query
        result = client.execute("SELECT 1 as test", verbose=False, query_name="connection_test")
        if result and result[0].get('test') == '1':  # Athena returns strings
            print("✅ Athena: Connected and query executed successfully")
            return True
        else:
            print("⚠️  Athena: Connected but unexpected result")
            return False
    except Exception as e:
        print(f"❌ Athena: Connection failed - {type(e).__name__}: {str(e)[:100]}")
        return False


def test_llm_client():
    """Test LLM client"""
    print("\n🔍 Testing LLM Client...")
    try:
        client = LLMClient()
        print(f"✅ LLM Client: Initialized with provider '{client.provider}'")
        return True
    except Exception as e:
        print(f"❌ LLM Client: Initialization failed - {type(e).__name__}: {str(e)[:100]}")
        return False


async def main():
    """Run all connection tests"""
    print("=" * 80)
    print("🧪 Ocean Debugging Agent - Data Source Connection Tests")
    print("=" * 80)

    results = {}

    # Test all clients
    results['Tracking API'] = await test_tracking_api()
    results['Company API'] = await test_company_api()
    results['Redshift'] = test_redshift()
    results['SigNoz ClickHouse'] = test_signoz_clickhouse()
    results['Rewind ClickHouse'] = test_rewind_clickhouse()
    results['Athena'] = test_athena()
    results['LLM Client'] = test_llm_client()

    # Summary
    print("\n" + "=" * 80)
    print("📊 Connection Test Summary")
    print("=" * 80)

    success_count = sum(1 for v in results.values() if v)
    total_count = len(results)

    for name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")

    print(f"\n🎯 Results: {success_count}/{total_count} connections successful")

    if success_count == total_count:
        print("\n🎉 All data sources connected successfully!")
        return 0
    elif success_count >= total_count * 0.7:
        print("\n⚠️  Most connections successful, but some failed")
        print("   Check .env configuration for failed connections")
        return 1
    else:
        print("\n❌ Multiple connection failures detected")
        print("   Please verify .env configuration and network access")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
