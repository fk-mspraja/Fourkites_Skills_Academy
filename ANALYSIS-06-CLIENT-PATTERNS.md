# Analysis 06: Data Source Clients & Integration Patterns

**Location:** `rca-bot-2.0/poc/*_client.py` + `rewind-app/app/services/*_client.py`
**Total Clients:** 11 in RCA Bot, 8+ in rewind-app
**Overlap:** ~70% duplicate implementations

---

## Executive Summary

Both `rca-bot-2.0` and `rewind-app` implement their own data source clients, creating significant duplication. All clients follow similar patterns but with inconsistent authentication, error handling, and connection management approaches.

**Key Finding:** These clients should be **replaced with MCP servers** to eliminate duplication and provide standardized access.

---

## Client Inventory

### RCA Bot 2.0 Clients (11 total)

| Client | Data Source | Auth Method | Connection | Purpose |
|--------|-------------|-------------|------------|---------|
| `clickhouse_client.py` | SigNoz ClickHouse | Basic (user/pass) | Direct TCP:9000 | Recent logs (30d) |
| `redshift_client.py` | AWS Redshift | IAM/Basic | psycopg2 | Load metadata, DWH |
| `trino_client.py` | Trino/Presto | Basic | HTTP | Historical logs (30-180d) |
| `athena_client.py` | AWS Athena | Boto3/IAM | boto3.client | Alternative to Trino |
| `github_client.py` | GitHub API | PAT (Personal Token) | requests/REST | Code search |
| `graphdb_client.py` | Neo4j | Basic (user/pass) | bolt:// driver | Code graph |
| `jira_client.py` | Jira Cloud | Basic (email/token) | REST API | Issue parsing |
| `tracking_api_client.py` | Tracking API | HMAC-SHA1 | requests/REST | Real-time loads |
| `company_api_client.py` | Company API | HMAC-SHA1 | requests/REST | Network relationships |
| `confluence_client.py` | Confluence Cloud | Basic (email/token) | REST API | Service docs |
| `llm_client.py` | Anthropic/Azure | API Key | REST API | LLM calls |

### rewind-app Clients (8+ total)

| Client | Data Source | Differences from RCA Bot |
|--------|-------------|--------------------------|
| `clickhouse_client.py` | SigNoz ClickHouse | ✅ Thread-local connections (more robust) |
| `rewind_clickhouse_client.py` | Rewind ClickHouse Cloud | ❌ Additional client (RCA Bot doesn't have) |
| `redshift_client.py` | AWS Redshift | ✅ Similar to RCA Bot |
| `athena_client.py` | AWS Athena | ✅ ThreadPoolExecutor for async (better) |
| `tracking_api_client.py` | Tracking API | ✅ Connection pooling |
| `company_api_client.py` | Company API | ✅ Connection pooling |
| `jira_client.py` | Jira Cloud | ✅ Similar to RCA Bot |
| `llm_client.py` | Anthropic/Azure | ✅ Dual provider support |

**Missing in rewind-app:**
- ❌ GitHub client (no code search)
- ❌ Neo4j client (no code graph)
- ❌ Confluence client (no docs)
- ❌ Trino client (uses Athena instead)

---

## Common Patterns

### Pattern 1: Basic Authentication

**Used by:** ClickHouse, Redshift, Neo4j, Jira, Confluence

```python
# Standard pattern
class Client:
    def __init__(self):
        self.host = os.getenv('SERVICE_HOST')
        self.user = os.getenv('SERVICE_USER')
        self.password = os.getenv('SERVICE_PASSWORD')
        self.client = self._connect()

    def _connect(self):
        return library.connect(
            host=self.host,
            user=self.user,
            password=self.password
        )
```

**Pros:**
- Simple to implement
- Works for most internal services

**Cons:**
- Credentials in environment variables
- No rotation support
- No centralized secret management

---

### Pattern 2: HMAC Authentication

**Used by:** Tracking API, Company API

```python
import hmac
import hashlib

class TrackingAPIClient:
    def __init__(self):
        self.app_id = os.getenv('FK_API_APP_ID')
        self.secret = os.getenv('FK_API_SECRET')

    def _sign_request(self, method, path, body=''):
        timestamp = str(int(time.time()))
        message = f"{method}\\n{path}\\n{timestamp}\\n{body}"
        signature = hmac.new(
            self.secret.encode(),
            message.encode(),
            hashlib.sha1
        ).hexdigest()

        return {
            'X-FourKitesDeviceId': self.app_id,
            'X-FourKitesSignature': signature,
            'X-FourKitesTimestamp': timestamp
        }
```

**Pros:**
- Request signing prevents tampering
- Timestamp prevents replay attacks
- Widely used for FourKites internal APIs

**Cons:**
- More complex to implement
- Clock sync required
- Secret management same issue

---

### Pattern 3: Personal Access Token (PAT)

**Used by:** GitHub

```python
class GitHubClient:
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN')
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }

    def search_code(self, query):
        response = requests.get(
            'https://api.github.com/search/code',
            headers=self.headers,
            params={'q': query}
        )
        return response.json()
```

**Pros:**
- Simple bearer token
- GitHub standard

**Cons:**
- Rate limiting (5,000 req/hour authenticated, 60 unauth)
- Token expiration
- Personal tokens not ideal for production

---

### Pattern 4: AWS IAM (Boto3)

**Used by:** Athena, (optional for Redshift)

```python
import boto3

class AthenaClient:
    def __init__(self):
        # Uses AWS credentials from:
        # 1. Environment (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)
        # 2. ~/.aws/credentials
        # 3. IAM role (if on EC2/ECS)
        self.client = boto3.client(
            'athena',
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )

    def execute_query(self, query):
        response = self.client.start_query_execution(
            QueryString=query,
            ResultConfiguration={
                'OutputLocation': os.getenv('ATHENA_OUTPUT_BUCKET')
            }
        )
        return response['QueryExecutionId']
```

**Pros:**
- Standard AWS auth
- Supports IAM roles (best practice)
- Key rotation built-in

**Cons:**
- AWS-specific
- Requires IAM setup

---

## Connection Management Patterns

### Pattern A: Single Connection (Simple)

**Used by:** GitHub, Jira, Confluence, Tracking API, Company API

```python
class Client:
    def __init__(self):
        self.session = requests.Session()
        # Reuse session for all requests
```

**Pros:** Simple, works for REST APIs
**Cons:** No reconnection logic, no pooling

---

### Pattern B: Connection per Request (Naive)

**Used by:** Early versions of some clients

```python
def query(self):
    conn = connect(...)  # New connection every time
    result = conn.execute(...)
    conn.close()
    return result
```

**Pros:** No state management
**Cons:** Slow (connection overhead), resource waste

---

### Pattern C: Thread-Local Connection (Best for ClickHouse)

**Used by:** rewind-app ClickHouse clients

```python
import threading

_local = threading.local()

class ClickHouseClient:
    def get_connection(self):
        if not hasattr(_local, 'client'):
            _local.client = Client(...)
        return _local.client
```

**Why:** ClickHouse throws "Simultaneous queries" error with shared connection
**Pros:** Thread-safe, one connection per thread
**Cons:** Doesn't work across processes (need multiprocessing.local)

---

### Pattern D: Connection Pooling (Best for APIs)

**Used by:** rewind-app API clients

```python
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class APIClient:
    def __init__(self):
        self.session = requests.Session()
        # Connection pool
        adapter = HTTPAdapter(
            pool_connections=10,
            pool_maxsize=50,
            max_retries=Retry(total=3, backoff_factor=0.5)
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
```

**Pros:** Reuses connections, retry logic, handles concurrency
**Cons:** More complex

---

### Pattern E: Auto-Reconnect with Timeout

**Used by:** Redshift, Neo4j (in some implementations)

```python
class RedshiftClient:
    def __init__(self):
        self.connection = None
        self.last_connect_time = 0
        self.timeout = 1800  # 30 minutes

    def get_connection(self):
        now = time.time()
        if not self.connection or (now - self.last_connect_time) > self.timeout:
            self._reconnect()
        return self.connection

    def _reconnect(self):
        if self.connection:
            self.connection.close()
        self.connection = psycopg2.connect(...)
        self.last_connect_time = time.time()
```

**Pros:** Prevents stale connections, automatic recovery
**Cons:** Potential mid-query reconnect issues

---

## Error Handling Patterns

### Pattern 1: Try-Except with Logging

**Most Common:**

```python
def query_data(self):
    try:
        result = self.client.execute(query)
        return result
    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        return None  # or raise
```

**Problems:**
- Generic exception catching
- Returns None (caller must handle)
- No retry logic

---

### Pattern 2: Specific Exception Handling

**Better Approach:**

```python
def query_data(self):
    try:
        result = self.client.execute(query)
        return result
    except TimeoutError:
        logger.warning("Query timed out, retrying...")
        return self._retry_query()
    except ConnectionError as e:
        logger.error(f"Connection lost: {e}")
        self._reconnect()
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise
```

**Pros:** Handles known errors specifically, preserves stack traces
**Cons:** More code

---

### Pattern 3: Progressive Fallback

**Used in:** Load metadata queries

```python
def get_load_metadata(self, tracking_id):
    try:
        # Try fastest source first
        return self.tracking_api.get_load(tracking_id)
    except APIError:
        logger.warning("Tracking API failed, trying Redshift...")

    try:
        # Fallback to DWH
        return self.redshift.query_fact_loads(tracking_id)
    except DatabaseError:
        logger.warning("fact_loads failed, trying validation table...")

    try:
        # Last resort
        return self.redshift.query_validation_data_mart(tracking_id)
    except Exception as e:
        logger.error(f"All sources failed: {e}")
        return None
```

**Pros:** Resilient, tries multiple sources
**Cons:** Slower on failures, complex flow

---

## Performance Characteristics

### Query Times (Typical)

| Client | Operation | Time | Notes |
|--------|-----------|------|-------|
| TrackingAPIClient | get_load() | 200-500ms | Fastest |
| RedshiftClient | query_fact_loads() | 1-3s | Indexed query |
| RedshiftClient | complex join | 5-15s | Depends on data volume |
| ClickHouseClient | recent logs (30d) | 2-5s | Fast columnar DB |
| TrinoClient | historical logs (>30d) | 10-30s | Slower, large dataset |
| AthenaClient | historical query | 5-20s | S3 scan, variable |
| GitHubClient | code search | 2-10s | Rate limited |
| GraphDBClient | code graph | 1-3s | Indexed graph |
| JiraClient | get_issue() | 1-2s | REST API |

### Concurrency Limits

| Client | Max Concurrent | Bottleneck |
|--------|----------------|------------|
| ClickHouse | ~10-20 | Memory limits |
| Redshift | ~50 | Connection pool |
| Trino | ~10 | Query complexity |
| Athena | ~25 | AWS quota |
| GitHub | Rate limit | 5,000/hour authenticated |
| APIs (Tracking, Company) | ~50 | Connection pool |

---

## Configuration Management

### Environment Variables (Typical Setup)

```bash
# ClickHouse
CLICKHOUSE_HOST=clickhouse-host.fourkites.internal
CLICKHOUSE_PORT=9000
CLICKHOUSE_USER=readonly_user
CLICKHOUSE_PASSWORD=***

# Redshift
REDSHIFT_HOST=redshift-host.fourkites.internal
REDSHIFT_PORT=5439
REDSHIFT_DB=dwh
REDSHIFT_USER=readonly
REDSHIFT_PASSWORD=***

# GitHub
GITHUB_TOKEN=ghp_***

# Jira
JIRA_SERVER=https://fourkites.atlassian.net
JIRA_EMAIL=user@fourkites.com
JIRA_API_TOKEN=***

# FourKites APIs (single secret for multiple APIs)
FK_API_APP_ID=airflow-worker
FK_API_SECRET=***  # HMAC-SHA1 secret

# AWS
AWS_REGION=us-east-1
AWS_ACCESS_KEY_ID=***  # Or use IAM role
AWS_SECRET_ACCESS_KEY=***

# Neo4j
NEO4J_URI=bolt://10.70.166.24:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=***

# LLM Providers
ANTHROPIC_API_KEY=sk-ant-***
# OR
AZURE_OPENAI_API_KEY=***
AZURE_OPENAI_ENDPOINT=https://tracy-dev.openai.azure.com/
```

**Problems:**
- No secret rotation
- Cleartext in .env files
- No expiration enforcement
- Manual management

**Should Be:**
- AWS Secrets Manager or HashiCorp Vault
- Auto-rotation
- Short-lived tokens

---

## Duplication Analysis

### Clients Implemented Multiple Times

1. **ClickHouseClient**
   - rca-bot-2.0: Direct connection
   - rewind-app: Thread-local + dual instance (SigNoz + Rewind Cloud)
   - signoz_mcp: MCP server wrapper
   - **3 implementations!**

2. **RedshiftClient**
   - rca-bot-2.0: Basic psycopg2
   - rewind-app: Similar with autocommit
   - mcp-redshift-loads: MCP server (ops schema)
   - historic-redshift-mcp: MCP server (historical)
   - **4 implementations!**

3. **TrackingAPIClient**
   - rca-bot-2.0: Basic requests
   - rewind-app: Connection pooling
   - tracking-api-mcp-server: MCP server
   - **3 implementations!**

4. **JiraClient**
   - rca-bot-2.0: LLM-powered parsing
   - rewind-app: Basic parsing
   - mcp-custom-jira: MCP server
   - neo4j_mcp: Has Jira integration
   - **4 implementations!**

**Total Duplication:** ~70% of clients have 2-4 implementations

---

## Recommendations

### Immediate (Quick Wins)

1. **Standardize Auth Pattern**
   - Use environment variables consistently
   - Document required variables
   - Add validation at startup

2. **Add Connection Pooling**
   - All REST API clients should use connection pools
   - Prevents connection exhaustion

3. **Implement Retry Logic**
   - Exponential backoff for transient failures
   - Max 3 retries
   - Different strategies per error type

### Medium-Term (Refactoring)

4. **Extract Base Client Class**
   ```python
   class BaseClient:
       def __init__(self):
           self._setup_logging()
           self._load_config()
           self._setup_connection()

       def _execute_with_retry(self, operation, max_retries=3):
           # Standard retry logic
           pass

       def _handle_error(self, error):
           # Standard error handling
           pass
   ```

5. **Migrate to MCP Architecture**
   - Replace all clients with MCP calls
   - Single implementation per data source
   - Consistent interface

6. **Add Circuit Breaker**
   - Prevent cascading failures
   - Fast-fail when service is down
   - Auto-recover when service returns

### Long-Term (Production)

7. **Secret Management**
   - AWS Secrets Manager integration
   - Auto-rotation
   - Short-lived credentials

8. **Observability**
   - OpenTelemetry instrumentation
   - Trace every client call
   - Monitor latency, errors, retries

9. **Health Checks**
   - Each client should expose health check
   - Verify connectivity at startup
   - Continuous health monitoring

---

## Migration to MCP Pattern

### Current State (Direct Clients)

```python
# In rca_bot.py
clickhouse = ClickHouseClient()
logs = clickhouse.query_logs(service, start_time, end_time)
```

### Target State (MCP Calls)

```python
# In rca_bot.py
from mcp_client import MCPClient

mcp = MCPClient()
logs = mcp.call('signoz_mcp', 'query_logs', {
    'service': service,
    'start_time': start_time,
    'end_time': end_time
})
```

**Benefits:**
- Single implementation (in MCP server)
- Consistent error handling
- Centralized logging
- Version control (MCP server versioning)
- Testing (mock MCP responses)

---

## Summary

**Current Situation:**
- ⚠️ 11 clients in RCA Bot, 8+ in rewind-app
- ⚠️ ~70% duplication (2-4 implementations per data source)
- ⚠️ Inconsistent patterns (auth, connection, error handling)
- ⚠️ No centralized secret management
- ⚠️ Manual configuration

**Opportunities:**
- ✅ Consolidate into MCP servers (eliminate duplication)
- ✅ Standardize patterns (base client class)
- ✅ Add production features (pooling, retry, circuit breaker)
- ✅ Improve security (secret manager, rotation)
- ✅ Add observability (OpenTelemetry)

**Strategic Value:**
- MCP architecture is the right target
- Need coordinated migration effort
- Opportunity to establish standards

---

**Status:** ✅ Analysis Complete
**Next:** Examine analysis modules (error, code flow, hypothesis generation)
