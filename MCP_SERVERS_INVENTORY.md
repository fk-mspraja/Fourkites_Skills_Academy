# MCP Servers Inventory

**FourKites AI-Understandable Data Layer**

Last Updated: January 27, 2026

---

## What is MCP?

**Model Context Protocol (MCP)** is Anthropic's standard for connecting AI models to data sources. MCP servers provide AI-friendly interfaces to databases, APIs, and other data systems.

**Why MCP?**
- AI agents can't query raw databases effectively
- Need structured, contextual interfaces with domain logic
- One MCP server → All AI agents benefit
- Centralized access control and monitoring

---

## Production MCP Servers ✅

### 1. Athena MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/athena`
**Owner:** Data Engineering Team

**What it does:**
- Queries AWS Athena tables
- Returns results in AI-friendly JSON format
- Handles query optimization and result pagination

**Data Sources:**
- `raw_data_db.callbacks_v2` - Webhook callback history
- `raw_data_db.tracking_events` - Tracking event stream
- `raw_data_db.location_updates` - GPS location data
- `raw_data_db.eld_events` - ELD device events

**Use Cases:**
- Callback failure investigation
- Tracking event analysis
- Location data queries
- ELD diagnostics

**Example Query:**
```json
{
  "query": "SELECT tracking_id, error_msg, ext_request_status FROM raw_data_db.callbacks_v2 WHERE tracking_id = ? AND datestr = ?",
  "params": [626717801, "2026-01-22"]
}
```

---

### 2. Redshift MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/redshift`
**Owner:** Data Engineering Team

**What it does:**
- Queries Redshift data warehouse
- Access to data marts and analytics tables
- Optimized for complex analytical queries

**Data Sources:**
- `platform_shared_db.platform.load_validation_data_mart` - Load creation validation
- `platform_shared_db.platform.network_relationships` - Shipper-carrier relationships
- `platform_shared_db.platform.company_configuration` - Company settings
- `platform_shared_db.analytics.tracking_metrics` - Tracking performance data

**Use Cases:**
- Load creation failure investigation
- Network relationship verification
- Company configuration lookup
- Tracking performance analysis

**Example Query:**
```json
{
  "query": "SELECT load_number, status, error, shipper_id FROM load_validation_data_mart WHERE load_number = ?",
  "params": ["S20251111-0041"]
}
```

---

### 3. Tracking API MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/tracking-api`
**Owner:** Platform Team

**What it does:**
- Wraps FourKites Tracking API v2
- Provides load search, status, and tracking data
- Handles authentication and rate limiting

**Endpoints:**
- `GET /shipments/search` - Search loads by tracking_id or load_number
- `GET /shipments/{id}` - Get load details
- `GET /shipments/{id}/events` - Get tracking events
- `GET /shipments/{id}/locations` - Get location history

**Use Cases:**
- Verify load exists
- Get current tracking status
- Retrieve tracking events
- Get location updates

**Example:**
```json
{
  "method": "search_load",
  "params": {
    "load_number": "U110123982"
  }
}
```

---

### 4. Network API MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/network-api`
**Owner:** Network Team

**What it does:**
- Queries network relationship configurations
- Provides shipper-carrier relationship data
- Access to ELD settings, tracking methods

**Endpoints:**
- `GET /relationships/{shipper_id}/{carrier_id}` - Get relationship config
- `GET /carriers/{carrier_id}/integrations` - Get carrier integrations
- `GET /shippers/{shipper_id}/settings` - Get shipper settings

**Use Cases:**
- Check if ELD is enabled
- Verify tracking method configuration
- Get carrier integration status
- Check network permissions

**Example:**
```json
{
  "method": "get_relationship",
  "params": {
    "shipper_id": 12345,
    "carrier_id": 67890
  }
}
```

---

### 5. Company API MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/company-api`
**Owner:** Platform Team

**What it does:**
- Queries company configuration and settings
- Access to feature flags, subscriptions
- Company metadata and contacts

**Endpoints:**
- `GET /companies/{id}` - Get company details
- `GET /companies/{id}/features` - Get enabled features
- `GET /companies/{id}/subscriptions` - Get active subscriptions
- `GET /companies/{id}/settings` - Get configuration settings

**Use Cases:**
- Check if feature is enabled for company
- Get subscription type
- Verify company configuration
- Get company contact information

**Example:**
```json
{
  "method": "get_company",
  "params": {
    "company_id": 12345
  }
}
```

---

### 6. SigNoz MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/signoz`
**Owner:** SRE Team

**What it does:**
- Queries SigNoz observability platform
- Access to logs, metrics, and traces
- Service health and performance data

**Data Sources:**
- Application logs (load-creation-service, callback-worker, etc.)
- Metrics (response times, error rates, throughput)
- Distributed traces (request flows)

**Use Cases:**
- Search application logs for errors
- Get service health metrics
- Trace request flow across services
- Identify performance bottlenecks

**Example:**
```json
{
  "method": "search_logs",
  "params": {
    "service": "load-creation-service",
    "query": "load_number:S20251111-0041",
    "time_range": "7d"
  }
}
```

---

### 7. Neo4j MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/neo4j`
**Owner:** Data Engineering Team

**What it does:**
- Queries Neo4j graph database
- Relationship mapping and traversal
- Graph analytics and pattern matching

**Data Models:**
- Company → Relationship → Carrier
- Load → Stop → Location
- User → Permission → Resource
- Data lineage graphs

**Use Cases:**
- Find relationship chains (Shipper → Broker → Carrier)
- Discover data dependencies
- Map organizational hierarchies
- Impact analysis (what breaks if X changes)

**Example:**
```cypher
MATCH (shipper:Company {id: $shipper_id})-[:HAS_RELATIONSHIP]->(carrier:Company)
WHERE carrier.tracking_enabled = true
RETURN shipper, carrier
```

---

### 8. DataHub Super API MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/datahub-super-api`
**Owner:** Data Engineering Team

**What it does:**
- Unified interface to DataHub catalog
- Metadata search across all data sources
- Schema discovery and lineage

**Capabilities:**
- Search datasets by name or description
- Get schema information
- Find data owners
- Discover related datasets

**Use Cases:**
- "What tables contain tracking data?"
- "Who owns the callbacks_v2 table?"
- "What's the schema for load_validation_data_mart?"
- Data discovery and exploration

**Example:**
```json
{
  "method": "search_datasets",
  "params": {
    "query": "callback"
  }
}
```

---

### 9. Slack MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/slack`
**Owner:** IT Team

**What it does:**
- Search historical Slack conversations
- Find relevant discussions and decisions
- Access institutional knowledge

**Channels Indexed:**
- #support-ops
- #engineering
- #ocean-team
- #carrier-integrations
- All public channels

**Use Cases:**
- Find previous discussions about similar issues
- Get context on past decisions
- Discover tribal knowledge
- Find SME recommendations

**Example:**
```json
{
  "method": "search_messages",
  "params": {
    "query": "callback failure DNS",
    "channels": ["#support-ops"],
    "date_range": "30d"
  }
}
```

---

### 10. Confluence MCP Server

**Status:** ✅ Production Ready
**Repository:** `mcp-servers/confluence`
**Owner:** IT Team

**What it does:**
- Search Confluence documentation
- Access runbooks, guides, and specs
- Retrieve structured documentation

**Spaces Indexed:**
- Support Operations
- Engineering
- Product Documentation
- Architecture & Design

**Use Cases:**
- Find runbooks for common issues
- Access technical documentation
- Discover troubleshooting guides
- Get API specifications

**Example:**
```json
{
  "method": "search_pages",
  "params": {
    "query": "ELD configuration",
    "spaces": ["Support Operations"]
  }
}
```

---

## MCP Servers in Development 🔨

### 11. JT Scraping API MCP Server

**Status:** 🔨 In Development
**Priority:** High (needed for Ocean tracking)
**Owner:** Ocean Team
**ETA:** 2-3 weeks

**What it will do:**
- Query JT (terminal) scraping results
- Container status and vessel schedules
- Port updates and delays

**Why needed:**
- Ocean tracking investigations require JT data
- Currently using REST API directly (not AI-friendly)
- Would enable Ocean skill agents

---

### 12. Carrier Files API MCP Server

**Status:** 🔨 Planned
**Priority:** Medium
**Owner:** Integrations Team
**ETA:** 4-6 weeks

**What it will do:**
- Query carrier file processing status
- EDI file validation results
- File ingestion history

**Why needed:**
- Investigate carrier file import issues
- Debug EDI parsing problems
- Currently requires manual database queries

---

## MCP Server Coverage by Domain

### OTR (Over-the-Road) RCA

**Required MCP Servers:**
- ✅ Tracking API - Load search
- ✅ Redshift - Load validation, network relationships
- ✅ Athena - Callbacks, events
- ✅ Network API - ELD configuration
- ✅ SigNoz - Service logs
- ✅ Neo4j - Relationship graphs

**Coverage:** 100% ✅ **READY FOR AGENTS**

---

### Ocean Tracking

**Required MCP Servers:**
- ✅ Tracking API - Container search
- ✅ Redshift - Subscription data
- ✅ Athena - Ocean events
- 🔨 JT Scraping API - Terminal data (in development)
- ✅ DataHub Super API - Vessel schedules
- ✅ SigNoz - Service logs

**Coverage:** 85% 🟡 **MOSTLY READY** (waiting on JT MCP)

**Workaround:** Use JT REST API directly until MCP server ready

---

### Drayage Operations

**Required MCP Servers:**
- ✅ Tracking API - Drayage load search
- ✅ Redshift - Drayage data
- ✅ Athena - Drayage events
- ✅ Network API - Terminal relationships
- ✅ Neo4j - Complex routing graphs

**Coverage:** 100% ✅ **READY FOR AGENTS**

---

### Air Freight

**Required MCP Servers:**
- ✅ Tracking API - Air shipment search
- ✅ Redshift - Air data
- ✅ Athena - Flight events
- ✅ DataHub Super API - Flight schedules

**Coverage:** 100% ✅ **READY FOR AGENTS**

---

### Customer Implementation

**Required MCP Servers:**
- ✅ Company API - Company configuration
- ✅ Network API - Relationship setup
- ✅ Confluence - Runbooks and guides
- ✅ Slack - Historical implementations

**Coverage:** 100% ✅ **READY FOR AGENTS**

---

## How to Use MCP Servers

### For Agent Developers

**1. Check if MCP server exists:**
```bash
# Check inventory above
# If exists: Use it
# If doesn't exist: Check workarounds or request new MCP server
```

**2. Test MCP server:**
```python
from mcp_client import MCPClient

client = MCPClient("athena")
result = client.query({
    "query": "SELECT * FROM callbacks_v2 WHERE tracking_id = ?",
    "params": [626717801]
})
```

**3. Handle responses:**
```python
# MCP servers return AI-friendly JSON
{
    "success": true,
    "data": [...],
    "metadata": {
        "row_count": 47,
        "query_time": "0.3s"
    }
}
```

### For Skill Developers

**In your SKILL.yaml, specify which MCP servers you need:**

```yaml
data_sources:
  - type: "mcp_server"
    server: "athena"
    tables:
      - "raw_data_db.callbacks_v2"
      - "raw_data_db.tracking_events"

  - type: "mcp_server"
    server: "tracking_api"
    endpoints:
      - "search_load"
      - "get_events"

  - type: "mcp_server"
    server: "redshift"
    tables:
      - "load_validation_data_mart"
```

This documents what data your skill needs. If MCP server doesn't exist, we know to build it.

---

## MCP Server Request Process

**Need a new MCP server?**

1. **Document requirement** in your skill's `DATA_SOURCES.md`
2. **Check if REST API exists** (can use as interim)
3. **Submit request** via #mcp-servers Slack channel
4. **Include:**
   - What data source
   - What queries/endpoints needed
   - Which skill/agent needs it
   - Priority (High/Medium/Low)

**SLA:**
- High priority: 2-3 weeks
- Medium priority: 4-6 weeks
- Low priority: 8-12 weeks

---

## MCP Server Quality Checklist

For each MCP server:

- [ ] Returns AI-friendly JSON (not raw database rows)
- [ ] Includes context and metadata
- [ ] Handles authentication securely
- [ ] Rate limiting configured
- [ ] Error messages are helpful
- [ ] Query optimization implemented
- [ ] Pagination for large results
- [ ] Timeout handling
- [ ] Logging and monitoring
- [ ] Documentation with examples

---

## Summary

**Production Ready:** 10 MCP servers ✅

**Coverage:**
- OTR: 100% ✅
- Ocean: 85% 🟡 (JT MCP in development)
- Drayage: 100% ✅
- Air: 100% ✅
- Implementation: 100% ✅

**Layer 4 Status:** 90% complete across all domains

**Most domains can start building agents NOW** (Layer 5) because Layer 4 is complete.

---

**Questions?**
- MCP Server requests: #mcp-servers Slack channel
- Technical issues: Data Engineering Team
- Documentation: `mcp-servers/` repository

---

**Last Updated:** January 27, 2026
**Maintainer:** MSP Raja, AI R&D Solutions Engineer
