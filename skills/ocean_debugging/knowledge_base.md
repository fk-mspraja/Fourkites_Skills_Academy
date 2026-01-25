# Ocean Debugging Knowledge Base

**Source:** Support Team Mental Model (Surya - Jan 7, 2026)
**Purpose:** Tribal knowledge and domain expertise for ocean shipment troubleshooting

---

## Quick Reference: Event Codes

| Code | Name | Description |
|------|------|-------------|
| **VD** | Vessel Departure | Ship has departed from port |
| **AG** | Arrived at Gate | Container arrived at terminal gate |
| **ET** | Estimated Time | ETA update |
| **AD** | Actual Delivery | Delivered to destination |
| **OA** | Ocean Arrival | Vessel arrived at destination port |
| **DL** | Delivered | Final delivery confirmation |

---

## Data Source Priority (Ocean)

### Why This Order Matters

**1. EA315 (EDI File)** - MOST RELIABLE
- Structured, validated format from carrier
- Direct carrier system → Our system
- May have delays (event today, file tomorrow)
- No parsing ambiguity

**2. Carrier API** - FAST & RELIABLE
- Real-time updates
- Only major carriers (MSK, MAEU, etc.)
- Direct integration = less error

**3. RPA/JT (Web Scraping)** - FALLBACK
- Supports 60-70 carriers
- ~6 hour latency
- **Risk:** Carrier portals change frequently
- Parsing errors common
- Use when EDI/API unavailable

### Current Behavior
> **Note:** ERPA (JT) is currently prioritized in multi-sourcing because it's faster than EDI. System processes whichever data arrives first.

---

## Identifier Priority (Ocean)

When load has multiple identifiers, tracking uses this priority:

| Priority | Identifier | Why |
|----------|------------|-----|
| **1st** | Booking Number | Best visibility from carrier portal |
| **2nd** | Bill of Lading | Good visibility, widely used |
| **3rd** | Container Number | Limited visibility, least preferred |

**Why it matters:** Determines which JT subscription to check

---

## Common Root Causes

### 1. Network Relationship Missing (7.7% of loads)

**The #1 cause of "Awaiting Tracking Info"**

**What happens:**
1. Carrier sends super file with load updates
2. System queries for active relationships between carrier and shipper
3. If NO relationship exists → Files processed but loads never matched
4. Load stays stuck forever

**How to check:**
```sql
SELECT * FROM company_relationships
WHERE shipper_id = '{shipper_id}'
  AND carrier_id = '{carrier_id}'
```

**Resolution:** Create carrier-shipper relationship

---

### 2. JT Scraping Error

**Common scenarios:**
- Carrier portal changed layout → JT scrapes wrong field
- Timestamp parsing error → Wrong date
- Location extraction fails → Missing city/state

**How to identify:**
- Compare `crawled_output` vs `formatted_response` in JT
- If they differ → JT formatting bug
- If same but wrong → Carrier portal had wrong data

**Resolution:** Create JT bug ticket with evidence

---

### 3. Rollover (Vessel Change)

**What is a rollover:**
Container moved from one vessel to another mid-journey.

**How it appears:**
- Multiple VD events with different timestamps
- Earlier VD shows original vessel
- Later VD shows new vessel
- Customer confused about which date is correct

**Resolution:** Explain to customer that vessel changed, latest date is correct

---

### 4. Duplicate Events

**What happens:**
- Same event received from multiple sources (JT + EDI)
- Or same source sends event twice
- Platform may show incorrect timestamp

**How to identify:**
- Check SigNoz logs for multiple entries with same event_code
- Compare timestamps and correlation_ids

---

## Key Tables Reference

### company_relationships (CRITICAL)

**THE MOST IMPORTANT TABLE**

```sql
-- Check if relationship exists
SELECT
  relationship_id,
  status,
  is_active,
  created_date
FROM company_relationships
WHERE shipper_id = '{shipper}'
  AND carrier_id = '{carrier}'
```

**Status values:**
- `ACTIVE` - Good, tracking should work
- `INACTIVE` - Relationship paused
- `PENDING` - Not yet approved
- Missing row = No relationship

---

### fact_carrier_file_logs

**Track carrier file processing (CFW → GWEX → LW)**

```sql
-- Check if carrier is sending files
SELECT
  file_id,
  file_type,
  received_at,
  status,
  record_count
FROM fact_carrier_file_logs
WHERE carrier_id = '{carrier}'
  AND received_at >= now() - INTERVAL 7 DAY
ORDER BY received_at DESC
```

**Status values:**
- `PROCESSED` - File fully processed
- `PARTIAL` - Some records failed
- `FAILED` - File processing failed
- `PENDING` - Waiting to process

---

### load_validation_data_mart

**Conventional load creation records**

> **Important:** Does NOT include Booking API created loads!
> For API-created loads, check `booking_api_logs`

---

## SigNoz Query Patterns

### Primary Investigation Query

```sql
-- Find all ocean updates for a load
SELECT
  body,
  timestamp,
  trace_id,
  severity_text
FROM signoz_logs.distributed_logs
WHERE service_name = 'multimodel_carrier_updates_worker'
  AND body LIKE '%PROCESS_OCEAN_UPDATE%'
  AND body LIKE '%{container_number}%'
  AND environment = 'production'
  AND timestamp >= now() - INTERVAL 30 DAY
ORDER BY timestamp DESC
LIMIT 1000
```

**Why 30 days?** Ocean shipments are long-duration (weeks to months). Need complete history to see all updates, corrections, rollovers.

### Extracting Key Fields from Log Body

```sql
-- Parse JSON body to extract fields
SELECT
  JSONExtractString(body, 'event_code') as event_code,
  JSONExtractString(body, 'event_time') as event_time,
  JSONExtractString(body, 'container_number') as container,
  JSONExtractString(body, 'correlation_id') as correlation_id,
  JSONExtractString(body, 'data_source') as data_source
FROM ...
```

---

## Carrier-Specific Quirks

### Known Issues by Carrier

| Carrier | Issue | Workaround |
|---------|-------|------------|
| *To be documented* | | |

### Carriers with API Integration
- MSK (Maersk)
- MAEU
- *(Full list in Confluence)*

### Carriers with JT Only
- ~60-70 carriers
- *(Full list maintained by product team in Confluence)*

---

## Custom Tools Reference

### Surya's EDI Parser (Python)

**Purpose:** Format EDI files (EA315, 214) into readable format

**Input:** Raw EDI file from S3
```
ISA*00*          *00*          *ZZ*SENDERID       *ZZ*RECEIVERID...
```

**Output:** Element-wise breakdown
```
ISA - Interchange Control Header
  01: Authorization Information Qualifier = 00
  02: Authorization Information = (blank)
  ...
```

**Use case:** Debug parsing errors, communicate with carriers

---

### Surya's HTML Log Analyzer (Python)

**Purpose:** Parse SigNoz logs into structured table

**Output:**
- Total records processed
- Unique ET updates
- Unique locations
- Table: Event code, location, data source, container, correlation ID, vessel, timestamp
- Map visualization (if lat/long present)

**Two versions:**
1. Ocean-specific
2. Common (all modes)

**Request:** Build into Re-tool so no manual export/import needed

---

## Escalation Paths

### JT Issues
1. Confirm JT is the source of wrong data
2. Create bug ticket for JT team with:
   - Subscription ID
   - Timestamps
   - Crawled output vs formatted response
   - Expected vs actual
3. JT investigates their scraping logic
4. Bi-weekly sync with ocean engineering to discuss

### Engineering Issues
1. Create JIRA bug ticket
2. Include evidence from all sources
3. Priority based on impact (number of loads affected)

### Carrier Issues
1. Usually: Inform customer it's carrier-side issue
2. Sometimes: Report to carrier (case by case)

---

## Performance Metrics

### Current State (Manual Process)

| Metric | Value |
|--------|-------|
| Average resolution time | 30-45 minutes |
| Data gathering time | 25-35 minutes (80%) |
| Analysis time | 5-10 minutes (20%) |
| Tools per investigation | 5-8 systems |
| Manual steps | 15-20 per ticket |

### Target (With Automation)

| Metric | Target | Improvement |
|--------|--------|-------------|
| Resolution time | 10-15 minutes | 60% reduction |
| Data gathering | Automated | 80% reduction |
| Tools needed | 1-2 | 75% reduction |
| Accuracy | 85%+ | - |

---

## Glossary

| Term | Definition |
|------|------------|
| **JT** | Just Transform - web scraping vendor |
| **RPA** | Robotic Process Automation - customer-facing name for web scraping |
| **EA315** | EDI format for ocean shipments |
| **ISBO** | International Shipment Business Operations (support queue) |
| **Omni-channel** | Salesforce auto-assignment feature |
| **Correlation ID** | Unique identifier linking related logs |
| **Rollover** | Vessel change - container moved to different vessel |
| **Super API** | Internal FourKites tracking API |
| **Data Hub** | Ocean-specific troubleshooting tool |
| **CFW** | Carrier File Worker |
| **GWEX** | Gateway Exchange (file processing) |
| **LW** | Load Worker |

---

## References

- **SUPPORT-TEAM-MENTAL-MODEL.md** - Full transcript analysis
- **SUPPORT-SKILLS-AND-TOOLS-CATALOG.md** - Tools inventory
- **Support-Troubleshooting-Mind-Map.html** - Visual workflow
- **Confluence:** Carrier List, Load Not Tracking Workflow, EDI Specs

---

*Last Updated: January 13, 2026*
*Maintained by: MSP Raja, AI R&D Solutions Engineer*
