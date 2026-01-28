# FourKites AI Framework - RCA Agent Implementation

## Overview

This repository contains the architecture and implementation approach for building AI-powered Root Cause Analysis (RCA) agents using the FourKites Native AI Framework with Skills Library pattern.

## Architecture

Based on the **5-Layer AI Framework**:

```
Layer 1: Classification & Routing (Cassie Agent)
    ↓
Layer 2: Skills Library (Diagnostic Intelligence)
    ↓
Layer 3: Investigation Engine (Orchestration)
    ↓
Layer 4: MCP Integration Layer (Data Access)
    ↓
Layer 5: Data Sources (Redshift, Clickhouse, APIs)
```

## Skills Library - Hierarchical Organization

Skills are organized as **hierarchical trees**, not flat lists. Parent skills orchestrate sub-skills with early exit when root cause is found.

### OTR Tracking Diagnostics (Parent Skill)

```
📦 otr_tracking_diagnostics
├─ 🔧 configuration_checks (Tier 1: Fast - Redshift ~100ms)
│   ├─ eld_enabled_check
│   │   • Query: network_configurations.eld_tracking_enabled
│   │   • Confidence: HIGH (100%)
│   │   • Auto-resolve: YES
│   │
│   ├─ network_config_check
│   │   • Query: network_configurations table
│   │   • Confidence: HIGH (95%)
│   │   • Auto-resolve: YES
│   │
│   └─ feature_flag_check
│       • Query: feature_flags table
│       • Confidence: HIGH (100%)
│       • Auto-resolve: YES
│
├─ 🎯 asset_validation (Tier 1: Fast - Redshift ~200ms)
│   ├─ asset_assignment_check
│   │   • Query: load_tracking.truck_number, trailer_number, device_id
│   │   • Confidence: HIGH (100%)
│   │   • Auto-resolve: YES
│   │
│   ├─ carrier_capability_check
│   │   • Query: carriers table (supports truck GPS vs trailer GPS)
│   │   • Confidence: MEDIUM (85%)
│   │   • Auto-resolve: PARTIAL
│   │
│   └─ device_assignment_check
│       • Query: device assignment status
│       • Confidence: HIGH (95%)
│       • Auto-resolve: YES
│
└─ 📊 data_flow_analysis (Tier 2: Slow - Clickhouse ~2-10s)
    ├─ gps_provider_health
    │   • Query: Clickhouse gps_provider_api_logs (last 2 hours)
    │   • Pattern match: "null timestamp", "API timeout", "invalid coordinates"
    │   • Confidence: MEDIUM (80%)
    │   • Auto-resolve: PARTIAL
    │
    ├─ outlier_detection_logs
    │   • Query: Clickhouse outlier_detection logs
    │   • Pattern match: "speed-based rejection", "stale coordinates"
    │   • Confidence: MEDIUM (75%)
    │   • Auto-resolve: NO (diagnostic guidance only)
    │
    └─ ingestion_status
        • Query: Clickhouse ingestion service logs
        • Cross-domain escalation: Routes to ingestion_diagnostics skill
        • Confidence: MEDIUM (70%)
        • Auto-resolve: NO (requires cross-domain investigation)
```

### Network Configuration Diagnostics

```
📦 network_configuration_diagnostics
├─ 🔧 connectivity_checks
│   ├─ connect_config_enabled
│   ├─ api_credentials_valid
│   └─ network_pairing_status
│
├─ 🎯 integration_health
│   ├─ webhook_delivery_status
│   ├─ api_rate_limit_check
│   └─ authentication_failures
│
└─ 📊 data_sync_analysis
    ├─ load_sync_status
    ├─ carrier_data_freshness
    └─ mapping_configuration
```

### Ingestion Diagnostics (Cross-Domain)

```
📦 ingestion_diagnostics
├─ 🔧 polling_service_health
│   ├─ gps_polling_active
│   ├─ polling_frequency_check
│   └─ api_connectivity
│
├─ 🎯 data_ingestion_pipeline
│   ├─ kafka_lag_check
│   ├─ message_processing_rate
│   └─ dead_letter_queue_analysis
│
└─ 📊 provider_integration_health
    ├─ provider_api_status
    ├─ authentication_health
    └─ data_quality_checks
```

## Execution Flow

### Sequential Execution with Early Exit

```
Case: Load Not Tracking

Step 1: Run otr_tracking_diagnostics
  └─ configuration_checks.eld_enabled_check
      ├─ Query Redshift: 100ms
      ├─ Result: eld_tracking_enabled = FALSE
      ├─ Confidence: 100%
      └─ ✅ ROOT CAUSE FOUND → Auto-resolve
          STOP (skip remaining 14 checks)

Total Time: ~150ms
Response: "ELD tracking not enabled at network level. Enable in Connect configuration."
```

```
Case: Load Not Tracking (Cross-Domain)

Step 1: Run otr_tracking_diagnostics
  ├─ configuration_checks → All PASS ✓
  ├─ asset_validation → All PASS ✓
  └─ data_flow_analysis.ingestion_status
      ├─ Symptoms: Asset assigned but no GPS data received
      ├─ Root cause NOT in OTR domain
      └─ ⚡ ESCALATE to ingestion_diagnostics skill

Step 2: Run ingestion_diagnostics (cross-domain handoff)
  └─ polling_service_health.gps_polling_active
      ├─ Query Clickhouse: 2-3s
      ├─ Result: GPS polling service DOWN
      ├─ Confidence: 90%
      └─ ✅ ROOT CAUSE FOUND → Create engineering ticket

Total Time: ~5s
Response: "GPS polling service not running. Engineering ticket created."
```

## Performance Strategy

### Tiered Execution by Speed

**Tier 1: Configuration & Assignment Checks (Fast)**
- Data source: Redshift
- Response time: 100-300ms
- Coverage: 70-80% of cases
- Checks: Boolean flags, simple joins

**Tier 2: Log Analysis (Slow)**
- Data source: Clickhouse
- Response time: 2-10s
- Coverage: 15-20% of cases
- Optimization:
  - Time-boxed queries (last 2 hours only)
  - Row limits (100 max)
  - Result caching (5 min TTL)
  - Query only when Tier 1 passes but no root cause

**Tier 3: Cross-Domain Investigation (Slowest)**
- Multiple data sources
- Response time: 5-15s
- Coverage: 5-10% of cases
- Requires agent handoff or collaboration

### Query Optimization

Skills define WHAT to check:
```yaml
skill: gps_provider_health
check: "Query GPS provider logs for error patterns"
patterns:
  - "null timestamp"
  - "API timeout"
  - "invalid coordinates"
```

Investigation Engine optimizes HOW to query:
```sql
-- Engine adds optimization constraints
SELECT timestamp, provider_name, error_message, location_data
FROM gps_provider_api_logs
WHERE load_id = ?
  AND timestamp >= NOW() - INTERVAL '2 hours'  -- Time-box
  AND error_message IS NOT NULL
ORDER BY timestamp DESC
LIMIT 100  -- Result limit
```

### Caching Strategy

```
First case for Load #12345 → Query Clickhouse (3s)
  └─ Cache result with 5 min TTL

Second case for Load #12345 within 5 min → Use cache (10ms)
  └─ Massive performance win for duplicate investigations
```

## Gap Analysis Findings

The comprehensive Gap Analysis (367KB PDF) identified:

### What's Working
- ✅ Classification & Routing (Cassie Agent)
- ✅ MCP Infrastructure (5 production MCPs)
- ✅ React Agent execution engine
- ✅ 100+ patterns documented (Arpit's category sheet)

### Critical Gaps
- ❌ MCP approach fundamentally flawed (built for human-assisted RCA, not autonomous)
- ❌ No diagnostic intelligence in specialized prompts
- ❌ No cross-domain investigation capability
- ❌ 100% escalation rate (0% auto-resolution)
- ❌ Decision loop bugs in classification layer

### Strategic Decision
- **Abandon incremental MCP fixes** → Would still result in 100% manual intervention
- **Adopt 5-Layer AI Framework** → Proper architecture with Skills Library as intelligence layer
- **Timeline: April 2026** → 16-week implementation for production-ready system

## Implementation Roadmap

### Phase 1: Skills Library Foundation (Weeks 1-4)
- Convert 20 HIGH-feasibility patterns to skills
- Implement hierarchical skill structure
- Build skill execution engine

### Phase 2: Investigation Orchestration (Weeks 5-8)
- Tier 1 fast checks (Redshift)
- Tier 2 log analysis (Clickhouse with optimization)
- Query optimization layer

### Phase 3: Cross-Domain Investigation (Weeks 9-12)
- Agent handoff mechanism
- Context passing between skills
- Investigation audit trail

### Phase 4: Production Deployment (Weeks 13-16)
- Testing on historical cases
- Shadow mode validation
- Phased rollout (10% → 50% → 100%)

## Success Metrics

| Metric | Current | Target (April 2026) |
|--------|---------|---------------------|
| Auto-Resolution Rate | 0% | 60-70% |
| Avg Investigation Time | 15-30 min | 30s - 3 min |
| Root Cause Accuracy | 0% | 85%+ |
| Customer Satisfaction | N/A | 80%+ |
| Manual Intervention | 100% | 10-20% (complex cases only) |

## Key Documents

- **FOURKITES_AI_FRAMEWORK_PROPOSAL.html** - Complete framework architecture with visual slides
- **docs/index.html** - Architecture diagrams and component breakdown
- **Gap Analysis PDF** (local only) - Detailed technical analysis of current system failures

## Architecture Principles

1. **Skills Library as Intelligence Layer** - Diagnostic intelligence belongs in Skills, not in data tools (MCPs)
2. **Hierarchical Skills** - Parent skills orchestrate sub-skills, not flat 85+ skill list
3. **Early Exit Pattern** - Stop execution when root cause found, don't waste time on remaining checks
4. **Tiered by Speed** - Fast checks first, slow log analysis only when needed
5. **Separation of Concerns** - Skills define WHAT, Investigation Engine optimizes HOW
6. **Cross-Domain Capability** - Skills can escalate to other domain skills when root cause crosses boundaries
7. **Evidence-Based Confidence** - Quantifiable confidence scores determine auto-resolve vs escalation

## Technology Stack

- **Classification Layer**: Cassie Agent (existing)
- **Skills Library**: YAML-based skill definitions
- **Investigation Engine**: Python orchestration layer
- **Data Access**: MCP integration (Redshift, Clickhouse, Salesforce, Knowledge, Support AI, Atlassian)
- **Caching**: Redis (5 min TTL for log query results)
- **Monitoring**: Investigation audit trail, performance metrics

---

**Status**: Framework approved by Engineering Leadership (January 2026)  
**Next Steps**: Begin Phase 1 implementation (Skills Library foundation)
