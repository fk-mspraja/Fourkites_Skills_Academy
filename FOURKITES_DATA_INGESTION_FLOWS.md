# FourKites Data Ingestion Architecture

This document explains the three primary data ingestion paths in the FourKites tracking platform, based on the source and type of tracking data.

---

## Overview

FourKites processes tracking updates through three distinct architectural paths:

1. **Load Files** → Integration Worker
2. **Carrier Files** → Carrier Files Worker
3. **Carrier API Integration** → Dispatcher API → Carrier Files Worker

Each path has different entry points, processing logic, and routing mechanisms.

---

## Path 1: Load File Ingestion

**Source:** Customer/shipper uploads load file

```
┌─────────────────────────────────────────────────────────────────┐
│                        LOAD FILE PATH                            │
└─────────────────────────────────────────────────────────────────┘

  Customer Upload (CSV/EDI/API)
           │
           ▼
  ┌─────────────────────┐
  │ Integration Worker  │  ← ENTRY POINT
  │                     │
  │ - Parse load file   │
  │ - Validate data     │
  │ - Extract loads     │
  └─────────────────────┘
           │
           │ queues to
           ▼
  ┌─────────────────────────┐
  │ Tracking Service        │
  │ Internal Queue          │
  │                         │
  │ - Create/update loads   │
  │ - Link relationships    │
  │ - Trigger subscriptions │
  └─────────────────────────┘
```

**Characteristics:**
- Entry point: `integration-worker`
- Processes shipper-provided load information
- Creates load records in platform
- Sets up tracking subscriptions
- Single queue destination: Tracking Service Internal

---

## Path 2: Carrier File Ingestion

**Source:** Carrier uploads status file (via SFTP/Portal/API)

```
┌─────────────────────────────────────────────────────────────────┐
│                      CARRIER FILE PATH                           │
└─────────────────────────────────────────────────────────────────┘

  Carrier File (SFTP/Portal/API)
           │
           ▼
  ┌─────────────────────────────────────┐
  │ Carrier Files Worker (CFW)          │  ← ENTRY POINT
  │                                     │
  │ - Parse carrier file                │
  │ - Identify mode (Ocean/LTL/TL)     │
  │ - Determine update vs insert        │
  │ - Route to appropriate queue        │
  └─────────────────────────────────────┘
           │
           │ routes to MULTIPLE queues based on mode
           │
           ├──────────────┬──────────────┬──────────────┐
           ▼              ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Ocean   │  │ Tracking │  │   LTL    │  │   ...    │
    │  Queue   │  │  Queue   │  │  Queue   │  │  Queue   │
    └──────────┘  └──────────┘  └──────────┘  └──────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
    Mode-specific workers process updates
```

**CFW Responsibilities:**
1. **Parse** carrier file format
2. **Identify** update type (new event vs update existing)
3. **Determine mode** (Ocean, LTL, Truckload, Rail, Air)
4. **Route** to correct queue based on mode

**Characteristics:**
- Entry point: `carrier-files-worker`
- Processes carrier-provided status updates
- Smart routing based on shipment mode
- Multiple queue destinations
- CFW does NOT process updates, only routes them

---

## Path 3: Carrier API Integration (Dispatcher Updates)

**Source:** Carrier system pushes updates via API

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   CARRIER API INTEGRATION PATH                               │
└─────────────────────────────────────────────────────────────────────────────┘

  Carrier System (Real-time push)
           │
           │ HTTPS POST
           ▼
  ┌───────────────────────────────────────┐
  │ Tracking Service External             │  ← API ENDPOINT
  │ (tracking-api.fourkites.com)          │
  │                                       │
  │ - Authenticate carrier                │
  │ - Validate request                    │
  │ - Log API call                        │
  │ - Create file in S3                   │  ⚠️ Creates file representation
  └───────────────────────────────────────┘
           │
           │ triggers event
           ▼
  ┌───────────────────────────────────────┐
  │ S3 Event → CFW Queue                  │
  └───────────────────────────────────────┘
           │
           ▼
  ┌───────────────────────────────────────┐
  │ Carrier Files Worker (CFW)            │
  │                                       │
  │ - Process "file" from S3              │
  │ - Parse dispatcher update             │
  │ - Identify mode                       │
  │ - Route to appropriate queue          │
  └───────────────────────────────────────┘
           │
           │ routes based on mode
           │
           ├──────────────┬──────────────┬──────────────┐
           ▼              ▼              ▼              ▼
    ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
    │  Ocean   │  │ Tracking │  │   LTL    │  │   ...    │
    │  Queue   │  │  Queue   │  │  Queue   │  │  Queue   │
    └──────────┘  └──────────┘  └──────────┘  └──────────┘
           │              │              │              │
           ▼              ▼              ▼              ▼
    ┌──────────────────────────────────────────────────┐
    │  Global Worker / Multimodal Workers              │
    │                                                  │
    │  - PROCESS_TRUCK_LOCATION                       │
    │  - PROCESS_OCEAN_UPDATE                         │
    │  - Update load status                           │
    │  - Generate milestones                          │
    └──────────────────────────────────────────────────┘
```

**Key Insight:** API calls are converted to "file" representation!

**Flow Details:**

1. **Carrier System** → Dispatcher API (HTTPS POST)
   ```json
   {
     "updates": [{
       "shipper": "102622",
       "billOfLading": "9118452",
       "latitude": 40.672,
       "longitude": -74.190,
       "locatedAt": "2025-11-25T21:15:42.636Z"
     }]
   }
   ```

2. **Tracking Service External** receives request
   - Authenticates carrier via client_id/signature
   - Logs API call (execution_time_in_ms: 7.39)
   - Creates file representation in S3
   - Returns 200 OK

3. **S3 Event** triggers CFW queue

4. **Carrier Files Worker** processes
   - Reads "file" from S3
   - Message type: `PROCESS_SUPER_RECORD`
   - Parses dispatcher update
   - Routes to appropriate queue (Tracking Queue in this case)

5. **Global Worker** executes final processing
   - Message type: `PROCESS_TRUCK_LOCATION`
   - Updates load position
   - Records metrics

**Characteristics:**
- Entry point: `tracking-service-external` (API)
- Converts API call → S3 file → CFW queue
- Real-time push from carrier
- Eventually follows same routing as Path 2
- Most responsive (< 10ms API response)

---

## Log Data Analysis: Path 3 Example

The provided log data (`log_data (38).csv`) shows **Path 3** in action:

### Timeline Reconstruction

| Time | Service | Message | Description |
|------|---------|---------|-------------|
| 21:15:58.451 | tracking-service-external | API Request | Carrier POSTs dispatcher update |
| 21:15:58.459 | tracking-service-external | API Response | Returns 200 OK (7.39ms) |
| 21:16:00.830 | carrier-files-worker | PROCESS_SUPER_RECORD | CFW processes "file" from S3 |
| 21:16:00.868 | carrier-files-worker | DataMonitoring | Records metrics: status=success |
| 21:16:00.935 | global-worker-ex | PROCESS_TRUCK_LOCATION | Updates load location |

**Total Processing Time:** ~2.5 seconds (API → Final update)

### Key Identifiers

```yaml
load_id: "9118452"
bol_number: "9118452"
carrier: "pepsi-logistics-company"
external_id: "102622"
source: "dispatcher_updates_api"
mode: "api"  # vs "file" for actual file uploads
tracking_method: "dispatcher_updates_api"
correlation_id: "3d56bb4db0b5", "7e06fd9157a6"
```

### Services Involved

1. **tracking-service-external**
   - Cluster: otr-eks-production
   - Namespace: tracking-service-external
   - Role: API ingestion

2. **carrier-files-worker**
   - Cluster: common-eks-prod
   - Namespace: carrier-files-worker
   - Role: Parse and route

3. **global-worker-ex**
   - Cluster: aws-kube-prod
   - Namespace: global-worker
   - Role: Execute location update

---

## Comparison Matrix

| Aspect | Load File (Path 1) | Carrier File (Path 2) | Carrier API (Path 3) |
|--------|-------------------|----------------------|---------------------|
| **Entry Point** | integration-worker | carrier-files-worker | tracking-service-external |
| **Source** | Shipper/Customer | Carrier file upload | Carrier API push |
| **Data Format** | Load manifest | Status updates | JSON API payload |
| **S3 File?** | Yes (original file) | Yes (original file) | Yes (generated file) |
| **CFW Involvement** | No | Yes (parse & route) | Yes (parse & route) |
| **Queue Count** | 1 (Tracking Internal) | Multiple (by mode) | Multiple (by mode) |
| **Latency** | Minutes (batch) | Minutes (batch) | Seconds (real-time) |
| **Use Case** | Create/update loads | Carrier status feed | Real-time tracking |

---

## Queue Routing Logic (CFW)

```python
# Pseudo-code for CFW routing logic

def route_message(parsed_data):
    mode = identify_mode(parsed_data)
    operation = determine_operation(parsed_data)  # insert vs update

    if mode == "OCEAN":
        queue = "ocean_queue"
    elif mode == "LTL":
        queue = "ltl_queue"
    elif mode == "TRUCKLOAD":
        queue = "tracking_queue"
    elif mode == "RAIL":
        queue = "rail_queue"
    elif mode == "AIR":
        queue = "air_queue"
    else:
        queue = "default_queue"

    publish_to_queue(queue, parsed_data)
```

---

## Ocean Debugging Agent: Query Patterns

Based on these flows, here's how to query logs for debugging:

### Pattern 1: Trace by Load ID

```sql
-- SigNoz ClickHouse
SELECT
    timestamp,
    service_name,
    JSONExtractString(body, 'MessageType') as message_type,
    body
FROM signoz_logs.distributed_logs
WHERE body LIKE '%9118452%'  -- load_id
ORDER BY timestamp
```

### Pattern 2: Trace by Correlation ID

```sql
SELECT
    timestamp,
    service_name,
    correlation_id,
    message_type,
    body
FROM signoz_logs.distributed_logs
WHERE correlation_id IN ('3d56bb4db0b5', '7e06fd9157a6')
ORDER BY timestamp
```

### Pattern 3: Find CFW Routing Decisions

```sql
SELECT
    timestamp,
    body
FROM signoz_logs.distributed_logs
WHERE service_name = 'carrier-files-worker'
  AND body LIKE '%queued_messages%'
  AND body LIKE '%9118452%'
```

### Pattern 4: Check API Ingestion

```sql
SELECT
    timestamp,
    JSONExtractString(body, 'execution_time_in_ms') as exec_time,
    JSONExtractString(body, 'response_code') as response,
    JSONExtractString(body, 'url') as url
FROM signoz_logs.distributed_logs
WHERE service_name = 'tracking-service-external'
  AND body LIKE '%TRACKING_SERVICE_API_SUMMARY%'
  AND body LIKE '%9118452%'
```

---

## Integration Points for Ocean Debugging Agent

### 1. Identify Ingestion Path

```python
def identify_ingestion_path(load_id: str) -> str:
    """Determine which path the load came through"""

    # Check for API ingestion
    api_logs = query_signoz(
        service="tracking-service-external",
        search=load_id
    )
    if api_logs:
        return "PATH_3_API"

    # Check for CFW processing
    cfw_logs = query_signoz(
        service="carrier-files-worker",
        search=load_id
    )
    if cfw_logs:
        return "PATH_2_CARRIER_FILE"

    # Check for integration worker
    iw_logs = query_signoz(
        service="integration-worker",
        search=load_id
    )
    if iw_logs:
        return "PATH_1_LOAD_FILE"

    return "UNKNOWN"
```

### 2. Check CFW Routing

```python
def check_cfw_routing(load_id: str) -> Dict:
    """Verify CFW correctly routed the message"""

    cfw_logs = query_signoz(
        service="carrier-files-worker",
        message_contains=["queued_messages", load_id]
    )

    for log in cfw_logs:
        metrics = parse_data_monitoring(log)
        return {
            "status": metrics.get("status"),
            "queued_messages": metrics.get("queued_messages"),
            "skipped_messages": metrics.get("skipped_messages"),
            "error": metrics.get("error")
        }
```

### 3. Validate End-to-End Flow

```python
def validate_e2e_flow(load_id: str) -> Dict:
    """Check if update made it through entire pipeline"""

    steps = {
        "api_received": check_tracking_service_external(load_id),
        "cfw_processed": check_carrier_files_worker(load_id),
        "worker_executed": check_global_worker(load_id),
        "load_updated": check_tracking_api(load_id)
    }

    return {
        "complete": all(steps.values()),
        "steps": steps,
        "bottleneck": identify_bottleneck(steps)
    }
```

---

## Common Issues by Path

### Path 1 (Load File) Issues
- Invalid load file format
- Missing required fields
- Duplicate load IDs
- Integration worker timeout

### Path 2 (Carrier File) Issues
- Unsupported carrier file format
- Incorrect mode detection
- CFW parsing errors
- Wrong queue routing

### Path 3 (API Integration) Issues ⚠️ **MOST COMMON**
- Authentication failures (invalid signature)
- S3 file creation failed
- CFW not picking up S3 event
- **Network relationship missing** (7.7% of loads)
- API timeout (> 30s)

---

## Recommendations

1. **For Ocean Debugging Agent:**
   - Always check ingestion path first
   - Path 3 issues are most common for stuck loads
   - Look for gaps in the timeline (API → CFW → Worker)
   - Verify S3 file was created
   - Check CFW routing decision

2. **Monitoring Priorities:**
   - Track API → S3 → CFW latency
   - Alert on CFW routing errors
   - Monitor queue depths
   - Track end-to-end processing time

3. **Debug Checklist:**
   ```
   □ Which path? (API, carrier file, load file)
   □ Did API respond 200 OK?
   □ Was S3 file created?
   □ Did CFW process it?
   □ Which queue was it routed to?
   □ Did worker pick it up?
   □ Was load updated?
   ```

---

**Last Updated:** 2026-01-13
**Author:** MSP Raja
**Related:** OCEAN_DEBUGGING_POC_CONFLUENCE.md
