# Analysis 05: rewind-app Architecture & Integration

**Location:** `rewind-app/`
**Technology:** FastAPI (Python 3.10+) + React 18 (Vite)
**Purpose:** Production web UI for load timeline replay and Auto RCA
**Deployed:** http://rewind.fourkites.internal/

---

## Executive Summary

**rewind-app** is the **production-ready web interface** for the Load Replay functionality that exists in `rca-bot-2.0/poc/load_replay.py`. It takes the same concept but implements it with:
- ✅ FastAPI backend with SSE streaming
- ✅ React frontend with progressive loading
- ✅ Multi-worker production deployment (Gunicorn + Kubernetes)
- ✅ Auto RCA feature (beta) with LLM analysis

**Critical Finding:** There are now **TWO implementations** of Load Replay:
1. **`rca-bot-2.0/poc/load_replay.py`** - CLI tool (3,373 lines)
2. **`rewind-app/`** - Web UI (backend + frontend)

Both query the same data sources but with **different architectures**. This is **duplication** that should be consolidated.

---

## Architecture Overview

### Core Pattern: Staged Orchestration

**Same concept as load_replay.py but with dependency stages:**

```
Stage 1: load_metadata (required by all)
   ↓ (sequential)
Stage 2: network_status (required by carrier_files)
   ↓ (sequential)
Stage 3: [PARALLEL EXECUTION]
   - load_creation
   - carrier_files
   - callbacks
   - ocean_events
```

**Performance:**
- Sequential: ~54% slower
- Parallel: Max latency (not sum)
- Results stream progressively via SSE

**Implementation:** `app/api/v1/load.py` + `app/services/orchestrator.py`

---

## Data Sources (7 systems)

### Priority-Based Query Strategy

| Source | Purpose | Fallback Order | Retention |
|--------|---------|---------------|-----------|
| **Tracking API** | Load metadata (fastest) | Priority 1 | Real-time |
| **Company API** | Shipper/carrier info | - | Real-time |
| **Redshift DWH** | Historical load data | Priority 2 (if API fails) | Historical |
| **SigNoz ClickHouse** | Recent logs | Priority 1 for logs | 30 days |
| **Rewind ClickHouse Cloud** | Long-term structured data | Priority 2 for logs | Months |
| **AWS Athena** | Historical logs/files | Priority 3 | 180 days |
| **AWS S3** | File backup paths | - | Archival |

**Smart Fallback Example:**
```python
loads = await tracking_api.search(tracking_id)
if not loads:
    loads = redshift.query("fact_loads", tracking_id)
if not loads:
    loads = redshift.query("load_validation_data_mart", tracking_id)
return loads
```

---

## Key Architecture Patterns

### 1. SSE (Server-Sent Events) Streaming

**Endpoint:** `POST /api/v1/load/search`

**Event Types:**
- `event: log` → Progress messages ("Querying Redshift...")
- `event: data` → Section data payload (load_metadata, carrier_files, etc.)
- `event: error` → Section-specific failures
- `event: complete` → Stream finished

**Frontend Hook:** `useRewindStream()`
```javascript
const {data, errors, isLoading} = useRewindStream(searchParams);
// Automatically handles:
// - Connection lifecycle
// - Event parsing
// - Section-level retry
// - Error handling
```

**Benefits:**
- Progressive loading (users see data as it arrives)
- No timeout issues (long-running queries stream results)
- Section isolation (one failure doesn't block others)
- Retry individual sections without re-querying all

---

### 2. Dual ClickHouse Architecture

**Why Two ClickHouse Instances?**

#### SigNoz ClickHouse (Port 9000, Non-SSL)
- **Table:** `signoz_logs.distributed_logs`
- **Retention:** 30 days
- **Use Case:** Recent file integration logs, application logs
- **Connection:** Thread-local, non-SSL

#### Rewind ClickHouse Cloud (Port 9440, SSL)
- **Tables:** `fact_load_file_records`, `fact_load_file_logs`
- **Retention:** Historical (months)
- **Use Case:** Fallback when SigNoz returns no results
- **Connection:** Thread-local, SSL (cert verification disabled due to issues)

**Query Flow:**
```
Check data age
   ↓
< 30 days? → Query SigNoz ClickHouse
   ↓ (no results)
Fallback → Query Rewind ClickHouse Cloud
   ↓ (no results)
Fallback → Query Athena
```

**Thread Safety:**
```python
# Thread-local connections prevent "Simultaneous queries" error
_local = threading.local()

def get_connection(self):
    if not hasattr(_local, 'client'):
        _local.client = Client(...)
    return _local.client
```

---

### 3. Thread Pool for Blocking I/O

**Problem:** Athena (boto3) and ClickHouse clients are **synchronous**, blocking the async event loop.

**Solution:** ThreadPoolExecutor
```python
_executor = ThreadPoolExecutor(max_workers=10)

async def execute_async(self, query):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_executor, self._execute_sync, query)
```

**Capacity:**
- 10 concurrent Athena queries per worker
- 50 HTTP connections for API calls
- Thread-safe ClickHouse per worker

---

### 4. Query Chunking (Performance)

**Problem:** Athena times out on large date ranges (>30 days)

**Solution:** Split into 7-day chunks
```python
# Config flags
ENABLE_TS_API_CHUNKING=true
ENABLE_CALLBACKS_CHUNKING=true
ENABLE_CARRIER_FILES_CHUNKING=true
```

**Implementation:**
```python
# Split 60-day range into 7-day chunks
chunks = split_date_range(start_date, end_date, days=7)
results = []
for chunk_start, chunk_end in chunks:
    chunk_results = await query_athena(chunk_start, chunk_end)
    results.extend(chunk_results)
```

---

## Production Deployment

### Multi-Worker Configuration

**Development (Single Worker):**
```bash
uvicorn app.main:app --reload
```
- Sequential request processing
- Fine for development
- Not suitable for production

**Production (Multi-Worker):**
```bash
gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8080 \
  --timeout 300
```

**Capacity (4 workers, 2 CPU):**
- **Users:** 40-80 concurrent
- **Queries:** 40 Athena + 200 API calls
- **Memory:** ~2GB per worker
- **Total:** ~8GB for 4 workers

**Kubernetes Deployment:**
- Values: `/Users/arpit.garg/Documents/Arpit/Work/gitrepos_fk/ai-deployments/values/aws/production`
- ArgoCD managed
- Horizontal scaling possible

---

## Auto RCA Feature (Beta)

**What It Does:**
- Accepts Jira ticket or manual text input
- LLM extracts identifiers (tracking_id, load_number, issue category)
- Analyzes errors with pattern grouping
- Generates investigation plan
- Streams progress via SSE

**Supported Issue Categories:**
- ✅ `callback_webhook_failure` - Full LLM analysis
- ✅ `load_creation_failure` - Pattern grouping (no LLM)
- ⏳ Others planned

**LLM Providers:**
- Claude Sonnet 4.5 (Anthropic)
- GPT-4o (Azure OpenAI)

**Key Components:**
- `app/api/v1/rca.py` - Main RCA endpoint
- `app/services/jira_client.py` - Jira parsing
- `app/services/llm_client.py` - Dual provider support
- `app/services/agents/planner/` - Investigation plan generation
- `app/services/agents/validation_error_analyzer.py` - Pattern grouping
- `frontend/src/components/AutoRCAView.jsx` - UI

**Feature Flag:** `ENABLE_AUTO_RCA_FRONTEND=false` (hide in production)

**Database Tables:**
- `raw_data_db.callbacks_v2` (Athena)
- `hadoop.load_validation_data_mart` (Redshift)

---

## Manual Log Search Feature

**Purpose:** Advanced SigNoz ClickHouse search for tech users

**Key Features:**
- Multi-select services (30+ predefined)
- Time modes: Relative (5m, 15m, 1h, 24h, 7d) or Custom datetime
- Search modes: Simple (single string) or Advanced (multiple conditions)
- Operators: `hasToken` (fast, indexed) or `contains` (flexible)
- AND/OR logic with proper parentheses
- Real-time SQL preview
- Export: JSON and CSV
- 200 record limit, no ORDER BY (performance)

**Auto-Fallback:**
```python
# hasToken doesn't support _, -, or spaces
# Backend auto-detects and falls back to LIKE:
if has_special_chars(value):
    query += f"body LIKE '%{value}%'"
else:
    query += f"hasToken(body, '{value}')"
```

**Feature Flag:** `ENABLE_MANUAL_LOG_SEARCH=true`

**Files:**
- `app/api/v1/logs.py` - SSE endpoint (368 lines)
- `app/services/clickhouse_client.py` - Query builder (388 lines)
- `frontend/src/components/ManualLogSearch.jsx` - UI (866 lines)

---

## UI Views

### Three Main Views:

1. **📅 Timeline View** (Default, always visible)
   - Load metadata
   - Network status
   - Load creation source
   - Carrier files
   - Callbacks
   - Ocean events

2. **🤖 Auto RCA** (Beta, flag-controlled)
   - JIRA or manual input
   - LLM identifier extraction
   - Error pattern analysis
   - Investigation plan streaming
   - Feature flag: `ENABLE_AUTO_RCA_FRONTEND`

3. **🔍 Manual Log Search** (Advanced, flag-controlled)
   - Multi-service log search
   - Advanced filtering
   - SQL preview
   - Export capabilities
   - Feature flag: `ENABLE_MANUAL_LOG_SEARCH`

**State Persistence:** All views persist when switching (CSS show/hide, not unmounting)

---

## Comparison: rewind-app vs rca-bot-2.0/poc

### Similarities ✅

| Feature | rewind-app | rca-bot-2.0/poc |
|---------|-----------|----------------|
| Data Sources | Tracking API, Redshift, ClickHouse, Athena | Same |
| Parallel Queries | ✅ Stage 3 sections | ✅ ThreadPoolExecutor |
| Smart Fallbacks | ✅ API → Redshift → validation | ✅ Same logic |
| Load Creation Source | ✅ File vs API detection | ✅ Same |
| Carrier Files | ✅ With external_id lookup | ✅ Same |
| Network Status | ✅ Relationship validation | ✅ Same |
| Error Analysis | ✅ Pattern grouping | ✅ Drain3 + LLM |

### Differences ⚠️

| Aspect | rewind-app | rca-bot-2.0/poc |
|--------|-----------|----------------|
| **Interface** | Web UI (React) | CLI (Rich console) |
| **Streaming** | SSE (Server-Sent Events) | Direct output |
| **Deployment** | Multi-worker Gunicorn + K8s | Single Python script |
| **Architecture** | FastAPI services | Monolithic orchestrator |
| **Code Organization** | `services/sections/` modular | Single 3,373-line file |
| **User Experience** | Progressive loading, retry sections | All-or-nothing |
| **RCA** | Auto RCA (beta, basic) | Full 10-step RCA pipeline |
| **Code Search** | ❌ Not implemented | ✅ GitHub + Neo4j |
| **Code Flow Analysis** | ❌ Not implemented | ✅ Neo4j validation |
| **Hypothesis Generation** | ❌ Not implemented | ✅ LLM-powered |
| **Fix Generation** | ❌ Not implemented | ✅ Code exists |

---

## Integration Analysis

### Shared Clients (Duplication)

Both implementations have their own clients:

| Client | rewind-app | rca-bot-2.0/poc |
|--------|-----------|----------------|
| ClickHouse | `clickhouse_client.py` | `clickhouse_client.py` |
| Redshift | `redshift_client.py` | `redshift_client.py` |
| Tracking API | `tracking_api_client.py` | `tracking_api_client.py` |
| Company API | `company_api_client.py` | `company_api_client.py` |
| Athena/Trino | `athena_client.py` | `trino_client.py` |
| Jira | `jira_client.py` | `jira_client.py` |

**Problem:** 6+ duplicate client implementations!

**Should Be:** One MCP server per data source, both tools use MCP

---

### RCA Capabilities Comparison

#### rewind-app Auto RCA (Basic)
- ✅ JIRA/manual input
- ✅ LLM identifier extraction
- ✅ Callback pattern analysis
- ✅ Load validation error grouping
- ❌ No code search
- ❌ No correlation ID tracing
- ❌ No hypothesis generation
- ❌ Basic pattern grouping (no Drain3)

**Use Case:** Quick issue triage, callback failures

#### rca-bot-2.0 RCA (Advanced)
- ✅ Everything Auto RCA has
- ✅ 10-step pipeline
- ✅ Correlation ID deep dive
- ✅ Dual code search (GitHub + Neo4j)
- ✅ Code flow analysis
- ✅ Drain3 log clustering
- ✅ Hypothesis generation
- ✅ Root cause validation

**Use Case:** Deep RCA, complex multi-service issues

**Opportunity:** Migrate rca-bot-2.0 capabilities to rewind-app

---

## Deployment Information

### Current Status

**rewind-app:**
- ✅ Production deployed: http://rewind.fourkites.internal/
- ✅ Kubernetes managed (ArgoCD)
- ✅ Multi-worker Gunicorn
- ✅ Frontend: Nginx

**rca-bot-2.0/poc:**
- ⚠️ CLI tool (not deployed)
- ⚠️ Manual execution
- ⚠️ POC status

**Web UI for Load Replay (in rca-bot-2.0/poc):**
- ⚠️ Separate implementation (`poc/web_ui/`)
- ⚠️ Not deployed
- ⚠️ Duplicates rewind-app

---

## Critical Gaps & Recommendations

### Immediate Issues

1. **Three Implementations of Load Replay!**
   - `rca-bot-2.0/poc/load_replay.py` (CLI, 3,373 lines)
   - `rca-bot-2.0/poc/web_ui/` (SSE web UI)
   - `rewind-app/` (Production web UI)

   **Problem:** Massive duplication, inconsistent features
   **Solution:** **Consolidate** into one system

2. **RCA Capabilities Split**
   - rewind-app: Basic pattern analysis
   - rca-bot-2.0: Advanced 10-step pipeline

   **Problem:** Users need both tools
   **Solution:** Migrate rca-bot-2.0 RCA to rewind-app backend

3. **Duplicate Clients**
   - 6+ clients implemented twice

   **Problem:** Double maintenance, inconsistent logic
   **Solution:** Create MCP servers, both use MCP

### Recommended Architecture

**Target State:**

```
rewind-app (Production Web UI)
   ↓
FastAPI Backend
   ↓
MCP Protocol
   ↓
[MCP Servers]
   ├─ signoz_mcp (logs)
   ├─ mcp-unified-redshift (DWH)
   ├─ mcp-github (code search)
   ├─ neo4j_mcp (code graph)
   ├─ mcp-tracking-api (real-time)
   ├─ mcp-company-api (network)
   └─ mcp-trino (historical)
```

**Benefits:**
- Single web UI (rewind-app)
- Shared MCP layer (no duplicate clients)
- Advanced RCA (migrate from rca-bot-2.0)
- Modular, testable, maintainable

---

### Migration Path

#### Phase 1: Consolidate Load Replay
1. **Retire:** `rca-bot-2.0/poc/web_ui/` (duplicate)
2. **Keep:** `rewind-app/` as primary web UI
3. **Convert:** `load_replay.py` to library (if needed for CLI use case)

#### Phase 2: Create MCP Layer
1. **Build:** Missing MCP servers (GitHub, Trino, Company API)
2. **Migrate:** rewind-app clients → MCP calls
3. **Retire:** Direct client implementations

#### Phase 3: Integrate Advanced RCA
1. **Migrate:** rca-bot-2.0 RCA logic to rewind-app backend
2. **Add:** Code search to Auto RCA
3. **Add:** Correlation tracing to Auto RCA
4. **Add:** Hypothesis generation to Auto RCA

#### Phase 4: Production Deployment
1. **Deploy:** Enhanced rewind-app with full RCA
2. **Train:** Support team on new features
3. **Retire:** rca-bot-2.0 CLI (if no longer needed)

---

## Performance Characteristics

### rewind-app Production Metrics

**Query Times (Average):**
- Load metadata: 200-500ms (Tracking API)
- Network status: 300-400ms (Company API + Redshift)
- Carrier files: 2-5s (Athena chunked)
- Callbacks: 3-7s (Athena chunked)
- Ocean events: 2-4s (ClickHouse with retry)

**Total Time (Parallel Stage 3):**
- Best case: ~8s (max of all Stage 3 queries)
- Worst case: ~15s (with retries)

**Capacity (4 workers):**
- 40-80 concurrent users
- 120s timeout per request
- ~2GB memory per worker

---

## Summary

**rewind-app Strengths:**
- ✅ Production-ready web UI
- ✅ SSE streaming (great UX)
- ✅ Multi-worker deployment
- ✅ Modular service architecture
- ✅ Section-level retry

**rewind-app Gaps:**
- ⚠️ Basic RCA (not full pipeline)
- ⚠️ No code search
- ⚠️ No correlation tracing
- ⚠️ No Drain3 clustering

**rca-bot-2.0 Strengths:**
- ✅ Advanced 10-step RCA
- ✅ Code search (GitHub + Neo4j)
- ✅ Correlation deep dive
- ✅ Drain3 + LLM pipeline
- ✅ Hypothesis generation

**rca-bot-2.0 Gaps:**
- ⚠️ CLI only (no web UI)
- ⚠️ Monolithic (3,373-line file)
- ⚠️ Not deployed

**Consolidation Opportunity:**
- Merge rca-bot-2.0 RCA capabilities into rewind-app
- Convert clients to MCP architecture
- Single production system with full capabilities

---

**Status:** ✅ Analysis Complete
**Next:** Analyze data source clients and integration patterns
