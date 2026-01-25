# Analysis 04: MCP Server Capabilities & Overlap Mapping

**Location:** `mcp-servers/` directory
**Total Servers:** 12 active MCP servers
**Source:** Compiled from `mcp-servers/CLAUDE.md` and individual READMEs

---

## Executive Summary

FourKites has **12 operational MCP servers** providing AI assistants access to various systems. There is **significant capability overlap** (3 servers access Redshift, 2 access logs, etc.) and **no unified orchestration layer**. The RCA Bot 2.0 does NOT use these MCP servers - it implements direct clients instead, creating duplication.

**Critical Finding:** The architecture is **fragmented** - each team built their own MCP server without coordination, leading to overlapping capabilities and inconsistent patterns.

---

## MCP Server Inventory

### 1. signoz_mcp (Observability Logs)

**Purpose:** Query SigNoz logs with natural language
**Technology:** Python 3.10+, FastMCP 2.8.1, streamable-http
**Port:** 8888
**Data Source:** SigNoz (ClickHouse backend)
**Table:** `signoz_logs.distributed_logs`

**Key Features:**
- Natural language → SQL query conversion
- Token caching for performance
- Multi-environment support (prod, staging, dev)
- Advanced filtering (severity, service, time range)

**Tools/Capabilities:**
- `query_logs(service, start_time, end_time, severity, contains, limit)`
- `search_by_correlation_id(correlation_id)`
- `get_service_list()`
- `get_log_statistics(service, time_range)`

**Credentials:** Hardcoded (needs migration to env vars)

**Relevant to RCA:** ✅ YES - Core log source

**Overlap:**
- `ClickHouseClient` in RCA Bot 2.0 (duplicates this functionality)
- Should be used instead of direct ClickHouse access

---

### 2. neo4j_mcp (RCA Server)

**Purpose:** Root Cause Analysis using Neo4j graph + SigNoz logs + ClickHouse
**Technology:** Python 3.12, FastMCP 2.11.2, streamable-http
**Ports:** 8000 (main), 8001 (heartbeat)
**Data Sources:** Neo4j, SigNoz, ClickHouse, Jira

**Key Features:**
- OpenTelemetry tracking
- Jira integration
- Drain log pattern analysis (same as RCA Bot 2.0!)
- Code graph search
- Execution flow validation

**Tools/Capabilities:**
- `search_code(class_name, method_name, service)`
- `get_code_flow(entry_point, depth=4)`
- `validate_execution_flow(logs, expected_flow)`
- `analyze_logs_with_drain(logs, max_patterns)`
- `query_jira_issue(issue_key)`
- `trace_correlation_id(correlation_id)`

**Architecture:** Modular with separate utils, database, tools directories

**Relevant to RCA:** ✅ YES - Overlaps heavily with RCA Bot 2.0

**Overlap:**
- **MAJOR DUPLICATION** with RCA Bot 2.0:
  - Both do Drain log analysis
  - Both search code in Neo4j
  - Both validate execution flows
  - Both integrate with Jira
- Could be the **SAME SYSTEM** with better coordination

---

### 3. mcp-custom-jira (Jira Integration)

**Purpose:** JIRA API integration for issue management
**Technology:** Python, FastMCP, stdio transport
**Base URL:** https://fourkites.atlassian.net

**Key Features:**
- Convert issue keys to IDs
- Fetch PR information from issues
- Comment on issues

**Tools/Capabilities:**
- `get_issue(issue_key)`
- `search_issues(jql)`
- `add_comment(issue_key, comment)`
- `get_pull_requests(issue_key)`
- `convert_issue_key_to_id(issue_key)`

**Credentials:** `JIRA_EMAIL`, `JIRA_API_TOKEN`

**Relevant to RCA:** ✅ YES

**Overlap:**
- `JiraClient` in RCA Bot 2.0 (duplicates functionality)
- Should consolidate

---

### 4. mcp-snowflake (Data Warehouse)

**Purpose:** Query Snowflake data warehouse
**Technology:** Python 3.10+, FastMCP, stdio transport
**Data Source:** Snowflake

**Key Features:**
- Write operation blocking (read-only by design)
- YAML formatting for complex data
- Insight collection

**Tools/Capabilities:**
- `query(sql, database, schema)`
- `list_databases()`
- `list_schemas(database)`
- `list_tables(database, schema)`
- `describe_table(database, schema, table)`

**Transport:** stdio (for local integration)

**Relevant to RCA:** ⚠️ MAYBE - If RCA needs Snowflake data

**Overlap:**
- No direct overlap with RCA Bot 2.0 (RCA uses Redshift, not Snowflake)
- Different data warehouse

---

### 5. mcp-redshift-loads (Operational Analytics)

**Purpose:** Redshift operational analytics (Salesforce, marketing, tracking data)
**Technology:** Python, FastMCP, stdio transport
**Data Source:** Redshift
**Default Schema:** `ops` (Salesforce and marketing tables)

**Key Features:**
- Read-only operations
- Table caching (5-min TTL)
- Widget/dashboard creation
- Focused on operational/business data (not core load data)

**Tools/Capabilities:**
- `query_redshift(sql, schema='ops')`
- `list_tables(schema='ops')`
- `describe_table(table_name, schema='ops')`
- `get_recent_data(table_name, limit=100)`

**Credentials:** `RS_HOST`, `RS_PORT`, `RS_USER`, `RS_PASSWORD`, `RS_DATABASE`, `RS_SCHEMA`

**Relevant to RCA:** ⚠️ PARTIAL

**Overlap:**
- **MAJOR OVERLAP** with `RedshiftClient` in RCA Bot 2.0
- RCA Bot queries different schema (`platform_shared_db.platform`)
- This server queries `ops` schema (Salesforce, marketing)
- **Should be unified** into single Redshift MCP with multiple schema support

---

### 6. historic-redshift-mcp (Historical Redshift)

**Purpose:** Historical Redshift data access
**Technology:** Python, FastMCP
**Data Source:** Redshift (same as mcp-redshift-loads but different focus?)

**Status:** Listed in directory but minimal info in CLAUDE.md

**Relevant to RCA:** ⚠️ UNKNOWN

**Overlap:**
- Unclear how this differs from `mcp-redshift-loads`
- Possibly same database, different retention or tables?
- **Needs investigation**

---

### 7. bootstrap-mcp-server (Template/Foundation)

**Purpose:** Template server for new MCP implementations
**Technology:** Python, FastMCP 2.8.1, streamable-http
**Port:** 8000

**Key Features:**
- Complete CI/CD pipeline
- fkai log syncing to Signoz
- Health check endpoints
- Example implementation patterns

**Tools/Capabilities:**
- `example_tool()` - Demo tool
- `/health` endpoint
- `/metrics` endpoint

**Credentials:** `PORT`, `ENV`, `GITHUB_TOKEN`

**Deployment:** Jenkins → Docker → Manual ArgoCD sync

**Relevant to RCA:** ❌ NO - Template only

**Overlap:**
- None - this is a starting point for new servers

---

### 8. tracking-api-mcp-server (FourKites Tracking API)

**Purpose:** FourKites tracking and shipment information retrieval
**Technology:** Python, FastMCP, SSE transport
**Port:** 8081
**Data Source:** Tracking API (real-time)

**Key Features:**
- Load lookup by tracking_id or load_number
- Comprehensive filtering
- Token-based auth (HMAC-SHA1)

**Tools/Capabilities:**
- `get_load(tracking_id)`
- `search_loads(load_number, shipper_id)`
- `get_load_stops(tracking_id)`
- `get_load_timeline(tracking_id)`
- `filter_loads(shipper, carrier, status, date_range)`

**Authentication:** Bearer token + `X-FourKitesDeviceId` + `X-FourKitesUserId` headers

**Relevant to RCA:** ✅ YES - Real-time load data

**Overlap:**
- `TrackingAPIClient` in RCA Bot 2.0 (duplicates functionality)
- `load_replay.py` uses direct client instead of this MCP server
- **Should be used** for real-time load queries

---

### 9. excel-mcp-server (Excel Manipulation)

**Purpose:** Excel file manipulation without Microsoft Excel
**Technology:** Python, FastMCP, SSE transport
**Port:** 8000 (configurable via `FASTMCP_PORT`)
**Library:** openpyxl

**Key Features:**
- Create/modify workbooks
- Charts, pivot tables
- Formula support
- No Excel installation required

**Tools/Capabilities:**
- `create_workbook(filename)`
- `add_worksheet(workbook, name)`
- `write_data(workbook, sheet, data, start_cell)`
- `create_chart(workbook, sheet, chart_type, data_range)`
- `create_pivot_table(workbook, sheet, source_range)`
- `apply_formula(workbook, sheet, cell, formula)`

**Note:** For Claude Desktop, use Supergateway to convert SSE to stdio

**Relevant to RCA:** ❌ NO - Utility for reports

**Overlap:**
- None - standalone utility

---

### 10. courier-mcp (Carrier Drop Analysis)

**Purpose:** Carrier drop performance and compliance analysis
**Technology:** Python, FastMCP
**Data Sources:** DWH (PostgreSQL), Cassandra

**Key Features:**
- Compare DWH vs Cassandra scan times
- CSV export
- Performance testing

**Tools/Capabilities:**
- `analyze_carrier_drops(carrier_id, date_range)`
- `compare_dwh_cassandra(carrier_id, date_range, tolerance_sec)`
- `export_analysis(carrier_id, format='csv')`
- `get_carrier_performance(carrier_id)`

**Testing:** `pytest` for test suite

**Credentials:** `DWH_HOST`, `CASSANDRA_HOST`, `DEFAULT_TOLERANCE_SEC`

**Relevant to RCA:** ⚠️ MAYBE - If analyzing carrier issues

**Overlap:**
- None directly with RCA Bot 2.0
- Could be useful for carrier performance RCA

---

### 11. tracking-mcp-server (Elasticsearch/OpenSearch)

**Purpose:** Elasticsearch/OpenSearch tracking cluster interface
**Technology:** Python, FastMCP
**Data Source:** OpenSearch/Elasticsearch

**Key Features:**
- 7 specialized tools for tracking operations
- Index management
- Search operations

**Tools/Capabilities:**
- `search_loads(query, index, filters)`
- `get_load_by_id(tracking_id, index)`
- `search_by_date_range(start, end, index)`
- `get_index_stats(index)`
- `list_indices()`
- `reindex_load(tracking_id, source_index, dest_index)`
- `bulk_update_loads(load_ids, updates)`

**Credentials:** `OPENSEARCH_HOST`, `OPENSEARCH_INDEX`

**Testing:** `fastmcp dev src/tracking_mcp_server/server.py`

**Relevant to RCA:** ⚠️ MAYBE

**Overlap:**
- Different data source (OpenSearch vs ClickHouse)
- May contain duplicate tracking data
- **Unclear relationship** to other tracking sources

---

### 12. rewind (Related to rewind-app?)

**Purpose:** Unclear from directory listing
**Location:** `mcp-servers/rewind/`

**Status:** Listed but not documented in main CLAUDE.md

**Contents (from earlier listing):**
```
rewind/
├── CLAUDE.md
├── README.md
├── backend/
└── frontend/
```

**Relevant to RCA:** ⚠️ UNKNOWN

**Needs Investigation:** May be related to rewind-app frontend

---

## Capability Matrix

| MCP Server | Logs | Code | Jira | Redshift | Tracking API | Neo4j | Excel | Other |
|------------|------|------|------|----------|--------------|-------|-------|-------|
| signoz_mcp | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ClickHouse |
| neo4j_mcp | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | Drain analysis |
| mcp-custom-jira | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | - |
| mcp-snowflake | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Snowflake |
| mcp-redshift-loads | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ops schema |
| historic-redshift-mcp | ❌ | ❌ | ❌ | ✅? | ❌ | ❌ | ❌ | Historical? |
| tracking-api-mcp | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | Real-time |
| tracking-mcp-server | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | OpenSearch |
| excel-mcp-server | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | - |
| courier-mcp | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Cassandra, PG |
| bootstrap-mcp | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Template |
| rewind | ❌? | ❌? | ❌? | ❌? | ❌? | ❌? | ❌? | Unknown |

---

## Overlap Analysis

### Critical Overlaps

#### 1. Log Access (3 servers!)
- **signoz_mcp** - SigNoz/ClickHouse logs
- **neo4j_mcp** - Also queries SigNoz/ClickHouse
- **RCA Bot 2.0 ClickHouseClient** - Direct ClickHouse access

**Problem:** 3 different implementations accessing same data source
**Solution:** Standardize on `signoz_mcp` server

#### 2. Redshift Access (3+ servers!)
- **mcp-redshift-loads** - `ops` schema (Salesforce, marketing)
- **historic-redshift-mcp** - Historical data (unclear schema)
- **RCA Bot 2.0 RedshiftClient** - `platform_shared_db.platform` schema

**Problem:** Multiple servers, different schemas, no coordination
**Solution:** Single unified Redshift MCP server with multi-schema support

#### 3. Jira Integration (2 servers!)
- **mcp-custom-jira** - Jira API wrapper
- **neo4j_mcp** - Also has Jira integration
- **RCA Bot 2.0 JiraClient** - Direct Jira access

**Problem:** Duplicate implementations
**Solution:** Standardize on `mcp-custom-jira`

#### 4. Tracking API (2 servers!)
- **tracking-api-mcp-server** - Tracking API wrapper
- **RCA Bot 2.0 TrackingAPIClient** - Direct API access

**Problem:** Duplicate implementations
**Solution:** Use `tracking-api-mcp-server`

#### 5. Neo4j Code Graph (2 servers!)
- **neo4j_mcp** - Code graph + flow analysis
- **RCA Bot 2.0 GraphDBClient** - Direct Neo4j access

**Problem:** Duplicate implementations
**Solution:** Use `neo4j_mcp`

#### 6. Drain Log Analysis (2 implementations!)
- **neo4j_mcp** - Has Drain log pattern analysis
- **RCA Bot 2.0 ErrorAnalyzer** - Also uses Drain3

**Problem:** Same algorithm implemented twice
**Solution:** Consolidate or share library

---

## RCA Bot 2.0 vs MCP Servers

### What RCA Bot 2.0 Implements Directly (Should Use MCP Instead)

| RCA Bot 2.0 Component | Duplicates MCP Server | Should Use |
|-----------------------|----------------------|------------|
| `ClickHouseClient` | signoz_mcp | ✅ Use signoz_mcp |
| `RedshiftClient` | mcp-redshift-loads | ✅ Use mcp-redshift-loads (extended) |
| `GitHubClient` | ❌ None | ❌ No MCP server (need to create) |
| `GraphDBClient` | neo4j_mcp | ✅ Use neo4j_mcp |
| `JiraClient` | mcp-custom-jira | ✅ Use mcp-custom-jira |
| `TrinoClient` | ❌ None | ❌ No MCP server (need to create) |
| `TrackingAPIClient` | tracking-api-mcp-server | ✅ Use tracking-api-mcp-server |
| `ConfluenceClient` | ❌ None | ❌ No MCP server (need to create) |
| `CompanyAPIClient` | ❌ None | ❌ No MCP server (need to create) |
| `ErrorAnalyzer` (Drain) | neo4j_mcp | ⚠️ Share library or consolidate |
| `HypothesisGenerator` | ❌ None | ❌ Unique to RCA Bot |
| `DomainInsightExtractor` | ❌ None | ❌ Unique to RCA Bot |

**Duplication Rate:** **6 out of 9 clients** duplicate existing MCP servers (67%)

---

## Missing MCP Servers (Need to Create)

### 1. mcp-github (GitHub Code Search)
**Why:** RCA Bot 2.0, neo4j_mcp, and future agents all need GitHub access
**Tools:**
- `search_code(query, repo, language)`
- `get_file_content(repo, path, ref)`
- `search_classes(class_name, repo)`
- `list_repos(org)`

### 2. mcp-trino (Historical Analytics)
**Why:** RCA Bot 2.0 and load_replay.py need Trino for 30-180 day data
**Tools:**
- `query(sql, catalog, schema)`
- `query_load_files(tracking_id, date_range)`
- `query_callbacks(tracking_id, date_range)`
- `query_logs(service, date_range, severity)`

### 3. mcp-confluence (Documentation)
**Why:** RCA Bot 2.0 fetches service docs for context
**Tools:**
- `search_docs(query, space)`
- `get_page(page_id)`
- `get_service_docs(service_name, category)`

### 4. mcp-company-api (Company/Network)
**Why:** load_replay.py and network_checker.py need company relationships
**Tools:**
- `get_company(company_id)`
- `get_relationships(company_id, relationship_type)`
- `check_network(shipper_id, carrier_id)`

### 5. mcp-unified-redshift (Consolidated Redshift)
**Why:** Unify mcp-redshift-loads, historic-redshift-mcp, and RCA Bot Redshift access
**Tools:**
- `query(sql, schema)` - Support multiple schemas
- `get_load_metadata(tracking_id)`
- `get_company(permalink)`
- `get_network_relationships(shipper_id, carrier_id)`
- `query_load_files(tracking_id)`

---

## Architectural Patterns

### Current State: Fragmented
```
Agent/Tool
   ↓
Direct Client (ClickHouseClient, RedshiftClient, etc.)
   ↓
Database/API
```

**Problems:**
- Duplication (6+ duplicate clients)
- No shared caching
- No consistent auth
- No observability
- Hard to maintain

### Target State: MCP-Based
```
Agent/Tool
   ↓
MCP Protocol
   ↓
MCP Server (signoz_mcp, mcp-unified-redshift, etc.)
   ↓
Database/API
```

**Benefits:**
- Shared implementations
- Consistent auth
- Centralized caching
- Observability (OpenTelemetry)
- Multi-agent access

---

## Transport Protocol Usage

| Transport | Servers | Use Case |
|-----------|---------|----------|
| **streamable-http** | signoz_mcp, neo4j_mcp, bootstrap-mcp | Remote HTTP-based, most common |
| **stdio** | mcp-snowflake, mcp-redshift-loads, mcp-custom-jira | Local integration, Claude Desktop |
| **SSE** | tracking-api-mcp-server, excel-mcp-server | Streaming responses |

**Observation:** No consistency - each team chose different transport

---

## Deployment Status

### Deployed to Production
- ✅ signoz_mcp (port 8888)
- ✅ neo4j_mcp (ports 8000, 8001)
- ✅ tracking-api-mcp-server (port 8081)
- ⚠️ Others - Unclear deployment status

### CI/CD Pattern
**Standard Pipeline:**
1. Jenkins builds Docker image
2. Push to container registry
3. Update image tag in `ai-deployments` repo
4. **Manual step:** Commit changes
5. ArgoCD auto-syncs after commit

**Problem:** Manual step required (not fully automated)

---

## Recommendations

### Immediate (Quick Wins)

1. **Consolidate Redshift Access**
   - Merge: mcp-redshift-loads + historic-redshift-mcp → `mcp-unified-redshift`
   - Support multiple schemas in one server
   - Migrate RCA Bot to use this MCP server

2. **Standardize on Existing MCP Servers**
   - RCA Bot should use:
     - `signoz_mcp` instead of ClickHouseClient
     - `mcp-custom-jira` instead of JiraClient
     - `neo4j_mcp` instead of GraphDBClient
     - `tracking-api-mcp-server` instead of TrackingAPIClient

3. **Document Deployment Status**
   - Which servers are production-ready?
   - Which are experimental?
   - Create inventory with status

### Medium-Term (Architecture)

4. **Create Missing MCP Servers**
   - mcp-github (GitHub code search)
   - mcp-trino (historical analytics)
   - mcp-confluence (documentation)
   - mcp-company-api (network relationships)

5. **Establish MCP Standards**
   - Standard transport protocol (recommend: streamable-http)
   - Standard auth pattern (env vars, secrets management)
   - Standard error handling
   - Standard logging/observability (OpenTelemetry)

6. **Create MCP Server Registry**
   - Central catalog of available servers
   - Capabilities listing
   - Connection info
   - Usage examples

### Long-Term (Governance)

7. **Prevent Future Duplication**
   - Before building new MCP server, check registry
   - Extend existing server instead of creating new
   - Mandatory review process

8. **Unified Orchestration Layer**
   - Create meta-MCP server that routes to others
   - Agent calls one endpoint, routing handled automatically
   - Similar to API gateway pattern

9. **Automated Testing**
   - Integration tests across MCP servers
   - End-to-end agent testing
   - Performance benchmarking

---

## Integration with Data Catalog

**Current State:**
- data_catalog.yaml documents tables/queries
- MCP servers implement access to those tables
- **No connection** between catalog and servers

**Target State:**
- data_catalog.yaml maps tables → MCP servers
  ```yaml
  redshift:
    tables:
      fact_loads:
        mcp_server: mcp-unified-redshift
        tool: get_load_metadata
  ```
- Agents read catalog to discover which MCP server to use
- Catalog becomes **service directory**

---

## Summary

**Current Situation:**
- ✅ 12 MCP servers operational
- ⚠️ Significant overlap (67% of RCA Bot clients duplicate MCP servers)
- ⚠️ No coordination between teams
- ⚠️ Inconsistent patterns (transport, auth, deployment)
- ⚠️ Missing servers (GitHub, Trino, Confluence, Company API)

**Opportunities:**
- ✅ Consolidate duplicate implementations
- ✅ Create missing MCP servers
- ✅ Migrate RCA Bot to use MCP architecture
- ✅ Establish governance to prevent future duplication
- ✅ Connect data catalog with MCP server registry

**Strategic Value:**
- MCP servers are the **right architectural pattern**
- Need **better coordination** across teams
- Opportunity to **standardize and consolidate**

---

**Status:** ✅ Analysis Complete
**Next:** Review architecture documentation from rewind-app
