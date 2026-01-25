# Support Team Skills & Tools Catalog

**Created:** January 7, 2026
**Based on:** Support team troubleshooting workflow transcript
**Purpose:** Document all tools, skills, and data sources used by support analysts

---

## 1. Tools Mentioned

### A. JT (Just Transform)
**What it is:** Web scraping service for carrier portals
**Access:** Shared credentials (common user)
**Used for:**
- Ocean shipment tracking when API/EDI unavailable
- 60-70 carriers supported
- View crawled data vs formatted response

**Capabilities:**
- History search by subscription ID
- JSON event viewing
- Event codes: VD (Vessel Departure), AG (Arrived Gate), ET (Estimated Time)
- Time-based filtering

**API Available:** Yes
- Can query programmatically instead of UI
- Same credentials as UI

**Limitations:**
- ~6 hour latency
- Carrier portals change frequently, breaking scrapers
- Data accuracy issues (wrong timestamps, locations)

**Priority in multi-source:** Currently #1 (prioritized over EDI)

---

### B. SigNoz
**What it is:** Log analytics platform (ClickHouse-based)
**Used for:** Deep dive investigation of processed events

**Query Pattern:**
```
Service: multimodel_carrier_updates_worker
Keyword: PROCESS_OCEAN_UPDATE
Filters: NOT contains [internal events]
Environment: production
Time range: Up to 1 month (ocean = 120 days)
```

**What analysts extract:**
- Event codes
- Event timestamps
- Container numbers
- Correlation IDs
- Data sources
- Vessel information
- Location details

**Pain point:** Returns raw JSON logs, needs manual parsing

**Time spent:** 15-20 minutes per investigation (most time-consuming)

**Improvement needed:** Structured extraction, table view

---

### C. FourKites Platform (Customer UI)
**What it is:** Production platform customers use
**Support access:** Same interface as customers

**Used for:**
- First look at issue
- See tracking method
- Check update sources (RPA, API, EDI, Vessel)
- View load timeline
- Hover feature shows data source (if enabled in user settings)

**Key pages:**
- Load details
- All milestones
- Stop information

**Time spent:** 2-3 minutes per investigation

---

### D. Super API / Tracking API
**What it is:** Internal FourKites APIs
**Tool:** Postman collections

**Provides:**
- Tracking ID to identifier mapping
- Primary tracking identifier (booking, container, BOL)
- JT subscription ID
- Tracking configuration
- Load metadata

**Authentication:** API key
**Format:** JSON responses

**Time spent:** 1-2 minutes per investigation

---

### E. Data Hub API
**What it is:** Ocean-specific troubleshooting tool
**Built by:** Engineering team
**Status:** Production

**Provides:**
- Basic data points for ocean troubleshooting
- Consolidated view (but not comprehensive)
- Missing: In-depth load updates, some creation details

**Access:** User login
**Format:** Web interface + API

**Current usage:** Support team uses regularly
**Integration plan:** Arpit to integrate into re-tool

---

### F. EDI Parser (Custom - Surya's Tool)
**What it is:** Python script to format EDI files
**Built by:** Surya (support analyst)
**Used for:** EA315 (ocean) and 214 (rail/OTR) files

**Capabilities:**
- Beautify/format EDI segments
- Element-wise breakdown
- Validate against Confluence specs
- Identify parsing errors
- Help communicate errors to carriers

**Integration:** Separate from other tools
**Flow:** Download from S3 → Run parser → Review

**Status:** Personal tool, not team-wide yet

---

### G. HTML Log Analyzer (Custom - Surya's Tool)
**What it is:** Python script to parse SigNoz logs
**Built by:** Surya (support analyst)

**Two versions:**
1. Ocean-specific
2. Common (all modes)

**Output:**
- HTML table view
- Key columns: Event code, location, data source, container, correlation ID, vessel, timestamp
- Statistics: Total records, unique updates, unique locations
- Map visualization (if lat/long present)

**Request:** Build into re-tool so no manual export/import needed

---

### H. S3 File Storage
**What it is:** AWS S3 bucket for file backups
**Access:** AWS CLI / Python scripts

**Contains:**
- EDI files (EA315, 214)
- Carrier super files
- Load creation files

**Usage:** Download files for offline analysis

---

### I. Database (Direct Access)
**Used for:** Load creation troubleshooting

**Tables accessed:**
- `load_validation_data_mart` - Conventional load creation
- Booking API logs - API-based creation

**Distinction:** Booking API data NOT in validation data mart

---

### J. Confluence
**What it is:** Knowledge base
**Access:** User login

**Contains:**
- Troubleshooting workflows
- Carrier lists (which have JT, API, EDI)
- EDI format specifications
- Support team processes
- Mind maps (load creation, load not tracking)

**Maintained by:** Product team + Support team

**Key pages:**
- Carrier coverage list (60-70 JT carriers)
- Load creation workflows
- Load tracking workflows

---

### K. Salesforce
**What it is:** Ticketing system
**Used for:** Case intake and management

**Features:**
- Triage queue (auto-routing)
- Queue split: ISBO (ocean/air/rail), Facilities (DY)
- Omni-channel auto-assignment
- Case tracking and updates

---

## 2. Skills Demonstrated

### Analytical Skills:

**1. Multi-source Correlation**
- Check 5-8 systems per investigation
- Correlate timestamps across sources
- Identify discrepancies

**2. Pattern Recognition**
- Spot duplicate events
- Identify rollovers (vessel changes)
- Recognize common failure modes

**3. Root Cause Analysis**
- Distinguish: Carrier issue vs JT issue vs Config issue
- Evidence-based decision making
- Triangulate across sources

**4. Technical Understanding**
- EDI formats (315, 214)
- Event codes (VD, AG, ET, etc.)
- API structures
- Database schemas
- Log formats

### Domain Knowledge:

**1. Ocean Shipping**
- Booking numbers, containers, bill of lading
- Vessel tracking and schedules
- Terminal operations
- Carrier behaviors
- Rollover scenarios

**2. Data Source Hierarchy**
- EA315 > Carrier API > Web scraping (JT)
- Booking number > Bill of lading > Container number
- Why each source is prioritized

**3. System Architecture**
- How loads are created
- How tracking works
- File processing flow
- Update propagation
- Platform limitations

### Tool Proficiency:

**1. Query Writing**
- SigNoz query syntax
- Database queries
- API requests (Postman)

**2. Scripting**
- Python for parsing
- AWS CLI for S3
- Custom tool development

**3. Data Interpretation**
- JSON parsing
- EDI reading
- Log analysis
- Correlation ID tracking

---

## 3. Data Sources Summary

| Data Source | Type | Used For | Latency | Priority |
|-------------|------|----------|---------|----------|
| **EA315 (EDI)** | File | Ocean updates | Hours-days | High |
| **Carrier API** | Real-time | Ocean updates | Real-time | High |
| **JT (Web scraping)** | Scraping | Ocean updates | ~6 hours | Medium |
| **Platform UI** | Interface | Customer view | Real-time | - |
| **Super API** | API | Tracking config | Real-time | - |
| **SigNoz** | Logs | Processing history | Real-time | - |
| **Data Hub** | Tool | Basic data | Real-time | - |
| **S3** | Storage | File backup | Historical | - |
| **Database** | DB | Load records | Real-time | - |
| **Confluence** | Docs | Knowledge | Static | - |

---

## 4. Carrier Integration Matrix

**From transcript mentions:**

### Integration Types:

**API Integration:**
- Major carriers: MSK (Maersk), MAEU, etc.
- Real-time updates
- Most reliable

**EDI (EA315):**
- Flat file format
- Structured, validated
- May have delays

**JT (Web Scraping):**
- 60-70 carriers
- Fallback option
- ~6 hour latency
- Maintained in Confluence

**Product team maintains:** Current list of carrier integrations

---

## 5. Investigation Workflows

### Ocean - Load Not Tracking

**Time:** 30-45 minutes average

**Steps:**
1. Platform: Check load, see tracking source
2. Super API: Get tracking identifier and subscription
3. JT Portal: View crawled data and events
4. SigNoz: Query logs for processing details
5. Analyze: Correlate findings
6. Decide: Carrier / JT / Config issue
7. Action: Fix, escalate, or explain to customer

**Tools used:** 5-6 different systems

---

### Ocean - Load Creation

**Documented in:** Confluence workflows

**Key checks:**
- Load validation data mart (conventional)
- Booking API logs (API creation)
- Different paths based on creation method

---

### DY (Drayage) - Check-in/Check-out

**Common issues:** 80% are bugs
**Quick fixes:** User access (email case sensitivity)
**Backend:** Engineering makes direct DB changes

**Full workflow:** To be documented in next session

---

### OTR (Over-the-Road) - TBD

**Next session:** Prashant will walk through

---

## 6. Key Mappings Needed

### Event Code Mappings:
- VD: Vessel Departure
- AG: Arrived at Gate
- ET: Estimated Time
- (Full list in system documentation)

### Priority Hierarchies:

**Data Source Priority (Ocean):**
```
1. EA315 (EDI file)
2. Carrier API
3. JT (Web scraping)
```

**Identifier Priority (Ocean):**
```
1. Booking number
2. Bill of lading
3. Container number
```

### Issue Category Mappings:
```
Load creation → Database + Validation logs
Load tracking → Platform + JT + SigNoz
ETA issues → Platform + Carrier data
Callbacks → Callback logs
DY check-in → Platform + Database
```

---

## 7. Automation Opportunities

### High-Priority (High impact, mentioned in transcript):

**1. Log Parser Integration**
- Build Surya's HTML tool into re-tool
- Auto-extract key fields from SigNoz
- Table view instead of raw JSON
- **Impact:** Save 10-15 min per ticket

**2. Multi-Source Data Aggregator**
- Input: Tracking ID
- Output: Platform + JT + SigNoz + API in one view
- **Impact:** Save 15-20 min per ticket

**3. Data Hub API Integration**
- Already exists, just needs integration into re-tool
- **Impact:** One less tool to switch to

**4. JT API Integration**
- Use API instead of portal UI
- Programmatic access
- **Impact:** Faster, automatable

### Medium-Priority:

**5. Root Cause Suggester**
- Based on patterns: "Likely JT error" or "Carrier issue"
- Show evidence
- **Impact:** Faster diagnosis

**6. Automatic Correlation**
- Compare JT vs SigNoz vs Platform
- Flag discrepancies
- **Impact:** Reduce manual work

**7. Smart Escalation**
- Pre-fill bug tickets
- Suggest assignee (JT team vs Engineering)
- **Impact:** Faster escalation

---

## 8. Knowledge Gaps to Fill

### Questions for next sessions:

**OTR (Over-the-Road):**
- Troubleshooting workflow
- Data sources used
- Common issues
- Tools specific to OTR

**DY (Drayage):**
- Full workflow (Priya to present)
- Common issues beyond bugs
- Tool usage
- Database queries

**Data Catalog:**
- Surya building (under construction)
- Expected structure
- How it will help

**EDI Parsing:**
- Full spec document locations
- Common parsing errors
- Carrier-specific formats

---

## 9. API Endpoints Inventory

**To be shared by Surya:**

1. **Super API** - Internal tracking API
   - Postman collection available
   - Get tracking config, subscription IDs

2. **Data Hub API** - Ocean checklist
   - Postman collection available
   - Basic troubleshooting data

3. **JT API** - Just Transform query API
   - Can replace UI access
   - Same credentials as portal
   - Need documentation

4. **Tracking API** - Load metadata
   - Used by platform
   - Real-time data

**Action:** Surya to share all collections

---

## 10. Custom Tooling Built by Team

### By Surya (Support Analyst):

**1. EDI Parser**
- Language: Python
- Input: EDI file (EA315, 214)
- Output: Formatted, element-wise breakdown
- Status: Personal tool

**2. HTML Log Analyzer**
- Language: Python
- Input: SigNoz log export
- Output: HTML with table view, statistics, maps
- Status: Personal tool
- **Request:** Integrate into re-tool

**3. S3 Download Script**
- Language: Python (assumed)
- Purpose: Batch download files
- Status: Personal tool

### To be built:

**4. Re-tool Integration** (Arpit's team)
- Log parsing (Surya's tool functionality)
- Data Hub API integration
- Multi-source aggregation
- AI-powered suggestions (Raja's expertise)

---

## 11. Communication & Collaboration

### Regular Meetings:

**Bi-weekly with Ocean Engineering:**
- Bug ticket reviews
- Discuss JT issues
- Escalate carrier problems

**Ad-hoc with JT Team:**
- When scraping issues found
- Data accuracy problems

**Internal Support Team:**
- Knowledge sharing
- Process updates

### Escalation Paths:

**JT Issues:**
- Create bug ticket for JT team
- Provide subscription ID, timestamps, evidence
- JT investigates their scraping

**Carrier Issues:**
- Report to carrier (sometimes)
- More often: Inform customer it's carrier-side

**Engineering Issues:**
- Bug tickets
- Configuration fixes
- Database updates

---

## 12. Training & Onboarding

### New analyst needs:

**Access to:**
- Platform (customer view)
- Super API credentials
- JT portal (shared creds)
- SigNoz
- Data Hub
- S3 (AWS)
- Database (read access)
- Confluence
- Salesforce

**Knowledge:**
- Ocean shipping domain
- EDI formats
- Event codes
- Query writing
- Tool navigation
- Escalation paths

**Documentation:**
- Confluence workflows
- Carrier integration list
- Troubleshooting guides
- EDI specs

**Current gap:** Mostly tribal knowledge, limited formal training

---

## 13. Performance Metrics

### Current:
- **Average resolution time:** 30-45 minutes
- **Tools per ticket:** 5-8 systems
- **Manual steps:** 15-20 per ticket
- **Data gathering time:** 25-35 minutes (80%)
- **Analysis time:** 5-10 minutes (20%)

### Target (with automation):
- **Resolution time:** 10-15 minutes (60% reduction)
- **Tools:** 1-2 (unified interface)
- **Manual steps:** 5-8 per ticket
- **Data gathering:** 5-10 minutes (automated aggregation)
- **Analysis time:** 5-10 minutes (same, AI-assisted)

---

## 14. Priority Actions

### Immediate (This week):

1. **Surya shares:**
   - Confluence mind maps
   - JT credentials
   - HTML log analyzer code + examples
   - API collections (Super API, Data Hub, JT)
   - Carrier list

2. **Arpit integrates:**
   - Data Hub API into re-tool
   - Begin log parsing feature design

3. **Raja creates:**
   - Mind map of data sources
   - Automation opportunity analysis
   - Tool usage pattern visualization

### Next session (Wednesday):

4. **Prashant:** OTR workflow walkthrough
5. **Priya:** DY workflow (prepared)
6. **Surya:** Data catalog progress update

---

## 15. Technology Stack

### Languages/Frameworks:
- **Python** - Scripting, parsing, automation
- **SQL** - Database queries
- **AWS CLI** - S3 access
- **Postman** - API testing

### Data Stores:
- **Redshift** - Data warehouse
- **ClickHouse** - SigNoz logs
- **S3** - File storage
- **Salesforce** - Ticketing

### Platforms:
- **FourKites Platform** - Customer UI
- **SigNoz** - Log analytics
- **Confluence** - Documentation
- **Re-tool** - Internal tooling (in progress)

### APIs:
- Super API
- Tracking API
- Data Hub API
- JT API

---

**Document Status:** Draft from initial session
**Next Update:** After OTR/DY workflow sessions + tool sharing
**Maintained by:** MSP Raja, AI R&D Solutions Engineer
