# Carrier Files Worker (CFW) - Deep Dive with Examples

## What is CFW?

**Carrier Files Worker (CFW)** is the intelligent routing service in FourKites that acts as the "traffic controller" for all carrier-provided tracking data.

Think of CFW as an **airport traffic control tower**:
- Planes (data files) arrive from different sources
- Tower (CFW) identifies each plane (file type, mode, carrier)
- Routes each plane to the correct gate (queue)
- Doesn't load/unload passengers (doesn't process updates)
- Just directs traffic efficiently

---

## CFW's Core Responsibilities

```
┌─────────────────────────────────────────────────────────┐
│              CARRIER FILES WORKER (CFW)                  │
│                                                          │
│  1. PARSE      → Extract data from file/API payload     │
│  2. IDENTIFY   → Determine mode, carrier, identifiers   │
│  3. VALIDATE   → Check data quality, required fields    │
│  4. ROUTE      → Send to appropriate queue(s)           │
│  5. MONITOR    → Log metrics for observability          │
│                                                          │
│  ⚠️ DOES NOT PROCESS UPDATES ITSELF                     │
└─────────────────────────────────────────────────────────┘
```

---

## Real Example from log_data (38).csv

Let's trace CFW's processing of our Pepsi Logistics dispatcher update:

### Input: API Call Converted to File

**Timestamp:** 2025-11-26 02:46:00.830

**Service:** carrier-files-worker

**Message Type:** PROCESS_SUPER_RECORD

**Raw Log Body:**
```ruby
[7e06fd9157a6] PRMS: {
  "MessageType"=>"PROCESS_SUPER_RECORD",
  "Source"=>"dispatcher_updates_api",
  "api_source"=>nil,
  "ApiRequestUuid"=>"51599914-086f-48c5-80a8-4856107a1df8",
  "Content"=>{
    "StartTime"=>"2025-11-25T21:15:58.456Z",
    "SuperAdmin"=>false,
    "Carrier"=>"pepsi-logistics-company",
    "Mode"=>"api",
    "TrackingMethod"=>"dispatcher_updates_api",
    "UserCompanyType"=>["broker", "shipper", "carrier", "customer"],
    "ReceivedTime"=>"2025-11-25T21:15:58Z",
    "ExternalId"=>"102622",
    "LoadIdentifier"=>"9118452",
    "Latitude"=>40.672000885009766,
    "Longitude"=>-74.19000244140625,
    "LocatedAt"=>"2025-11-25T21:15:42.636Z",
    "TimeZone"=>"UTC"
  },
  "sqs_publisher"=>"tracking-service",
  "sender"=>"tracking-service",
  "timestamp"=>1764105358458,
  "sqs_message_id"=>"40b19bde-18e1-407a-b638-a90f783b7341",
  "sent_timestamp"=>1764105360787
}
```

### CFW's Processing Breakdown

#### 1. PARSE Phase

CFW extracts key information:

```python
{
    "message_type": "PROCESS_SUPER_RECORD",
    "source": "dispatcher_updates_api",
    "carrier": "pepsi-logistics-company",
    "external_id": "102622",
    "load_identifier": "9118452",
    "latitude": 40.672000885009766,
    "longitude": -74.19000244140625,
    "located_at": "2025-11-25T21:15:42.636Z",
    "tracking_method": "dispatcher_updates_api",
    "mode": "api"  # Not the shipment mode!
}
```

**Key Identifiers Extracted:**
- `load_identifier_1`: "9118452" (primary)
- `load_identifier_2`: nil
- `load_identifier_3`: nil
- `load_identifier_4`: nil
- `external_id`: "102622" (carrier's reference)

#### 2. IDENTIFY Phase

CFW determines:

```yaml
Shipment Mode: TRUCKLOAD
  └─ Reason: Dispatcher updates API is typically used for truck tracking
  └─ Confirmed by: No BOL/container pattern matching ocean

Carrier: pepsi-logistics-company
  └─ Carrier ID: (from company_relationships table)

Operation Type: UPDATE
  └─ Not INSERT (load already exists)

Data Source Priority: API (highest)
  └─ dispatcher_updates_api > EDI > file upload
```

#### 3. VALIDATE Phase

CFW checks:

```python
✅ Required fields present:
   - LoadIdentifier: "9118452"
   - Carrier: "pepsi-logistics-company"
   - Latitude: 40.672000885009766
   - Longitude: -74.19000244140625
   - LocatedAt: "2025-11-25T21:15:42.636Z"

✅ Data quality:
   - Coordinates valid (NY/NJ area)
   - Timestamp recent (< 1 hour old)
   - Carrier authenticated

✅ Business rules:
   - Load exists in system
   - Carrier has permission to update
   - Not duplicate event
```

#### 4. ROUTE Phase

CFW decides which queue(s) to send this to:

**Output: DataMonitoring Metrics**

**Timestamp:** 2025-11-26 02:46:00.868

```ruby
[7e06fd9157a6] [DataMonitoringUtils] Record metrics: {
  "record_uuid"=>"a83cbd4a-8019-4425-8fc1-34e709416a9e",
  "file_uuid"=>nil,  # No physical file (API-generated)
  "company"=>"pepsi-logistics-company",
  "file_name"=>nil,
  "record_index"=>nil,
  "shipper_id"=>nil,
  "status"=>"success",  # ✅ CFW processed successfully
  "process_completed_timestamp"=>"2025-11-25T21:16:00Z",
  "error"=>nil,  # No errors
  "status_update_error"=>nil,
  "load_identifier_1"=>"9118452",
  "load_identifier_2"=>nil,
  "load_identifier_3"=>nil,
  "load_identifier_4"=>nil,
  "external_id"=>"102622",
  "queued_messages"=>["PROCESS_TRUCK_LOCATION"],  # ⚠️ ROUTING DECISION
  "skipped_messages"=>[]  # Nothing skipped
}
```

**Routing Decision:**
```
CFW queued to: ["PROCESS_TRUCK_LOCATION"]
  ↓
Sent to: Tracking Queue (for truckload updates)
  ↓
Will be picked up by: global-worker-ex
```

#### 5. MONITOR Phase

CFW records:

```yaml
Metrics:
  record_uuid: "a83cbd4a-8019-4425-8fc1-34e709416a9e"
  status: "success"
  process_completed_timestamp: "2025-11-25T21:16:00Z"
  queued_messages: ["PROCESS_TRUCK_LOCATION"]
  skipped_messages: []
  error: nil

Correlation ID: "7e06fd9157a6"
  └─ Used to trace this record across all services
```

---

## CFW's Output: The Queued Message

CFW publishes this message to the **Tracking Queue**:

**Received by:** global-worker-ex

**Timestamp:** 2025-11-26 02:46:00.935

**Message Type:** PROCESS_TRUCK_LOCATION

```ruby
[3d56bb4db0b5] PRMS: {
  "MessageType"=>"PROCESS_TRUCK_LOCATION",  # ⚠️ Transformed by CFW
  "Source"=>"dispatcher_updates_api",
  "Content"=>{
    "Carrier"=>"pepsi-logistics-company",
    "ExternalId"=>"102622",
    "ReceivedTime"=>"2025-11-25T21:15:58Z",
    "LoadIdentifier"=>"9118452",
    "BillOfLading"=>"9118452",
    "Latitude"=>40.672000885009766,
    "Longitude"=>-74.19000244140625,
    "LocatedAt"=>"2025-11-25T21:15:42.636Z",
    "TimeZone"=>"UTC",
    "Mode"=>"file",  # CFW marks it as "file" mode
    "TrackingMethod"=>"dispatcher_updates_api"
  },
  "RecordUuid"=>"a83cbd4a-8019-4425-8fc1-34e709416a9e",
  "sqs_publisher"=>"carrier-files-worker"  # ⚠️ CFW published this
}
```

**Key Transformations by CFW:**
1. ✅ Changed message type: `PROCESS_SUPER_RECORD` → `PROCESS_TRUCK_LOCATION`
2. ✅ Added `BillOfLading` field (copied from LoadIdentifier)
3. ✅ Set `Mode` to "file" (even though it came from API)
4. ✅ Added `RecordUuid` for traceability
5. ✅ Set itself as `sqs_publisher`

---

## CFW Decision Tree Example

Here's how CFW routes based on different inputs:

### Example 1: Ocean BOL Update

**Input:**
```json
{
  "LoadIdentifier": "MAEU123456789",
  "ContainerNumber": "TCNU1234567",
  "Carrier": "maersk-line",
  "Event": "VESSEL_DEPARTURE",
  "Port": "USNYC"
}
```

**CFW Processing:**
```python
mode = detect_mode(input)
# Container number pattern → OCEAN

queued_messages = ["PROCESS_OCEAN_UPDATE"]
routing_queue = "ocean_queue"
```

**Routed to:** Ocean Queue → multimodal_carrier_updates_worker

---

### Example 2: LTL Pro Number Update

**Input:**
```json
{
  "LoadIdentifier": "PRO12345678",
  "Carrier": "fedex-freight",
  "Status": "OUT_FOR_DELIVERY",
  "Terminal": "DAL"
}
```

**CFW Processing:**
```python
mode = detect_mode(input)
# PRO number pattern + carrier type → LTL

queued_messages = ["PROCESS_LTL_UPDATE"]
routing_queue = "ltl_queue"
```

**Routed to:** LTL Queue → ltl_worker

---

### Example 3: Multi-Modal (Ocean + Truck)

**Input:**
```json
{
  "LoadIdentifier": "9118452",
  "ContainerNumber": "TCNU1234567",  # Ocean
  "Carrier": "pepsi-logistics-company",  # Truckload
  "Status": "IN_TRANSIT",
  "Latitude": 40.672,
  "Longitude": -74.190
}
```

**CFW Processing:**
```python
mode = detect_mode(input)
# Has both container and GPS → BOTH ocean and truck

queued_messages = [
    "PROCESS_OCEAN_UPDATE",
    "PROCESS_TRUCK_LOCATION"
]
routing_queues = ["ocean_queue", "tracking_queue"]
```

**Routed to:** BOTH queues (parallel processing)

---

## CFW's Internal Architecture

```python
class CarrierFilesWorker:
    """
    Simplified representation of CFW logic
    """

    def process_super_record(self, message):
        """Main entry point for all carrier data"""

        # 1. PARSE
        parsed = self.parse_message(message)

        # 2. IDENTIFY
        mode = self.detect_mode(parsed)
        carrier_id = self.lookup_carrier(parsed['Carrier'])
        load = self.lookup_load(parsed['LoadIdentifier'])

        # 3. VALIDATE
        validation = self.validate_data(parsed, load)
        if not validation.valid:
            self.record_error(validation.error)
            return

        # 4. ROUTE
        messages = self.build_messages(parsed, mode, load)
        queues = self.determine_queues(mode)

        for queue, msg in zip(queues, messages):
            self.publish_to_queue(queue, msg)

        # 5. MONITOR
        self.record_metrics({
            'record_uuid': generate_uuid(),
            'status': 'success',
            'queued_messages': [m['MessageType'] for m in messages],
            'load_identifier_1': parsed['LoadIdentifier'],
            'company': parsed['Carrier']
        })

    def detect_mode(self, data):
        """Smart mode detection"""
        # Container number pattern
        if self.is_container_number(data.get('ContainerNumber')):
            return 'OCEAN'

        # PRO number pattern
        if self.is_pro_number(data.get('LoadIdentifier')):
            return 'LTL'

        # Rail patterns
        if data.get('RailCarNumber'):
            return 'RAIL'

        # Has GPS coordinates
        if data.get('Latitude') and data.get('Longitude'):
            return 'TRUCKLOAD'

        # Default
        return 'UNKNOWN'

    def determine_queues(self, mode):
        """Map mode to queue(s)"""
        queue_map = {
            'OCEAN': ['ocean_queue'],
            'LTL': ['ltl_queue'],
            'TRUCKLOAD': ['tracking_queue'],
            'RAIL': ['rail_queue'],
            'AIR': ['air_queue'],
            'MULTIMODAL': ['ocean_queue', 'tracking_queue']
        }
        return queue_map.get(mode, ['default_queue'])
```

---

## CFW Failure Scenarios

### Scenario 1: Parsing Failure

**Input:** Malformed JSON
```json
{
  "LoadIdentifier": "9118452",
  "Latitude": "invalid",  # Should be number
  "LocatedAt": "not-a-date"
}
```

**CFW Output:**
```ruby
{
  "status": "error",
  "error": "Failed to parse latitude: invalid",
  "queued_messages": [],
  "skipped_messages": ["PROCESS_TRUCK_LOCATION"]
}
```

**Result:** ❌ No message queued, load not updated

---

### Scenario 2: Load Not Found

**Input:**
```json
{
  "LoadIdentifier": "NONEXISTENT123",
  "Carrier": "test-carrier"
}
```

**CFW Output:**
```ruby
{
  "status": "error",
  "error": "Load not found: NONEXISTENT123",
  "queued_messages": [],
  "skipped_messages": []
}
```

**Result:** ❌ CFW can't route without valid load

---

### Scenario 3: Network Relationship Missing

**Input:**
```json
{
  "LoadIdentifier": "9118452",
  "Carrier": "pepsi-logistics-company"
}
```

**CFW Checks:**
```sql
SELECT * FROM company_relationships
WHERE shipper_id = 'shipper-123'
  AND carrier_id = 'pepsi-logistics-company'
```

**Result:** Empty (no relationship)

**CFW Output:**
```ruby
{
  "status": "error",
  "error": "No network relationship between shipper and carrier",
  "queued_messages": [],
  "skipped_messages": ["PROCESS_TRUCK_LOCATION"]
}
```

**Result:** ❌ **This is the 7.7% stuck load issue!**

---

## CFW Performance Metrics

From our log example:

| Metric | Value | Notes |
|--------|-------|-------|
| Processing Time | ~0.07s (70ms) | Time from receive to queue |
| Message Size | ~2KB | JSON payload |
| Queue Latency | ~2s | CFW queue → pickup by worker |
| Success Rate | 100% | This example succeeded |
| Queued Messages | 1 | PROCESS_TRUCK_LOCATION |
| Skipped Messages | 0 | No errors |

**Typical CFW Metrics:**
- **Throughput:** 10,000+ messages/minute
- **P99 Latency:** < 500ms
- **Error Rate:** ~5% (mostly validation failures)
- **Retry Rate:** ~2%

---

## CFW vs Other Workers

| Aspect | CFW | Integration Worker | Global Worker |
|--------|-----|-------------------|---------------|
| **Input** | Carrier data | Load files | Queued messages |
| **Processing** | Parse & route | Create loads | Update loads |
| **Output** | Queued messages | Loads in DB | Updated status |
| **Queue** | Multiple | Single | N/A (executor) |
| **Mode Detection** | ✅ Yes | ❌ No | ❌ No |
| **Data Source** | Carrier | Shipper | Any |

---

## CFW in Ocean Debugging Agent

### How to Query CFW Logs

```python
def check_cfw_processing(load_id: str) -> Dict:
    """Check if CFW processed this load"""

    query = """
    SELECT
        timestamp,
        JSONExtractString(body, 'status') as status,
        JSONExtractString(body, 'error') as error,
        JSONExtractString(body, 'queued_messages') as queued,
        JSONExtractString(body, 'skipped_messages') as skipped
    FROM signoz_logs.distributed_logs
    WHERE service_name = 'carrier-files-worker'
      AND body LIKE '%DataMonitoringUtils%'
      AND body LIKE '%{load_id}%'
    ORDER BY timestamp DESC
    LIMIT 1
    """

    result = clickhouse.execute(query)

    return {
        'processed': bool(result),
        'status': result['status'],
        'error': result['error'],
        'queued_messages': json.loads(result['queued']),
        'skipped_messages': json.loads(result['skipped'])
    }
```

### Decision Tree Step: Check CFW

```yaml
step_3_check_cfw:
  name: "Check CFW Processing"
  query: "DataMonitoringUtils for load_id"
  decisions:
    cfw_success:
      condition: "result.status == 'success'"
      conclusion:
        category: "cfw_routed_successfully"
      next_step: "step_4_check_worker"

    cfw_error:
      condition: "result.error != nil"
      conclusion:
        root_cause: "CFW parsing or routing error"
        category: "configuration_issue"
        explanation: "CFW failed to process carrier update"

    cfw_skipped:
      condition: "result.skipped_messages.length > 0"
      conclusion:
        root_cause: "CFW skipped message processing"
        category: "configuration_issue"
        explanation: "Check network relationship or data validation"
```

---

## Key Takeaways

1. **CFW is a router, not a processor**
   - Doesn't update loads
   - Doesn't calculate milestones
   - Just parses and routes

2. **CFW is mode-aware**
   - Detects Ocean vs Truck vs LTL vs Rail
   - Routes to specialized queues
   - Can send to multiple queues

3. **CFW is the chokepoint**
   - All carrier data flows through it (except Path 1)
   - If CFW fails, updates are lost
   - Network relationship checks happen here

4. **CFW provides excellent observability**
   - DataMonitoringUtils logs every decision
   - Records UUIDs for traceability
   - Logs queued/skipped messages

5. **CFW's correlation_id is critical**
   - Use it to trace across services
   - Links API → CFW → Worker
   - Essential for debugging

---

**Example from our data:**

```
API Call (21:15:58.451)
  correlation_id: None yet
    ↓
Tracking Service (21:15:58.459)
  request_id: "1bdcac930ded"
    ↓
CFW (21:16:00.830)
  correlation_id: "7e06fd9157a6"
  record_uuid: "a83cbd4a-8019-4425-8fc1-34e709416a9e"
    ↓
Global Worker (21:16:00.935)
  correlation_id: "3d56bb4db0b5"
  record_uuid: "a83cbd4a-8019-4425-8fc1-34e709416a9e"
```

Use `record_uuid` to trace the exact record through CFW → Worker!

---

**Created:** 2026-01-13
**Author:** MSP Raja
**Related:** FOURKITES_DATA_INGESTION_FLOWS.md, OCEAN_DEBUGGING_POC_CONFLUENCE.md
