# RCA Agent Project - Repository Structure

**Location:** `/Users/msp.raja/rca-agent-project/`
**Cloned:** 2026-01-05

---

## Overview

Three repositories have been cloned for analysis:

1. **rewind-app** - Frontend for human load timeline replaying
2. **mcp-servers** (refactoring branch) - MCP server implementations including RCA bot 2.0
3. **hr-agent** - HR-specific agent implementation

---

## 1. rewind-app

**Path:** `~/rca-agent-project/rewind-app/`
**GitHub:** https://github.com/cloudqwest/rewind-app
**Purpose:** Load timeline and replay UI for human analysts

### Key Documentation
- `ARCHITECTURE.md` - System architecture
- `CLAUDE.md` - Claude integration details
- `DEBUGGING.md` - Debugging guide
- `SCALABILITY.md` - Scalability considerations
- `README.md` - Main documentation

### Structure
```
rewind-app/
├── backend/          # Backend services
├── frontend/         # Frontend application
├── helm-charts/      # Kubernetes deployment
├── docs/             # Additional documentation
├── Jenkinsfile-backend
└── Jenkinsfile-frontend
```

### Deployment
- Internal URL: http://rewind.fourkites.internal/
- Jenkins-based CI/CD
- Helm charts for K8s deployment

---

## 2. mcp-servers (refactoring branch)

**Path:** `~/rca-agent-project/mcp-servers/`
**GitHub:** https://github.com/cloudqwest/mcp-servers
**Branch:** `refactoring` ✓ (checked out)
**Purpose:** Collection of MCP server implementations

### MCP Server Modules

#### Core RCA Components

**rca-bot-2.0/** - Latest RCA bot implementation
- **poc/** - Proof of concept with 38 files
  - `data_catalog.yaml` (64KB) - **KEY FILE** - Unified data catalog
  - `rca_bot.py` - Main RCA bot logic (57KB)
  - `load_replay.py` - Load replay functionality (153KB)
  - Python clients for various data sources:
    - `clickhouse_client.py` (49KB)
    - `athena_client.py`
    - `redshift_client.py` (37KB)
    - `trino_client.py` (24KB)
    - `github_client.py` (22KB)
    - `jira_client.py` (39KB)
    - `tracking_api_client.py` (37KB)
    - `company_api_client.py`
    - `confluence_client.py`
    - `graphdb_client.py`
  - Analysis modules:
    - `error_analyzer.py` (24KB)
    - `code_flow_analyzer.py` (14KB)
    - `hypothesis_generator.py`
    - `log_pattern_analyzer.py`
    - `issue_mapper.py`
    - `network_checker.py` (33KB)
    - `validator.py`
  - Configuration files:
    - `event_mappings.yaml` (34KB)
    - `issue_mappings.yaml` (25KB)
    - `domain_rules.yaml`
    - `github_repos.yaml`
  - `web_ui/` - Web interface components
  - `requirements.txt`, `pyproject.toml` - Dependencies

**rewind/** - Related rewind functionality
```
rewind/
├── CLAUDE.md
├── README.md
├── backend/
└── frontend/
```

**neo4j_mcp/** - Neo4j graph database MCP server (25 dirs)
- GitHub integration ✓
- Log drain algorithm ✓
- Graph-based relationship tracking

#### Data Source MCP Servers

**signoz_mcp/** - Signoz observability integration
**mcp-redshift-loads/** - Redshift data warehouse access
**historic-redshift-mcp/** - Historical Redshift data
**mcp-snowflake/** - Snowflake data warehouse
**tracking-mcp-server/** - Tracking service integration
**tracking-api-mcp-server/** - Tracking API wrapper

#### Business Logic MCP Servers

**courier-mcp/** - Courier/delivery tracking (17 items)
**mcp-custom-jira/** - Custom Jira integration
**bootstrap-mcp-server/** - Bootstrap/initialization
**excel-mcp-server/** - Excel file processing

### Repository Documentation
- `CLAUDE.md` (11KB) - Claude integration guide
- `README.md` - Repository overview

---

## 3. hr-agent

**Path:** `~/rca-agent-project/hr-agent/`
**GitHub:** https://github.com/cloudqwest/hr-agent
**Purpose:** HR-specific agent implementation

### Structure
```
hr-agent/
├── app/                    # Application code
├── packages/               # Shared packages
├── Dockerfile             # Container build
├── Jenkinsfile.build      # CI/CD pipeline
├── test_session_resume.py # Session testing
└── README.md (10 bytes - empty/minimal)
```

### Observations
- Minimal README (needs documentation)
- Docker-based deployment
- Jenkins CI/CD integration
- Session resume capability

---

## Key Files to Review

### Critical Files

1. **data_catalog.yaml** - `mcp-servers/rca-bot-2.0/poc/data_catalog.yaml`
   - 64KB - Core unified catalog
   - Defines data sources, search APIs, callbacks
   - Central to Arpit's catalog-driven approach

2. **rca_bot.py** - `mcp-servers/rca-bot-2.0/poc/rca_bot.py`
   - 57KB - Main RCA bot implementation
   - Orchestration logic

3. **load_replay.py** - `mcp-servers/rca-bot-2.0/poc/load_replay.py`
   - 153KB - Largest file, likely core replay logic

### Configuration Files

4. **event_mappings.yaml** - Issue-to-event mappings (34KB)
5. **issue_mappings.yaml** - Issue categorization (25KB)
6. **domain_rules.yaml** - Domain-specific rules

### Architecture Documentation

7. **rewind-app/ARCHITECTURE.md** - System architecture
8. **rewind-app/CLAUDE.md** - Claude integration patterns
9. **mcp-servers/CLAUDE.md** - MCP Claude integration

---

## Data Source Integrations

### Currently Integrated
✓ ClickHouse
✓ Athena (AWS)
✓ Redshift (AWS)
✓ Trino (SPOG)
✓ Neo4j (Graph DB)
✓ Signoz (Observability)
✓ Snowflake
✓ GitHub
✓ Jira
✓ Confluence
✓ Tracking API
✓ Company API

### Missing (from discussion)
⚠ Support SQL Catalog (Notion) - Mentioned but not yet integrated
⚠ Unified Search API layer - In progress

---

## Analysis Capabilities

### Implemented
✓ Error analysis
✓ Code flow analysis
✓ Hypothesis generation
✓ Log pattern analysis
✓ Issue mapping
✓ Network checking
✓ Domain insights extraction
✓ Fix generation

### Missing (from requirements)
⚠ First-focus routing logic (which microservice to start with)
⚠ Auto-scope narrowing
⚠ Human playbook encoding

---

## Branch Information

### mcp-servers Branches
- **Current:** `refactoring` ✓
- Other notable branches:
  - `Rail-Rca-bot`
  - Various feature branches (CA-*, MM-*, Story/*)
  - QA/test branches (Vani/QATTS, etc.)

---

## Next Steps for Analysis

### Immediate
1. ✅ Review `data_catalog.yaml` structure
2. ✅ Analyze `rca_bot.py` orchestration logic
3. ✅ Understand `load_replay.py` replay mechanism
4. ✅ Map data source client capabilities

### Short-term
5. Identify overlaps between MCP servers
6. Document existing search API patterns
7. Find where "first focus" logic could plug in
8. Review Cassey agent integration points (not in these repos)

### Research Questions
- How does `data_catalog.yaml` define search APIs?
- What's the relationship between rca-bot-2.0 and rewind app?
- How do MCP servers currently communicate?
- Where is the issue type → microservice routing logic?
- What's the gap between existing capabilities and unified search API?

---

## Repository Statistics

```
rewind-app:       ~15 top-level items (backend, frontend, docs, helm)
mcp-servers:      20 directories (12+ MCP servers + 2 RCA implementations)
hr-agent:         11 items (minimal structure, needs expansion)
```

**Total:** 3 repos with significant codebase

**Key POC:** `mcp-servers/rca-bot-2.0/poc/` - 38 files, ~800KB of code

---

## Contact Points for Each Repo

- **rewind-app:** Arpit Garg (frontend team support needed)
- **mcp-servers/rca-bot-2.0:** Arpit Garg (actively developing)
- **mcp-servers/neo4j_mcp:** Original team (GitHub, Neo4j, log drain)
- **mcp-servers/cassey:** Goutham's team (not in this repo checkout)
- **hr-agent:** Separate team (minimal docs)

---

## Commands to Navigate

```bash
# Main project directory
cd ~/rca-agent-project

# Key RCA bot code
cd ~/rca-agent-project/mcp-servers/rca-bot-2.0/poc

# View data catalog
cat ~/rca-agent-project/mcp-servers/rca-bot-2.0/poc/data_catalog.yaml

# Rewind app architecture
cd ~/rca-agent-project/rewind-app
cat ARCHITECTURE.md

# Neo4j MCP server
cd ~/rca-agent-project/mcp-servers/neo4j_mcp
```

---

**Status:** ✅ All repos cloned and ready for analysis
**Branch:** ✅ Correct refactoring branch checked out
**Key file:** ✅ data_catalog.yaml located and accessible
