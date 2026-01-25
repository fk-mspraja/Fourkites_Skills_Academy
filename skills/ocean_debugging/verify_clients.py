#!/usr/bin/env python3
"""Quick verification that all data clients are available"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def verify_clients():
    """Verify all client imports work"""
    clients_status = {}

    try:
        from clients.redshift_client import RedshiftClient
        clients_status['RedshiftClient'] = '✅ Available'
    except Exception as e:
        clients_status['RedshiftClient'] = f'❌ {str(e)[:50]}'

    try:
        from clients.clickhouse_client import ClickHouseClient
        clients_status['ClickHouseClient (SigNoz)'] = '✅ Available'
    except Exception as e:
        clients_status['ClickHouseClient (SigNoz)'] = f'❌ {str(e)[:50]}'

    try:
        from clients.rewind_clickhouse_client import RewindClickHouseClient
        clients_status['RewindClickHouseClient'] = '✅ Available'
    except Exception as e:
        clients_status['RewindClickHouseClient'] = f'❌ {str(e)[:50]}'

    try:
        from clients.athena_client import AthenaClient
        clients_status['AthenaClient'] = '✅ Available'
    except Exception as e:
        clients_status['AthenaClient'] = f'❌ {str(e)[:50]}'

    try:
        from clients.tracking_api_client import TrackingAPIClient
        clients_status['TrackingAPIClient'] = '✅ Available'
    except Exception as e:
        clients_status['TrackingAPIClient'] = f'❌ {str(e)[:50]}'

    try:
        from clients.company_api_client import CompanyAPIClient
        clients_status['CompanyAPIClient'] = '✅ Available'
    except Exception as e:
        clients_status['CompanyAPIClient'] = f'❌ {str(e)[:50]}'

    try:
        from clients.jt_client import JustTransformClient
        clients_status['JustTransformClient'] = '✅ Available'
    except Exception as e:
        clients_status['JustTransformClient'] = f'❌ {str(e)[:50]}'

    try:
        from clients.super_api_client import SuperApiClient
        clients_status['SuperApiClient'] = '✅ Available'
    except Exception as e:
        clients_status['SuperApiClient'] = f'❌ {str(e)[:50]}'

    try:
        from clients.salesforce_client import SalesforceClient
        clients_status['SalesforceClient'] = '✅ Available'
    except Exception as e:
        clients_status['SalesforceClient'] = f'❌ {str(e)[:50]}'

    try:
        from utils.llm_client import LLMClient
        clients_status['LLMClient'] = '✅ Available'
    except Exception as e:
        clients_status['LLMClient'] = f'❌ {str(e)[:50]}'

    try:
        from utils.config import config
        clients_status['Config'] = '✅ Available'
    except Exception as e:
        clients_status['Config'] = f'❌ {str(e)[:50]}'

    return clients_status

def check_key_methods():
    """Check that key methods exist in clients"""
    print("\n" + "="*80)
    print("🔍 Checking Key Methods in Data Clients")
    print("="*80)

    from clients.redshift_client import RedshiftClient
    from clients.clickhouse_client import ClickHouseClient
    from clients.tracking_api_client import TrackingAPIClient
    from clients.company_api_client import CompanyAPIClient
    from clients.athena_client import AthenaClient

    methods_to_check = {
        'RedshiftClient': [
            'get_load_by_identifiers',
            'check_network_relationship',
            'get_load_validation_errors',
            'execute'
        ],
        'ClickHouseClient': [
            'execute',
            'build_log_search_query',
            'search_logs_manual'
        ],
        'TrackingAPIClient': [
            'get_tracking_by_id',
            'get_tracking_by_load_number',
            'extract_load_metadata'
        ],
        'CompanyAPIClient': [
            'get_company_relationship',
            'extract_relationship_details'
        ],
        'AthenaClient': [
            'execute',
            'execute_async'
        ]
    }

    for client_name, methods in methods_to_check.items():
        print(f"\n{client_name}:")
        client_class = eval(client_name)
        for method in methods:
            if hasattr(client_class, method):
                print(f"  ✅ {method}()")
            else:
                print(f"  ❌ {method}() - NOT FOUND")

if __name__ == "__main__":
    print("="*80)
    print("🧪 Ocean Debugging Agent - Data Client Verification")
    print("="*80)

    status = verify_clients()

    print("\n📊 Client Availability:")
    for client, status_msg in status.items():
        print(f"  {client}: {status_msg}")

    success_count = sum(1 for s in status.values() if '✅' in s)
    total_count = len(status)

    if success_count == total_count:
        print(f"\n🎉 All {total_count} clients are available!")
        check_key_methods()
        sys.exit(0)
    else:
        print(f"\n⚠️  {success_count}/{total_count} clients available")
        sys.exit(1)
