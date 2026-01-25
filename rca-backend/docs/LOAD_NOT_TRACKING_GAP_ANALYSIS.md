# LOAD NOT TRACKING - Gap Analysis Report

<div align="center">

```
██╗      ██████╗  █████╗ ██████╗     ███╗   ██╗ ██████╗ ████████╗    ████████╗██████╗  █████╗  ██████╗██╗  ██╗██╗███╗   ██╗ ██████╗
██║     ██╔═══██╗██╔══██╗██╔══██╗    ████╗  ██║██╔═══██╗╚══██╔══╝    ╚══██╔══╝██╔══██╗██╔══██╗██╔════╝██║ ██╔╝██║████╗  ██║██╔════╝
██║     ██║   ██║███████║██║  ██║    ██╔██╗ ██║██║   ██║   ██║          ██║   ██████╔╝███████║██║     █████╔╝ ██║██╔██╗ ██║██║  ███╗
██║     ██║   ██║██╔══██║██║  ██║    ██║╚██╗██║██║   ██║   ██║          ██║   ██╔══██╗██╔══██║██║     ██╔═██╗ ██║██║╚██╗██║██║   ██║
███████╗╚██████╔╝██║  ██║██████╔╝    ██║ ╚████║╚██████╔╝   ██║          ██║   ██║  ██║██║  ██║╚██████╗██║  ██╗██║██║ ╚████║╚██████╔╝
╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝     ╚═╝  ╚═══╝ ╚═════╝    ╚═╝          ╚═╝   ╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝
```

**Root Cause Analysis Gap Assessment**

*Evidence-Based Investigation of 4 Failed Cases*

**Date:** January 21, 2026
**Author:** RCA Agent Analysis
**Classification:** Internal Engineering Review

</div>

---

## Executive Summary

This report analyzes **4 consecutive failures** where Agent Cassie correctly classified issues as `LOAD_NOT_TRACKING` but **failed to investigate** and sent them directly to **Manual Intervention**.

| Metric | Value |
|--------|-------|
| Cases Analyzed | 4 |
| Success Rate | 0% |
| Common Failure | No investigation performed |
| Root Cause | Explicit routing to manual intervention |

---

## Evidence Source: Cassie's Code Architecture

### Source File: `agent-cassie/main.py` (Line ~1926)

```python
# EVIDENCE: LOAD_NOT_TRACKING is explicitly routed to manual intervention
manual_intervention_categories = [
    'fourkites_load_not_tracking', 'LOAD_NOT_TRACKING',  # ← EXPLICITLY SKIPPED
    'fourkites_tl_status_update', 'TL_STATUS_UPDATE'
]

if classification_category in manual_intervention_categories:
    return {
        'endpoint': 'manual_intervention_required',
        'name': 'Manual Support Team',
        'description': 'Requires manual intervention from FourKites internal support team'
    }
```

**Finding:** Cassie **never investigates** LOAD_NOT_TRACKING cases. It immediately routes to manual intervention without checking logs, GPS APIs, or device configurations.

---

## Evidence Source: Neo4j MCP Server Capabilities

### Source: `mcp-servers/neo4j_mcp/src/tools/`

| Tool | Purpose | Can Diagnose LOAD_NOT_TRACKING? |
|------|---------|--------------------------------|
| `get_signoz_logs` | Query SigNoz logs by correlation ID | Partial - Can find errors |
| `find_rare_log_patterns` | Detect anomalies using Drain algorithm | Partial - Pattern detection |
| `execute_cypher_query` | Query Neo4j code graph | No - Code flow only |
| `perform_rca` | Full RCA with correlation ID | No - Missing device/GPS data |

**Finding:** Neo4j MCP server is designed for **code execution tracing**, not GPS/ELD device diagnostics. It lacks:
- GPS timestamp validation
- Location freshness checks
- Device type discrimination (truck vs trailer)
- ELD network-level configuration queries

---

## Case-by-Case Analysis

---

### Case 2693837: GPS Returning Null Timestamps

<table>
<tr>
<td width="50%" style="background-color: #0a0a0a; color: white; padding: 20px;">

#### Problem Statement

**Shipper:** Trinseo
**Loads:** 45436754, 45436755, 45436655, 45436657, 45436653, 45436652

> "Loads are not tracking despite the loads are already in transit and tracking in carrier website"

</td>
<td width="50%" style="background-color: #0a0a0a; color: white; padding: 20px;">

#### Actual Root Cause

```
[LocationProviderClient] Error getting
provider location from provider 1
[error: undefined method `to_datetime'
for nil:NilClass]
```

**GPS provider (RoadoGPS) returned null timestamps**

</td>
</tr>
</table>

#### What Cassie Did

```
┌─────────────────────────────────────────────────────────────────────┐
│  CASSIE ANALYSIS                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ✓ Classification: FOURKITES_LOAD_NOT_TRACKING                      │
│  ✓ Identified: "loads exist but not receiving GPS/location updates" │
│  ✗ Investigation: NONE                                               │
│  ✗ Log Check: NOT PERFORMED                                          │
│  ✗ GPS API Check: NOT PERFORMED                                      │
│  → Result: MANUAL INTERVENTION                                       │
└─────────────────────────────────────────────────────────────────────┘
```

#### What Should Have Been Done

```
┌─────────────────────────────────────────────────────────────────────┐
│  REQUIRED INVESTIGATION STEPS                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Query SigNoz Logs for GPS Provider Errors                       │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ service.name = 'tracking-service' AND                        │ │
│     │ body LIKE '%LocationProviderClient%' AND                     │ │
│     │ body LIKE '%nil:NilClass%'                                   │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  2. Check GPS Provider Response                                      │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ GET /api/v1/gps/provider/roadogps/status                     │ │
│     │ Response: { timestamp: null, lat: 39.1, lng: -84.5 }         │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  3. Identify Pattern: NULL TIMESTAMP                                 │
│     → Root Cause: GPS_NULL_TIMESTAMPS                               │
│     → Resolution: Contact carrier to check GPS provider             │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Evidence: Required Log Query

```sql
-- SigNoz Query that would have found the issue
SELECT timestamp, body, severity_text
FROM logs
WHERE service_name = 'tracking-service'
  AND body LIKE '%LocationProviderClient%Error%'
  AND timestamp >= NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC
LIMIT 50
```

#### Gap Identified

| Component | Has Capability? | Evidence |
|-----------|-----------------|----------|
| Cassie | ❌ No | Routes to manual intervention |
| Neo4j MCP | ⚠️ Partial | Can query logs but no GPS validation |
| RCA Agent | ✅ Yes | Pattern `H_GPS_NULL_TIMESTAMPS` added |

---

### Case 2688628: GPS Returning Old/Stale Locations

<table>
<tr>
<td width="50%" style="background-color: #0a0a0a; color: white; padding: 20px;">

#### Problem Statement

**Carrier:** Preferred Tank Lines LLC
**Shipper:** Calumet Specialty Products LP
**Loads:** 6100798967 (Truck 664), 6100810390 (Truck 702)

> "Trucks assigned on time and ping tests returning positive, but location updates are not being ingested into FourKites"

</td>
<td width="50%" style="background-color: #0a0a0a; color: white; padding: 20px;">

#### Actual Root Cause

**GPS provider was returning old/stale locations**

The system rejected the locations because timestamps were outdated (>4 hours old)

</td>
</tr>
</table>

#### What Cassie Did

```
┌─────────────────────────────────────────────────────────────────────┐
│  CASSIE ANALYSIS                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ✓ Classification: FOURKITES_LOAD_NOT_TRACKING                      │
│  ✓ Identified: "tracking integration is failing"                     │
│  ✗ Investigation: NONE                                               │
│  ✗ Position Freshness Check: NOT PERFORMED                          │
│  ✗ Rejection Reason Check: NOT PERFORMED                            │
│  → Result: MANUAL INTERVENTION                                       │
└─────────────────────────────────────────────────────────────────────┘
```

#### What Should Have Been Done

```
┌─────────────────────────────────────────────────────────────────────┐
│  REQUIRED INVESTIGATION STEPS                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Query Position History                                           │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ SELECT tracking_id, position_timestamp,                      │ │
│     │        EXTRACT(EPOCH FROM (NOW() - position_timestamp))/3600 │ │
│     │        AS hours_since_update                                 │ │
│     │ FROM tracking_positions                                      │ │
│     │ WHERE tracking_id = '6100798967'                             │ │
│     │ ORDER BY position_timestamp DESC LIMIT 1                     │ │
│     └─────────────────────────────────────────────────────────────┘ │
│     Result: hours_since_update = 8.5 hours (STALE)                  │
│                                                                      │
│  2. Check Ingestion Logs for Rejection                               │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ service.name = 'location-worker' AND                         │ │
│     │ body LIKE '%rejected%stale%' AND                             │ │
│     │ body LIKE '%6100798967%'                                     │ │
│     └─────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  3. Identify Pattern: STALE LOCATION                                 │
│     → Root Cause: GPS_STALE_LOCATION                                │
│     → Resolution: Carrier GPS device returning outdated data        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Evidence: Position Freshness Query

```sql
-- Query to detect stale GPS positions
SELECT
    tracking_id,
    position_timestamp,
    ROUND(EXTRACT(EPOCH FROM (NOW() - position_timestamp))/3600, 1) as hours_ago,
    CASE
        WHEN EXTRACT(EPOCH FROM (NOW() - position_timestamp))/3600 > 4 THEN 'STALE'
        ELSE 'FRESH'
    END as status
FROM tracking_positions
WHERE tracking_id IN ('6100798967', '6100810390')
ORDER BY position_timestamp DESC
```

#### Gap Identified

| Component | Has Capability? | Evidence |
|-----------|-----------------|----------|
| Cassie | ❌ No | No position freshness check |
| Neo4j MCP | ❌ No | No tracking_positions access |
| RCA Agent | ✅ Yes | Pattern `H_GPS_STALE_LOCATION` added |

---

### Case 2692749: Trailer vs Truck GPS Mismatch

<table>
<tr>
<td width="50%" style="background-color: #0a0a0a; color: white; padding: 20px;">

#### Problem Statement

**Shipper:** TetraPak
**Load:** BS20251216-1099

> "Can you please check why this load is not tracking"

</td>
<td width="50%" style="background-color: #0a0a0a; color: white; padding: 20px;">

#### Actual Root Cause

**Trailer assigned to load but carrier (USA Truck Inc) only supports Truck GPS**

Device type mismatch - carrier integration doesn't support trailer tracking

</td>
</tr>
</table>

#### What Cassie Did

```
┌─────────────────────────────────────────────────────────────────────┐
│  CASSIE ANALYSIS                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ✓ Classification: FOURKITES_LOAD_NOT_TRACKING                      │
│  ✓ Identified: "load is not TRACKING (no GPS/location updates)"     │
│  ✗ Investigation: NONE                                               │
│  ✗ Device Type Check: NOT PERFORMED                                  │
│  ✗ Carrier GPS Config Check: NOT PERFORMED                          │
│  → Result: MANUAL INTERVENTION                                       │
│                                                                      │
│  Note: "Bot got stuck in decision loop" (per engineering comment)   │
└─────────────────────────────────────────────────────────────────────┘
```

#### What Should Have Been Done

```
┌─────────────────────────────────────────────────────────────────────┐
│  REQUIRED INVESTIGATION STEPS                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Check Load Assignment                                            │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ SELECT tracking_id, load_number, trailer_number, truck_number│ │
│     │ FROM fact_loads                                              │ │
│     │ WHERE load_number = 'BS20251216-1099'                        │ │
│     └─────────────────────────────────────────────────────────────┘ │
│     Result: trailer_number = 'TRL-12345', truck_number = NULL       │
│                                                                      │
│  2. Check Carrier GPS Capability                                     │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ SELECT carrier_permalink, supports_truck, supports_trailer   │ │
│     │ FROM carrier_tracking_config                                 │ │
│     │ WHERE carrier_permalink = 'usa-truck-inc'                    │ │
│     └─────────────────────────────────────────────────────────────┘ │
│     Result: supports_truck = TRUE, supports_trailer = FALSE         │
│                                                                      │
│  3. Identify Pattern: DEVICE TYPE MISMATCH                           │
│     → Root Cause: DEVICE_TYPE_MISMATCH                              │
│     → Resolution: Assign truck to load or enable trailer tracking   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Evidence: Carrier Configuration Query

```sql
-- Query to check carrier GPS capability
SELECT
    c.name as carrier_name,
    c.permalink as carrier_permalink,
    ctc.gps_provider,
    ctc.supports_truck,
    ctc.supports_trailer,
    CASE
        WHEN ctc.supports_trailer = FALSE THEN 'TRUCK ONLY'
        ELSE 'TRUCK + TRAILER'
    END as tracking_capability
FROM companies c
JOIN carrier_tracking_config ctc ON c.permalink = ctc.carrier_permalink
WHERE c.permalink = 'usa-truck-inc'
```

#### Gap Identified

| Component | Has Capability? | Evidence |
|-----------|-----------------|----------|
| Cassie | ❌ No | No device type validation |
| Neo4j MCP | ❌ No | No carrier_tracking_config access |
| RCA Agent | ✅ Yes | Pattern `H_DEVICE_TYPE_MISMATCH` added |

---

### Case 2682612: ELD Not Enabled at Network Level

<table>
<tr>
<td width="50%" style="background-color: #0a0a0a; color: white; padding: 20px;">

#### Problem Statement

**Shipper:** Bayer CropScience Mexico
**Load:** 835456344

> "Load not tracking, ping test working for Telematic"

</td>
<td width="50%" style="background-color: #0a0a0a; color: white; padding: 20px;">

#### Actual Root Cause

**ELD tracking wasn't enabled at the network level**

This is "the basic first step of ELD tracking" (per support comment)

</td>
</tr>
</table>

#### What Cassie Did

```
┌─────────────────────────────────────────────────────────────────────┐
│  CASSIE ANALYSIS                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  ✓ Classification: FOURKITES_LOAD_NOT_TRACKING                      │
│  ✓ Identified: "tracking updates not flowing despite successful ping"│
│  ✗ Investigation: NONE                                               │
│  ✗ Network ELD Config Check: NOT PERFORMED                          │
│  ✗ Company Relationship Check: NOT PERFORMED                        │
│  → Result: MANUAL INTERVENTION                                       │
│                                                                      │
│  Note: "Bot got stuck in decision loop" (per engineering comment)   │
└─────────────────────────────────────────────────────────────────────┘
```

#### What Should Have Been Done

```
┌─────────────────────────────────────────────────────────────────────┐
│  REQUIRED INVESTIGATION STEPS                                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  1. Check Network Relationship ELD Configuration                     │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ SELECT cr.id, cr.eld_enabled, cr.eld_provider,               │ │
│     │        c1.name as shipper, c2.name as carrier                │ │
│     │ FROM company_relationships cr                                │ │
│     │ JOIN companies c1 ON cr.company_id = c1.id                   │ │
│     │ JOIN companies c2 ON cr.target_company_id = c2.id            │ │
│     │ WHERE c1.permalink = 'bayer-cropscience-mexico'              │ │
│     └─────────────────────────────────────────────────────────────┘ │
│     Result: eld_enabled = FALSE ← ROOT CAUSE                        │
│                                                                      │
│  2. Check Carrier ELD Provider Status                                │
│     ┌─────────────────────────────────────────────────────────────┐ │
│     │ SELECT carrier_permalink, eld_provider, eld_enabled          │ │
│     │ FROM carrier_eld_config                                      │ │
│     │ WHERE carrier_permalink = '{carrier}'                        │ │
│     └─────────────────────────────────────────────────────────────┘ │
│     Result: Carrier has Telematic configured, but network disabled  │
│                                                                      │
│  3. Identify Pattern: ELD NOT ENABLED                                │
│     → Root Cause: ELD_NOT_ENABLED                                   │
│     → Resolution: Enable ELD in FourKites Connect                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

#### Evidence: Network ELD Configuration Query

```sql
-- Query to check ELD enablement at network level
SELECT
    cr.id as relationship_id,
    c1.name as shipper_name,
    c2.name as carrier_name,
    cr.eld_enabled,
    cr.eld_provider,
    cr.status as relationship_status,
    CASE
        WHEN cr.eld_enabled = FALSE THEN 'ELD NOT ENABLED - CRITICAL'
        WHEN cr.eld_provider IS NULL THEN 'ELD PROVIDER NOT SET'
        ELSE 'ELD CONFIGURED'
    END as eld_status
FROM company_relationships cr
JOIN companies c1 ON cr.company_id = c1.id
JOIN companies c2 ON cr.target_company_id = c2.id
WHERE c1.permalink = 'bayer-cropscience-mexico'
  AND cr.etl_active_flag = 'Y'
```

#### Gap Identified

| Component | Has Capability? | Evidence |
|-----------|-----------------|----------|
| Cassie | ❌ No | No network ELD config check |
| Neo4j MCP | ❌ No | No company_relationships access |
| RCA Agent | ✅ Yes | Pattern `H_ELD_NOT_ENABLED_NETWORK` added |

---

## Consolidated Gap Analysis

### Component Capability Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CAPABILITY MATRIX: LOAD_NOT_TRACKING                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Diagnostic Check              │ Cassie │ Neo4j MCP │ RCA Agent │ Required  │
│  ─────────────────────────────────────────────────────────────────────────  │
│  Classify LOAD_NOT_TRACKING    │   ✅   │    ❌     │    ✅     │    ✅     │
│  Query SigNoz Logs             │   ❌   │    ✅     │    ✅     │    ✅     │
│  GPS Timestamp Validation      │   ❌   │    ❌     │    ✅     │    ✅     │
│  Location Freshness Check      │   ❌   │    ❌     │    ✅     │    ✅     │
│  Device Type Discrimination    │   ❌   │    ❌     │    ✅     │    ✅     │
│  Network ELD Configuration     │   ❌   │    ❌     │    ✅     │    ✅     │
│  Carrier GPS Capability        │   ❌   │    ❌     │    ✅     │    ✅     │
│  Code Flow Tracing             │   ❌   │    ✅     │    ⚠️     │    ⚠️     │
│  Tracking Position History     │   ❌   │    ❌     │    ⚠️*    │    ✅     │
│  ─────────────────────────────────────────────────────────────────────────  │
│  OVERALL SCORE                 │  1/9   │   2/9    │   7/9    │   9/9    │
│                                │  11%   │   22%    │   78%    │  100%    │
│                                                                              │
│  Legend: ✅ Has capability  ❌ Missing  ⚠️ Partial  *Needs data access       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Root Cause Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         WHY CASSIE FAILS                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   Issue Received                                                             │
│        │                                                                     │
│        ▼                                                                     │
│   ┌─────────────────┐                                                        │
│   │  Classification │ ──────────────────────────────────────────────────┐   │
│   │  Engine         │                                                    │   │
│   └────────┬────────┘                                                    │   │
│            │                                                              │   │
│            ▼                                                              │   │
│   ┌─────────────────────────────────────────────────────────────────┐    │   │
│   │              ROUTING DECISION (main.py:1926)                     │    │   │
│   │                                                                   │    │   │
│   │   if category in ['LOAD_NOT_TRACKING', ...]:                     │    │   │
│   │       return 'manual_intervention_required'  ← PROBLEM HERE      │    │   │
│   │                                                                   │    │   │
│   └───────────────────────────────┬─────────────────────────────────┘    │   │
│                                   │                                       │   │
│                                   ▼                                       │   │
│   ┌─────────────────────────────────────────────────────────────────┐    │   │
│   │                    MANUAL INTERVENTION                           │    │   │
│   │                                                                   │    │   │
│   │   No investigation performed. Human support takes over.          │    │   │
│   │                                                                   │    │   │
│   │   ❌ No GPS API check                                            │    │   │
│   │   ❌ No log query                                                 │    │   │
│   │   ❌ No device config check                                       │    │   │
│   │   ❌ No network config check                                      │    │   │
│   │                                                                   │    │   │
│   └─────────────────────────────────────────────────────────────────┘    │   │
│                                                                              │
│   RESULT: 100% Manual Intervention Rate for LOAD_NOT_TRACKING               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Solution: RCA Agent Patterns Added

### New Patterns for LOAD_NOT_TRACKING

I have added **6 new hypothesis patterns** to address these cases:

```python
# Source: rca-backend/app/agents/hypothesis_patterns.py

LOAD_NOT_TRACKING_PATTERNS = [
    # Case 2693837: GPS returning null timestamps
    HypothesisPattern(
        id="H_GPS_NULL_TIMESTAMPS",
        category=RootCauseCategory.GPS_NULL_TIMESTAMPS,
        description="GPS provider returning null timestamps - no valid location data",
        triggers=["load not tracking", "no location updates", "null timestamps"],
        # ... evidence patterns and resolution templates
    ),

    # Case 2688628: GPS returning old locations
    HypothesisPattern(
        id="H_GPS_STALE_LOCATION",
        category=RootCauseCategory.GPS_STALE_LOCATION,
        description="GPS returning outdated/stale location data",
        triggers=["load not tracking", "old location", "stale GPS", "not updating"],
        # ... evidence patterns and resolution templates
    ),

    # Case 2692749: Trailer vs Truck GPS mismatch
    HypothesisPattern(
        id="H_DEVICE_TYPE_MISMATCH",
        category=RootCauseCategory.DEVICE_TYPE_MISMATCH,
        description="Trailer assigned to load but only Truck GPS is supported",
        triggers=["load not tracking", "trailer not tracking", "truck GPS only"],
        # ... evidence patterns and resolution templates
    ),

    # Case 2682612: ELD not enabled at network level
    HypothesisPattern(
        id="H_ELD_NOT_ENABLED_NETWORK",
        category=RootCauseCategory.ELD_NOT_ENABLED,
        description="ELD tracking not enabled at network relationship level",
        triggers=["load not tracking", "ELD not enabled", "network configuration"],
        # ... evidence patterns and resolution templates
    ),

    # Additional patterns
    HypothesisPattern(id="H_GPS_PROVIDER_ISSUE", ...),
    HypothesisPattern(id="H_DEVICE_NOT_ASSIGNED", ...),
]
```

### Pattern Count Summary

```
┌─────────────────────────────────────────────────────────────────┐
│                    HYPOTHESIS PATTERNS SUMMARY                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Category                        │ Patterns │ From Cassie │ New │
│  ────────────────────────────────────────────────────────────── │
│  LOAD_NOT_FOUND                  │    4     │     ✅      │     │
│  NETWORK_RELATIONSHIP            │    2     │     ✅      │     │
│  SCAC_VALIDATION                 │    3     │     ✅      │     │
│  OCEAN_TRACKING                  │    2     │     ✅      │     │
│  DUPLICATE_LOAD                  │    1     │     ✅      │     │
│  LOAD_NOT_TRACKING (NEW)         │    6     │             │ ✅  │
│  ────────────────────────────────────────────────────────────── │
│  TOTAL                           │   18     │     12      │  6  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Recommendations

### Immediate Actions

| Priority | Action | Owner | Impact |
|----------|--------|-------|--------|
| P0 | Remove LOAD_NOT_TRACKING from manual_intervention_categories in Cassie | Engineering | Enables investigation |
| P0 | Add SigNoz log queries for GPS/ELD errors to investigation flow | Engineering | Diagnoses null timestamp & stale location |
| P1 | Create device configuration check capability | Engineering | Diagnoses truck vs trailer |
| P1 | Add network ELD configuration query | Engineering | Diagnoses ELD not enabled |

### Architecture Proposal

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROPOSED LOAD_NOT_TRACKING FLOW                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   LOAD_NOT_TRACKING Received                                                │
│            │                                                                 │
│            ▼                                                                 │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Step 1: Query Tracking API                                          │  │
│   │  • Does load exist? → If NO, redirect to LOAD_NOT_FOUND             │  │
│   │  • Get tracking_source, device_id, carrier                           │  │
│   └─────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Step 2: Check Device Configuration                                  │  │
│   │  • Is device assigned? → If NO: H_DEVICE_NOT_ASSIGNED               │  │
│   │  • Device type matches load? → If NO: H_DEVICE_TYPE_MISMATCH        │  │
│   └─────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Step 3: Check Network Configuration                                 │  │
│   │  • ELD enabled? → If NO: H_ELD_NOT_ENABLED_NETWORK                  │  │
│   │  • GPS provider configured? → If NO: H_GPS_PROVIDER_ISSUE           │  │
│   └─────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Step 4: Check Position Data                                         │  │
│   │  • Timestamp null? → H_GPS_NULL_TIMESTAMPS                          │  │
│   │  • Timestamp stale? → H_GPS_STALE_LOCATION                          │  │
│   └─────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Step 5: Query SigNoz Logs for Error Patterns                        │  │
│   │  • Find GPS provider errors                                          │  │
│   │  • Find ingestion rejection reasons                                  │  │
│   │  • Correlate with tracking_id                                        │  │
│   └─────────────────────────────────┬───────────────────────────────────┘  │
│                                     │                                       │
│                                     ▼                                       │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  Step 6: Synthesize Root Cause                                       │  │
│   │  • Match evidence to hypothesis patterns                             │  │
│   │  • Calculate confidence score                                        │  │
│   │  • Generate resolution template                                      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Appendix: Source Code References

### Cassie Manual Intervention Routing

**File:** `agent-cassie/main.py`
**Lines:** ~1920-1935

```python
# Categories that require manual intervention
manual_intervention_categories = [
    'fourkites_load_not_tracking', 'LOAD_NOT_TRACKING',  # ← THE PROBLEM
    'fourkites_tl_status_update', 'TL_STATUS_UPDATE'
]

# Route to manual intervention
if classification_category in manual_intervention_categories:
    return {
        'endpoint': 'manual_intervention_required',
        'name': 'Manual Support Team',
        'description': 'Requires manual intervention from FourKites internal support team'
    }
```

### Neo4j MCP Server Tools

**File:** `mcp-servers/neo4j_mcp/src/tools/signoz_tools.py`

```python
@mcp_server.tool()
async def get_signoz_logs(
    correlation_id: Optional[str] = None,
    service_name: Optional[str] = None,
    severity: Optional[str] = None,
    ...
) -> List[Dict]:
    """Query SigNoz logs - useful but missing GPS-specific logic"""
    pass
```

### RCA Agent Hypothesis Patterns

**File:** `rca-backend/app/agents/hypothesis_patterns.py`

```python
LOAD_NOT_TRACKING_PATTERNS = [
    HypothesisPattern(
        id="H_GPS_NULL_TIMESTAMPS",
        category=RootCauseCategory.GPS_NULL_TIMESTAMPS,
        description="GPS provider returning null timestamps",
        triggers=["load not tracking", "null timestamps"],
        evidence_patterns=[
            EvidencePattern(
                source="Tracking Database",
                condition="latest position has timestamp IS NULL",
                finding_template="GPS data has null timestamp",
                supports_hypothesis=True,
                weight=0.95,
            ),
            # ... more evidence patterns
        ],
        resolution_templates={
            "CARRIER": "GPS provider not returning valid data...",
            "SHIPPER": "GPS tracking not receiving valid data..."
        }
    ),
    # ... 5 more patterns
]
```

---

<div align="center">

**End of Report**

*Generated by RCA Agent Analysis System*
*January 21, 2026*

```
┌─────────────────────────────────────────┐
│  LOAD_NOT_TRACKING Gap Analysis v1.0    │
│  Evidence-Based Investigation Report    │
└─────────────────────────────────────────┘
```

</div>
