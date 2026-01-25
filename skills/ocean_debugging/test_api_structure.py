#!/usr/bin/env python3
"""Test API structure without requiring all dependencies"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

print("Testing API structure...")
print()

# Test 1: Check directory structure
print("✅ Test 1: Directory structure")
dirs = [
    "api",
    "api/models",
    "api/routes",
    "api/utils",
    "core",
    "core/models",
    "core/engine",
    "core/clients",
    "core/utils",
    "modes",
    "modes/ocean"
]

for dir_path in dirs:
    if Path(dir_path).exists():
        print(f"  ✅ {dir_path}/")
    else:
        print(f"  ❌ {dir_path}/ NOT FOUND")
        sys.exit(1)

print()

# Test 2: Check API files exist
print("✅ Test 2: API files")
files = [
    "api/__init__.py",
    "api/main.py",
    "api/models/requests.py",
    "api/models/responses.py",
    "api/routes/health.py",
    "api/routes/config.py",
    "api/routes/investigate.py",
    "api/utils/sse.py",
    "api/utils/tracing.py"
]

for file_path in files:
    if Path(file_path).exists():
        print(f"  ✅ {file_path}")
    else:
        print(f"  ❌ {file_path} NOT FOUND")
        sys.exit(1)

print()

# Test 3: Import API models (no heavy dependencies)
print("✅ Test 3: Import API models")
try:
    from api.models.requests import InvestigateRequest
    print(f"  ✅ InvestigateRequest")
except Exception as e:
    print(f"  ❌ InvestigateRequest: {e}")
    sys.exit(1)

try:
    from api.models.responses import InvestigationResponse
    print(f"  ✅ InvestigationResponse")
except Exception as e:
    print(f"  ❌ InvestigationResponse: {e}")
    sys.exit(1)

print()

# Test 4: Import SSE utilities
print("✅ Test 4: Import SSE utilities")
try:
    from api.utils.sse import format_sse_event, convert_datetimes
    print(f"  ✅ format_sse_event")
    print(f"  ✅ convert_datetimes")
except Exception as e:
    print(f"  ❌ SSE utilities: {e}")
    sys.exit(1)

print()

# Test 5: Validate request model
print("✅ Test 5: Validate request model")
try:
    request = InvestigateRequest(case_number="00123456", mode="ocean")
    print(f"  ✅ Valid request: case_number={request.case_number}, mode={request.mode}")
except Exception as e:
    print(f"  ❌ Request validation: {e}")
    sys.exit(1)

# Test invalid mode
try:
    invalid_request = InvestigateRequest(case_number="00123456", mode="invalid")
    print(f"  ❌ Should have rejected invalid mode")
    sys.exit(1)
except ValueError as e:
    print(f"  ✅ Correctly rejected invalid mode")

print()

# Test 6: SSE formatting
print("✅ Test 6: SSE event formatting")
try:
    event = format_sse_event("log", {"message": "test", "level": "info"})
    if 'event: log' in event and 'data:' in event:
        print(f"  ✅ SSE format correct")
    else:
        print(f"  ❌ SSE format incorrect: {event}")
        sys.exit(1)
except Exception as e:
    print(f"  ❌ SSE formatting: {e}")
    sys.exit(1)

print()

# Test 7: Updated config
print("✅ Test 7: Check LLM config updates")
try:
    from core.utils.config import config
    print(f"  ✅ Claude model: {config.CLAUDE_MODEL}")
    if "claude-sonnet-4-5" in config.CLAUDE_MODEL:
        print(f"  ✅ Using Sonnet 4.5")
    else:
        print(f"  ⚠️  Not using Sonnet 4.5 (current: {config.CLAUDE_MODEL})")
except Exception as e:
    print(f"  ❌ Config import: {e}")
    sys.exit(1)

print()
print("="*50)
print("✅ ALL TESTS PASSED!")
print("="*50)
print()
print("Phase 2 implementation complete!")
print()
print("Next steps to run the API:")
print("1. Install dependencies: pip install -r requirements.txt")
print("2. Configure .env file with API keys")
print("3. Run: python -m api.main")
print("4. Test: curl http://localhost:8080/health")
