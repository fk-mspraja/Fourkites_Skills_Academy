# Meeting Analysis: Troubleshooting Workflows Discussion
**Date:** January 14, 2026
**Attendees:** Surya, Prashant, Arpit, MSP Raja

---

## Executive Summary

Key meeting discussing carrier file processing workflows, debugging methodologies, and integration with the Ocean Debugging Agent POC. Prashant provided deep dive into carrier files worker (CFW) and support team's troubleshooting process.

---

## 1. Current Tool Access & Usage

### Rewind Tool
- **Current Users:** 6 people using daily
- **Use Case:** Solving support tickets based on available data
- **Target Audience:** Less expert users who need simpler interface than raw ClickHouse

### ClickHouse Access
- **Current Access:** Surya, Prashant, 1 other + all leads/managers
- **Tool:** Table Plus (trial version) - need licensed version
- **Issue:** Team needs proper licensed tool for database access

---

## 2. Infrastructure & Cost Optimization Strategy

### Current State
```
Primary ClickHouse:  $100k/year (60+ days retention)
Replica ClickHouse:   $90k/year (30 days retention)
S3 Storage:          Additional cost
─────────────────────────────────────────────────
Total:               ~$190k+ (burning 3x money)
```

### Target State
```
Merged ClickHouse:   $150k/year
  ├─ Hot Tier:       30 days (fast queries)
  ├─ S3 Tier:        60 days (archived)
  └─ Spog:           180 days (batch access)
```

### Strategy
1. Analyze usage patterns from rewind tool queries
2. Review Prashant's data catalog to understand common queries
3. Determine optimal retention per data type
4. Merge primary + replica into single higher-capacity system
5. Possibly eliminate Spog entirely (consolidate to one log system)

**Current Bottleneck:** Don't know usage patterns yet, so running replica safely

---

## 3. Carrier Files Processing - Deep Dive

### Overview: 60-80% of Tracking Happens via Files & API

### Debugging Workflow

```
┌────────────────────────────────────────────────────────────────┐
│                   SUPPORT DEBUGGING FLOW                        │
└────────────────────────────────────────────────────────────────┘

Step 1: Check Platform UI
  └─ Can issue be resolved from UI alone?
     ├─ Yes → Answer from UI (e.g., "no delivery location update")
     └─ No → Proceed to data debugging

Step 2: Identify Tracking Method
  └─ For this shipper-carrier relationship, what method?
     ├─ Files (multiple possible)
     ├─ GPS
     ├─ API
     └─ EDI

Step 3: Get Configuration
  └─ Carrier → Edit Company Page
     ├─ File integrations (may have multiple)
     ├─ Column mappings
     └─ Identifier configuration

Step 4: Check Network Relationship
  └─ Carrier → Network Page
     ├─ Which shipper-carrier relationships?
     ├─ What identifier is mapped? (load number, reference, BOL, etc.)
     └─ Which file integration for this relationship?

Step 5: Query Logs
  └─ ClickHouse / Spog
     ├─ Process Super Record (API)
     ├─ Process Super File Task (Files)
     └─ Raw data before system manipulation

Step 6: Identify Discrepancy
  └─ Data issue, integration issue, or configuration issue
```

---

## 4. Network Relationship Complexity (Critical for Debugging)

### The Core Problem

**Carriers don't send FourKites internal tracking ID**

```
Carrier sends:
{
  "external_id": "102622",        // Their shipper reference
  "identifier": "9118452",        // Could be anything
  "latitude": 40.672,
  "longitude": -74.190
}

FourKites needs to find:
{
  "tracking_id": "U110123982",    // Our internal ID
  "load_id": "...",
  "shipper_id": "...",
  "carrier_id": "..."
}
```

### Reverse Lookup Process

1. **Identify Shipper** (from external_id + carrier)
2. **Check Network Configuration** (shipper-carrier relationship)
3. **Match Identifier** (could be mapped to multiple fields)
   - Load number
   - Reference number
   - PRO number (LTL)
   - BOL (ocean)
   - Container number (ocean)
   - Custom fields

4. **Fallback Logic**
   - If no network match → Try load number
   - Still no match → Try reference numbers
   - Still no match → Error (most common failure mode)

### Example: CR England + Smithfield

**Carrier:** CR England
- Has 3+ file integrations
- Serves multiple shippers
- Each shipper may use different identifier

**Configuration Check:**
```
Edit Company Page → File Integrations → Column Mapping
  ├─ Integration 1: Identifier = Column 2 (load number)
  ├─ Integration 2: Identifier = Column 3 (reference number)
  └─ Integration 3: Identifier = Column 1 (BOL)

Network Page → Smithfield + CR England
  ├─ Super File 1: identifier_one = load_number
  ├─ Super File 2: identifier_one = reference_number_1
  └─ Super File 3: identifier_one = bill_of_lading
```

**Debugging Steps:**
1. Check historical delivered loads
2. Identify which integration was used
3. Check column mapping for that integration
4. Verify identifier field matches load data

---

## 5. Real Example: Pepsi Logistics Load (Exception Case)

### Load Details
- **Load Number:** 9118452
- **Carrier:** None (Pepsi Logistics Company is the carrier)
- **Tracking Method:** Dispatcher API (unusual for no-carrier loads)
- **Identifier Type:** Reference number (not load number)

### The Mystery
```
Normal Pattern:
  No carrier → Only carrier link tracking

This Load:
  No carrier → Dispatcher API updates (?!)
```

### What Happened
1. Pepsi Logistics created load for their own visibility
2. They are both shipper and carrier
3. Sent updates via dispatcher API
4. Load identifier was **reference number**, not load number
5. **System fallback:** Even without network mapping, system checks reference numbers
6. Update processed successfully

### Key Learning
**Prashant:** "This is the first time I'm seeing this... definite outlier"

**System Behavior:**
- Always falls back to checking load number + reference numbers
- Even without explicit network configuration
- Allows "carrier-less" loads to track via API (not just carrier link)

---

## 6. Source of Truth: CFW Logs

### Primary Logs for Debugging

**For API Updates:**
```sql
-- process_super_record
SELECT *
FROM signoz_logs.distributed_logs
WHERE service_name = 'carrier-files-worker'
  AND body LIKE '%process_super_record%'
  AND body LIKE '%9118452%'
```

**For File Updates:**
```sql
-- process_super_file_task
SELECT *
FROM signoz_logs.distributed_logs
WHERE service_name = 'carrier-files-worker'
  AND body LIKE '%process_super_file_task%'
  AND body LIKE '%9118452%'
```

### Why These Logs Matter

1. **Raw Data Before Manipulation**
   - Shows exactly what carrier sent
   - Before FourKites processing/transformation
   - Source of truth for disputes

2. **Identifier Validation**
   - Shows which identifier was received
   - Shows which field it was matched to
   - Reveals mismatches (configured as load number, sent reference number)

3. **Duplicate Detection**
   - UI doesn't show duplicate count
   - Logs show all updates received
   - Example: Carrier claims 1000 updates sent
     - UI shows: 3 updates
     - Logs reveal: 959 duplicates + 41 valid = 1000 ✓

4. **Integration Issues**
   - Email address changed on carrier side
   - FourKites not updated
   - Logs show: "Receiving but not processing (no match)"

---

## 7. Common Issue Categories

### Load-Level Issues
1. **Identifier Mismatch** (most common)
   - Configured: load_number
   - Carrier sends: reference_number
   - Result: No match, no update

2. **Network Relationship Missing** (7.7% of ocean loads)
   - Shipper-carrier relationship not configured
   - CFW can't route updates
   - Load stuck in "Awaiting Tracking Info"

3. **Incorrect Data from Carrier**
   - Carrier portal has wrong info
   - FourKites scrapes correct data (from JT)
   - Carrier fixes portal
   - **FourKites doesn't backfill** ❌

4. **Duplicate Updates**
   - Carrier sends same update multiple times
   - System filters most, but some get through
   - Causes milestone duplication

### Integration-Level Issues
1. **Email Address Changed**
   - Carrier updates their email
   - FourKites integration still uses old email
   - Files received but not processed

2. **File Format Changed**
   - Carrier changes CSV structure
   - Column mapping no longer matches
   - Parsing fails

3. **Authentication Issues**
   - API credentials expired
   - Signature validation fails
   - Updates rejected

### Mode-Specific Patterns

**Ocean:**
- JT scraping issues (carrier portal wrong → we scrape → carrier fixes → we don't backfill)
- BOL/container number confusion
- Vessel schedule changes

**Truckload:**
- GPS coordinate issues
- Reference number variations
- Dispatcher API authentication

**LTL:**
- PRO number format variations
- Terminal code mismatches
- Multiple carriers per load

---

## 8. Data Sources Used by Support Team

| Source | Purpose | Access Method |
|--------|---------|---------------|
| **Platform UI** | Quick load checks, customer view | Web browser |
| **ClickHouse** | Log queries, CFW processing | SQL (Table Plus) |
| **Redshift** | Network relationships, historical data | SQL |
| **Spog** | 180-day log retention, batch queries | SQL |
| **JT (Just Transform)** | Scraping history, carrier portal data | Portal + API |
| **Tracking API** | Load details, milestones, status | API |
| **Super API** | Internal configs, subscriptions | API |
| **Salesforce** | Ticket details, customer context | Web + API |
| **DW (Data Warehouse)** | Sometimes easier than Redshift | SQL |

---

## 9. Deliverables Promised by Prashant

### Data Dictionary (by end of day)

**Scope:**
- Carrier files processing (all types)
- API updates
- Status updates
- EDI updates

**Content:**
- Log query catalog
- Flow diagrams (service → service)
- Explanation of each log message
- Sub-log messages
- Queued messages
- What happens next

**Format:**
- Raw text
- JSON
- Flow from receipt → posting
- Explanations of what each log means

**Purpose:**
- Enable Raja to understand CFW processing
- Test if catalog is clear enough for beginners
- If Arpit + Raja can understand, team can understand

---

## 10. Ocean Debugging Agent - Approach Agreed

### Strategy

**Focus:** 2 use cases only (ocean tracking issues)
- Don't try to solve all random cases
- Build depth, not breadth

**Development Process:**
```
1. Raja leads implementation (with Arpit support)
2. Build agents/skills + human-in-the-loop
3. Internal workshop with Surya + Prashant
4. Get feedback, iterate
5. Demo to wider audience (leaders from both sides)
6. Determine path forward with management buy-in
```

### Expectations Set

**Arpit:** "There is assumption once we build something it will run forever and everyone can join. That may not be the case."

**Reality:**
- Randomness in support cases
- Can't automate everything
- Need ongoing participation from Surya + Prashant for future phases
- Some engineer time required

### Weekly Sync Format

**Surya's Proposal:**
- Not specific use cases (too random, never-ending)
- **Functional overviews:**
  - Week 1: Load creation
  - Week 2: Load not tracking (general)
  - Week 3: ETA issues
  - Week 4: Milestone problems
  - Etc.

**Goal:** Give Raja perspective on how to approach tickets → add to rewind tool

---

## 11. Tool Improvement Requests

### From Support Team

1. **EZ Load Creation Coverage**
   - Currently: Only API + flat file loads
   - Missing: Booking API (easy load creation)
   - Need: Add this flow to rewind tool

2. **Categorize by Load Mode**
   - Ocean
   - Truckload
   - LTL
   - Rail
   - Air

   **Why:** Different modes have different flows, easier to bucket queries

3. **Flow Visualization**
   - Which service to start with
   - Which service to check next
   - Complete log retrieval path

### From Infrastructure Team

4. **Anomaly Detection for Log Changes**
   - Alert when log format changes
   - Alert when log volume drops
   - Prevent "logs disappeared" scenarios

5. **AI PR Review**
   - Automatic review when PR touches logging code
   - Warn if log format changes
   - Flag if critical logs removed

---

## 12. Key Insights for Ocean Debugging Agent

### Critical Path: Network Relationship

```python
def check_network_relationship(shipper_id, carrier_id):
    """
    7.7% of stuck ocean loads caused by missing network relationship
    """
    query = """
    SELECT relationship_id, status, is_active
    FROM company_relationships
    WHERE shipper_id = ? AND carrier_id = ?
    """

    if not result:
        return {
            "root_cause": "network_relationship_missing",
            "impact": "7.7% of loads",
            "fix": "Create shipper-carrier relationship",
            "assignee": "Network Team"
        }
```

### CFW Source of Truth Pattern

```python
def get_cfw_processing_details(load_id):
    """
    Always start with CFW logs (process_super_record)
    """
    cfw_logs = query_signoz(
        service="carrier-files-worker",
        message_type="process_super_record",
        load_identifier=load_id
    )

    return {
        "raw_data_received": cfw_logs.get("Content"),
        "identifier_used": cfw_logs.get("LoadIdentifier"),
        "identifier_type": detect_type(cfw_logs.get("LoadIdentifier")),
        "queued_messages": cfw_logs.get("queued_messages"),
        "skipped_messages": cfw_logs.get("skipped_messages"),
        "error": cfw_logs.get("error")
    }
```

### Identifier Resolution Logic

```python
def resolve_identifier(identifier_value, carrier_id, shipper_id):
    """
    System fallback logic for identifier matching
    """
    # 1. Check network configuration
    network = get_network_config(shipper_id, carrier_id)
    if network:
        mapped_field = network.get("identifier_one")
        # Try configured field
        load = find_load(mapped_field, identifier_value)
        if load:
            return load

    # 2. Fallback: Try load_number
    load = find_load("load_number", identifier_value)
    if load:
        return load

    # 3. Fallback: Try reference_numbers
    load = find_load("reference_number", identifier_value)
    if load:
        return load

    # 4. No match
    return None  # → "Awaiting Tracking Info"
```

### Exception Handling: Carrier-less Loads

```python
def handle_carrierless_load(load):
    """
    Special case: Loads without carrier assignment
    """
    # Normal pattern: Only carrier link
    if not load.carrier_id:
        expected_tracking = "carrier_link_app"

    # But system allows: Dispatcher API fallback
    # Uses reference number matching
    # Rare but possible

    if updates_via_dispatcher_api(load):
        # Prashant: "First time seeing this, definite outlier"
        log_exception("carrierless_load_via_api", load.id)
```

---

## 13. Action Items

### Immediate (By End of Day)

**Prashant:**
- [ ] Share data dictionary (carrier files processing)
- [ ] Include API, status, EDI updates
- [ ] Provide both raw text + JSON format
- [ ] Include flow diagrams
- [ ] Add explanations for each log

**IT/Arpit:**
- [ ] Research licensed tool for ClickHouse access (Table Plus alternative)
- [ ] Recommend to Surya

### Short-term (This Week)

**Raja:**
- [ ] Review Prashant's data dictionary
- [ ] Map CFW processing flows
- [ ] Identify integration points for Ocean Debugging Agent
- [ ] Sync with Arpit on findings

**Arpit + Raja:**
- [ ] Add Raja to Slack group (Arpit, Surya, Prashant)
- [ ] Analyze usage patterns from rewind tool queries
- [ ] Design decision tree for carrier file issues

### Medium-term (Next 2 Weeks)

**Raja:**
- [ ] Build CFW analyzer module
- [ ] Implement network relationship checker
- [ ] Add identifier resolution logic
- [ ] Test against Prashant's examples

**Team:**
- [ ] Schedule weekly functional overview sessions
- [ ] Week 1: Load creation
- [ ] Week 2: Load not tracking

### Long-term (Before Wider Demo)

**Raja + Arpit:**
- [ ] Complete 2 use case implementations
- [ ] Internal workshop with Surya + Prashant
- [ ] Incorporate feedback
- [ ] Prepare demo for leadership

**Support Team:**
- [ ] Continue using rewind tool, provide feedback
- [ ] Test Ocean Debugging Agent with real tickets
- [ ] Validate decision tree accuracy

---

## 14. Quotes & Key Moments

### On Complexity
**Arpit:** "This is definitely one of the complex parts... there are many exceptions."

### On Network Configuration
**Prashant:** "For an update to get processed, there should be an existing network. That is mandatory."

**But then...**
**Surya:** "Our backend processing logic always falls back to reference numbers even if not configured."

**Prashant:** "Most loads without carrier only track through carrier link... this is the first time I'm seeing this [dispatcher API]. Definite outlier issue."

### On Source of Truth
**Prashant:** "That log is source of truth. We take that as source of truth. We look at process_super_record... that becomes our source of truth."

### On Testing the Catalog
**Arpit:** "You can think of this as a real test of your catalog, right? Because we both would be beginners. If me and Raja can make it like easily understand it, then your objective is achieved for your team to be enabled to debug."

### On Realistic Expectations
**Arpit:** "Right now there is assumption that once we have done something it will just run on its own forever and everyone can join it, which possibly may not be the case. We have to see if we can make it that simple but I don't think it will be that simple because of the randomness which you guys have in the cases."

---

## 15. Technical Discoveries

### CFW Processing Flow

```
Carrier sends update (API or File)
  ↓
tracking-service-external (API) OR file upload
  ↓
S3 file created (even for API)
  ↓
S3 event triggers CFW queue
  ↓
carrier-files-worker receives
  ↓
Log: process_super_record (API) or process_super_file_task (File)
  ↓
Parse raw data (before manipulation)
  ↓
Identify shipper (external_id + carrier)
  ↓
Check network configuration
  ↓
Match identifier (multiple fallbacks)
  ↓
Route to queue (Ocean/Tracking/LTL/Rail)
  ↓
Log: queued_messages + skipped_messages
  ↓
Worker picks up (multimodal_carrier_updates_worker, global-worker-ex, etc.)
  ↓
Update load
```

### Historical Load Pattern for Configuration Discovery

```python
def discover_tracking_method(carrier, shipper):
    """
    Prashant's method: Look at historical delivered loads
    """
    # 1. Find recent delivered load for this relationship
    load = get_recent_delivered_load(carrier, shipper)

    # 2. Check which tracking method was used
    tracking_method = load.tracking_method  # e.g., "location_file"

    # 3. Go to carrier edit page
    carrier_page = get_carrier_config(carrier)

    # 4. Check all file integrations
    integrations = carrier_page.file_integrations  # May have 3-4

    # 5. Query logs to see which integration processed this load
    logs = query_cfw_logs(load.id, tracking_method)

    # 6. Identify the specific integration
    integration = find_integration_from_logs(logs)

    # 7. Check column mapping for that integration
    mapping = integration.column_mapping
    # Identifier field → Column 2 (load number)
    # External ID → Column 1 (shipper reference)

    return {
        "integration": integration.name,
        "identifier_column": mapping.identifier,
        "identifier_type": mapping.identifier_type
    }
```

---

## 16. Cost Optimization Context

**Why duplicate systems exist:**
- Primary: Can't risk breaking production
- Replica: Safe for experimentation
- But: Burning 3x money (S3 + Primary + Replica)

**Path forward depends on:**
- Usage pattern analysis
- Query catalog from Prashant
- Rewind tool usage metrics
- Understanding retention needs per data type

**Goal:** Merge to single system once confident in patterns

---

## 17. Next Meeting Preparation

**For Surya/Prashant:**
- Share data dictionary
- Prepare load creation functional overview for next week

**For Raja:**
- Study Prashant's dictionary
- Map CFW flows
- Prepare questions on unclear flows

**For Arpit:**
- Review usage patterns
- Plan anomaly detection approach
- Design PR review AI prompts

---

**Meeting Duration:** ~57 minutes
**Next Sync:** Weekly (functional overviews)
**Critical Deliverable:** Prashant's data dictionary (today)
**Long-term Goal:** Ocean Debugging Agent that saves support team time

---

**Created:** 2026-01-14
**Author:** MSP Raja
**Related Docs:**
- FOURKITES_DATA_INGESTION_FLOWS.md
- CFW_DEEP_DIVE.md
- OCEAN_DEBUGGING_POC_CONFLUENCE.md
