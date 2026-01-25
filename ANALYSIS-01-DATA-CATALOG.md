# Analysis 01: data_catalog.yaml - Unified Data Catalog

**File:** `mcp-servers/rca-bot-2.0/poc/data_catalog.yaml`
**Size:** 64KB, 1,647 lines
**Last Updated:** 2025-12-04
**Purpose:** Comprehensive catalog of ALL data sources for Load Replay and RCA features

---

## Executive Summary

This is **THE CORE CATALOG** that Arpit built for his catalog-driven approach. It's essentially a **data encyclopedia** that documents:

✅ **3 major data systems** (Redshift, Trino, S3)
✅ **12+ tables** with complete schemas
✅ **300+ event types** with volume statistics
✅ **Query templates** for common investigations
✅ **Troubleshooting guides** for known issues
✅ **Relationship mappings** between tables

This catalog enables both humans and agents to:
- Understand what data exists and where
- Know which tables to query for different questions
- See production-tested query patterns
- Understand data relationships and join logic

---

## Structure Overview

### 1. Redshift (Data Warehouse - productiondwh)

**Primary Load Data (3 core tables):**

#### tracking_update_v3s
- **Description:** ALL updates/events for loads (event stream)
- **Volume:** Millions of records per day
- **Key Insight:** 300+ unique status values documented with volume stats
- **Top Event:** "Arrived At Terminal" (82.6M records in 2 months!)
- **Critical Error:** "Invalid Timestamp" (45.2M records - highest volume error)
- **Schema:** 15+ columns documented (tracking_id, status, message, update_time, source, etc.)

**Event Categories Documented:**
- Load lifecycle (assignment events)
- Asset tracking (GPS, ELD, CarrierLink)
- Milestones: terminals (82.6M), pickup (42.6M), delivery (44.9M)
- ETA updates (45M+ carrier ETA updates)
- Schedule changes (39.4M reschedules)
- Exceptions/errors
- Mode-specific: ocean, rail, air, customs

**Top Events by Volume (Oct-Dec 2025):**
1. Arrived At Terminal: 82.6M
2. Departed Terminal: 53.1M
3. SCAC Changed: 53.2M
4. Invalid Timestamp: 45.2M (ERROR!)
5. Carrier ETA Updated: 45.0M

#### fact_loads
- **Description:** Core load metadata - one row per load
- **Schema:** 80+ columns documented
- **Key Fields:**
  - Identifiers: load_id, load_number, pro_number, tracking_number
  - Parties: shipper_id, carrier_id, managing_carrier_id, operating_carrier_id
  - Assets: truck_number, trailer_number, driver_phone, device_id
  - Tracking: tracking_method, location_provider, tracking_strategy
  - Statistics: distance, speed, transit_time, number_of_check_calls
  - Flags: is_brokered_load, relay_load, test_load, demo_load
  - Mode: TL, LTL, Parcel, Ocean, Rail, Air

**Terminal States Distribution (Oct-Dec 2025):**
- Delivered: 73.8% (17.1M loads)
- Expired: 8.3% (1.9M loads)
- Awaiting Tracking Info: 7.7% (1.8M loads) ⚠️ **PROBLEM AREA**
- In Transit: ~5%
- Other: ~5%

**CRITICAL NOTE - Two "status" Fields:**
1. `fact_loads.status` = CURRENT/FINAL state (one value)
   - Example: "Delivered", "Expired", "At Terminal"
2. `tracking_update_v3s.status` = EVENT STREAM (many values)
   - Example: "Picked Up" → "In Transit" → "Delivered"

#### fact_stops
- **Description:** Stop details - multiple stops per load
- **Key Fields:** stop_sequence, stop_type, appointment_time, arrival_time, departure_time
- **Use:** Timeline construction, milestone tracking

**File Processing Tables (4 tables):**

#### load_validation_data_mart
- **Key Insight:** Determines load creation source
- **Critical Field:** `file_name`
  - "API Request" = created via API
  - Actual filename = created via file upload
- **Use Case:** Debug load creation issues

#### fact_carrier_file_logs
- **Description:** Carrier file processing (super files, EDI)
- **Volume:** Tracks all carrier update files
- **S3 Integration:** Contains s3_file_path to actual files
- **Key Fields:** file_format, data_source, data_type, stage, error
- **S3 Path Pattern:** `super_files/{company_id}/{config_name}/{YYYY-MM-DD}/{filename}`

#### fact_carrier_record_logs
- **Description:** Individual records within carrier files
- **Linkage:** file_id → fact_carrier_file_logs.id
- **Key Fields:** load_identifier_1/2/3/4 (multiple ways to match loads)
- **Use:** Trace which carrier files updated specific loads

#### fact_load_file_logs
- **Description:** Shipper/customer load file processing
- **Similar to:** fact_carrier_file_logs but for load creation
- **S3 Path Pattern:** `loads/{company_id}/{YYYY-MM-DD}/{timestamp}-{filename}`

**CRITICAL TABLE - fact_load_file_records:**
- **Has load_id (tracking_id) mapping!**
- **Use:** Find exact files that created/updated a specific load
- **Join with:** fact_load_file_logs to get S3 paths

**Company Master Data (3 tables):**

#### companies
- **Description:** Master company data (shippers, carriers, 3PLs, brokers)
- **Primary Key:** `permalink` (URL-safe company identifier, NOT id)
- **Key Fields:**
  - Identifiers: name, permalink, company_type, MC, USDOT, SCAC
  - Status: active, verified, ready_for_networking
  - Configurations (JSON): load_creation_configuration, tracking_configurations, etc.
  - Modules: requested_modules, enabled_modules, package_name
  - Flags: ltl_carrier, disallow_load_creation_without_carrier

**Important Flags:**
- `ready_for_networking=false` → Cannot create relationships
- `disallow_load_creation_without_network=true` → Loads fail without carrier relationship
- `active=false` → Company deactivated, all integrations inactive

#### company_configurations
- **Description:** Detailed configurations (JSON-based)
- **Critical Types:**
  - `onboarding` - Onboarding parameters (misconfiguration → loads stuck)
  - `super_file` - Carrier file parsing rules (misconfiguration → files not parsed)
  - `external_integrations` - TMS/ERP integrations

#### company_relationships ⚠️ **MOST CRITICAL TABLE**
- **Description:** Network relationships between companies
- **Purpose:** **DETERMINES IF CARRIER FILES MATCH TO SHIPPER LOADS**

**Critical Fields:**
- `company_id` - Shipper/3PL (creates loads)
- `target_company_id` - Carrier (moves loads)
- `active` - **MUST be true for relationship to work**
- `status` - Should be "live" for production
- `allow_tracking` - Must be true for location sharing
- `super_file_configurations` - Carrier file parsing rules

**FILE MATCHING LOGIC (Root Cause of "Awaiting Tracking Info"):**

```
1. Carrier sends super file with load updates
2. System queries: SELECT company_id FROM company_relationships
   WHERE target_company_id = :carrier_id AND active = true AND status = 'live'
3. For each shipper in network:
   - Search for loads belonging to that shipper
   - Match load identifiers in file to shipper's loads
4. If NO relationship exists:
   - File is processed but NO loads are matched
   - Loads stay in "Awaiting Tracking Info" FOREVER
   - THIS IS THE ROOT CAUSE!
```

**Troubleshooting "Awaiting Tracking Info" Checklist:**
1. ✅ Does relationship exist?
2. ✅ Is relationship active?
3. ✅ Is relationship status = 'live'?
4. ✅ Is allow_tracking = true?
5. ✅ Check super_file_configurations for parsing rules

---

### 2. Trino (Historical Data - log database)

**hive.log database** (3 tables documented):

#### callbacks_v2
- **Description:** Customer webhook/callback delivery logs
- **Format:** Parquet, partitioned by datestr (YYYY-MM-DD)
- **Key Fields:** fk_tracking_id, ext_request_status (HTTP codes), error_msg
- **Use:** Debug webhook delivery failures

#### load_files
- **Description:** Historical load file processing (alternative to Redshift)
- **Retention:** Longer than Redshift
- **Use:** Historical analysis beyond Redshift retention

#### vw_location_processing_flow
- **Description:** 8 months of location processing flow
- **Shows:** carrier-files-worker → global-worker → location-worker
- **Retention:** 8 months vs 30 days in ClickHouse
- **Use:** Debug location processing issues

---

### 3. S3 File Locations

**production-files-backup bucket:**

**Carrier Files:**
- Pattern: `super_files/{carrier_id}/{config_name}/{YYYY-MM-DD}/{filename}`
- Example: `super_files/celtic-international/CelticSuper/2025-12-01/20251201000012-FourKites_update_20251130173002.csv-1.csv`

**Load Files:**
- Pattern: `loads/{shipper_id}/{YYYY-MM-DD}/{timestamp}-{filename}`
- Example: `loads/cdw-corporation/2025-11-01/20251101000032-s3_load_file_a9a605be05af42369a1f3ea7b2127dcc.json`

**Access Methods:**
- CLI: `aws s3 ls s3://production-files-backup/{path}`
- API: `boto3.client('s3').get_object(Bucket='production-files-backup', Key=path)`

---

## Event Taxonomy

**Based on tracking_update_v3s.status (300+ unique values)**

**Categories Defined:**
1. **LOAD_LIFECYCLE** - Load creation, asset assignment (priority: critical)
2. **TRACKING_START_STOP** - Tracking initiated/stopped (priority: high)
3. **MILESTONES_PICKUP** - Pickup events (priority: critical)
4. **MILESTONES_DELIVERY** - Delivery events (priority: critical)
5. **MILESTONES_TRANSIT** - In-transit events (priority: high)
6. **MILESTONES_TERMINAL** - Terminal/facility events (priority: medium)
7. **ETA_UPDATES** - ETA calculations (priority: high)
8. **SCHEDULE_CHANGES** - Appointment changes (priority: high)
9. **STATUS_UPDATES** - General updates (priority: medium)
10. **EXCEPTIONS_ERRORS** - Exceptions/errors (priority: critical)
11. **CUSTOMS_HOLDS** - Customs processing (priority: medium)
12. **OCEAN_EVENTS** - Ocean shipping (priority: medium)
13. **RAIL_EVENTS** - Rail shipping (priority: medium)

---

## Query Templates

**Six production-tested query templates provided:**

### 1. load_timeline_complete
**Purpose:** Get complete timeline from all sources
**Steps:**
1. Get load metadata from fact_loads
2. Get all events from tracking_update_v3s
3. Get stops from fact_stops
4. Get creation source from load_validation_data_mart
5. Get carrier files from fact_carrier_file_logs
6. Get load files from fact_load_file_logs
7. Get callbacks from callbacks_v2 (Trino)
8. Merge chronologically

### 2. determine_load_creation_source
**Purpose:** How was this load created?
**Logic:**
- "API Request" → Created via API
- Filename present → Created via file
- NULL → Unknown

### 3. get_carrier_files_for_load
**Purpose:** Get all carrier files that updated this load
**Joins:** fact_carrier_file_logs + fact_carrier_record_logs
**Searches:** load_identifier_1/2/3/4 fields

### 4. investigate_awaiting_tracking_info ⚠️ **CRITICAL**
**Purpose:** Root cause analysis for 7.7% of loads stuck
**Query Logic:**
1. Find loads stuck in "Awaiting Tracking Info" (>24 hours)
2. Join with company_relationships
3. Identify network issues:
   - NO_RELATIONSHIP
   - RELATIONSHIP_INACTIVE
   - RELATIONSHIP_NOT_LIVE
   - TRACKING_DISABLED
   - RELATIONSHIP_OK

### 5. check_network_for_load
**Purpose:** Check carrier-shipper network for specific load
**Output:** ✅ RELATIONSHIP OK or ❌ various error states

### 6. find_carriers_without_network
**Purpose:** Find carriers with loads but no active relationships
**Output:** Total loads, stuck loads, relationship count

---

## Table Relationships

**Primary Keys:**
- `load_id` = tracking_id (bigint)
- `company_id` = Company permalink (string)
- `stop_id` = Stop ID (bigint)
- `file_id` = File processing UUID

**Join Patterns:**

**Load Timeline:**
- fact_loads.load_id = tracking_update_v3s.tracking_id
- fact_loads.load_id = fact_stops.load_id
- fact_loads.load_id = load_validation_data_mart.load_id
- fact_loads.load_id = callbacks_v2.fk_tracking_id
- fact_loads.load_id = load_files.fk_tracking_id

**File Processing:**
- fact_carrier_file_logs.id = fact_carrier_record_logs.file_id
- fact_load_file_logs.file_name = fact_load_file_records.file_name
- fact_carrier_record_logs.load_identifier_* = fact_loads.load_id

---

## Key Insights & Design Patterns

### 1. Catalog-Driven Architecture

This catalog enables **discovery over hard-coding**:
- Agents can query: "What tables contain load information?"
- Catalog returns: fact_loads, tracking_update_v3s, fact_stops, etc.
- Agent can then ask: "What columns does fact_loads have?"
- Catalog provides schema + documentation

### 2. Production Statistics Embedded

Volume statistics help prioritize:
- "Arrived At Terminal" (82.6M) - Most common event, probably not an error
- "Invalid Timestamp" (45.2M) - High volume error, likely systemic issue
- Helps agents distinguish between "normal high volume" vs "error high volume"

### 3. Troubleshooting Playbooks

The catalog includes investigation guides:
- "Awaiting Tracking Info" troubleshooting steps
- Network relationship validation checklist
- File matching logic explanation

This codifies human analyst knowledge.

### 4. Query Patterns as Knowledge

Production-tested SQL templates:
- Show exactly how to query each table
- Include WHERE clauses for performance
- Document JOIN relationships
- Provide ORDER BY for timeline ordering

### 5. Multi-System Integration

The catalog spans 3 systems (Redshift, Trino, S3):
- Provides unified namespace
- Documents which system for which use case
- Shows data retention differences (30 days vs 8 months)

### 6. Critical Path Identification

The catalog highlights **critical tables**:
- company_relationships - "MOST CRITICAL TABLE"
- fact_load_file_records - "CRITICAL: This table HAS load_id mapping"
- Helps agents focus on high-impact data sources

---

## Gap Analysis vs Requirements

### What's Well-Covered ✅

1. **Data Source Documentation** ✅
   - All major tables documented
   - Schemas complete with column descriptions
   - Query patterns provided

2. **Event Taxonomy** ✅
   - 300+ events categorized
   - Volume statistics included
   - Priority levels defined

3. **Troubleshooting Knowledge** ✅
   - "Awaiting Tracking Info" investigation guide
   - Network relationship validation
   - File matching logic explained

4. **Query Templates** ✅
   - 6 production-tested templates
   - Cover common investigations
   - Include JOIN logic

### What's Missing or Unclear ⚠️

1. **MCP Server Mapping** ⚠️
   - Catalog doesn't specify which MCP server to use for each table
   - Example: Should I use neo4j_mcp or signoz_mcp for logs?
   - Need mapping: data_catalog.yaml table → MCP server endpoint

2. **API vs Database Priority** ⚠️
   - Catalog focuses on database tables
   - Doesn't mention Tracking API, Company API
   - Missing: When to use API vs when to query database?

3. **Real-time vs Historical** ⚠️
   - Not clear which data sources are real-time
   - Which have latency (e.g., Redshift ETL delay)?
   - Agents need to know data freshness

4. **Access Patterns Not Defined** ⚠️
   - No guidance on query performance
   - Which queries are expensive?
   - Which require pagination?
   - No rate limiting information

5. **First-Focus Routing Logic Missing** ⚠️
   - Catalog shows WHAT data exists
   - Doesn't show: "For issue type X, start with table Y"
   - This is the "auto-narrow scope" logic mentioned in requirements

6. **Cross-Table Workflow** ⚠️
   - Individual tables documented well
   - Missing: "To investigate stuck load, query tables in THIS order"
   - No decision trees or flowcharts

7. **Support SQL Catalog Not Integrated** ⚠️
   - Conversation mentioned "Support SQL catalog in Notion"
   - Not reflected in this YAML
   - Missing: Human analyst's proven queries

---

## How This Fits Into RCA Agent Vision

### Current Use (Load Replay)

From `load_replay.py` and `rca_bot.py`:
- **Data Discovery:** Catalog tells agent which tables to query
- **Schema Validation:** Agent validates query results against catalog schema
- **Query Generation:** Agent uses query templates as starting point

### Future Use (RCA Bot 2.0)

**For "First Focus" Routing:**
1. Agent receives issue: "Load 123 stuck in Awaiting Tracking Info"
2. Agent queries catalog: "What causes Awaiting Tracking Info?"
3. Catalog returns: "Check company_relationships table first"
4. Agent follows troubleshooting checklist from catalog
5. Agent queries in priority order: network → files → logs

**For Human Playbook Encoding:**
- Catalog query templates = encoded playbook steps
- Example: "investigate_awaiting_tracking_info" template = analyst's mental model
- Agent follows same steps human would

### Integration with Other Systems

**ClickHouse (Logs):**
- Catalog documents tracking_update_v3s event types
- Agent uses event taxonomy to filter relevant logs
- Volume stats help distinguish normal vs error

**Neo4j (Code Graph):**
- Not currently in catalog
- Should add: service → repository → code paths mapping

**Signoz (Observability):**
- Not in catalog
- Should add: service → metrics → thresholds mapping

---

## Recommendations for Enhancement

### 1. Add MCP Server Mapping Section

```yaml
mcp_server_mapping:
  fact_loads:
    primary: mcp-redshift-loads
    alternative: tracking-api-mcp-server  # Real-time alternative
  tracking_update_v3s:
    primary: mcp-redshift-loads
    use_case: "Historical event timeline"
  signoz_logs:
    primary: signoz_mcp
    use_case: "Real-time log search"
```

### 2. Add First-Focus Decision Trees

```yaml
issue_routing:
  awaiting_tracking_info:
    step1:
      query: company_relationships
      check: "Does relationship exist and is active?"
    step2_if_yes:
      query: fact_carrier_file_logs
      check: "Are carrier files being received?"
    step2_if_no:
      action: "Create relationship or contact account manager"
```

### 3. Add Performance Metadata

```yaml
tables:
  tracking_update_v3s:
    query_cost: high
    recommended_limit: 1000
    requires_date_filter: true
    partition_key: created_at
```

### 4. Integrate Support SQL Catalog

```yaml
analyst_proven_queries:
  stuck_load_investigation:
    source: "Notion - Support SQL Catalog"
    query: |
      -- Query from support team's playbook
      SELECT ...
    use_cases:
      - "Load not tracking"
      - "Missing location updates"
```

### 5. Add Data Freshness Info

```yaml
tables:
  fact_loads:
    latency: "5-10 minutes (ETL delay)"
    update_frequency: "Real-time → 5min delay → Redshift"
    prefer_api_for: "Real-time status queries"
```

---

## Comparison to Requirements

### From Spec Document Requirements:

**✅ Achieved:**
- Unified catalog of data sources
- Query patterns documented
- Troubleshooting guides included
- Production statistics embedded

**⚠️ Partially Achieved:**
- Human playbook encoded (query templates exist, but not complete decision trees)
- Data source capabilities listed (but not MCP server mapping)

**❌ Missing:**
- First-focus routing logic (no decision trees)
- Support SQL catalog integration (mentioned in conversation but not in YAML)
- MCP server capability mapping
- Real-time vs historical guidance

---

## Integration with RCA Bot 2.0 Code

**Files That Use This Catalog:**

1. **load_replay.py** (153KB, 900+ lines)
   - Uses query patterns from catalog
   - Queries tables documented in catalog
   - Implements load timeline assembly

2. **redshift_client.py** (37KB)
   - Implements queries defined in catalog
   - Uses table schemas from catalog
   - Handles company lookups

3. **issue_mapper.py** (9KB)
   - Should reference catalog for service mappings
   - Maps issue types → data sources

**How Code Should Use Catalog:**

```python
# Load catalog
with open('data_catalog.yaml') as f:
    catalog = yaml.safe_load(f)

# Get query pattern
query_pattern = catalog['redshift']['tables']['fact_loads']['query_pattern']

# Get schema for validation
schema = catalog['redshift']['tables']['fact_loads']['key_columns']

# Get troubleshooting guide
guide = catalog['query_templates']['investigate_awaiting_tracking_info']
```

---

## Summary

**Strengths:**
- ✅ Extremely comprehensive (1,647 lines)
- ✅ Production statistics embedded
- ✅ Query templates production-tested
- ✅ Troubleshooting guides included
- ✅ Well-organized by system (Redshift, Trino, S3)

**Gaps:**
- ⚠️ No MCP server mapping
- ⚠️ No first-focus routing logic
- ⚠️ Missing Support SQL catalog integration
- ⚠️ No performance/cost metadata
- ⚠️ No real-time vs historical guidance

**Strategic Value:**
- This catalog is the **foundation** for catalog-driven architecture
- Enables both humans and agents to discover data
- Codifies institutional knowledge (event types, troubleshooting)
- Reduces cognitive load (all info in one place)

**Next Steps:**
1. Add MCP server mapping section
2. Create first-focus decision trees
3. Integrate Support SQL catalog from Notion
4. Add performance and freshness metadata
5. Map to existing MCP servers in the repo

---

**Status:** ✅ Analysis Complete
**Next:** Review rca_bot.py to understand orchestration logic
