# Skills-Empowered RCA Agent Platform Architecture

**Plan Created:** 2026-01-26
**Status:** READY FOR IMPLEMENTATION
**Owner:** MSP Raja / Arpit Garg Team

---

## Executive Summary

This plan transforms OTR's struggling RCA bot into a **production-ready L1 support automation system** using a Skills-empowered architecture. The approach addresses Arpit's explicit requirements by providing:

1. **End-to-end RCA automation** through specialized Skills
2. **Flawless architecture** solving the routing/scaling problem for 10-12 domains
3. **Knowledge extraction templates** for capturing support team mental models
4. **Building blocks** Arpit's team can extend
5. **FourSight/Cassie integration path** preserving existing investments

**Key Insight:** The UX mock demonstrates the exact pattern we need - confidence scores, multi-agent investigation flow, human-in-the-loop approval. Skills provide the missing orchestration layer.

---

## Part 1: Requirements Summary

### 1.1 Core Problems from Meeting Transcript

| Problem | Evidence | Impact |
|---------|----------|--------|
| **OTR bot premature release** | "fails for most L1 support cases" | Zero automation |
| **85+ subcategories** | "load not tracking" alone has 85+ causes | Impossible to hardcode |
| **No captured mental model** | Support team's playbook not encoded | Knowledge silos |
| **Expectation mismatch** | Conversational tool vs autonomous agent | Wrong UX paradigm |
| **Limited data sources** | Only logs vs 4-5 sources needed | Incomplete investigation |
| **Routing at scale** | 10-12 domains = intent switching chaos | FourSight concern |

### 1.2 Arpit's Explicit Requirements

1. **End-to-end Skills approach** for RCA process
2. **Flawless architecture** for OTR and Cassie
3. **Knowledge extraction template** from support teams
4. **Initial building blocks** his team can take forward
5. **Follow the UX mock** from UX expert

**UX Mock Reference:** `/Users/msp.raja/rca-agent-project/fourkites-skills-academy/docs/RCA_UX_ANALYSIS.md`
This document contains the detailed breakdown of the UX mock shared by Arpit, including:
- Investigation Results screen (92% confidence, root cause card)
- Multi-agent investigation flow (Identifier → Tracking API → Redshift → Hypothesis → Synthesis)
- Email preview with human-in-the-loop approval
- Suggested action UI pattern

### 1.3 Acceptance Criteria

| Deliverable | Acceptance Criteria |
|-------------|---------------------|
| Architecture Document | Addresses all 6 core problems, integrates with FourSight |
| Knowledge Extraction Template | Can capture 1 domain's mental model in 2 days |
| Pattern Library Structure | Supports 85+ subcategories with versioning |
| Building Blocks | Running code for at least 3 patterns |
| Integration Plan | Clear path to connect with Cassie/FourSight |

---

## Part 2: Skills-Empowered Architecture

### 2.1 Why Skills Solve the Routing/Scaling Problem

**Current Problem (FourSight):**
```
User Query --> Single Router --> 10-12 Domain KBs --> Intent Confusion
```

**Skills Solution:**
```
User Query --> Skill Router --> Specialized Skills --> Domain-Specific Investigation
                    |                    |
                    v                    v
             Pattern Matching     Data Source Orchestration
             (85+ patterns)       (5+ sources per skill)
```

**Key Advantages:**
1. **Isolation:** Each skill owns its patterns, data sources, and logic
2. **Versioning:** Skills can be updated independently
3. **Testing:** Each skill tested against known cases
4. **Scaling:** Add new domains by adding new skills (no router changes)

### 2.2 Architecture Diagram

```
                                SKILLS-EMPOWERED RCA PLATFORM
===================================================================================

                              +------------------+
                              |   CASSIE AGENT   |  <-- Existing Salesforce Intake
                              |   (FourSight)    |
                              +--------+---------+
                                       |
                                       v
+------------------------------------------------------------------------------+
|                            SKILLS ROUTER                                      |
|  +------------------------------------------------------------------------+  |
|  |  Intent Classification  |  Domain Detection  |  Confidence Scoring     |  |
|  +------------------------------------------------------------------------+  |
+-----+----------------+----------------+----------------+----------------+-----+
      |                |                |                |                |
      v                v                v                v                v
+----------+    +----------+    +----------+    +----------+    +----------+
| OTR RCA  |    | Ocean    |    | DY Ops   |    | Carrier  |    | [Future] |
| Skill    |    | Tracking |    | Skill    |    | Files    |    | Domain   |
|          |    | Skill    |    |          |    | Skill    |    | Skills   |
+----+-----+    +----+-----+    +----+-----+    +----+-----+    +----+-----+
     |               |               |               |               |
     v               v               v               v               v
+------------------------------------------------------------------------------+
|                           SKILL EXECUTION LAYER                               |
|  +------------------------------------------------------------------------+  |
|  | State Machine | Decision Trees | Evidence Scoring | Human Handoff     |  |
|  +------------------------------------------------------------------------+  |
+-----+----------------+----------------+----------------+----------------+-----+
      |                |                |                |                |
      v                v                v                v                v
+----------+    +----------+    +----------+    +----------+    +----------+
| Tracking |    | JT/RPA   |    | Redshift |    | SigNoz   |    | Company  |
| API      |    | DataHub  |    | DWH      |    | Logs     |    | API      |
| MCP      |    | MCP      |    | MCP      |    | MCP      |    | MCP      |
+----------+    +----------+    +----------+    +----------+    +----------+
                           |                |
                           v                v
                    +-------------+  +-------------+
                    | Confluence  |  | Slack/Jira  |
                    | KB RAG      |  | History RAG |
                    +-------------+  +-------------+

+------------------------------------------------------------------------------+
|                              OUTPUT LAYER                                     |
|  +------------------------------------------------------------------------+  |
|  | Root Cause Card | Confidence Score | Recommended Actions | Email Draft |  |
|  | (UX Mock Style) | (92% etc.)       | (Human Approval)    | (Preview)   |  |
|  +------------------------------------------------------------------------+  |
+------------------------------------------------------------------------------+
```

### 2.3 Skills Router Design

The router solves the "10-12 domain routing problem" through **hierarchical classification**:

```yaml
# skills_router_config.yaml
router:
  version: "1.0.0"
  classification_strategy: "hierarchical"

  # Level 1: Transport Mode
  mode_detection:
    rules:
      - pattern: "ocean|container|vessel|booking|bol"
        mode: OCEAN
      - pattern: "truck|eld|gps|driver|ground"
        mode: GROUND_OTR
      - pattern: "dray|trailer|yard|facility"
        mode: DRAYAGE
      - pattern: "air|flight|awb"
        mode: AIR
    default: GROUND_OTR

  # Level 2: Issue Category
  category_detection:
    GROUND_OTR:
      - pattern: "not tracking|awaiting tracking|no updates"
        category: LOAD_NOT_TRACKING
        skill: otr-rca-skill
      - pattern: "eld|gps|position"
        category: ELD_ISSUES
        skill: otr-rca-skill
      - pattern: "callback|webhook|notification"
        category: CALLBACK_FAILURES
        skill: callback-debug-skill

    OCEAN:
      - pattern: "not tracking|no events"
        category: CONTAINER_NOT_TRACKING
        skill: ocean-tracking-skill
      - pattern: "vessel|departure|eta"
        category: VESSEL_ISSUES
        skill: ocean-tracking-skill

    DRAYAGE:
      - pattern: "check.?in|check.?out"
        category: CHECKIN_ISSUES
        skill: dy-ops-skill
      - pattern: "user|access|login"
        category: ACCESS_ISSUES
        skill: dy-ops-skill

  # Level 3: Confidence Thresholds
  confidence:
    auto_route_threshold: 0.85
    human_review_threshold: 0.60
    reject_threshold: 0.40

  # Skill Registry
  skills:
    otr-rca-skill:
      path: "skills/otr-rca/"
      patterns: 85+
      data_sources: [tracking-api, company-api, signoz, redshift]

    ocean-tracking-skill:
      path: "skills/ocean-tracking/"
      patterns: 40+
      data_sources: [tracking-api, jt-datahub, super-api, signoz]

    dy-ops-skill:
      path: "skills/dy-ops/"
      patterns: 25+
      data_sources: [tracking-api, facility-api, signoz]
```

### 2.4 Skill Anatomy (Standard Structure)

Every skill follows this structure for consistency:

```
skills/otr-rca/
├── SKILL.md                    # Skill definition (Anthropic standard)
├── skill_definition.yaml       # Machine-readable config
├── decision_tree.yaml          # Step-by-step investigation flow
├── api_mappings.yaml           # Data source queries per step
├── patterns/                   # Pattern library (85+ files)
│   ├── network_relationship_missing.yaml
│   ├── eld_not_enabled.yaml
│   ├── gps_timestamp_null.yaml
│   ├── carrier_api_down.yaml
│   └── ...
├── knowledge_base/             # Extracted mental models
│   ├── surya_ocean_workflow.md
│   ├── prashant_otr_workflow.md
│   └── troubleshooting_runbooks/
├── prompts/                    # LLM prompts for this skill
│   ├── classify_issue.txt
│   ├── analyze_evidence.txt
│   └── generate_hypothesis.txt
├── test_cases/                 # Validation test cases
│   ├── case_001_network_missing.yaml
│   ├── case_002_eld_disabled.yaml
│   └── ...
├── templates/                  # Action templates
│   ├── email_carrier_eld.md
│   ├── email_carrier_files.md
│   └── escalation_template.md
└── metrics/                    # Skill performance tracking
    ├── accuracy_log.json
    └── resolution_times.json
```

---

## Part 3: Knowledge Extraction Template

### 3.1 Process for Capturing Mental Models

**Goal:** Systematically extract support analyst workflows into machine-readable skills.

**Timeline:** 2 days per domain

```
Day 1: Shadow Session (4 hours)
├── Watch analyst handle 5-10 real tickets
├── Record screen + audio
├── Note every tool/system accessed
├── Capture decision points ("If X, then Y")
└── Document data sources in order of access

Day 2: Documentation + Validation (4 hours)
├── Create decision tree YAML
├── Map API calls to each step
├── Define confidence thresholds
├── Create test cases from observed tickets
└── Review with analyst for accuracy
```

### 3.2 Knowledge Extraction Template

```yaml
# templates/knowledge_extraction_template.yaml
# Use this template when shadowing support analysts

session:
  analyst_name: ""
  analyst_role: ""
  domain: ""  # OTR, Ocean, DY, Carrier Files, etc.
  session_date: ""
  duration_hours: 0
  tickets_observed: 0

tools_used:
  - name: ""
    url: ""
    purpose: ""
    auth_type: ""  # SSO, API Key, Basic Auth, etc.
    access_time_seconds: 0  # How long to get data

issue_categories_observed:
  - category: ""
    frequency: ""  # High, Medium, Low
    avg_resolution_time: ""
    data_sources:
      - source: ""
        query_type: ""  # API, SQL, UI search
        fields_checked: []
    decision_points:
      - condition: ""
        if_true: ""
        if_false: ""
    common_resolutions:
      - resolution: ""
        action_type: ""  # Email, Config Change, Escalate, etc.
        human_approval_required: true/false

decision_tree:
  entry_point: "step_1"
  steps:
    step_1:
      name: ""
      description: ""
      data_source: ""
      query: ""
      decisions:
        - condition: ""
          confidence: 0.0
          next_step: ""
          conclusion: null
        - condition: ""
          confidence: 0.0
          next_step: null
          conclusion:
            root_cause: ""
            explanation: ""
            recommended_action: ""

edge_cases:
  - description: ""
    how_analyst_handled: ""
    should_escalate: true/false

tribal_knowledge:
  - insight: ""
    source: ""  # Analyst's experience, Confluence, etc.
    applicable_when: ""
```

### 3.3 Example: OTR "Load Not Tracking" Extraction

```yaml
# skills/otr-rca/knowledge_base/prashant_workflow.yaml
# Extracted from session with Prashant (OTR Support Lead)

session:
  analyst_name: "Prashant"
  analyst_role: "OTR Support Lead"
  domain: "OTR"
  session_date: "2026-01-XX"
  duration_hours: 4
  tickets_observed: 8

tools_used:
  - name: "FourKites Platform"
    url: "https://platform.fourkites.com"
    purpose: "Verify load exists, check carrier assignment"
    auth_type: "SSO"
    access_time_seconds: 10

  - name: "Tracking API"
    url: "https://api.fourkites.com/tracking/v1"
    purpose: "Get load details, position history"
    auth_type: "API Key"
    access_time_seconds: 5

  - name: "Company API"
    url: "https://api.fourkites.com/companies/v1"
    purpose: "Check network relationships, ELD config"
    auth_type: "API Key"
    access_time_seconds: 3

  - name: "SigNoz"
    url: "https://signoz.fourkites.internal"
    purpose: "Deep dive into processing logs"
    auth_type: "SSO"
    access_time_seconds: 30

issue_categories_observed:
  - category: "Load Not Tracking - Network Missing"
    frequency: "High (25%)"
    avg_resolution_time: "15 minutes"
    data_sources:
      - source: "Company API"
        query_type: "API"
        fields_checked: ["relationship_id", "is_active", "eld_enabled"]
    decision_points:
      - condition: "relationship.count == 0"
        if_true: "Root cause = Network relationship missing"
        if_false: "Check ELD enablement"
    common_resolutions:
      - resolution: "Create network relationship in FourKites Connect"
        action_type: "Config Change"
        human_approval_required: true

  - category: "Load Not Tracking - ELD Not Enabled"
    frequency: "Medium (15%)"
    avg_resolution_time: "10 minutes"
    data_sources:
      - source: "Company API"
        query_type: "API"
        fields_checked: ["eld_enabled", "eld_provider"]
    decision_points:
      - condition: "eld_enabled == false AND carrier.has_eld_capability"
        if_true: "Root cause = ELD not enabled at network level"
        if_false: "Check carrier ELD devices"
    common_resolutions:
      - resolution: "Enable ELD in Connect for shipper-carrier relationship"
        action_type: "Config Change"
        human_approval_required: true

decision_tree:
  entry_point: "check_load_exists"
  steps:
    check_load_exists:
      name: "Verify Load Exists"
      description: "Check if load was created in system"
      data_source: "Tracking API"
      query: "GET /loads/{load_number}"
      decisions:
        - condition: "response.status == 404"
          confidence: 0.98
          next_step: null
          conclusion:
            root_cause: "Load not found in system"
            explanation: "Load was never created or was deleted"
            recommended_action: "Check load creation logs, verify customer submitted correct ID"
        - condition: "response.status == 200"
          confidence: 0.80
          next_step: "check_network_relationship"

    check_network_relationship:
      name: "Check Network Relationship"
      description: "Verify carrier-shipper relationship exists and is active"
      data_source: "Company API"
      query: "GET /companies/{shipper_id}/relationships?carrier_id={carrier_id}"
      decisions:
        - condition: "relationships.count == 0"
          confidence: 0.95
          next_step: null
          conclusion:
            root_cause: "Network relationship missing"
            explanation: "Carrier-shipper relationship does not exist. This is the #1 cause of 'Awaiting Tracking Info' (7.7% of loads)."
            recommended_action: "Create relationship in FourKites Connect"
        - condition: "relationships[0].is_active == false"
          confidence: 0.90
          next_step: null
          conclusion:
            root_cause: "Network relationship inactive"
            explanation: "Relationship exists but is not active"
            recommended_action: "Activate relationship in FourKites Connect"
        - condition: "relationships[0].is_active == true"
          confidence: 0.85
          next_step: "check_eld_enabled"

    check_eld_enabled:
      name: "Check ELD Enablement"
      description: "Verify ELD tracking is enabled at network level"
      data_source: "Company API"
      query: "GET /companies/{shipper_id}/relationships/{relationship_id}"
      decisions:
        - condition: "eld_enabled == false AND carrier.capabilities.eld == true"
          confidence: 0.92
          next_step: null
          conclusion:
            root_cause: "ELD not enabled at network relationship level"
            explanation: "Carrier has ELD capability but ELD tracking is disabled in the network configuration"
            recommended_action: "Enable ELD in FourKites Connect for this relationship"
        - condition: "eld_enabled == true"
          confidence: 0.80
          next_step: "check_carrier_devices"

    check_carrier_devices:
      name: "Check Carrier ELD Devices"
      description: "Verify carrier has active ELD devices assigned"
      data_source: "SigNoz Logs"
      query: "service:tracking-worker-global AND carrier_code:{carrier_code} AND level:error"
      decisions:
        - condition: "log.contains('GPS timestamp is null')"
          confidence: 0.88
          next_step: null
          conclusion:
            root_cause: "Carrier GPS returning null timestamps"
            explanation: "Carrier ELD device is sending data but with null/invalid timestamps"
            recommended_action: "Contact carrier to fix GPS device configuration"
        - condition: "log.contains('No ELD device assigned')"
          confidence: 0.90
          next_step: null
          conclusion:
            root_cause: "No ELD device assigned to driver/truck"
            explanation: "Carrier has ELD but no device is assigned to this specific load"
            recommended_action: "Contact carrier to assign ELD device to the load"
        - condition: "no errors found"
          confidence: 0.60
          next_step: "escalate_to_engineering"

    escalate_to_engineering:
      name: "Escalate for Deep Investigation"
      description: "Issue requires deeper technical investigation"
      data_source: null
      query: null
      decisions:
        - condition: "always"
          confidence: 0.50
          next_step: null
          conclusion:
            root_cause: "Complex issue - requires engineering investigation"
            explanation: "Standard troubleshooting did not identify root cause"
            recommended_action: "Escalate to engineering team with collected evidence"

tribal_knowledge:
  - insight: "CR England always sends ref number, not standard load ID"
    source: "Prashant experience"
    applicable_when: "carrier_code == 'CRST' OR carrier_code == 'CRENGLAND'"

  - insight: "Pepsi loads sometimes have no carrier (dispatcher API)"
    source: "Recent edge case"
    applicable_when: "shipper_id == 'pepsi' AND carrier_id IS NULL"

  - insight: "First check network, then ELD - 40% of cases solved in step 1"
    source: "Prashant best practice"
    applicable_when: "category == 'load_not_tracking'"
```

---

## Part 4: Pattern Library Structure

### 4.1 Pattern File Format

Each of the 85+ subcategories gets a pattern file:

```yaml
# patterns/eld_not_enabled_network.yaml
pattern:
  id: "ELD_NOT_ENABLED_NETWORK"
  name: "ELD Not Enabled at Network Level"
  category: "ELD_ISSUES"
  subcategory: "NETWORK_CONFIG"
  version: "1.2.0"

  # Statistics from production
  stats:
    frequency: "15% of load_not_tracking cases"
    avg_resolution_time: "10 minutes"
    automation_rate: "95%"
    last_updated: "2026-01-20"
    cases_resolved: 1247

  # Detection criteria
  symptoms:
    - "Load exists in system"
    - "Carrier has ELD capability"
    - "No position updates received"
    - "Network relationship exists and is active"

  # Evidence requirements
  evidence:
    required:
      - source: "Company API"
        field: "relationships[0].eld_enabled"
        condition: "equals false"
        weight: 10  # Critical evidence

      - source: "Carrier Config"
        field: "carrier.capabilities.eld"
        condition: "equals true"
        weight: 5  # Supporting evidence

    supporting:
      - source: "Tracking API"
        field: "load.last_position"
        condition: "is null OR older than 4 hours"
        weight: 3

  # Confidence calculation
  confidence:
    formula: "sum(matched_evidence.weight) / sum(all_evidence.weight)"
    min_required: 0.85
    auto_resolve_threshold: 0.90

  # Root cause determination
  root_cause:
    statement: "ELD tracking not enabled at network relationship level"
    explanation: |
      The carrier {carrier_name} has ELD capability (provider: {eld_provider}),
      but ELD tracking is disabled in the network configuration between
      shipper {shipper_name} and carrier {carrier_name}.

      This prevents the system from polling the carrier's ELD provider for
      position updates.

    impact: |
      - Load will show "Awaiting Tracking Info" indefinitely
      - Customer receives no position updates
      - ETA calculations unavailable

  # Resolution workflow
  resolution:
    automated_steps: false  # Requires human approval
    human_approval_required: true

    steps:
      - step: 1
        action: "Enable ELD in FourKites Connect"
        details: |
          1. Navigate to Network Relationships
          2. Search for {shipper_name}
          3. Find relationship with {carrier_name}
          4. Enable "ELD Tracking"
          5. Select Provider: {eld_provider}
        button: "Open Connect"
        button_url: "https://connect.fourkites.com/relationships/{relationship_id}"

      - step: 2
        action: "Verify configuration"
        details: "Confirm carrier has active ELD devices"
        button: "Check Carrier Config"
        button_url: null  # API check

      - step: 3
        action: "Monitor for updates"
        details: "Position updates should appear within 15 minutes"
        button: "View Load Timeline"
        button_url: "https://platform.fourkites.com/loads/{load_number}"

      - step: 4
        action: "Escalate if no updates after 30 minutes"
        details: "Contact carrier operations team"
        button: "Escalate to Carrier"
        button_url: null  # Email template

  # Email template
  email_template:
    to: "{carrier_dispatch_email}"
    subject: "Action Required: Enable ELD Tracking for Load {load_number}"
    body: |
      Dear {carrier_name} Team,

      We are reaching out regarding Load {load_number} for shipper {shipper_name}.

      Our system indicates that ELD tracking needs to be enabled for this shipment.
      To ensure accurate tracking and visibility, please confirm:

      1. An ELD device is assigned to this load
      2. The ELD device is transmitting location data
      3. Your ELD provider ({eld_provider}) integration is active

      If you have any questions, please contact our support team.

      Best regards,
      FourKites Support Team

  # Test cases
  test_cases:
    - case_id: "TC_ELD_001"
      description: "Standard ELD not enabled case"
      input:
        load_number: "U110123982"
        shipper: "walmart"
        carrier: "crst-logistics"
      expected_output:
        pattern_matched: true
        confidence: 0.92
        root_cause: "ELD_NOT_ENABLED_NETWORK"

    - case_id: "TC_ELD_002"
      description: "Carrier without ELD capability (should NOT match)"
      input:
        load_number: "U110123983"
        shipper: "target"
        carrier: "small-carrier-no-eld"
      expected_output:
        pattern_matched: false
        reason: "Carrier does not have ELD capability"

  # Related patterns
  related_patterns:
    - "ELD_NOT_ENABLED_LOAD"
    - "CARRIER_ELD_DEVICE_INACTIVE"
    - "NETWORK_RELATIONSHIP_MISSING"

  # Metadata
  metadata:
    created_by: "MSP Raja"
    created_date: "2026-01-22"
    last_modified: "2026-01-25"
    source: "Prashant OTR workflow session"
    confluence_link: "https://confluence.fourkites.com/display/SUP/ELD+Troubleshooting"
```

### 4.2 Pattern Library Organization

```
skills/otr-rca/patterns/
├── README.md                           # Pattern library overview
├── index.yaml                          # Pattern catalog with stats
│
├── load_not_found/                     # Category: Load Not Found (~25%)
│   ├── load_never_created.yaml
│   ├── load_deleted.yaml
│   ├── load_number_typo.yaml
│   └── ...
│
├── network_issues/                     # Category: Network Issues (~20%)
│   ├── relationship_missing.yaml
│   ├── relationship_inactive.yaml
│   ├── relationship_wrong_direction.yaml
│   └── ...
│
├── eld_issues/                         # Category: ELD Issues (~25%)
│   ├── eld_not_enabled_network.yaml
│   ├── eld_not_enabled_load.yaml
│   ├── eld_device_inactive.yaml
│   ├── gps_timestamp_null.yaml
│   ├── gps_location_stale.yaml
│   ├── wrong_truck_vs_trailer.yaml
│   └── ...
│
├── carrier_issues/                     # Category: Carrier Issues (~15%)
│   ├── carrier_api_down.yaml
│   ├── carrier_not_configured.yaml
│   ├── carrier_wrong_provider.yaml
│   └── ...
│
├── callback_issues/                    # Category: Callback Issues (~10%)
│   ├── webhook_endpoint_down.yaml
│   ├── webhook_auth_failure.yaml
│   ├── payload_validation_error.yaml
│   └── ...
│
└── edge_cases/                         # Category: Edge Cases (~5%)
    ├── carrierless_load.yaml           # Pepsi dispatcher API case
    ├── reference_number_only.yaml      # CR England case
    └── ...
```

### 4.3 Pattern Index

> **Note:** The "85+ subcategories" figure comes from Arpit's meeting feedback ("load not tracking alone has 85+ causes").
> This will be validated during Task 1.0 (Pattern Frequency Data Extraction) and may be adjusted based on actual data.

```yaml
# skills/otr-rca/patterns/index.yaml
pattern_library:
  name: "OTR RCA Pattern Library"
  version: "1.0.0"
  total_patterns: 85  # TBD - pending validation from data extraction (Task 1.0)
  last_updated: "2026-01-25"

  categories:
    - name: "Load Not Found"
      code: "LOAD_NOT_FOUND"
      pattern_count: 12
      frequency: "25%"
      avg_resolution: "5 min"

    - name: "Network Issues"
      code: "NETWORK_ISSUES"
      pattern_count: 15
      frequency: "20%"
      avg_resolution: "15 min"

    - name: "ELD Issues"
      code: "ELD_ISSUES"
      pattern_count: 28
      frequency: "25%"
      avg_resolution: "10 min"

    - name: "Carrier Issues"
      code: "CARRIER_ISSUES"
      pattern_count: 18
      frequency: "15%"
      avg_resolution: "30 min"

    - name: "Callback Issues"
      code: "CALLBACK_ISSUES"
      pattern_count: 8
      frequency: "10%"
      avg_resolution: "20 min"

    - name: "Edge Cases"
      code: "EDGE_CASES"
      pattern_count: 4
      frequency: "5%"
      avg_resolution: "varies"

  # Top patterns by frequency
  # NOTE: Statistics below are ESTIMATES pending data extraction.
  # Action Item: Extract actual pattern frequency from Salesforce/Redshift (last 6 months of support cases)
  # Source: TBD - Requires data extraction in Phase 1, Task 1.0
  top_patterns:
    - pattern_id: "NETWORK_RELATIONSHIP_MISSING"
      frequency: "~7.7% (TBD - pending data extraction)"
      automation_rate: "95%"

    - pattern_id: "ELD_NOT_ENABLED_NETWORK"
      frequency: "~5.2% (TBD - pending data extraction)"
      automation_rate: "92%"

    - pattern_id: "LOAD_NOT_FOUND"
      frequency: "~4.8% (TBD - pending data extraction)"
      automation_rate: "98%"

    - pattern_id: "GPS_TIMESTAMP_NULL"
      frequency: "~3.5% (TBD - pending data extraction)"
      automation_rate: "60%"  # Requires carrier contact
```

---

## Part 5: Building Blocks (Initial Code)

### 5.1 Core Components

#### 5.1.1 Skill Base Class

```python
# building_blocks/skill_base.py
"""
Base class for all RCA Skills.
Every skill inherits from this and implements domain-specific logic.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Any
import yaml
import json

class ConfidenceLevel(Enum):
    HIGH = "high"       # >= 85%
    MEDIUM = "medium"   # 60-84%
    LOW = "low"         # < 60%

@dataclass
class Evidence:
    """Single piece of evidence from a data source"""
    source: str
    field: str
    value: Any
    condition: str
    matched: bool
    weight: int
    timestamp: str = ""
    raw_data: Dict = field(default_factory=dict)

@dataclass
class Hypothesis:
    """A potential root cause with supporting evidence"""
    pattern_id: str
    description: str
    confidence: float
    evidence_for: List[Evidence]
    evidence_against: List[Evidence]

    @property
    def confidence_level(self) -> ConfidenceLevel:
        if self.confidence >= 0.85:
            return ConfidenceLevel.HIGH
        elif self.confidence >= 0.60:
            return ConfidenceLevel.MEDIUM
        else:
            return ConfidenceLevel.LOW

@dataclass
class Resolution:
    """Recommended resolution steps"""
    root_cause: str
    explanation: str
    steps: List[Dict]
    email_template: Optional[Dict] = None
    estimated_time: str = ""
    human_approval_required: bool = True

@dataclass
class InvestigationResult:
    """Complete investigation result"""
    ticket_id: str
    load_number: str
    confidence: float
    confidence_level: ConfidenceLevel
    root_cause: str
    hypotheses: List[Hypothesis]
    resolution: Resolution
    evidence_summary: List[Evidence]
    investigation_time_seconds: float
    data_sources_queried: List[str]
    skill_version: str

class Skill(ABC):
    """
    Base class for all RCA Skills.

    Usage:
        class OTRRCASkill(Skill):
            def investigate(self, context):
                # Implementation
                pass
    """

    def __init__(self, skill_dir: str):
        self.skill_dir = skill_dir
        self.definition = self._load_yaml("skill_definition.yaml")
        self.decision_tree = self._load_yaml("decision_tree.yaml")
        self.patterns = self._load_patterns()
        self.name = self.definition.get("name", "unknown")
        self.version = self.definition.get("version", "0.0.0")

    def _load_yaml(self, filename: str) -> Dict:
        """Load YAML configuration file"""
        filepath = f"{self.skill_dir}/{filename}"
        with open(filepath, 'r') as f:
            return yaml.safe_load(f)

    def _load_patterns(self) -> Dict[str, Dict]:
        """Load all patterns from patterns/ directory"""
        import os
        patterns = {}
        patterns_dir = f"{self.skill_dir}/patterns"

        for root, dirs, files in os.walk(patterns_dir):
            for file in files:
                if file.endswith('.yaml'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r') as f:
                        pattern = yaml.safe_load(f)
                        if pattern and 'pattern' in pattern:
                            pattern_id = pattern['pattern']['id']
                            patterns[pattern_id] = pattern['pattern']

        return patterns

    @abstractmethod
    def investigate(self, context: Dict) -> InvestigationResult:
        """
        Main investigation method. Must be implemented by each skill.

        Args:
            context: Dict containing ticket_id, load_number, description, etc.

        Returns:
            InvestigationResult with root cause, confidence, and resolution
        """
        pass

    def execute_decision_tree(self, context: Dict) -> Hypothesis:
        """
        Execute the decision tree step by step.
        Returns the highest confidence hypothesis.
        """
        current_step = self.decision_tree.get("entry_point")
        evidence_collected = []

        while current_step:
            step_config = self.decision_tree["steps"].get(current_step)
            if not step_config:
                break

            # Execute step query
            evidence = self._execute_step(step_config, context)
            evidence_collected.append(evidence)

            # Evaluate decisions
            decision = self._evaluate_decisions(step_config["decisions"], evidence)

            if decision.get("conclusion"):
                # Found root cause
                return Hypothesis(
                    pattern_id=decision.get("pattern_id", "UNKNOWN"),
                    description=decision["conclusion"]["root_cause"],
                    confidence=decision["confidence"],
                    evidence_for=evidence_collected,
                    evidence_against=[]
                )

            # Move to next step
            current_step = decision.get("next_step")

        # No conclusive root cause found
        return Hypothesis(
            pattern_id="UNKNOWN",
            description="Unable to determine root cause",
            confidence=0.5,
            evidence_for=evidence_collected,
            evidence_against=[]
        )

    @abstractmethod
    def _execute_step(self, step_config: Dict, context: Dict) -> Evidence:
        """Execute a single step query. Implemented by each skill."""
        pass

    def _evaluate_decisions(self, decisions: List[Dict], evidence: Evidence) -> Dict:
        """Evaluate decision conditions against evidence"""
        for decision in decisions:
            condition = decision.get("condition", "")
            if self._check_condition(condition, evidence):
                return decision

        # No condition matched - return default
        return {"next_step": None, "confidence": 0.5}

    def _check_condition(self, condition: str, evidence: Evidence) -> bool:
        """Check if condition matches evidence"""
        # Simple condition evaluation
        # In production, use a proper expression evaluator
        if "==" in condition:
            field, value = condition.split("==")
            return str(evidence.value) == value.strip()
        elif "is null" in condition.lower():
            return evidence.value is None
        elif "count == 0" in condition:
            return evidence.value == 0 or evidence.value == [] or evidence.value is None

        return False

    def match_patterns(self, evidence_list: List[Evidence]) -> List[Hypothesis]:
        """Match collected evidence against pattern library"""
        hypotheses = []

        for pattern_id, pattern in self.patterns.items():
            score = self._calculate_pattern_score(pattern, evidence_list)
            if score > 0:
                hypotheses.append(Hypothesis(
                    pattern_id=pattern_id,
                    description=pattern.get("root_cause", {}).get("statement", ""),
                    confidence=score,
                    evidence_for=[e for e in evidence_list if e.matched],
                    evidence_against=[e for e in evidence_list if not e.matched]
                ))

        # Sort by confidence
        hypotheses.sort(key=lambda h: h.confidence, reverse=True)
        return hypotheses

    def _calculate_pattern_score(self, pattern: Dict, evidence_list: List[Evidence]) -> float:
        """Calculate confidence score for a pattern based on evidence"""
        required_evidence = pattern.get("evidence", {}).get("required", [])
        supporting_evidence = pattern.get("evidence", {}).get("supporting", [])

        total_weight = sum(e.get("weight", 1) for e in required_evidence)
        matched_weight = 0

        for req in required_evidence:
            for evidence in evidence_list:
                if evidence.source == req.get("source") and evidence.matched:
                    matched_weight += req.get("weight", 1)
                    break

        if total_weight == 0:
            return 0

        return matched_weight / total_weight

    def generate_resolution(self, hypothesis: Hypothesis) -> Resolution:
        """Generate resolution steps from matched pattern"""
        pattern = self.patterns.get(hypothesis.pattern_id, {})
        resolution_config = pattern.get("resolution", {})

        return Resolution(
            root_cause=hypothesis.description,
            explanation=pattern.get("root_cause", {}).get("explanation", ""),
            steps=resolution_config.get("steps", []),
            email_template=pattern.get("email_template"),
            estimated_time=resolution_config.get("estimated_time", "Unknown"),
            human_approval_required=resolution_config.get("human_approval_required", True)
        )
```

#### 5.1.2 OTR RCA Skill Implementation

```python
# building_blocks/otr_rca_skill.py
"""
OTR RCA Skill - Handles ground transportation tracking issues.
Covers 85+ patterns including ELD, GPS, network, and carrier issues.
"""

import time
from typing import Dict, List
from skill_base import (
    Skill, InvestigationResult, Evidence, Hypothesis,
    Resolution, ConfidenceLevel
)

# Data source clients (would import from MCP clients in production)
from data_sources import (
    TrackingAPIClient,
    CompanyAPIClient,
    SigNozClient,
    RedshiftClient
)

class OTRRCASkill(Skill):
    """
    OTR (Over-the-Road) RCA Skill for ground transportation issues.
    """

    def __init__(self, skill_dir: str = "skills/otr-rca"):
        super().__init__(skill_dir)

        # Initialize data source clients
        self.tracking_api = TrackingAPIClient()
        self.company_api = CompanyAPIClient()
        self.signoz = SigNozClient()
        self.redshift = RedshiftClient()

        # Track data sources queried
        self.data_sources_queried = []

    def investigate(self, context: Dict) -> InvestigationResult:
        """
        Main investigation method for OTR tracking issues.

        Args:
            context: {
                "ticket_id": "SF-12345",
                "load_number": "U110123982",
                "shipper": "walmart",
                "carrier": "crst-logistics",
                "description": "Load not tracking..."
            }

        Returns:
            InvestigationResult with root cause and resolution
        """
        start_time = time.time()
        self.data_sources_queried = []

        # Step 1: Execute decision tree
        primary_hypothesis = self.execute_decision_tree(context)

        # Step 2: Match additional patterns for confidence boost
        all_hypotheses = self.match_patterns(primary_hypothesis.evidence_for)

        # Insert primary hypothesis at top if not already there
        if primary_hypothesis.pattern_id != "UNKNOWN":
            all_hypotheses.insert(0, primary_hypothesis)

        # Step 3: Select best hypothesis
        best_hypothesis = all_hypotheses[0] if all_hypotheses else primary_hypothesis

        # Step 4: Generate resolution
        resolution = self.generate_resolution(best_hypothesis)

        # Step 5: Build result
        investigation_time = time.time() - start_time

        return InvestigationResult(
            ticket_id=context.get("ticket_id", ""),
            load_number=context.get("load_number", ""),
            confidence=best_hypothesis.confidence,
            confidence_level=best_hypothesis.confidence_level,
            root_cause=best_hypothesis.description,
            hypotheses=all_hypotheses[:5],  # Top 5 hypotheses
            resolution=resolution,
            evidence_summary=best_hypothesis.evidence_for,
            investigation_time_seconds=investigation_time,
            data_sources_queried=self.data_sources_queried,
            skill_version=self.version
        )

    def _execute_step(self, step_config: Dict, context: Dict) -> Evidence:
        """Execute a single investigation step"""
        data_source = step_config.get("data_source", "")
        query = step_config.get("query", "")

        self.data_sources_queried.append(data_source)

        if data_source == "Tracking API":
            return self._query_tracking_api(query, context)
        elif data_source == "Company API":
            return self._query_company_api(query, context)
        elif data_source == "SigNoz Logs":
            return self._query_signoz(query, context)
        elif data_source == "Redshift":
            return self._query_redshift(query, context)
        else:
            return Evidence(
                source=data_source,
                field="unknown",
                value=None,
                condition="",
                matched=False,
                weight=0
            )

    def _query_tracking_api(self, query: str, context: Dict) -> Evidence:
        """Query Tracking API for load data"""
        load_number = context.get("load_number", "")

        try:
            load_data = self.tracking_api.get_load(load_number)

            return Evidence(
                source="Tracking API",
                field="load",
                value=load_data,
                condition="load exists",
                matched=load_data is not None,
                weight=5,
                raw_data=load_data or {}
            )
        except Exception as e:
            return Evidence(
                source="Tracking API",
                field="load",
                value=None,
                condition="load exists",
                matched=False,
                weight=5,
                raw_data={"error": str(e)}
            )

    def _query_company_api(self, query: str, context: Dict) -> Evidence:
        """Query Company API for network relationships"""
        shipper = context.get("shipper", "")
        carrier = context.get("carrier", "")

        try:
            relationships = self.company_api.get_relationships(
                shipper_id=shipper,
                carrier_id=carrier
            )

            if not relationships:
                return Evidence(
                    source="Company API",
                    field="relationships",
                    value=0,
                    condition="relationships.count == 0",
                    matched=True,
                    weight=10,  # Critical evidence
                    raw_data={"relationships": []}
                )

            rel = relationships[0]

            if not rel.get("is_active", False):
                return Evidence(
                    source="Company API",
                    field="relationships[0].is_active",
                    value=False,
                    condition="relationship inactive",
                    matched=True,
                    weight=8,
                    raw_data=rel
                )

            if not rel.get("eld_enabled", True):
                return Evidence(
                    source="Company API",
                    field="relationships[0].eld_enabled",
                    value=False,
                    condition="eld_enabled == false",
                    matched=True,
                    weight=10,
                    raw_data=rel
                )

            return Evidence(
                source="Company API",
                field="relationships",
                value=rel,
                condition="relationship active and eld enabled",
                matched=False,  # No issue found
                weight=5,
                raw_data=rel
            )

        except Exception as e:
            return Evidence(
                source="Company API",
                field="relationships",
                value=None,
                condition="error",
                matched=False,
                weight=0,
                raw_data={"error": str(e)}
            )

    def _query_signoz(self, query: str, context: Dict) -> Evidence:
        """Query SigNoz for log analysis"""
        carrier = context.get("carrier", "")
        load_number = context.get("load_number", "")

        try:
            logs = self.signoz.query_logs(
                service="tracking-worker-global",
                filters={
                    "carrier_code": carrier,
                    "load_number": load_number,
                    "level": "error"
                },
                time_range="24h"
            )

            # Check for specific error patterns
            for log in logs:
                if "GPS timestamp is null" in log.get("message", ""):
                    return Evidence(
                        source="SigNoz Logs",
                        field="gps_timestamp_error",
                        value="GPS timestamp is null",
                        condition="gps timestamp null",
                        matched=True,
                        weight=8,
                        raw_data=log
                    )

                if "No ELD device assigned" in log.get("message", ""):
                    return Evidence(
                        source="SigNoz Logs",
                        field="eld_device_error",
                        value="No ELD device assigned",
                        condition="no eld device",
                        matched=True,
                        weight=9,
                        raw_data=log
                    )

            return Evidence(
                source="SigNoz Logs",
                field="error_logs",
                value=logs,
                condition="no specific errors",
                matched=False,
                weight=3,
                raw_data={"log_count": len(logs)}
            )

        except Exception as e:
            return Evidence(
                source="SigNoz Logs",
                field="error_logs",
                value=None,
                condition="error",
                matched=False,
                weight=0,
                raw_data={"error": str(e)}
            )

    def _query_redshift(self, query: str, context: Dict) -> Evidence:
        """Query Redshift for historical data"""
        load_number = context.get("load_number", "")

        try:
            validation_data = self.redshift.query(
                f"""
                SELECT * FROM load_validation_data_mart
                WHERE load_number = '{load_number}'
                ORDER BY processed_at DESC
                LIMIT 10
                """
            )

            return Evidence(
                source="Redshift",
                field="validation_data",
                value=validation_data,
                condition="validation records found",
                matched=len(validation_data) > 0,
                weight=5,
                raw_data={"records": validation_data}
            )

        except Exception as e:
            return Evidence(
                source="Redshift",
                field="validation_data",
                value=None,
                condition="error",
                matched=False,
                weight=0,
                raw_data={"error": str(e)}
            )


# Example usage
if __name__ == "__main__":
    skill = OTRRCASkill()

    result = skill.investigate({
        "ticket_id": "SF-12345",
        "load_number": "U110123982",
        "shipper": "walmart",
        "carrier": "crst-logistics",
        "description": "Load not tracking, no updates since yesterday"
    })

    print(f"Root Cause: {result.root_cause}")
    print(f"Confidence: {result.confidence:.0%}")
    print(f"Investigation Time: {result.investigation_time_seconds:.1f}s")
    print(f"Data Sources: {result.data_sources_queried}")
```

#### 5.1.3 Skills Router

```python
# building_blocks/skills_router.py
"""
Skills Router - Routes incoming requests to appropriate skills.
Solves the "10-12 domain routing problem" through hierarchical classification.
"""

import re
import yaml
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

@dataclass
class RoutingDecision:
    """Result of routing decision"""
    skill_name: str
    confidence: float
    mode: str
    category: str
    reasoning: str

class SkillsRouter:
    """
    Routes incoming support tickets to the appropriate skill.

    Usage:
        router = SkillsRouter("config/router_config.yaml")
        decision = router.route({
            "description": "Load U123 not tracking",
            "shipper": "walmart"
        })
        print(f"Route to: {decision.skill_name}")
    """

    def __init__(self, config_path: str):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for faster matching"""
        # Mode detection patterns
        self.mode_patterns = {}
        for rule in self.config["router"]["mode_detection"]["rules"]:
            pattern = rule["pattern"]
            mode = rule["mode"]
            self.mode_patterns[mode] = re.compile(pattern, re.IGNORECASE)

        # Category patterns per mode
        self.category_patterns = {}
        for mode, rules in self.config["router"]["category_detection"].items():
            self.category_patterns[mode] = []
            for rule in rules:
                self.category_patterns[mode].append({
                    "pattern": re.compile(rule["pattern"], re.IGNORECASE),
                    "category": rule["category"],
                    "skill": rule["skill"]
                })

    def route(self, context: Dict) -> RoutingDecision:
        """
        Route a support ticket to the appropriate skill.

        Args:
            context: Dict with at least "description" field

        Returns:
            RoutingDecision with skill name and confidence
        """
        description = context.get("description", "")

        # Step 1: Detect transport mode
        mode, mode_confidence = self._detect_mode(description)

        # Step 2: Detect issue category
        category, skill, category_confidence = self._detect_category(
            description, mode
        )

        # Step 3: Calculate overall confidence
        overall_confidence = (mode_confidence + category_confidence) / 2

        # Check thresholds
        thresholds = self.config["router"]["confidence"]

        if overall_confidence < thresholds["reject_threshold"]:
            return RoutingDecision(
                skill_name="human_review",
                confidence=overall_confidence,
                mode=mode,
                category=category,
                reasoning="Confidence too low for automated routing"
            )

        return RoutingDecision(
            skill_name=skill,
            confidence=overall_confidence,
            mode=mode,
            category=category,
            reasoning=f"Matched mode={mode}, category={category}"
        )

    def _detect_mode(self, text: str) -> Tuple[str, float]:
        """Detect transport mode from text"""
        for mode, pattern in self.mode_patterns.items():
            if pattern.search(text):
                return mode, 0.9

        # Default mode
        default_mode = self.config["router"]["mode_detection"]["default"]
        return default_mode, 0.6

    def _detect_category(
        self, text: str, mode: str
    ) -> Tuple[str, str, float]:
        """Detect issue category within a mode"""
        patterns = self.category_patterns.get(mode, [])

        for rule in patterns:
            if rule["pattern"].search(text):
                return rule["category"], rule["skill"], 0.85

        # Fallback to generic skill for mode
        skills = self.config["router"]["skills"]
        for skill_name, skill_config in skills.items():
            if mode.lower() in skill_name.lower():
                return "UNKNOWN", skill_name, 0.5

        return "UNKNOWN", "human_review", 0.4

    def get_skill(self, skill_name: str):
        """Get skill instance by name"""
        # Import dynamically to avoid circular imports
        if skill_name == "otr-rca-skill":
            from otr_rca_skill import OTRRCASkill
            return OTRRCASkill()
        elif skill_name == "ocean-tracking-skill":
            from ocean_tracking_skill import OceanTrackingSkill
            return OceanTrackingSkill()
        elif skill_name == "dy-ops-skill":
            from dy_ops_skill import DYOpsSkill
            return DYOpsSkill()
        else:
            raise ValueError(f"Unknown skill: {skill_name}")

    def investigate(self, context: Dict):
        """
        Route and investigate in one call.
        Convenience method that combines routing and investigation.
        """
        decision = self.route(context)

        if decision.skill_name == "human_review":
            return {
                "status": "needs_human_review",
                "routing": decision,
                "result": None
            }

        skill = self.get_skill(decision.skill_name)
        result = skill.investigate(context)

        return {
            "status": "completed",
            "routing": decision,
            "result": result
        }


# Example usage
if __name__ == "__main__":
    router = SkillsRouter("config/router_config.yaml")

    # Test OTR routing
    decision = router.route({
        "description": "Load U110123982 not tracking, no ELD updates",
        "shipper": "walmart",
        "carrier": "crst-logistics"
    })
    print(f"Route to: {decision.skill_name} (confidence: {decision.confidence:.0%})")

    # Test Ocean routing
    decision = router.route({
        "description": "Container MSCU1234567 no vessel events",
        "shipper": "global-foods"
    })
    print(f"Route to: {decision.skill_name} (confidence: {decision.confidence:.0%})")
```

#### 5.1.4 Multi-Agent Investigation Flow

```python
# building_blocks/multi_agent_flow.py
"""
Multi-Agent Investigation Flow
Implements the UX mock pattern: Identifier --> Tracking API --> Redshift --> Hypothesis --> Synthesis
"""

import asyncio
from dataclasses import dataclass
from typing import List, Dict, Callable, Any
from enum import Enum

class AgentStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AgentStep:
    """Single agent step in investigation"""
    name: str
    status: AgentStatus
    result: Any = None
    error: str = None
    duration_seconds: float = 0.0

@dataclass
class InvestigationFlow:
    """Complete investigation flow with all agent steps"""
    steps: List[AgentStep]
    total_duration_seconds: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "steps": [
                {
                    "name": s.name,
                    "status": s.status.value,
                    "duration": s.duration_seconds
                }
                for s in self.steps
            ],
            "total_duration": self.total_duration_seconds
        }

class MultiAgentInvestigator:
    """
    Orchestrates multi-agent investigation following UX mock pattern.

    Agents run in this order:
    1. Identifier Agent - Extract load/container/carrier IDs
    2. Tracking API Agent - Check load existence and status
    3. Redshift Agent - Query historical data
    4. Hypothesis Agent - Form hypotheses from evidence
    5. Synthesis Agent - Determine root cause

    Supports both sequential and parallel execution.
    """

    def __init__(self):
        self.agents = [
            ("Identifier Agent", self._run_identifier_agent),
            ("Tracking API Agent", self._run_tracking_api_agent),
            ("Redshift Agent", self._run_redshift_agent),
            ("Hypothesis Agent", self._run_hypothesis_agent),
            ("Synthesis Agent", self._run_synthesis_agent),
        ]

    async def investigate(
        self,
        context: Dict,
        progress_callback: Callable[[AgentStep], None] = None
    ) -> InvestigationFlow:
        """
        Run full investigation with progress updates.

        Args:
            context: Investigation context (load_number, description, etc.)
            progress_callback: Optional callback for real-time progress updates

        Returns:
            InvestigationFlow with all agent results
        """
        steps = []
        accumulated_evidence = {}
        start_time = asyncio.get_event_loop().time()

        for agent_name, agent_func in self.agents:
            step = AgentStep(name=agent_name, status=AgentStatus.RUNNING)

            # Notify progress
            if progress_callback:
                progress_callback(step)

            step_start = asyncio.get_event_loop().time()

            try:
                # Run agent
                result = await agent_func(context, accumulated_evidence)
                accumulated_evidence[agent_name] = result

                step.status = AgentStatus.COMPLETED
                step.result = result

            except Exception as e:
                step.status = AgentStatus.FAILED
                step.error = str(e)

            step.duration_seconds = asyncio.get_event_loop().time() - step_start
            steps.append(step)

            # Notify completion
            if progress_callback:
                progress_callback(step)

            # Stop if agent failed (optional - could continue)
            if step.status == AgentStatus.FAILED:
                break

        total_duration = asyncio.get_event_loop().time() - start_time

        return InvestigationFlow(
            steps=steps,
            total_duration_seconds=total_duration
        )

    async def _run_identifier_agent(
        self, context: Dict, evidence: Dict
    ) -> Dict:
        """Extract identifiers from ticket description"""
        # In production, use LLM for extraction
        # Here we use simple regex patterns
        import re

        description = context.get("description", "")

        identifiers = {
            "load_number": None,
            "container_number": None,
            "tracking_id": None,
            "shipper": context.get("shipper"),
            "carrier": context.get("carrier"),
        }

        # Extract load number (U followed by digits)
        load_match = re.search(r'U\d{9,}', description)
        if load_match:
            identifiers["load_number"] = load_match.group()

        # Extract container number (4 letters + 7 digits)
        container_match = re.search(r'[A-Z]{4}\d{7}', description)
        if container_match:
            identifiers["container_number"] = container_match.group()

        return identifiers

    async def _run_tracking_api_agent(
        self, context: Dict, evidence: Dict
    ) -> Dict:
        """Query Tracking API for load/container status"""
        identifiers = evidence.get("Identifier Agent", {})
        load_number = identifiers.get("load_number") or context.get("load_number")

        # Simulate API call (in production, use actual client)
        await asyncio.sleep(0.5)  # Simulated latency

        return {
            "load_exists": True,
            "load_status": "IN_TRANSIT",
            "last_position": None,
            "carrier_assigned": True,
            "eld_enabled": False  # This will trigger ELD pattern
        }

    async def _run_redshift_agent(
        self, context: Dict, evidence: Dict
    ) -> Dict:
        """Query Redshift for historical data"""
        identifiers = evidence.get("Identifier Agent", {})

        # Simulate query (in production, use actual client)
        await asyncio.sleep(0.3)

        return {
            "validation_records": 2,
            "last_error": "ELD not configured",
            "network_relationship": "active",
            "relationship_eld_enabled": False
        }

    async def _run_hypothesis_agent(
        self, context: Dict, evidence: Dict
    ) -> Dict:
        """Form hypotheses based on collected evidence"""
        tracking_data = evidence.get("Tracking API Agent", {})
        redshift_data = evidence.get("Redshift Agent", {})

        hypotheses = []

        # Check for ELD not enabled pattern
        if not tracking_data.get("eld_enabled") or not redshift_data.get("relationship_eld_enabled"):
            hypotheses.append({
                "pattern_id": "ELD_NOT_ENABLED_NETWORK",
                "description": "ELD not enabled at network relationship level",
                "confidence": 0.92,
                "evidence": [
                    "Load exists in system",
                    "Carrier has ELD capability",
                    "Network relationship ELD disabled"
                ]
            })

        # Check for network missing pattern
        if redshift_data.get("network_relationship") == "missing":
            hypotheses.append({
                "pattern_id": "NETWORK_RELATIONSHIP_MISSING",
                "description": "Network relationship missing between shipper and carrier",
                "confidence": 0.95,
                "evidence": [
                    "No carrier-shipper relationship found"
                ]
            })

        return {"hypotheses": hypotheses}

    async def _run_synthesis_agent(
        self, context: Dict, evidence: Dict
    ) -> Dict:
        """Determine root cause and generate resolution"""
        hypothesis_data = evidence.get("Hypothesis Agent", {})
        hypotheses = hypothesis_data.get("hypotheses", [])

        if not hypotheses:
            return {
                "root_cause": "Unable to determine root cause",
                "confidence": 0.5,
                "resolution": {
                    "steps": ["Escalate to engineering team"],
                    "human_approval_required": True
                }
            }

        # Select highest confidence hypothesis
        best = max(hypotheses, key=lambda h: h["confidence"])

        # Generate resolution based on pattern
        resolution = self._get_resolution_for_pattern(best["pattern_id"])

        return {
            "root_cause": best["description"],
            "confidence": best["confidence"],
            "pattern_id": best["pattern_id"],
            "evidence": best["evidence"],
            "resolution": resolution
        }

    def _get_resolution_for_pattern(self, pattern_id: str) -> Dict:
        """Get resolution steps for a pattern"""
        resolutions = {
            "ELD_NOT_ENABLED_NETWORK": {
                "steps": [
                    {
                        "step": 1,
                        "action": "Enable ELD in FourKites Connect",
                        "button": "Open Connect"
                    },
                    {
                        "step": 2,
                        "action": "Verify carrier ELD devices are active",
                        "button": "Check Config"
                    },
                    {
                        "step": 3,
                        "action": "Monitor for position updates",
                        "button": "View Timeline"
                    }
                ],
                "email_template": "eld_enablement_request",
                "estimated_time": "15 minutes",
                "human_approval_required": True
            },
            "NETWORK_RELATIONSHIP_MISSING": {
                "steps": [
                    {
                        "step": 1,
                        "action": "Create network relationship in FourKites Connect",
                        "button": "Create Relationship"
                    },
                    {
                        "step": 2,
                        "action": "Configure ELD settings for relationship",
                        "button": "Configure ELD"
                    }
                ],
                "email_template": None,
                "estimated_time": "20 minutes",
                "human_approval_required": True
            }
        }

        return resolutions.get(pattern_id, {
            "steps": [{"step": 1, "action": "Manual investigation required"}],
            "human_approval_required": True
        })


# Example usage with progress callback
async def main():
    investigator = MultiAgentInvestigator()

    def on_progress(step: AgentStep):
        status_icon = {
            AgentStatus.PENDING: "⏸️",
            AgentStatus.RUNNING: "🔄",
            AgentStatus.COMPLETED: "✓",
            AgentStatus.FAILED: "✗"
        }
        print(f"{status_icon[step.status]} {step.name}")

    result = await investigator.investigate(
        context={
            "ticket_id": "SF-12345",
            "load_number": "U110123982",
            "shipper": "walmart",
            "carrier": "crst-logistics",
            "description": "Load U110123982 not tracking, no ELD updates"
        },
        progress_callback=on_progress
    )

    print(f"\nInvestigation complete in {result.total_duration_seconds:.1f}s")

    # Get final result
    synthesis = result.steps[-1].result
    print(f"\nRoot Cause: {synthesis['root_cause']}")
    print(f"Confidence: {synthesis['confidence']:.0%}")


if __name__ == "__main__":
    asyncio.run(main())
```

---

## Part 6: FourSight/Cassie Integration Plan

### 6.1 Integration Architecture

```
                    CASSIE AGENT (FourSight)
                           │
                           │ Salesforce ticket intake
                           │
                           v
                  ┌─────────────────┐
                  │   CASSIE LLM    │
                  │   Router        │
                  │                 │
                  │  - Intent       │
                  │  - Sentiment    │
                  │  - Priority     │
                  └────────┬────────┘
                           │
                           │ If category = "TRACKING_ISSUE"
                           │
                           v
              ┌────────────────────────────┐
              │    SKILLS ROUTER API       │
              │                            │
              │  POST /api/v1/investigate  │
              │  {                         │
              │    "ticket_id": "SF-123",  │
              │    "description": "...",   │
              │    "shipper": "walmart",   │
              │    "carrier": "crst"       │
              │  }                         │
              └────────────┬───────────────┘
                           │
                           │ Returns InvestigationResult
                           │
                           v
              ┌────────────────────────────┐
              │    CASSIE RESPONSE         │
              │                            │
              │  - Includes root cause     │
              │  - Includes confidence     │
              │  - Includes resolution     │
              │  - Shows evidence          │
              └────────────────────────────┘
```

### 6.2 API Contract

```yaml
# api/skills_api.yaml
openapi: "3.0.0"
info:
  title: "Skills Router API"
  version: "1.0.0"
  description: "API for integrating Skills-based RCA with Cassie/FourSight"

paths:
  /api/v1/investigate:
    post:
      summary: "Investigate a support ticket"
      description: "Routes ticket to appropriate skill and returns investigation result"
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - ticket_id
                - description
              properties:
                ticket_id:
                  type: string
                  description: "Salesforce case ID"
                description:
                  type: string
                  description: "Issue description from ticket"
                shipper:
                  type: string
                  description: "Shipper company permalink"
                carrier:
                  type: string
                  description: "Carrier company permalink"
                load_number:
                  type: string
                  description: "Load number if known"
                container_number:
                  type: string
                  description: "Container number if known"
                mode:
                  type: string
                  enum: [GROUND_OTR, OCEAN, DRAYAGE, AIR]
                  description: "Transport mode hint (optional)"
      responses:
        "200":
          description: "Investigation result"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/InvestigationResult"
        "202":
          description: "Investigation in progress (async)"
          content:
            application/json:
              schema:
                type: object
                properties:
                  investigation_id:
                    type: string
                  status_url:
                    type: string
        "400":
          description: "Invalid request"
        "500":
          description: "Investigation failed"

  /api/v1/investigate/{investigation_id}/status:
    get:
      summary: "Get investigation status (async flow)"
      parameters:
        - name: investigation_id
          in: path
          required: true
          schema:
            type: string
      responses:
        "200":
          description: "Investigation status"
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/InvestigationStatus"

components:
  schemas:
    InvestigationResult:
      type: object
      properties:
        ticket_id:
          type: string
        load_number:
          type: string
        confidence:
          type: number
          format: float
          minimum: 0
          maximum: 1
        confidence_level:
          type: string
          enum: [high, medium, low]
        root_cause:
          type: string
        hypotheses:
          type: array
          items:
            $ref: "#/components/schemas/Hypothesis"
        resolution:
          $ref: "#/components/schemas/Resolution"
        evidence_summary:
          type: array
          items:
            $ref: "#/components/schemas/Evidence"
        investigation_time_seconds:
          type: number
        skill_used:
          type: string
        skill_version:
          type: string

    Hypothesis:
      type: object
      properties:
        pattern_id:
          type: string
        description:
          type: string
        confidence:
          type: number
        evidence_for:
          type: array
          items:
            type: string

    Resolution:
      type: object
      properties:
        root_cause:
          type: string
        explanation:
          type: string
        steps:
          type: array
          items:
            type: object
            properties:
              step:
                type: integer
              action:
                type: string
              button:
                type: string
              button_url:
                type: string
        email_template:
          type: object
          nullable: true
        estimated_time:
          type: string
        human_approval_required:
          type: boolean

    Evidence:
      type: object
      properties:
        source:
          type: string
        field:
          type: string
        value:
          type: string
        matched:
          type: boolean
        weight:
          type: integer

    InvestigationStatus:
      type: object
      properties:
        investigation_id:
          type: string
        status:
          type: string
          enum: [pending, running, completed, failed]
        current_agent:
          type: string
        agents_completed:
          type: array
          items:
            type: string
        result:
          $ref: "#/components/schemas/InvestigationResult"
```

### 6.3 Integration Code (Cassie Side)

```python
# cassie/skills_integration.py
"""
Integration code for Cassie to call Skills Router API.
"""

import httpx
from typing import Dict, Optional

class SkillsRouterClient:
    """Client for Skills Router API"""

    def __init__(self, base_url: str = "http://skills-router.fourkites.internal"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def investigate(
        self,
        ticket_id: str,
        description: str,
        shipper: Optional[str] = None,
        carrier: Optional[str] = None,
        load_number: Optional[str] = None,
        container_number: Optional[str] = None
    ) -> Dict:
        """
        Call Skills Router to investigate a ticket.

        Returns investigation result with root cause and resolution.
        """
        payload = {
            "ticket_id": ticket_id,
            "description": description
        }

        if shipper:
            payload["shipper"] = shipper
        if carrier:
            payload["carrier"] = carrier
        if load_number:
            payload["load_number"] = load_number
        if container_number:
            payload["container_number"] = container_number

        response = await self.client.post(
            f"{self.base_url}/api/v1/investigate",
            json=payload
        )

        if response.status_code == 200:
            return response.json()
        elif response.status_code == 202:
            # Async investigation - poll for result
            return await self._poll_for_result(response.json())
        else:
            raise Exception(f"Skills API error: {response.status_code}")

    async def _poll_for_result(self, initial_response: Dict) -> Dict:
        """Poll for async investigation result"""
        import asyncio

        status_url = initial_response["status_url"]
        max_attempts = 30  # 30 seconds max

        for _ in range(max_attempts):
            response = await self.client.get(status_url)
            status = response.json()

            if status["status"] == "completed":
                return status["result"]
            elif status["status"] == "failed":
                raise Exception("Investigation failed")

            await asyncio.sleep(1)

        raise Exception("Investigation timed out")


# Usage in Cassie agent
class CassieAgent:
    """Cassie classification agent with Skills integration"""

    def __init__(self):
        self.skills_client = SkillsRouterClient()

    async def handle_ticket(self, ticket: Dict) -> Dict:
        """Handle incoming support ticket"""

        # Step 1: Classify ticket (existing Cassie logic)
        classification = self.classify(ticket)

        # Step 2: If tracking issue, use Skills Router
        if classification["category"] == "TRACKING_ISSUE":
            investigation = await self.skills_client.investigate(
                ticket_id=ticket["id"],
                description=ticket["description"],
                shipper=ticket.get("shipper"),
                carrier=ticket.get("carrier")
            )

            # Step 3: Format response
            return self._format_response(ticket, classification, investigation)

        # Other categories use existing Cassie logic
        return self._handle_other_categories(ticket, classification)

    def _format_response(
        self, ticket: Dict, classification: Dict, investigation: Dict
    ) -> Dict:
        """Format response combining Cassie classification and Skills investigation"""
        return {
            "ticket_id": ticket["id"],
            "classification": classification,

            # Skills investigation results
            "root_cause": investigation["root_cause"],
            "confidence": investigation["confidence"],
            "confidence_level": investigation["confidence_level"],

            # Resolution for agent/user
            "resolution": investigation["resolution"],

            # Evidence for transparency
            "evidence": investigation["evidence_summary"],

            # Metadata
            "skill_used": investigation["skill_used"],
            "investigation_time": investigation["investigation_time_seconds"],

            # Action recommendations
            "recommended_action": self._get_recommended_action(investigation)
        }

    def _get_recommended_action(self, investigation: Dict) -> Dict:
        """Get primary recommended action from investigation"""
        resolution = investigation.get("resolution", {})
        steps = resolution.get("steps", [])

        if steps:
            first_step = steps[0]
            return {
                "action": first_step.get("action"),
                "button": first_step.get("button"),
                "button_url": first_step.get("button_url"),
                "human_approval_required": resolution.get("human_approval_required", True)
            }

        return {
            "action": "Manual investigation required",
            "human_approval_required": True
        }
```

---

## Part 7: Implementation Roadmap

### 7.1 Phase Breakdown

| Phase | Duration | Focus | Deliverables |
|-------|----------|-------|--------------|
| **Phase 1** | Week 1-2 | Foundation | Skills framework, 1 skill (OTR), 10 patterns |
| **Phase 2** | Week 3-4 | Expansion | 2 more skills (Ocean, DY), 50 patterns total |
| **Phase 3** | Week 5-6 | Integration | Cassie API integration, UX components |
| **Phase 4** | Week 7-8 | Validation | Test against 100+ cases, tune confidence |
| **Phase 5** | Week 9-10 | Production | Deploy, monitor, iterate |

### 7.2 Detailed Task List

#### Phase 1: Foundation (Week 1-2)

| Task | Owner | Duration | Depends On |
|------|-------|----------|------------|
| **1.0 Extract pattern frequency data** | Raja/Support | 1 day | - |
| 1.1 Create skills directory structure | Raja | 1 day | - |
| 1.2 Implement Skill base class | Raja | 2 days | 1.1 |
| 1.3 Implement Skills Router | Raja | 2 days | 1.2 |
| 1.4 Shadow Prashant for OTR workflow | Raja | 1 day | - |
| 1.5 Document OTR mental model | Raja | 1 day | 1.4 |
| 1.6 Create OTR RCA Skill | Raja | 3 days | 1.2, 1.5 |
| 1.7 Create 10 initial OTR patterns (see list below) | Raja | 2 days | 1.6 |
| 1.8 Test OTR skill on 20 cases | Raja | 1 day | 1.7 |

**Task 1.0: Pattern Frequency Data Extraction**
- Query Salesforce for "Load Not Tracking" cases (category breakdown)
- Query Redshift `load_validation_data_mart` for error distribution
- Time range: Last 6 months
- Output: Validated percentages for top patterns (replacing TBD estimates)

**Task 1.7: Initial 10 OTR Patterns**
The following 10 patterns will be implemented first (covering ~60% of "Load Not Tracking" cases):

| # | Pattern ID | Description | Est. Frequency |
|---|------------|-------------|----------------|
| 1 | `ELD_NOT_ENABLED_NETWORK` | ELD disabled at network relationship level | ~5.2% |
| 2 | `NETWORK_RELATIONSHIP_MISSING` | No shipper-carrier relationship exists | ~7.7% |
| 3 | `LOAD_NOT_FOUND` | Load number not in system | ~4.8% |
| 4 | `CARRIER_API_DOWN` | Carrier ELD provider API unavailable | ~3.0% |
| 5 | `GPS_NULL_TIMESTAMPS` | Carrier sending null/invalid GPS timestamps | ~3.5% |
| 6 | `DEVICE_CONFIG_WRONG` | Wrong tracking method (Truck vs Trailer mismatch) | ~2.5% |
| 7 | `CARRIER_NOT_CONFIGURED` | Carrier not set up in FourKites system | ~2.0% |
| 8 | `LATE_ASSIGNMENT` | Driver/device assigned after pickup time | ~1.5% |
| 9 | `STALE_LOCATION` | No position update in >4 hours (device offline) | ~2.8% |
| 10 | `CALLBACK_FAILURE` | Carrier webhook/callback not delivered | ~1.8% |

#### Phase 2: Expansion (Week 3-4)

| Task | Owner | Duration | Depends On |
|------|-------|----------|------------|
| 2.1 Shadow Surya for Ocean workflow | Raja | 1 day | - |
| 2.2 Document Ocean mental model | Raja | 1 day | 2.1 |
| 2.3 Create Ocean Tracking Skill | Raja/Arpit | 3 days | 2.2 |
| 2.4 Create 20 Ocean patterns | Raja/Arpit | 2 days | 2.3 |
| 2.5 Shadow Priya for DY workflow | Raja | 1 day | - |
| 2.6 Create DY Ops Skill | Raja/Arpit | 2 days | 2.5 |
| 2.7 Create 20 DY patterns | Raja/Arpit | 2 days | 2.6 |
| 2.8 Validate all skills on test cases | Raja | 2 days | 2.4, 2.7 |

#### Phase 3: Integration (Week 5-6)

| Task | Owner | Duration | Depends On |
|------|-------|----------|------------|
| 3.1 Design Skills API contract | Raja/Arpit | 1 day | Phase 2 |
| 3.2 Implement Skills Router API | Arpit team | 3 days | 3.1 |
| 3.3 Create Cassie integration client | Arpit team | 2 days | 3.2 |
| 3.4 Implement multi-agent flow | Raja | 3 days | 3.2 |
| 3.5 Create UX components (following mock - see RCA_UX_ANALYSIS.md) | Arpit team | 4 days | 3.4 |
| 3.6 Integration testing | Both | 2 days | 3.3, 3.5 |

#### Phase 4: Validation (Week 7-8)

| Task | Owner | Duration | Depends On |
|------|-------|----------|------------|
| 4.1 Collect 100+ test cases | Support team | 2 days | - |
| 4.2 Run all skills against test cases | Raja | 3 days | 4.1 |
| 4.3 Measure accuracy per pattern | Raja | 2 days | 4.2 |
| 4.4 Tune confidence thresholds | Raja/Arpit | 2 days | 4.3 |
| 4.5 Add patterns for missed cases | Raja | 3 days | 4.3 |
| 4.6 Re-validate | Raja | 2 days | 4.5 |

**Task 4.1: Test Case Collection Details**
- **Source:** Salesforce export (Support team: Priya/Hiran will provide)
- **Category:** "Load Not Tracking" cases
- **Date Range:** October - December 2025 (3 months of recent data)
- **Minimum Count:** 100+ cases with known resolutions
- **Format:** CSV with fields: case_id, load_number, shipper, carrier, description, root_cause, resolution, resolution_time
- **Stratification:** Include mix across all 10 initial patterns to ensure coverage

#### Phase 5: Production (Week 9-10)

| Task | Owner | Duration | Depends On |
|------|-------|----------|------------|
| 5.1 Deploy Skills Router service | Arpit team | 2 days | Phase 4 |
| 5.2 Connect to Cassie production | Arpit team | 1 day | 5.1 |
| 5.3 Monitor and alert setup | Arpit team | 1 day | 5.2 |
| 5.4 Gradual rollout (10% -> 50% -> 100%) | Both | 5 days | 5.3 |
| 5.5 Support team training | Raja | 2 days | 5.4 |
| 5.6 Handoff documentation | Raja | 2 days | 5.5 |

---

## Part 8: Risk Identification and Mitigation

### 8.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Pattern coverage gaps** | High | Medium | Start with top 20 patterns (80% of cases), iterate |
| **Confidence scoring accuracy** | Medium | High | Validate on 100+ cases, tune thresholds |
| **Data source latency** | Medium | Medium | Parallel queries, timeouts, caching |
| **LLM extraction errors** | Low | Medium | Fall back to regex patterns, human review |

### 8.2 Organizational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| **Support team adoption** | Medium | High | Involve Surya/Prashant from day 1 |
| **Knowledge extraction delays** | Medium | Medium | Schedule dedicated shadow sessions |
| **Integration timeline slip** | Medium | Medium | Decouple Skills from Cassie initially |

### 8.3 Mitigation Details

**Pattern Coverage Gaps:**
- Priority order: Network missing (7.7%), ELD not enabled (5.2%), Load not found (4.8%)
- Track "unmatched" cases in production
- Weekly pattern review to add new patterns

**Confidence Scoring:**
- Start conservative (threshold=0.90 for auto-resolve)
- Measure human override rate
- Lower threshold as accuracy proven

**Data Source Latency:**
```python
# Parallel query with timeout
async def query_all_sources(context, timeout=10.0):
    tasks = [
        asyncio.wait_for(tracking_api.get_load(...), timeout),
        asyncio.wait_for(company_api.get_relationships(...), timeout),
        asyncio.wait_for(signoz.query_logs(...), timeout),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    # Handle partial results if some timed out
```

---

## Part 9: Verification Steps

### 9.1 Acceptance Test Plan

| Test | Pass Criteria |
|------|---------------|
| **Skills Router routes correctly** | 95% accuracy on 100 sample tickets |
| **OTR Skill matches patterns** | 85% accuracy on OTR test cases |
| **Ocean Skill matches patterns** | 85% accuracy on Ocean test cases |
| **Multi-agent flow completes** | <10 seconds for 95% of investigations |
| **Cassie integration works** | End-to-end test passes |
| **UX matches mock** | All 5 UX elements present (see UX mock reference below) |

**UX Mock Verification Reference:** `/Users/msp.raja/rca-agent-project/fourkites-skills-academy/docs/RCA_UX_ANALYSIS.md`

The 5 UX elements that must be present (from the mock):
1. **Confidence Score** (e.g., "92%") - Transparent accuracy indication
2. **Root Cause Card** - Pattern-specific diagnosis with explanation
3. **Recommended Actions** - 1-4 steps with action buttons
4. **Multi-Agent Progress** - Real-time investigation flow visualization
5. **Email Preview** - Human-in-the-loop approval before carrier contact

### 9.2 Performance Benchmarks

| Metric | Target | Measurement |
|--------|--------|-------------|
| Investigation time | < 10 seconds | Median of 100 runs |
| Confidence accuracy | > 85% | Validated against human diagnosis |
| Pattern match rate | > 90% | % of cases matching a known pattern |
| Human override rate | < 15% | % of agent recommendations changed by human |

### 9.3 Production Readiness Checklist

- [ ] All 85+ OTR patterns documented
- [ ] 40+ Ocean patterns documented
- [ ] 25+ DY patterns documented
- [ ] Skills Router deployed and monitored
- [ ] Cassie integration tested end-to-end
- [ ] Support team trained on new workflow
- [ ] Rollback plan documented
- [ ] Performance alerts configured

---

## Part 10: Success Metrics

### 10.1 Target Outcomes

| Metric | Current | Target | Timeline |
|--------|---------|--------|----------|
| L1 automation rate | 0% | 60% | 3 months |
| Time to diagnosis | 30-45 min | 2-5 min | 3 months |
| Pattern coverage | 0 patterns | 85+ patterns | 2 months |
| Human override rate | N/A | < 15% | 3 months |

### 10.2 Measurement Plan

**Weekly:**
- Pattern match rate
- Average investigation time
- Human override count

**Monthly:**
- Accuracy validation (sample 50 cases)
- New patterns added
- Support team satisfaction survey

---

## Conclusion

This plan provides Arpit's team with:

1. **Skills-empowered architecture** that solves the routing/scaling problem
2. **Knowledge extraction templates** to capture support team expertise
3. **Pattern library structure** supporting 85+ subcategories
4. **Building blocks** (working code) that can be extended
5. **FourSight/Cassie integration path** preserving existing investments

The approach follows the UX mock exactly: confidence scores, multi-agent investigation flow, human-in-the-loop approval.

**Next Step:** Run `/oh-my-claudecode:start-work rca-skills-platform-architecture` to begin implementation.

---

**PLAN_READY: .omc/plans/rca-skills-platform-architecture.md**
