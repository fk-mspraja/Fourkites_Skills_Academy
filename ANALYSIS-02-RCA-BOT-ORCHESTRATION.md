# Analysis 02: rca_bot.py - RCA Orchestration Logic

**File:** `mcp-servers/rca-bot-2.0/poc/rca_bot.py`
**Size:** ~1,100 lines
**Main Function:** `run_timeout_rca()` - End-to-end RCA orchestration
**Entry Point:** `main()` - Command-line interface

---

## Executive Summary

`rca_bot.py` is the **orchestrator** that coordinates all RCA Bot 2.0 components. It implements a **10-step analysis pipeline** that:

1. ✅ Extracts identifiers from issue descriptions using LLM
2. ✅ Validates identifiers against Redshift (100% confirmed data)
3. ✅ Determines optimal time windows (4-tier priority system)
4. ✅ Queries logs from ClickHouse or Trino (auto-selects based on age)
5. ✅ Traces correlation IDs automatically (daily batch optimization)
6. ✅ Cross-references load states from Redshift
7. ✅ Searches code using BOTH GitHub and Neo4j (parallel comparison)
8. ✅ Analyzes errors using Drain3 FIRST, then LLM (optimal flow)
9. ✅ Extracts domain insights using rules + LLM
10. ✅ Generates comprehensive error analysis report

**Key Innovation:** **Drain3 → LLM** pipeline reduces thousands of logs to ~10-20 patterns BEFORE expensive LLM analysis.

---

## Three Operating Modes

### Mode 1: Jira Issue Analysis
**Command:** `python rca_bot.py ENG-1234 [--post]`

**Flow:**
1. Parse Jira issue → Extract context (summary, description, priority)
2. Use LLM to extract identifiers (tracking IDs, load numbers, shipper, carrier)
3. Validate identifiers in Redshift fact_loads table
4. Run full 10-step RCA pipeline
5. Optionally post results back to Jira with `--post` flag

**Use Cases:**
- Production issues reported via Jira
- Automated RCA for support team tickets
- Historical issue analysis

### Mode 2: Manual Input
**Command:** `python rca_bot.py --manual ["text" | < file | interactive]`

**Flow:**
1. Accept issue description via:
   - Command line argument: `python rca_bot.py --manual "Error: timeout occurred..."`
   - Pipe from file: `cat error.log | python rca_bot.py --manual`
   - Interactive: `python rca_bot.py --manual` (paste and Ctrl+D)
2. Create mock IssueContext (key="MANUAL-001")
3. Run same RCA pipeline as Jira mode
4. Display results to console only (no Jira posting)

**Use Cases:**
- Quick RCA without creating Jira ticket
- Testing RCA bot with custom scenarios
- Ad-hoc analysis from chat/email descriptions

### Mode 3: Load Replay
**Command:** `python rca_bot.py --replay --tracking-id 610038256 [--format json]`

**Flow:**
1. Invoke LoadReplayOrchestrator (separate module)
2. Query multiple data sources in parallel (Redshift, ClickHouse, APIs)
3. Build comprehensive load timeline
4. Output in CLI, JSON, or Markdown format

**Use Cases:**
- Debug stuck loads ("Awaiting Tracking Info")
- Load creation source investigation (File vs API)
- Network relationship validation
- File processing activity audit

**Detailed Coverage:** See `load_replay.py` analysis (next task)

---

## The 10-Step RCA Pipeline

### Step 0: Initialization
**Lines:** 96-113

```python
clickhouse = ClickHouseClient()
github = GitHubClient()
jira = JiraClient()
issue_mapper = IssueMapper()
error_analyzer = ErrorAnalyzer(
    use_drain=True,
    enable_flow_analysis=config.ENABLE_CODE_FLOW_ANALYSIS
)
validator = RootCauseValidator()
```

**Key Decision:**
- Code flow analysis enabled if `ENABLE_CODE_FLOW_ANALYSIS=true` and Neo4j configured
- Drain3 log clustering always enabled (`use_drain=True`)

---

### Step 1: Identifier Extraction (LLM-Powered)
**Lines:** 144-163
**Duration:** ~5-10 seconds

**What It Does:**
1. Sends issue description to LLM (Claude Sonnet 4.5 or GPT-4o)
2. Extracts structured identifiers:
   - `tracking_ids`: [123456, 789012, ...]
   - `load_numbers`: ["ACME12345", ...]
   - `pro_numbers`: ["PRO789", ...]
   - `bol_numbers`: ["BOL456", ...]
   - `shipper_name`: "Walmart"
   - `carrier_name`: "ACME Trucking"
   - `issue_category`: "timeout_performance"
   - `dates_mentioned`: ["2025-12-01 10:30", ...]
   - `sql_queries`: ["SELECT * FROM fact_loads WHERE ...", ...]

3. Normalizes company names to permalinks:
   - "Walmart" → "walmart"
   - "ACME Trucking" → "acme-trucking"
   - Uses `issue_mapper.normalize_company_name()` (best-effort guess)

**Output:**
```
📋 Normalized shipper (guess): Walmart → walmart
   (Will be validated against Redshift companies table)
```

**Why LLM?**
- Handles natural language ("load 123 for Walmart", "tracking id: 456")
- Extracts dates in various formats
- Categorizes issue type automatically
- Identifies SQL queries if user provided them

---

### Step 2: Redshift Validation (REQUIRED)
**Lines:** 166-318
**Duration:** ~2-5 seconds
**Priority:** **HIGHEST** - Most accurate data source

**What It Does:**

#### Step 2a: Validate Shipper Permalink
**Lines:** 194-215

Queries `companies` table to confirm shipper exists:
```sql
SELECT id, permalink, name
FROM platform_shared_db.pgs_company.companies
WHERE (
    permalink = 'walmart' OR
    name ILIKE '%Walmart%'
) AND active = true
```

**Why This Matters:**
- LLM guesses might be wrong ("Walmart Inc" → "walmart-inc" but actual is "walmart")
- Prevents false negatives (no results because wrong permalink)
- Clears shipper filter if validation fails (better to search broadly than miss data)

#### Step 2b: Query fact_loads (Primary Source)
**Lines:** 217-276

**Priority 1 Query:**
```sql
SELECT *
FROM platform_shared_db.platform.fact_loads
WHERE (
    load_id IN (123456, 789012) OR
    load_number IN ('ACME12345') OR
    pro_number IN ('PRO789')
) AND shipper_id = 'walmart'  -- Only if validated
LIMIT 1
```

**Success Case (Load Found):**
```
✅ LOAD FOUND IN FACT_LOADS (100% confirmed):
   🔢 Tracking ID: 123456
   📦 Load Number: ACME12345
   🏢 Shipper ID: walmart
   🚛 Carrier ID: acme-trucking
   📊 Status: Delivered
   📅 Created: 2025-12-01 10:00:00
   🏁 Terminated: 2025-12-01 18:30:00
```

**Benefits:**
- 100% confirmed identifiers (no guessing)
- Accurate timestamps (`created_at`, `terminated_at`)
- Actual shipper/carrier IDs (not normalized guesses)
- Load status (Delivered, Expired, Awaiting Tracking Info)

#### Step 2c: Fallback to load_validation_data_mart
**Lines:** 278-309

If NOT found in fact_loads, check validation table:
```sql
SELECT load_id, load_number, error, processed_at
FROM platform_shared_db.platform.load_validation_data_mart
WHERE load_number IN ('ACME12345') OR load_id IN (123456)
ORDER BY processed_at DESC
```

**Why This Matters:**
- Catches loads that failed creation
- Gets validation errors (schema issues, missing fields, etc.)
- Extracts tracking_id even if load creation failed
- Expands time window to include validation attempts

**Output (Failure Case):**
```
⚠️ Load NOT found in fact_loads
✅ Found 2 validation records in load_validation_data_mart
   Record 1: Load creation failed - Missing required field: carrier_id
   Record 2: Load creation retry succeeded
   ✅ Extracted tracking_id from validation: 123456
```

#### Step 2 Results:

**Updated Identifiers (Confirmed):**
```python
confirmed_identifiers = {
    'tracking_ids': ['123456'],  # Confirmed from database
    'load_numbers': ['ACME12345'],
    'pro_numbers': ['PRO789'],
    'shipper_id': 'walmart',  # Validated permalink
    'carrier_id': 'acme-trucking',  # From fact_loads
    # Preserved from LLM:
    'issue_category': 'timeout_performance',
    'dates_mentioned': ['2025-12-01 10:30'],
    'sql_queries': [...]
}
```

---

### Step 3: Issue Categorization
**Lines:** 337-371
**Duration:** <1 second

**LLM Already Categorized - Use That!**

Instead of keyword matching, use LLM's `issue_category`:

**LLM Categories:**
- `eta_calculation_issue` → Maps to "eta" keyword
- `carrier_update_missing` → Maps to "carrier"
- `load_creation_failure` → Maps to "load creation"
- `load_update_failure` → Maps to "load update"
- `callback_webhook_failure` → Maps to "callback"
- `timeout_performance` → Maps to "timeout"
- `configuration_issue` → Maps to "configuration"
- `data_quality_issue` → Maps to "data quality"
- `other` → Fallback to full issue text

**Mapping to Services:**

Uses `issue_mapper.analyze_issue()` with `issue_mappings.yaml`:
```python
issue_mapping = issue_mapper.analyze_issue("timeout")
# Returns:
{
    'category': 'performance_timeout',
    'services': ['tracking-service-internal', 'global-worker'],
    'github_repos': ['tracking-service', 'global-worker'],
    'dependent_services': ['carrier-files-worker', 'location-worker']
}
```

**Output:**
```
📂 Issue Category (from LLM): timeout_performance
   Using keyword 'timeout' to find services/repos
```

---

### Step 4: Extract Search Keywords
**Lines:** 373-374

**Simple Step:**
```python
search_keyword = jira.extract_issue_keywords(issue)
# Example: "timeout" or "callback failed" or "load creation"
```

Used later for log filtering if no identifiers found.

---

### Step 5: Time Window Determination (4-Tier Priority)
**Lines:** 376-439
**Duration:** <1 second

**CRITICAL:** Accurate time windows = better log quality

**Priority 1: Redshift Load Lifecycle Dates** (Best)
**Lines:** 382-408

If `load_metadata` exists (from Step 2b):
```python
start_log_time = load_metadata['created_at'] - timedelta(hours=1)
end_log_time = load_metadata['terminated_at'] + timedelta(hours=1) if load_metadata['terminated_at']
              else datetime.now(timezone.utc)
```

**Expansion Logic:**
- If validation errors exist outside this window, expand to include them
- Adds ±1 hour buffer for pre/post-load events

**Output:**
```
✅ Using load lifecycle dates from Redshift (Priority 1)
   Tracking ID: 123456
   Shipper: walmart
   Carrier: acme-trucking
   Created: 2025-12-01 10:00:00
   Terminated: 2025-12-01 18:30:00
   📅 Search window: 2025-12-01 09:00 to 2025-12-01 19:30
```

**Priority 2: Validation Error Dates**
**Lines:** 410-423

If fact_loads failed but validation_data_mart has records:
```python
earliest_validation = min(v['processed_at'] for v in validation_errors)
latest_validation = max(v['processed_at'] for v in validation_errors)
start_log_time = earliest_validation - timedelta(hours=6)
end_log_time = latest_validation + timedelta(hours=6)
```

**Priority 3: Dates from Jira Description**
**Lines:** 425-431

LLM extracted dates in Step 1:
```python
if llm_data['dates_mentioned']:
    start_log_time = min(dates_mentioned)
    end_log_time = max(dates_mentioned) + timedelta(hours=2)
```

**Priority 4: Jira Creation Time (Fallback)**
**Lines:** 433-436

Least accurate - issue might be reported hours/days after problem:
```python
start_log_time = issue.created - timedelta(hours=6)
end_log_time = issue.created + timedelta(hours=2)
```

**Why Priority Matters:**
- Priority 1 (Redshift): **±1 hour accuracy**
- Priority 4 (Jira created): **±6 hours accuracy**
- Tighter windows = fewer irrelevant logs = faster analysis

---

### Step 6: Determine Services to Search
**Lines:** 441-457

**Logic:**
1. Use services from `issue_mapping` (Step 3)
2. If no mapping and load_metadata exists, derive from metadata
3. Fallback to `config.DEFAULT_SERVICE` ("tracking-service-internal")

**Example:**
```
✅ Services to search: tracking-service-internal, global-worker
```

**Why Multiple Services?**
- Issues often span multiple microservices
- Example: Timeout in tracking-service might be caused by global-worker delay
- `issue_mappings.yaml` defines cross-service dependencies

---

### Step 7: Query Logs (Auto-select ClickHouse vs Trino)
**Lines:** 459-664
**Duration:** ~10-30 seconds

**Decision Logic:**
```python
days_ago = (datetime.now(timezone.utc) - start_log_time).days

if days_ago > 180:
    # Beyond Trino's 180-day retention
    return None  # Data too old
elif days_ago <= 30:
    # Recent logs - use ClickHouse (faster)
    logs = clickhouse.query_logs(...)
else:
    # 30-180 days - use Trino (historical)
    logs = trino.query_logs(...)
```

#### Path A: ClickHouse (Recent Logs)
**Lines:** 479-539

**Query Pattern:**
```python
for service in services_to_search:
    logs = clickhouse.query_logs(
        service=service,
        start_time=start_log_time,
        end_time=end_log_time,
        severity=["ERROR", "WARN"],
        tracking_ids=confirmed_identifiers['tracking_ids'],
        load_numbers=confirmed_identifiers['load_numbers'],
        pro_numbers=confirmed_identifiers['pro_numbers'],
        bol_numbers=identifiers['bol_numbers'],
        contains=search_keyword,  # Only if no identifiers
        limit=config.MAX_LOGS_INITIAL  # Default: 100
    )
```

**Filtering Strategy:**
1. **Try with identifiers first** (tracking_id, load_number, pro_number, bol)
2. **Fallback to keyword search** if no results with identifiers
3. **Query all mapped services** (tracking-service, global-worker, etc.)

**Output:**
```
📊 Date range is within 30 days, using ClickHouse

🔍 Filtering logs by:
   • Tracking IDs: 123456
   • Load Numbers: ACME12345
   • PRO Numbers: PRO789

   Querying service: tracking-service-internal
   Querying service: global-worker
✅ Found 47 initial logs across 2 services
```

#### Path B: Trino (Historical Logs 30-180 days)
**Lines:** 540-621

**Extended Queries:**
1. **load_files** - Loads created via flat files (30-hour latency, 180-day retention)
2. **ts_api** - API load creation/updates
3. **callbacks_v2** - Customer webhook notifications
4. **signoz logs** - Historical error logs

**Output:**
```
📊 Date range is 45 days ago (within Trino's 180-day retention), using Trino

📋 Querying additional historical data tables...
📊 Historical data summary:
   Load files: 3 records
   API calls: 12 records
   Callbacks: 8 records

   Querying service: tracking-service-internal
   Querying service: global-worker
✅ Found 35 initial logs across 2 services
```

**No Logs Found? STOP**
**Lines:** 623-634

```
❌ UNABLE TO PROCEED - No logs found for the specified time range

Suggestions:
  1. Verify the time range is correct
  2. Check if the issue type mapping is correct (edit issue_mappings.yaml)
  3. Try a different search keyword or remove keyword filter
  4. Check if logs exist for this load in the system
```

---

### Step 7b: Automatic Correlation ID Deep Dive
**Lines:** 636-664
**Duration:** ~15-30 seconds (optimized)
**Only for ClickHouse** (Skip for Trino due to performance)

**CRITICAL OPTIMIZATION:** Daily batch queries (not one-by-one)

**What It Does:**
```python
all_logs = clickhouse.trace_all_correlation_ids(
    initial_logs=initial_logs,  # 47 logs found in Step 7
    start_time=start_log_time,
    end_time=end_log_time,
    max_ids=config.MAX_CORRELATION_IDS,  # Default: 5
    deep_dive=True  # Extract correlation IDs from log bodies
)
```

**Algorithm:**
1. **Extract correlation IDs from initial logs:**
   - `correlation_id` field (structured)
   - `trace_id` field (OpenTelemetry)
   - Log body extraction (regex: `correlation_id:(\S+)`) - if deep_dive=True

2. **For each correlation ID (up to 5):**
   - Query ENTIRE DAY at once (not hour-by-hour):
     ```sql
     SELECT * FROM signoz_logs.distributed_logs
     WHERE toDate(timestamp) = '2025-12-01'
       AND (
         correlation_id = 'abc123' OR
         trace_id = 'abc123' OR
         body LIKE '%abc123%'  -- Only if deep_dive=True
       )
     ORDER BY timestamp
     ```
   - **Performance:** ~3-5 seconds per correlation ID vs 30-50s with hourly queries

3. **Collect all related logs** (following execution traces across services)

**Output:**
```
🔍 AUTOMATIC CORRELATION ID DEEP DIVE
   Extracting ALL correlation IDs from initial logs and tracing complete execution flows...

   Auto-tracing correlation IDs...
   ✅ Auto-traced 5 correlation IDs with deep dive
   ✅ Total logs collected: 234 logs
```

**Why This Matters:**
- A single request might spawn 10+ worker jobs across 3+ services
- Correlation ID links them all together
- Get complete execution timeline (request → worker → callback → response)

---

### Step 7c: Cross-reference Load States
**Lines:** 666-693
**Duration:** ~2-3 seconds

**What It Does:**
Extracts all `tracking_id` values found in logs and queries their current state in Redshift:

```python
tracking_ids_in_logs = set(log.tracking_id for log in all_logs if log.tracking_id)
load_states = redshift.get_load_states(list(tracking_ids_in_logs))
```

**Query:**
```sql
SELECT
    load_id,
    load_number,
    status,
    terminated_at,
    is_deleted
FROM platform_shared_db.platform.fact_loads
WHERE load_id IN (123456, 789012, 456789)
```

**Why This Matters:**
- Logs mention load 123456 - is it still active or terminated?
- Pattern: "Error processing load 789012" - what's the current status?
- Cross-reference: Logs show errors → Load status = "Expired" → Confirms error impact

**Output:**
```
Cross-referencing load states for 3 tracking IDs...
✅ Retrieved states for 3 loads
   • Load 123456: Delivered, Terminated: 2025-12-01 18:30
   • Load 789012: Expired, Terminated: 2025-12-01 15:45
   • Load 456789: Awaiting Tracking Info, Active
```

**Usage in Error Analysis:**
Error analyzer receives `load_states` and can classify:
- "Load 789012 expired" → Expected behavior (load naturally expired)
- "Load 456789 stuck" → Real error (should be tracking)

---

### Step 8: Dual Code Search (GitHub + Neo4j)
**Lines:** 695-773
**Duration:** ~10-20 seconds
**Innovation:** **Parallel execution + comparison**

**Why Dual Search?**
- GitHub: Full-text search across all repos (slower, comprehensive)
- Neo4j: Graph-based search with relationships (faster, contextual)
- Compare results to evaluate which method works better

#### GitHub Search
**Lines:** 703-721

```python
github_results = github.search_classes_from_logs_multi_repo(
    logs=all_logs,
    github_repos=['tracking-service', 'global-worker'],
    max_searches=config.MAX_CODE_SEARCHES  # Default: 3
)
```

**What It Does:**
1. Extract class/method names from logs:
   - "TrackingController#update_tracking" → search: `class:TrackingController function:update_tracking`
   - "UpdateService.process_load" → search: `class:UpdateService function:process_load`

2. Multi-repo search using GitHub Code Search API:
   ```
   repo:fourkites/tracking-service class:TrackingController
   repo:fourkites/global-worker class:UpdateService
   ```

3. Score results by relevance (filename match, class match, line proximity to error)

**Output:**
```
Searching code on GitHub...
   📂 GitHub repos: tracking-service, global-worker
✅ GitHub: Found 8 code locations
```

#### Neo4j Graph Search
**Lines:** 723-741

```python
from graphdb_client import GraphDBClient
graph = GraphDBClient()
neo4j_results = graph.search_code_context(
    logs=all_logs,
    service='tracking-service',
    max_results=config.MAX_CODE_SEARCHES,
    max_class_search=7
)
```

**What It Does:**
1. Extract class names from logs (same as GitHub)
2. Query Neo4j code graph:
   ```cypher
   MATCH (c:Class {name: 'TrackingController'})
   -[:HAS_METHOD]->(m:Method)
   -[:CALLS*1..4]->(downstream:Method)
   RETURN c, m, downstream
   ```

3. Get code context with relationships:
   - Which methods this class calls
   - Which classes call this class
   - 4-level downstream call graph

**Output:**
```
Searching code graph in Neo4j...
   🗄️ Neo4j service: tracking-service
✅ Neo4j: Found 12 code locations
```

#### Comparison Display
**Lines:** 743-760

```
📊 CODE SEARCH COMPARISON:
Source     Score    Repo/File                                   Class
==========================================================================================
GitHub     8.50     tracking-service/controllers/tracking.rb   TrackingController
GitHub     7.20     global-worker/services/update.rb           UpdateService
Neo4j      12.00    tracking-service/services/update.rb        UpdateService
Neo4j      10.50    tracking-service/models/load.rb            Load
Neo4j      9.80     global-worker/workers/process.rb           ProcessWorker
```

**Merge Results:**
**Lines:** 762-773

```python
# Sort by score (descending), deduplicate by file
all_code_results = github_results + neo4j_results
code_locations = []
seen_files = set()

for loc in sorted(all_code_results, key=lambda x: x.score or 0, reverse=True):
    file_key = f"{loc.repo}:{loc.file}"
    if file_key not in seen_files:
        seen_files.add(file_key)
        code_locations.append(loc)
```

**Output:**
```
📋 Using top 15 unique code locations (merged from both sources)
```

**Why Merge?**
- Best of both worlds: GitHub's coverage + Neo4j's context
- Deduplication prevents redundant LLM analysis
- Score-based ranking prioritizes most relevant code

---

### Step 8.5: Fetch Confluence Documentation (Optional)
**Lines:** 775-811
**Duration:** ~3-5 seconds
**Enabled:** `ENABLE_CONFLUENCE_DOCS=true`

**What It Does:**

```python
confluence = ConfluenceClient()

for service in services_to_search:
    context = confluence.get_service_context(
        service_name=service,
        issue_category=llm_category  # From Step 3
    )
    # Fetches:
    # - Architecture docs (design, diagrams)
    # - Troubleshooting docs (runbooks, known issues)
    # - General docs (README, setup guides)

all_docs = []
for ctx in service_contexts:
    all_docs.extend(ctx["architecture_docs"])
    all_docs.extend(ctx["troubleshooting_docs"])
    all_docs.extend(ctx["general_docs"])

confluence_docs_formatted = confluence.format_docs_for_llm(
    all_docs,
    max_total_length=8000  # Token limit
)
```

**Output:**
```
Fetching service documentation from Confluence...
✅ Retrieved 4 Confluence document(s)
```

**Why This Helps:**
- Provides business context to LLM
- Known issues documented in runbooks
- Architecture constraints (e.g., "Service X has 30s timeout")
- Helps LLM classify errors as "expected_behavior" vs "real_error"

---

### Step 9: Analyze Errors with Drain3 + LLM
**Lines:** 813-835
**Duration:** ~20-40 seconds
**CRITICAL:** **Drain3 FIRST, then LLM** (don't reverse!)

**Algorithm Overview:**

1. **Drain3 Log Clustering** (automated pattern discovery)
   ```
   234 logs → ~12 unique patterns

   Pattern 1 (82x): "Timeout waiting for response from [service]"
   Pattern 2 (45x): "Load [tracking_id] not found in database"
   Pattern 3 (31x): "Invalid timestamp format in field [field_name]"
   ...
   ```

2. **For Each Pattern:**
   - Cross-reference with load states
   - Cross-reference with code (which file/class logged this?)
   - **Code flow analysis** (if enabled):
     - Extract actual execution flow from pattern
     - Query Neo4j for expected flow
     - Compare actual vs expected
     - Calculate confidence score
   - Send to LLM with full context:
     ```
     Pattern: "Timeout waiting for response from carrier-files-worker"
     Occurred: 82 times
     Affected loads: 12 loads (show first 3 with states)
     Code: tracking-service/services/update.rb:145
     Flow analysis:
       Expected: UpdateService → CallCarrierFilesWorker → ReceiveResponse
       Actual: UpdateService → CallCarrierFilesWorker → [TIMEOUT - no response]
       Confidence: 85%
     Confluence docs: "Carrier-files-worker has 30s timeout..."

     Question: Is this expected behavior or a real error?
     ```

3. **LLM Classification:**
   ```python
   {
       "pattern": "Timeout waiting for response from [service]",
       "classification": "real_error",
       "explanation": "Service timeout indicates performance issue...",
       "confidence": 0.85,
       "code_reference": "tracking-service/services/update.rb:145",
       "affected_loads": [...]
   }
   ```

**Code:**
```python
error_explanations = error_analyzer.analyze_errors(
    logs=all_logs,  # 234 logs
    code_locations=code_locations,  # 15 unique files
    load_states=load_states,  # 3 loads with states
    max_patterns=10,  # Analyze top 10 patterns
    confluence_docs=confluence_docs_formatted  # Service documentation
)
```

**Output:**
```
Analyzing errors with LLM...
✅ Analyzed 12 error patterns

Error Analysis Summary:

  1. [82x] Timeout waiting for response from carrier-files-worker...
      Classification: real_error
      Explanation: Service timeout indicates carrier-files-worker is overloaded...

  2. [45x] Load [tracking_id] not found in database...
      Classification: expected_behavior
      Explanation: Load queries before creation completes are normal...

  3. [31x] Invalid timestamp format in field [timestamp_field]...
      Classification: real_error
      Explanation: Data quality issue requiring validation fix...
```

**Why Drain3 First?**
- **Without Drain3:** LLM analyzes 234 logs individually → expensive, slow, redundant
- **With Drain3:** LLM analyzes 12 patterns → cheaper, faster, focused
- **Token savings:** ~95% (234 logs vs 12 patterns)
- **Quality improvement:** Patterns reveal systemic issues vs one-off errors

---

### Step 10: Generate Report & Post to Jira
**Lines:** 836-1011
**Duration:** ~2-5 seconds

#### Build Root Cause Object
**Lines:** 844-894

```python
from models import RootCause, Hypothesis, Evidence

# Count error types
expected_errors = [e for e in error_explanations if e.classification == "expected_behavior"]
real_errors = [e for e in error_explanations if e.classification == "real_error"]

# Build hypothesis statement
if real_errors:
    top_error = real_errors[0]
    hypothesis_statement = f"Primary issue: {top_error.pattern[:150]}"
    likelihood = "high" if len(real_errors) >= 2 else "medium"
else:
    top_error = expected_errors[0]
    hypothesis_statement = f"Most common pattern: {top_error.pattern[:150]}"
    likelihood = "low"

# Create hypothesis
hypothesis = Hypothesis(
    statement=hypothesis_statement,
    evidence=f"Analyzed {len(error_explanations)} error patterns: "
            f"{len(expected_errors)} expected, {len(real_errors)} require attention",
    likelihood=likelihood,
    confidence=0.8 if real_errors else 0.6
)

# Create evidence from top 5 patterns
evidence_list = []
for exp in error_explanations[:5]:
    evidence_list.append(Evidence(
        type="log_pattern",
        source="tracking-service-internal",
        content=f"Pattern occurred {exp.count} times: {exp.pattern[:200]}",
        explanation=exp.explanation,
        confidence=0.9 if exp.classification == "real_error" else 0.7
    ))

# Create RootCause object
root_cause = RootCause(
    hypothesis=hypothesis,
    confidence=hypothesis.confidence,
    evidence=evidence_list
)
```

#### Generate Markdown Report
**Lines:** 902-949

```markdown
## Error Analysis Report

**Total Logs Analyzed:** 234
**Error Patterns Found:** 12
**Analysis Time:** 45.3s

---

### 1. Error Pattern (occurred 82 times)

**Pattern:** `Timeout waiting for response from carrier-files-worker`

**Classification:** Real Error

**Explanation:** Service timeout indicates carrier-files-worker is overloaded or experiencing latency issues. This causes downstream timeouts in tracking-service.

**Code Reference:** tracking-service/services/update.rb:145

**Reasoning:** Expected flow includes response within 30s. Actual flow shows no response, indicating worker is stuck or slow.

**Affected Loads:** 12
- Load 123456 (ACME12345): Status=Expired, Terminated=2025-12-01 15:45, Errors=8
- Load 789012 (WALMART789): Status=Delivered, Terminated=2025-12-01 18:30, Errors=3
- Load 456789 (TARGET456): Status=Awaiting Tracking Info, Active, Errors=5

---

### 2. Error Pattern (occurred 45 times)

**Pattern:** `Load [tracking_id] not found in database`

**Classification:** Expected Behavior

**Explanation:** Load queries before creation completes are normal. System queues the load for creation and retries after 5 seconds.

...
```

#### Domain Insights Extraction
**Lines:** 937-949

```python
domain_extractor = DomainInsightExtractor()
domain_insights = domain_extractor.extract(
    logs=all_logs,
    load_states=load_states,
    services=services_to_search
)
# Uses domain_rules.yaml to identify known patterns:
# - stop_departure failures
# - arrival event issues
# - ETA calculation problems
# etc.

if domain_insights:
    error_report += domain_extractor.to_markdown(domain_insights)
```

**Example Output:**
```markdown
## Domain-Specific Insights

### Stop Departure Failures
- **Pattern:** Missing departure events for 5 loads
- **Impact:** High - affects ETA calculations
- **Recommendation:** Check location provider connectivity
```

#### Post to Jira
**Lines:** 954-964

```python
if post_to_jira and config.ENABLE_JIRA_POSTING:
    jira.post_rca(issue_key, report)
    # Posts as comment to Jira issue
```

**Conditional:**
- `--post` flag provided in command line
- `ENABLE_JIRA_POSTING=true` in config

#### Create RCAResult Object
**Lines:** 966-975

```python
result = RCAResult(
    issue_key=issue.key,
    root_cause=root_cause,
    fix=None,  # Fix generation removed in current version
    logs_analyzed=len(all_logs),
    correlation_ids=correlation_ids,
    analysis_time_seconds=analysis_time,
    report=report
)
```

#### Display Summary
**Lines:** 977-1009

```
==================================================
✅ RCA COMPLETE
==================================================

Issue: ENG-1234
Error Patterns Analyzed: 12
Logs Analyzed: 234
Analysis Time: 45.3s

Classification Breakdown:
  ✓ Expected Behavior: 7 patterns
  ⚠ Real Errors: 5 patterns

Top Error Patterns:
  1. [82x] ✓ Timeout waiting for response from carrier-files-worker
  2. [45x] ✓ Load [tracking_id] not found in database
  3. [31x] ⚠ Invalid timestamp format in field [timestamp_field]

==================================================
[Full Error Analysis Report]
==================================================
```

---

## Main Entry Point

### main() Function
**Lines:** 1014-1120

**Responsibilities:**
1. Validate configuration (`config.validate()`)
2. Parse command-line arguments
3. Route to appropriate mode:
   - `--replay` → Load Replay mode
   - `--manual` → Manual input mode
   - `<ISSUE_KEY>` → Jira mode

**Command Line Parsing:**

```python
# Load Replay Mode
if "--replay" in sys.argv:
    orchestrator = LoadReplayOrchestrator()
    result = orchestrator.replay_load(
        tracking_id=tracking_id,
        load_number=load_number,
        shipper_id=shipper_id,
        output_format=output_format  # cli, json, markdown
    )

# Manual Mode
elif sys.argv[1] == "--manual":
    # Read from: CLI arg, stdin pipe, or interactive
    result = run_timeout_rca(
        issue_key=None,
        manual_input=manual_text,
        post_to_jira=False
    )

# Jira Mode
else:
    issue_key = sys.argv[1]
    post_to_jira = "--post" in sys.argv
    result = run_timeout_rca(
        issue_key=issue_key,
        manual_input=None,
        post_to_jira=post_to_jira
    )
```

**Help Output:**
```
🤖 RCA Bot 2.0 - Root Cause Analysis Tool

Usage:
  Jira mode:     python rca_bot.py <JIRA_ISSUE_KEY> [--post]
  Manual mode:   python rca_bot.py --manual [TEXT]
  Load Replay:   python rca_bot.py --replay --tracking-id <ID> [OPTIONS]

Options:
  --post           Post RCA results back to Jira (Jira mode only)
  --manual         Enter manual mode (accepts text as argument, from stdin, or interactively)
  --replay         Load Replay mode - unified timeline of all events for a load
  --tracking-id    Load tracking ID (for replay mode)
  --load-number    Load number (requires --shipper)
  --shipper        Shipper company ID (permalink)
  --format         Output format: cli, json, markdown (default: cli)
  --help, -h       Show this help message

Examples:
  # Analyze Jira issue (read-only)
  python rca_bot.py TRACNG-1234

  # Analyze and post results to Jira
  python rca_bot.py TRACNG-1234 --post

  # Manual mode with text as argument
  python rca_bot.py --manual "Error: timeout occurred..."

  # Manual mode with pipe from file
  cat error.log | python rca_bot.py --manual

  # Manual mode interactive (paste and Ctrl+D)
  python rca_bot.py --manual

  # Load Replay by tracking ID
  python rca_bot.py --replay --tracking-id 610038256

  # Load Replay by load number (requires shipper)
  python rca_bot.py --replay --load-number ACME12345 --shipper walmart

  # Load Replay with JSON output
  python rca_bot.py --replay --tracking-id 610038256 --format json
```

---

## Key Design Patterns

### 1. Progressive Enhancement Pattern

The bot has **fallback layers** at every step:

**Identifier Validation:**
- Try: Redshift fact_loads (100% confirmed)
- Fallback 1: load_validation_data_mart (partial data)
- Fallback 2: LLM extraction (best-effort guess)

**Time Window Determination:**
- Priority 1: Redshift lifecycle dates (±1 hour accuracy)
- Priority 2: Validation error dates (±6 hours)
- Priority 3: LLM extracted dates (±2 hours)
- Priority 4: Jira creation time (±6 hours)

**Log Query:**
- Try: Identifiers (tracking_id, load_number, etc.)
- Fallback: Keyword search
- Fallback: All ERROR/WARN logs in time window

### 2. Dual Code Search Pattern

**Why Both GitHub AND Neo4j?**
- GitHub: Comprehensive but slow (API rate limits)
- Neo4j: Fast but requires graph build/maintenance
- **Solution:** Run both in parallel, compare results
- **Outcome:** User sees which method works better

**Benefits:**
- No vendor lock-in (can switch based on performance)
- Cross-validation (both find same code = higher confidence)
- Evaluation data (which search works better?)

### 3. Drain3 → LLM Pipeline Pattern

**Problem:** Analyzing 234 logs with LLM is expensive/slow

**Solution:**
1. **Drain3 clusters logs into patterns** (automated, no LLM)
   - 234 logs → ~12 patterns
   - Groups similar messages: "Load 123 failed" + "Load 456 failed" → "Load <*> failed"

2. **LLM analyzes patterns, not logs** (focused, efficient)
   - Each pattern gets full context (code, flow, load states, docs)
   - Classification: expected_behavior vs real_error
   - Explanation with reasoning

**Benefits:**
- 95% token savings (234 logs → 12 patterns)
- Better quality (patterns reveal systemic issues)
- Faster execution (~20s vs ~2min)

### 4. Code Flow Analysis Pattern

**Flow:**
1. Extract actual execution from logs:
   ```
   Actual: UpdateService.update → CallWorker → [TIMEOUT]
   ```

2. Query Neo4j for expected flow:
   ```cypher
   MATCH (entry:Method {name: 'update'})
   -[:CALLS*1..4]->(downstream:Method)
   RETURN downstream
   ```
   ```
   Expected: UpdateService.update → CallWorker → ReceiveResponse → SaveResult
   ```

3. Compare:
   ```
   Missing: ReceiveResponse, SaveResult
   Unexpected: [TIMEOUT]
   Confidence: 85%
   ```

4. LLM receives comparison and classifies:
   ```
   Is Expected: ❌
   Reasoning: Expected flow includes response, actual shows timeout
   Classification: real_error
   ```

**Why This Matters:**
- Distinguishes "expected retries" from "unexpected failures"
- Validates business logic (is system working as designed?)
- Increases classification confidence (Neo4j = source of truth)

### 5. Load State Cross-Reference Pattern

**Problem:** Logs alone don't tell if issue was resolved

**Solution:**
1. Extract tracking_ids from logs (123, 456, 789)
2. Query current state in Redshift:
   ```
   123 → Delivered (resolved)
   456 → Expired (failed)
   789 → Awaiting Tracking Info (stuck)
   ```

3. Error analyzer sees:
   ```
   "Error processing load 456" + Load 456 status=Expired
   → Classification: real_error (load failed)

   "Error processing load 123" + Load 123 status=Delivered
   → Classification: expected_behavior (transient error, recovered)
   ```

**Benefits:**
- Outcome-based classification (did load succeed?)
- Prioritizes stuck loads (789) over recovered loads (123)
- Confirms error impact (expired loads = real problem)

---

## Integration with Other Components

### Called Clients & Modules

**Data Clients:**
- `ClickHouseClient` - Log queries (recent, <30 days)
- `TrinoClient` - Historical logs (30-180 days)
- `RedshiftClient` - Load metadata, validation, company lookups
- `GitHubClient` - Code search across repos
- `GraphDBClient` (Neo4j) - Code graph search
- `ConfluenceClient` - Service documentation

**Analysis Modules:**
- `ErrorAnalyzer` - Drain3 + LLM error analysis
- `DomainInsightExtractor` - Business logic extraction (rules + LLM)
- `RootCauseValidator` - Evidence validation (not used in current flow)

**Utility Modules:**
- `JiraClient` - Issue parsing, identifier extraction, date parsing, RCA posting
- `IssueMapper` - Issue categorization, service mapping (`issue_mappings.yaml`)
- `config` - Configuration management

**Data Models:**
- `IssueContext` - Parsed Jira issue
- `LogEntry` - Structured log with correlation IDs
- `CodeLocation` - GitHub/Neo4j code reference
- `ErrorExplanation` - Drain pattern + LLM classification
- `Hypothesis` - Root cause theory
- `Evidence` - Supporting evidence
- `RootCause` - Hypothesis + evidence
- `RCAResult` - Complete RCA output

### Configuration Dependencies

**Required:**
- `CLICKHOUSE_HOST`, `CLICKHOUSE_USER`, `CLICKHOUSE_PASSWORD`
- `GITHUB_TOKEN`
- `ANTHROPIC_API_KEY` or `AZURE_OPENAI_API_KEY`

**Recommended:**
- `REDSHIFT_HOST`, `REDSHIFT_USER`, `REDSHIFT_PASSWORD`
- `NEO4J_URI`, `NEO4J_USERNAME`, `NEO4J_PASSWORD`
- `ENABLE_LOAD_METADATA_LOOKUP=true`
- `ENABLE_CODE_FLOW_ANALYSIS=true`

**Optional:**
- `TRINO_HOST` (for historical logs >30 days)
- `CONFLUENCE_URL`, `ENABLE_CONFLUENCE_DOCS=true`
- `JIRA_EMAIL`, `JIRA_API_TOKEN` (for Jira mode)
- `ENABLE_JIRA_READING=true`, `ENABLE_JIRA_POSTING=true`

**Tuning:**
- `MAX_LOGS_INITIAL=100` - Initial log fetch size
- `MAX_CORRELATION_IDS=5` - How many correlation IDs to trace
- `MAX_CODE_SEARCHES=3` - GitHub API calls per RCA

---

## Performance Characteristics

**Typical RCA Timeline:**
- Step 1 (LLM extraction): ~5-10s
- Step 2 (Redshift validation): ~2-5s
- Step 5 (Time window): <1s
- Step 7 (Log query): ~10-15s
- Step 7b (Correlation tracing): ~15-30s
- Step 7c (Load states): ~2-3s
- Step 8 (Code search): ~10-20s (parallel)
- Step 9 (Error analysis): ~20-40s
- **Total:** ~45-60 seconds

**Bottlenecks:**
1. Correlation ID tracing (15-30s) - optimized with daily batches
2. LLM error analysis (20-40s) - can't optimize further
3. Code search (10-20s) - GitHub API rate limited

**Optimizations Applied:**
- ✅ Daily batch correlation queries (vs hourly)
- ✅ Drain3 before LLM (95% token savings)
- ✅ Parallel GitHub + Neo4j search
- ✅ Redshift validation (accurate time windows)
- ✅ Identifier filtering (vs keyword search)

**Potential Improvements:**
- Cache code search results (same class searched repeatedly)
- Pre-compute common patterns (via ML classifier)
- Async correlation tracing (background workers)

---

## Gaps & Opportunities

### What's Working Well ✅

1. **Multi-mode flexibility** - Jira, Manual, Load Replay
2. **Progressive fallbacks** - Never fails, always tries alternatives
3. **Dual code search** - Comparison data for evaluation
4. **Drain3 → LLM** - Optimal token usage
5. **Code flow analysis** - Neo4j validation of execution
6. **Load state cross-reference** - Outcome-based classification
7. **Redshift validation** - 100% confirmed identifiers

### What's Missing ⚠️

1. **No MCP Architecture** - Everything is monolithic clients
   - Should be: `mcp-redshift.query_loads()` via MCP protocol
   - Current: `RedshiftClient().get_load_by_identifiers()`

2. **No First-Focus Routing** - Services determined by keyword matching
   - Should be: Decision tree ("For stuck load, check network first, then files, then logs")
   - Current: Generic service list from `issue_mappings.yaml`

3. **No Multi-Agent Orchestration** - Single sequential flow
   - Should be: LangGraph with parallel agents (logs agent + code agent + docs agent)
   - Current: One orchestrator doing everything

4. **No Fix Generation** - Only explains errors
   - Code has `FixGenerator` but it's not called
   - Should generate code fixes with unit tests

5. **No Hypothesis Validation** - Old validator not used
   - Code has `RootCauseValidator` but skipped
   - Should validate evidence quality/relevance

6. **No Visual Timeline** - Text-only reports
   - Should generate Mermaid sequence diagrams
   - Show execution flow visually

7. **No Feedback Loop** - No learning from outcomes
   - Should track: Was RCA helpful? Was classification correct?
   - Use feedback to improve classifier

8. **No Batch Mode** - One issue at a time
   - Should process multiple Jira issues in parallel
   - Generate summary reports (top 10 systemic issues)

9. **Limited Cross-Service Analysis** - `issue_mappings.yaml` has dependency mapping but underutilized
   - Should automatically follow message flow across services
   - Example: Timeout in tracking-service → Check global-worker → Check carrier-files-worker

10. **No Support SQL Catalog Integration** - Mentioned in conversation but not implemented
    - Should leverage Notion-based SQL catalog from support team
    - Human-validated queries for common issues

---

## How This Fits Into Requirements

### From Original Spec:

**✅ Achieved:**
- End-to-end orchestration (10 steps)
- LLM-powered identifier extraction
- Database validation (Redshift)
- Automated correlation tracing
- Dual code search (GitHub + Neo4j)
- Drain3 log clustering
- Code flow analysis
- Error classification
- Report generation

**⚠️ Partially Achieved:**
- Multi-mode support (Jira, Manual, Replay) ✅
- Cross-service analysis (mappings exist but underutilized) ⚠️
- Domain insights (rules-based, not ML) ⚠️

**❌ Missing:**
- MCP architecture (monolithic clients)
- Multi-agent orchestration (LangGraph)
- First-focus routing logic
- Fix generation (code exists but not called)
- Hypothesis validation (code exists but not used)
- Visual timeline generation
- Feedback loop / continuous learning
- Support SQL catalog integration

---

## Recommendations

### Short-Term (Quick Wins)

1. **Enable Fix Generation** - Uncomment/fix `FixGenerator` code
   - Already exists in codebase (`fix_generator.py`)
   - Just needs integration in Step 10

2. **Enhance Cross-Service Analysis** - Better utilize `dependent_services` from `issue_mappings.yaml`
   - Automatically query dependent services
   - Follow message flow (carrier-files-worker → global-worker → location-worker)

3. **Integrate Support SQL Catalog** - Add Notion API client
   - Query support team's proven SQL queries
   - Use for "similar issue" matching

4. **Add Visual Timeline** - Generate Mermaid diagrams
   - Show execution flow from correlation IDs
   - Embed in reports

### Medium-Term (Refactoring)

5. **Convert Clients to MCP Servers** - Decouple data access
   - `RedshiftClient` → `mcp-redshift-loads` server
   - `ClickHouseClient` → `signoz_mcp` server
   - `GraphDBClient` → `neo4j_mcp` server

6. **Add First-Focus Routing** - Decision trees per issue category
   - "Awaiting Tracking Info" → Network relationships first
   - "Timeout" → Performance metrics first
   - "Callback failure" → Webhook logs first

7. **Implement Feedback Loop** - Track RCA outcomes
   - Was classification correct? (user feedback)
   - Did fix work? (automated testing)
   - Use to fine-tune classifier

### Long-Term (Architecture)

8. **LangGraph Multi-Agent** - Parallel evidence collection
   - Logs agent, Code agent, Docs agent, Metrics agent
   - Each runs independently, coordinator merges results

9. **ML-Based Classifier** - Replace Drain3 + LLM
   - Train on historical issues (features: log patterns, code, outcomes)
   - Predict: issue category, root cause, affected services
   - Faster + cheaper than LLM

10. **Automated Testing & PR Creation** - Close the loop
    - Generate fix → Run tests → Create PR → Notify user
    - 80% automation target

---

## Summary

**Strengths:**
- ✅ Comprehensive 10-step pipeline
- ✅ Progressive fallbacks at every step
- ✅ Optimal Drain3 → LLM flow
- ✅ Dual code search for comparison
- ✅ Code flow analysis with Neo4j
- ✅ Load state cross-referencing
- ✅ Redshift validation (100% accuracy)

**Gaps:**
- ⚠️ Monolithic architecture (not MCP-based)
- ⚠️ No first-focus routing logic
- ⚠️ No fix generation (code exists but not called)
- ⚠️ No visual timeline generation
- ⚠️ No feedback loop / learning

**Strategic Value:**
- This orchestrator is **production-ready** for current scope
- Demonstrates end-to-end RCA capability
- Provides data for next phase (multi-agent, ML)
- Architecture can be incrementally refactored to MCP

**Next Steps:**
1. Enable fix generation (quick win)
2. Add visual timelines (quick win)
3. Refactor to MCP architecture (medium-term)
4. Implement first-focus routing (medium-term)
5. Add multi-agent orchestration (long-term)

---

**Status:** ✅ Analysis Complete
**Next:** Examine load_replay.py to understand replay mechanism
