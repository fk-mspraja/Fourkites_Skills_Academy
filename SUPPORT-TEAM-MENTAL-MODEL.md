# Support Team Mental Model - Ocean Troubleshooting Workflow

**Date:** January 7, 2026
**Participants:** Suriyanarayanan (Surya), Arpit, MSP Raja, Priya (DY team)
**Source:** Transcript of troubleshooting walkthrough session

---

## Executive Summary

Support team follows a **multi-source triangulation approach** to troubleshoot issues. They manually check 5-8 different systems to piece together what happened, spending **30-45 minutes per ticket** on average. No single source of truth exists - analysts correlate data across Platform UI, JT Portal, SigNoz logs, APIs, and databases to reach conclusions.

**Key Finding:** 80% of troubleshooting time is spent **data gathering and correlation** across systems, not actual analysis.

---

## 1. Ticket Intake & Classification

### Source: Salesforce
- Customers create cases in Salesforce
- Cases auto-route to queues:
  - **Ocean/Air/Rail** → ISBO queue
  - **Drayage (DY)** → Facilities queue
- **Omni-channel** auto-assigns to available analysts

### Primary Issue Categories:
1. **Load not found / Load creation** (~25%)
2. **Load not tracking** (~35%) ⭐ Most common
3. **ETA related issues** (~20%)
4. **Callbacks related issues** (~10%)
5. **Check-in/check-out issues** (~10% - DY specific)

---

## 2. Investigation Flow (Ocean Mode)

### Step 1: Platform Check (FourKites UI)
**Purpose:** Understand the issue from customer perspective

**What they check:**
- Load existence and current state
- **Tracking method** - Which identifier is being used?
- **Source of update** - Where did the data come from?
  - "RPA" = JT (web scraping)
  - "API" = Carrier API
  - "EDI" = EA315 file
  - "Vessel tracking" = Vessel-based location

**Key identifiers visible:**
- Tracking ID (internal FourKites ID)
- Booking number
- Container number
- Bill of lading

**Time spent:** 2-3 minutes

---

### Step 2: Super API / Tracking API
**Purpose:** Get subscription and tracking details

**Tool:** Postman collection with internal APIs

**What they check:**
- Which **primary identifier** is the load tracking on?
  - Priority: Booking number > Bill of lading > Container number
- JT subscription ID (if using web scraping)
- Tracking configuration

**API Response shows:**
```json
{
  "tracking_id": "...",
  "primary_identifier": "booking_number",
  "subscription_id": "...",
  "tracking_source": "RPA"
}
```

**Time spent:** 1-2 minutes

---

### Step 3: Just Transform (JT) Portal
**Purpose:** See exactly what was scraped from carrier portal

**Login:** Shared credentials (common user access)

**Navigation:**
1. Go to Ocean mode
2. History section
3. Paste subscription ID
4. Filter by time range (when issue occurred)

**What they examine:**
- **Crawled output** - Raw data from carrier portal
- **Response** - Formatted data sent to FourKites
- **JSON events** - Individual milestone events (VD = Vessel Departure, etc.)

**Example investigation:**
- Load shows vessel departure on Dec 22 (incorrect)
- Customer says actual departure was Dec 30
- Check JT: Find JSON with event_code=VD, event_time=Dec 22
- Confirms JT scraped/sent incorrect data

**Common checks:**
- Event codes (VD, AG, ET, etc.)
- Location (city_state field)
- Timestamps
- Multiple events on same day

**Time spent:** 10-15 minutes (checking multiple JSON files)

---

### Step 4: SigNoz Logs (Primary Investigation Tool)
**Purpose:** Deep dive into what system actually processed

**Query Syntax:**
```
log_set: signoz_logs.distributed_logs
service_name: multimodel_carrier_updates_worker
keyword: PROCESS_OCEAN_UPDATE (all caps)
NOT contains: [filters to exclude internal events]
environment: production
time_range: Up to 1 month (ocean loads = 120 day expiry)
```

**Why 1 month of logs?**
- Ocean shipments are long-duration (weeks to months)
- Need complete history to see all updates
- Check for duplicate updates, corrections, rollovers

**What they extract:**
- Event code (VD, AG, etc.)
- Event time
- Container number
- Correlation ID
- Data source (JT, EDI, API)
- Vessel name
- Location details

**Pattern they look for:**
- Duplicate events with different timestamps
- Correction events (rollover = vessel change)
- Processing errors

**Time spent:** 15-20 minutes (most time-consuming step)

---

### Step 5: Decision & Action

**Three possible outcomes:**

#### A. Carrier Issue
- JT scraped correctly, but carrier portal had wrong data
- **Action:** Inform customer it's carrier-side issue
- **Escalation:** May notify carrier (not always)

#### B. JT Issue
- JT scraped incorrectly or applied wrong logic
- **Action:** Create bug ticket for JT team
- **Escalation:** Bi-weekly sync with ocean engineering to discuss
- **Follow-up:** JT investigates their scraping logic

#### C. Configuration Issue
- Load misconfigured (wrong identifier, missing data)
- **Action:** Fix configuration or escalate to engineering
- **Database check:** Load validation data mart, booking API logs

**Time to resolution:** 30-45 minutes average

---

## 3. Data Source Hierarchy & Priority

### For Ocean Load Tracking:

**Priority 1: EA315 (EDI File)**
- Flat file from carrier
- Most reliable, structured format
- May have delays (event today, file tomorrow)

**Priority 2: Carrier API**
- Real-time updates
- Only available for major carriers (MSK, MAEU, etc.)
- Direct integration

**Priority 3: RPA/JT (Web Scraping)**
- Fallback when API/EDI unavailable
- ~6 hour latency
- 60-70 carriers supported via JT
- **Risk:** Carrier portals change frequently, breaking scrapers

**Why this priority?**
- EDI = Structured, validated by carrier
- API = Real-time, direct source
- Web scraping = Prone to errors, parsing issues

### Multi-sourcing Strategy:
- **ERPA (JT) prioritized currently** (faster than EDI)
- System processes whichever data arrives first
- Can receive same update from multiple sources

---

## 4. Identifier Priority (Ocean)

When multiple identifiers available:

**1st Priority: Booking Number**
- Best visibility from carrier portal
- Most comprehensive data

**2nd Priority: Bill of Lading**
- Good visibility, widely used

**3rd Priority: Container Number**
- Limited visibility from carrier portals
- Least preferred

**Why it matters:** Determines which JT subscription to check

---

## 5. Tools & Access

### Platform-facing Tools:

| Tool | Purpose | Auth | Used For |
|------|---------|------|----------|
| **FourKites Platform** | Customer UI | User login | First look, see customer view |
| **Super API** | Internal tracking API | API key | Get tracking config, subscription |
| **JT Portal** | Web scraping data | Shared creds | See raw scraped data |
| **SigNoz** | Log analytics | User login | Deep investigation |
| **Data Hub** | Ocean checklist tool | User login | Quick basic data |
| **S3** | File storage | AWS CLI/script | Download EDI files |
| **Database** | Direct DB query | Credentials | Load validation, booking API |
| **Confluence** | Knowledge base | User login | Workflows, carrier lists |

### Custom Tools Built by Surya:

**1. EDI Parser (Python)**
- Purpose: Format EDI files (315, 214) into readable format
- Input: Raw EDI file from S3
- Output: Element-wise breakdown
- Use case: Debug parsing errors, communicate with carriers

**2. HTML Log Analyzer**
- Purpose: Parse SigNoz logs into structured table
- Input: Downloaded log files
- Output: HTML with:
  - Total records processed
  - Unique ET updates
  - Unique locations
  - Table: Event code, location, data source, container, correlation ID, vessel, timestamp
  - Map plotting (if lat/long present)
- **Two versions:** Ocean-specific, Common (all modes)

---

## 6. Knowledge Sources

### Confluence Documentation:

**1. Carrier List**
- 60-70 carriers using JT
- Which have API, EDI, or JT only
- Maintained by product team

**2. Troubleshooting Workflows**
- Load creation (different methods)
- Load not tracking
- Updated regularly by support team

**3. EDI Format Specs**
- Segment definitions
- Field mappings
- Used to validate file format correctness

### Tribal Knowledge:
- Which logs to check for which issue
- Common failure patterns
- Carrier-specific quirks
- JT scraping limitations

---

## 7. Example Investigation: Wrong Departure Date

**Ticket:** Load U110123982 showing vessel departure on Dec 22, customer says it was Dec 30

**Investigation Steps:**

1. **Platform:** Confirmed vessel departure shows Dec 22, source = RPA (JT)
2. **Super API:** Get subscription ID, confirm tracking via booking number
3. **JT Portal:**
   - Search subscription history on Dec 22
   - Found 3 events that day
   - One JSON has: `event_code: VD, city_state: Hamburg, event_time: Dec 22`
   - Confirmed JT sent this update
4. **SigNoz:**
   - Query: `PROCESS_OCEAN_UPDATE` + container number
   - Found log entry: VD processed with timestamp Dec 22
   - Also found: Later VD with Dec 30 (rollover)
5. **Decision:** JT issue - need to verify if carrier portal had wrong data or JT scraped incorrectly
6. **Action:** Create bug ticket for JT team to investigate source

**Total time:** ~40 minutes

---

## 8. Pain Points & Challenges

### Current Challenges:

**1. Tool Fragmentation**
- 5-8 different systems per investigation
- Multiple authentications
- Manual correlation required

**2. Time-Consuming**
- 30-45 minutes per ticket
- 80% time on data gathering
- Only 20% on actual analysis

**3. Logs are Difficult**
- SigNoz returns raw JSON logs
- Need to manually parse and correlate
- No structured extraction

**4. EDI Files Unreadable**
- Need custom parser
- Error-prone to read raw

**5. JT Scraping Issues**
- Carrier portals change frequently
- Scraping breaks
- Data accuracy problems
- ~6 hour latency

**6. No Automation**
- Every step is manual
- No automatic correlation
- No pattern detection
- No suggested root cause

**7. Knowledge Scattered**
- Confluence docs
- Tribal knowledge
- No unified view

---

## 9. DY (Drayage) Specifics

**From Priya (brief mention):**

**Common issues:**
- Check-in/check-out of trailers
- User access problems (case sensitivity in email IDs)
- Task moves
- Reports not loading

**80% are bugs** - Most issues are software bugs, not data issues

**Backend fixes:**
- User access: Engineering changes email case in backend
- Quick fixes available

**Note:** Full DY workflow to be discussed in next session

---

## 10. Ideal State (What Support Wants)

### From Surya's Custom Tool (HTML Log Analyzer):

**Desired Output:**
- Auto-parsed logs in table format
- Key columns only (not all fields)
- Visual map of lat/long data
- Breakdown: Total records, unique updates, unique locations
- Easy to read, share with engineering/JT

**Current gap:**
- Manual download from SigNoz
- Run through custom Python script
- Time-consuming

**Request for Re-tool integration:**
- Same functionality
- Built into existing tooling
- No manual export/import

---

## 11. Automation Opportunities

### High-Impact Areas:

**1. Automatic Data Aggregation**
- Input: Tracking ID
- Output: Platform data + JT data + SigNoz logs + API data in one view
- **Time saved:** 15-20 minutes per ticket

**2. Log Parsing & Structuring**
- Auto-extract key fields from SigNoz
- Present in table format (like Surya's HTML tool)
- Highlight anomalies (duplicates, corrections)
- **Time saved:** 10-15 minutes per ticket

**3. Root Cause Suggestion**
- Based on patterns: "Likely JT scraping error" or "Carrier data issue"
- Show evidence from multiple sources
- Confidence score
- **Time saved:** 5-10 minutes per ticket

**4. Automated Correlation**
- Compare JT vs SigNoz vs Platform
- Flag discrepancies automatically
- Timeline view of events
- **Time saved:** 5-10 minutes per ticket

**5. Smart Escalation**
- Auto-detect: JT issue vs Carrier issue vs Config issue
- Pre-fill bug ticket with evidence
- Suggested assignee
- **Time saved:** 5 minutes per ticket

---

## 12. Key Metrics

### Current State:
- **Average resolution time:** 30-45 minutes
- **Time breakdown:**
  - Data gathering: 25-35 minutes (80%)
  - Analysis: 5-10 minutes (20%)
- **Tools per investigation:** 5-8 different systems
- **Manual steps:** 15-20 per ticket

### Success Criteria for Automation:
- Reduce time to 10-15 minutes (60% reduction)
- Single tool for investigation (no switching)
- Automated data correlation
- Root cause suggestion with 80%+ accuracy
- Auto-generate evidence for bug tickets

---

## 13. Next Steps from Meeting

### Action Items:

**From Surya:**
1. Share Confluence mind maps (load creation, load not tracking)
2. Share JT API credentials
3. Share HTML log analyzer tool (code + examples)
4. Share data hub API collection
5. Provide carrier list from Confluence

**From Arpit:**
1. Integrate data hub API into re-tool
2. Build log parsing feature (like HTML tool)
3. Connect to JT API directly

**From Raja:**
1. Create mind map of data sources and flow
2. Understand tool usage patterns
3. Identify automation opportunities

**Next Session (Wednesday):**
- Prashant: OTR troubleshooting workflow
- Priya: DY workflow (prepared walkthrough)
- Surya: Data catalog (under construction)

---

## 14. Technology Stack Summary

### Languages/Tools Used:
- **Python:** EDI parser, log analyzer
- **Postman:** API testing
- **SigNoz:** Log analytics
- **S3/AWS CLI:** File access
- **Salesforce:** Ticketing
- **Confluence:** Documentation
- **Re-tool:** Internal tooling (being built)

### APIs:
- Super API (tracking data)
- JT API (scraping data)
- Data Hub API (ocean checklist)
- Tracking API (load metadata)

### Databases:
- Load validation data mart
- Booking API logs
- Production DWH (Redshift)

---

## 15. Mental Model Summary

**Think like an analyst:**

```
Ticket arrives
   ↓
Classify issue type (load creation, tracking, ETA, callbacks)
   ↓
Check Platform (customer view)
   ↓
Get tracking config (API)
   ↓
Check data source (JT, EDI, API)
   ↓
Deep dive logs (SigNoz)
   ↓
Correlate findings across sources
   ↓
Determine root cause (Carrier, JT, Config, Bug)
   ↓
Take action (Fix, Escalate, Explain)
```

**Key principle:** Triangulate across multiple sources to find ground truth

---

## Appendix: Glossary

- **JT:** Just Transform (web scraping vendor)
- **RPA:** Robotic Process Automation (customer-facing name for web scraping)
- **EA315:** EDI format for ocean shipments
- **VD:** Vessel Departure (event code)
- **AG:** Arrived at Gate (event code)
- **ET:** Estimated Time (event code)
- **ISBO:** International Shipment Business Operations (queue name)
- **Omni-channel:** Salesforce auto-assignment feature
- **Correlation ID:** Unique identifier linking related logs
- **Rollover:** Vessel change (container moved to different vessel)
- **Super API:** Internal FourKites tracking API
- **Data Hub:** Ocean-specific troubleshooting tool

---

**Document Status:** Initial draft from transcript
**Next Update:** After OTR/DY workflow sessions
**Maintained by:** MSP Raja, AI R&D Solutions Engineer
