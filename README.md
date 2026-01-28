# FourKites Native AI Framework - Skills Library Pattern

## Overview

This repository contains the **FourKites Native AI Framework** - a reusable, product-agnostic architecture for building intelligent AI agents using the Skills Library pattern.

**Key Principle:** Skills are organizational assets that encode domain expertise in machine-executable form, reusable across products, agents, and use cases.

## Architecture

The **5-Layer AI Framework** provides clear separation of concerns:

```
Layer 1: Classification & Routing
    ↓
Layer 2: Skills Library (Reusable Intelligence)
    ↓
Layer 3: Investigation Engine (Orchestration)
    ↓
Layer 4: Data Integration Layer
    ↓
Layer 5: Data Sources
```

### Layer Responsibilities

**Layer 1: Classification & Routing**
- Intent classification
- Domain identification
- Agent selection
- Request routing

**Layer 2: Skills Library** ⭐ **Core Innovation**
- Domain expertise encoding
- Pattern-based intelligence
- Hierarchical skill organization
- Cross-product reusability

**Layer 3: Investigation Engine**
- Skill orchestration
- Execution sequencing
- Context management
- Cross-skill coordination

**Layer 4: Data Integration**
- Unified data access
- Query optimization
- Result caching
- Performance management

**Layer 5: Data Sources**
- Databases
- APIs
- External services
- Log systems

## Skills Library - Core Concepts

### What is a Skill?

A **skill** is:
- Domain expertise encoded in machine-executable format
- Self-contained diagnostic or operational intelligence
- Reusable across products and use cases
- Versioned and independently testable

A skill is **NOT**:
- Product-specific code
- Static documentation
- Data access logic
- Business process workflow

### Hierarchical Organization

Skills are organized as **trees**, not flat lists:

```
📦 parent_skill (orchestrator)
├─ 🔧 skill_family_1 (fast checks)
│   ├─ sub_skill_1a
│   ├─ sub_skill_1b
│   └─ sub_skill_1c
├─ 🎯 skill_family_2 (medium complexity)
│   ├─ sub_skill_2a
│   └─ sub_skill_2b
└─ 📊 skill_family_3 (deep analysis)
    ├─ sub_skill_3a
    └─ sub_skill_3b (may escalate to another parent skill)
```

**Execution pattern:**
- Parent skill orchestrates sub-skills sequentially
- Early exit when objective achieved
- No wasted computation on unnecessary checks

### Skill Anatomy

```yaml
skill_id: example_diagnostic_skill
family: diagnostics
tier: 1  # 1=fast, 2=medium, 3=slow
category: configuration

# What the skill checks
objective: "Verify system configuration state"

# Data requirements
data_sources:
  - source: primary_db
    query_template: "SELECT config_value FROM configs WHERE..."
  
# Decision logic
checks:
  - name: "config_enabled"
    condition: "config_value == true"
    confidence: HIGH
    
# Execution constraints
optimization:
  timeout_ms: 500
  cache_ttl_seconds: 300
  
# Outcomes
outcomes:
  - condition: "config_enabled == false"
    result: "Configuration disabled"
    confidence: 100
    action: auto_resolve
    template: "Enable {config_name} in system settings"
  - condition: "config_enabled == true"
    result: "Configuration valid"
    action: continue
    
# Cross-skill dependencies
escalation:
  - trigger: "symptoms_present AND no_root_cause"
    target_skill: "deeper_analysis_skill"
    context: ["symptom_data", "checked_configurations"]
```

## Execution Patterns

### Pattern 1: Sequential with Early Exit

```
Input: Problem report

Step 1: Run parent_skill
  └─ family_1.sub_skill_1a
      ├─ Execute check (100ms)
      ├─ Result: OBJECTIVE_ACHIEVED
      └─ ✅ STOP (skip remaining 14 skills)

Total Time: ~150ms
Efficiency: Avoided 14 unnecessary checks
```

### Pattern 2: Cross-Domain Escalation

```
Input: Problem report

Step 1: Run domain_a_skill
  ├─ family_1 checks → PASS ✓
  ├─ family_2 checks → PASS ✓
  └─ family_3.deep_analysis
      ├─ Symptoms found but no root cause in domain A
      └─ ⚡ ESCALATE to domain_b_skill

Step 2: Run domain_b_skill (cross-domain handoff)
  └─ family_1.critical_check
      ├─ Execute check (2s)
      ├─ Result: ROOT_CAUSE_FOUND
      └─ ✅ RESOLVED

Total Time: ~5s
Cross-domain: Domain A → Domain B handoff successful
```

## Performance Architecture

### Tiered Execution by Speed

**Tier 1: Fast Checks (100-300ms)**
- Data source: Primary database
- Query type: Boolean flags, simple lookups
- Coverage: 70-80% of cases
- Example: Configuration validation, assignment checks

**Tier 2: Medium Analysis (1-5s)**
- Data source: Analytical databases
- Query type: Aggregations, pattern matching
- Coverage: 15-20% of cases
- Example: Log analysis, trend detection

**Tier 3: Deep Investigation (5-15s)**
- Data source: Multiple systems
- Query type: Complex joins, cross-domain queries
- Coverage: 5-10% of cases
- Example: Cross-system correlation, historical analysis

### Optimization Strategies

**1. Query Optimization**

Skills define WHAT to check:
```yaml
check: "Analyze system logs for error patterns"
patterns: ["timeout", "connection_refused", "null_pointer"]
```

Investigation Engine optimizes HOW:
```sql
-- Engine adds optimization constraints
SELECT timestamp, error_type, error_message
FROM system_logs
WHERE timestamp >= NOW() - INTERVAL '2 hours'  -- Time-box
  AND error_type IN ('timeout', 'connection_refused', 'null_pointer')
ORDER BY timestamp DESC
LIMIT 100  -- Result limit
```

**2. Result Caching**

```
First execution for entity #12345 → Query database (3s)
  └─ Cache result with TTL

Subsequent execution within TTL → Use cache (10ms)
  └─ 300x performance improvement
```

**3. Parallel Execution**

When skills have no dependencies:
```
Run skill_a, skill_b, skill_c in parallel
Wait for all results
Aggregate findings
```

## Example Application: RCA Diagnostics

This section shows how the framework is applied to build diagnostic agents. **These are examples, not the framework itself.**

### Example Skill: OTR Tracking Diagnostics

```
📦 otr_tracking_diagnostics (example parent skill)
├─ 🔧 configuration_checks (Tier 1: Fast ~100ms)
│   ├─ eld_enabled_check
│   ├─ network_config_check
│   └─ feature_flag_check
├─ 🎯 asset_validation (Tier 1: Fast ~200ms)
│   ├─ asset_assignment_check
│   ├─ carrier_capability_check
│   └─ device_assignment_check
└─ 📊 data_flow_analysis (Tier 2: Slow ~2-10s)
    ├─ gps_provider_health
    ├─ outlier_detection_logs
    └─ ingestion_status (cross-domain escalation)
```

### Example Execution

```
Case: System not functioning as expected

Step 1: configuration_checks.eld_enabled_check
  ├─ Query: config_db (100ms)
  ├─ Result: enabled = FALSE
  ├─ Confidence: 100%
  └─ ✅ ROOT CAUSE FOUND → Auto-resolve

Total Time: ~150ms
Response: "Feature disabled in configuration. Enable in settings."
```

## Architecture Principles

1. **Skills Library as Intelligence Layer** - Domain expertise belongs in Skills, not in data access tools
2. **Hierarchical Organization** - Parent skills orchestrate sub-skills, not flat skill lists
3. **Early Exit Pattern** - Stop when objective achieved, don't waste computation
4. **Tiered by Speed** - Fast checks first, slow analysis only when needed
5. **Separation of Concerns** - Skills define WHAT, Investigation Engine optimizes HOW
6. **Cross-Domain Capability** - Skills can escalate to other domain skills
7. **Evidence-Based Confidence** - Quantifiable confidence scores drive automation decisions
8. **Product Agnostic** - Skills are reusable organizational assets, not product-specific code

## Technology Stack

- **Skills Definition**: YAML-based declarative format
- **Investigation Engine**: Python orchestration layer
- **Data Integration**: Pluggable adapters for any data source
- **Caching**: Redis or similar (configurable TTL)
- **Monitoring**: Execution traces, performance metrics, skill analytics

## Strategic Value

### For Engineering
- **Reusability**: Write diagnostic logic once, use in multiple products
- **Maintainability**: Update skill = instant deployment across all agents
- **Testability**: Skills are independently testable units
- **Scalability**: Add new skills without changing core architecture

### For Organization
- **Knowledge Capture**: Expert knowledge becomes organizational asset
- **Onboarding**: New hires learn from Skills Library
- **Consistency**: Same diagnostic approach across all products
- **Continuous Improvement**: Skills evolve based on operational data

### For Products
- **Faster Time-to-Market**: Leverage existing skills for new features
- **Higher Quality**: Reuse proven diagnostic patterns
- **Lower Maintenance**: Shared intelligence layer reduces duplication
- **Innovation Enablement**: Focus on product features, not diagnostic reinvention

## Key Documents

- **FOURKITES_AI_FRAMEWORK_PROPOSAL.html** - Complete framework architecture with visual presentation
- **docs/index.html** - Architecture diagrams and component breakdown

## Use Cases

The Skills Library framework enables:

- **Diagnostic Agents**: Automated root cause analysis
- **Operational Agents**: System health monitoring and remediation
- **Support Agents**: Intelligent ticket routing and resolution
- **Data Quality Agents**: Automated data validation and cleansing
- **Security Agents**: Threat detection and response
- **Compliance Agents**: Policy enforcement and audit automation

Any domain where **pattern-based intelligence** + **systematic investigation** creates value.

---

**Framework Status**: Approved for implementation (January 2026)  
**Current Application**: Diagnostic agents for support operations  
**Future Applications**: Cross-product skill reuse across Ocean, Yard, Visibility, and Operations domains
