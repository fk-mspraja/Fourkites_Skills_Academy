# Rewind-App vs Skills Library Comparison

**Date:** Jan 27, 2026
**Author:** MSP Raja + Claude Sonnet 4.5

## Executive Summary

Arpit's **rewind-app** and our **Skills Library** are solving the same problem with highly complementary approaches. Arpit has built more mature operational playbooks for OTR domain, while we built knowledge extraction templates and architectural framework. **We should merge these efforts.**

---

## Side-by-Side Comparison

### Architecture

| Component | Rewind-App (Arpit) | Skills Library (MSP) |
|-----------|-------------------|----------------------|
| **Investigation Workflows** | Playbooks (step-by-step with branching) | Skills (agent-orchestrated investigation) |
| **Diagnostic Rules** | Patterns (evidence rules with weights) | Patterns (embedded in SKILL.yaml) |
| **Evidence Scoring** | confirms/rejects with weights | confidence scoring with thresholds |
| **Investigation Flow** | Sequential steps with outcomes | 6 parallel/sequential agents |
| **Root Cause Resolution** | Remediation templates with priorities | Resolution steps per pattern |
| **UI** | ✅ http://rewind.fourkites.internal/ | ❌ None |
| **Knowledge Extraction** | ❌ None | ✅ 2,850+ lines of templates |
| **Framework** | Backend implementation | skill_base.py, skills_router.py, multi_agent_investigator.py |
| **Test Cases** | Production data | ✅ Test case YAML files with expected outcomes |

---

## Detailed Comparison

### 1. Playbooks vs Skills

**Arpit's Playbooks:**
```yaml
# callback_failure.yaml (476 lines)
playbook_id: "callback_failure"
triggers:
  categories: ["CALLBACK_FAILURE", "WEBHOOK_FAILURE"]
  keywords: ["callback not working", "webhook failure"]

steps:
  - step: 1
    id: "check_load_exists"
    action: "api_call"
    endpoint: "search_load"
    outcomes:
      - condition: "status == 200"
        result: "LOAD_FOUND"
        next_step: 2
      - condition: "status == 404"
        result: "LOAD_NOT_FOUND"
        action: "STOP"
```

**Our Skills:**
```yaml
# SKILL.yaml (703 lines)
skill_id: "otr-rca"
trigger_keywords:
  - "not tracking"
  - "no updates"
  - "ELD not enabled"

investigation_capabilities:
  - tracking_api_search
  - redshift_query
  - athena_query
  - network_api_check
  - signoz_logs

patterns:
  - pattern_id: "ELD_NOT_ENABLED"
    confidence_threshold: 0.85
```

**Analysis:**
- Arpit's playbooks are **more operational** - explicit step-by-step logic
- Our skills are **more abstract** - define what to investigate, agents decide how
- **Arpit's approach is better** for production RCA automation
- **Our approach is better** for flexibility and extensibility

**Recommendation:** Adopt Arpit's playbook structure, use our knowledge extraction to scale it to 10-12 domains.

---

### 2. Patterns

**Arpit's Patterns:**
```yaml
# webhook_5xx.yaml (232 lines)
pattern_id: "H_WEBHOOK_5XX"
category: "CALLBACK_WEBHOOK_FAILURE"

investigation_steps:
  - skill: "analyze_callbacks"
  - skill: "check_network_tracking"

evidence_rules:
  confirms:
    - condition: "ext_request_status >= 500"
      weight: 0.8
      message: "HTTP {ext_request_status} server error"

  rejects:
    - condition: "hours_since_last_success < 1"
      weight: 0.8

root_causes:
  - cause: "Customer endpoint experiencing internal errors"
    likelihood: "high"
    conditions: ["ext_request_status = 500"]

remediation:
  - action: "Notify customer of endpoint failures"
    priority: 1
    template: |
      Your webhook endpoint is returning server errors.
      HTTP Status: {ext_request_status}
      Please investigate...
```

**Our Patterns:**
```yaml
# Embedded in SKILL.yaml
patterns:
  callback_delivery_failed:
    category: "CALLBACK_FAILURE"
    evidence_checks:
      - type: athena_query
        table: callbacks_v2
        condition: error_msg IS NOT NULL
        confidence_weight: 0.90
    resolution_steps:
      - "Check customer webhook endpoint"
      - "Verify authentication"
```

**Analysis:**
- Arpit's patterns are **separate files** - better organization
- Arpit's patterns have **confirms/rejects** - bidirectional evidence
- Our patterns have **test cases** - validation framework
- Arpit has **12 patterns** already built, we only defined structure

**Recommendation:** Adopt Arpit's pattern file structure. Add our test case approach for validation.

---

### 3. Knowledge Extraction

**Arpit's Approach:**
- ❌ No formal process documented
- Mentioned: "I am planning to more focus on how support teams can easily add their skills for a specific issue"

**Our Approach:**
- ✅ Complete 2-day extraction process (2,850+ lines)
- ✅ 12-section knowledge_extraction_template.yaml
- ✅ 8 supporting guides (README, QUICK_START, VALIDATION_CHECKLIST, etc.)
- ✅ Extraction-to-skill conversion guide

**Analysis:**
- This is our **key contribution** - Arpit doesn't have this yet
- This is exactly what Arpit needs to scale to 10-12 domains
- Support teams can use our templates to create new playbooks/patterns

**Recommendation:** Integrate our knowledge extraction templates into rewind-app as a `/docs/knowledge-extraction/` directory.

---

### 4. Investigation Flow

**Arpit's Playbook Flow:**
```
Step 1: Check load exists (API call)
  ↓ (if found)
Step 2: Query ALL callbacks (Athena)
  ↓ (if callbacks exist)
Step 3: Query FAILED callbacks (Athena)
  ↓ (if failures found)
Step 4: Analyze error patterns (regex matching)
  ↓
Step 5: Check persistence (analysis)
  ↓
Generate Report
```

**Our Multi-Agent Flow:**
```
Agent 1: IdentifierAgent (extract tracking_id, load_number)
  ↓
Agents 2-4: PARALLEL DATA COLLECTION
  ├─→ TrackingAPIAgent
  ├─→ RedshiftAgent
  └─→ NetworkAgent
  ↓ (evidence collected)
Agent 5: HypothesisAgent (evaluate patterns, rank by confidence)
  ↓
Agent 6: SynthesisAgent (generate root cause + resolution)
  ↓
Investigation Result
```

**Analysis:**
- Arpit's flow is **sequential with branching** - explicit control flow
- Our flow is **parallel with synthesis** - faster but less predictable
- Arpit's flow is **easier to debug** - clear step-by-step trace
- Our flow is **faster for complex investigations** - parallel data collection

**Recommendation:** Support both approaches. Use Arpit's playbooks for well-defined patterns, use our multi-agent for exploratory investigations.

---

## Pattern Inventory

### Arpit's Patterns (12)

1. `carrier_not_found.yaml` (7,531 bytes)
2. `device_not_assigned.yaml` (4,873 bytes)
3. `device_offline.yaml` (6,290 bytes)
4. `eld_connection_error.yaml` (6,739 bytes)
5. `eld_not_enabled.yaml` (5,196 bytes)
6. `gps_stale_location.yaml` (5,094 bytes)
7. `network_tracking_disabled.yaml` (6,359 bytes)
8. `provider_api_error.yaml` (8,053 bytes)
9. `validation_error.yaml` (6,093 bytes)
10. `webhook_4xx.yaml` (7,693 bytes)
11. `webhook_5xx.yaml` (7,885 bytes)
12. `webhook_timeout.yaml` (6,466 bytes)

**Total:** ~78KB of pattern definitions

### Our Patterns (15 identified, 2 with test cases)

**OTR (10):**
- ELD_NOT_ENABLED ✅ (Arpit has)
- NETWORK_RELATIONSHIP_MISSING
- LOAD_NOT_FOUND
- CARRIER_API_DOWN
- GPS_NULL_TIMESTAMPS ✅ (Arpit has as gps_stale_location)
- DEVICE_CONFIG_WRONG ✅ (Arpit has as device_not_assigned)
- CARRIER_NOT_CONFIGURED
- LATE_ASSIGNMENT
- STALE_LOCATION ✅ (Arpit has)
- CALLBACK_FAILURE ✅ (Arpit has 3 patterns)
- LOAD_ASSIGNED_DIFFERENT_CARRIER
- LOAD_CREATION_FAILED_VALIDATION ✅ (Arpit has playbook + pattern)

**Test Cases:**
- ✅ callback_failure_jan22_2026.yaml (Arpit's real production issue - 3 tracking IDs)
- ✅ load_creation_failed_address_validation.yaml (Arpit's real production issue - S20251111-0041)

**Analysis:**
- Arpit has **12 production-ready patterns**
- We have **15 pattern categories identified**, with 8 overlapping
- Arpit's patterns are **more detailed** (remediation templates, runbook links)
- We have **real test cases** from Arpit's production issues

---

## Integration Proposal

### Option 1: Merge Skills Library into Rewind-App (RECOMMENDED)

**Actions:**
1. Copy `/skills/_templates/` → `/rewind-app/docs/knowledge-extraction/`
2. Add test cases to `/rewind-app/tests/playbooks/`
3. Archive rca-agent-project (keep as reference)
4. Update rewind-app README to include knowledge extraction process

**Pros:**
- Single source of truth
- Arpit's UI + our knowledge extraction
- Production-ready system with scaling process

**Cons:**
- Lose separation between framework and implementation

---

### Option 2: Keep Separate, Cross-Reference

**Actions:**
1. Skills Library becomes "meta-framework" and knowledge extraction toolkit
2. Rewind-app references Skills Library for new domain onboarding
3. Both repos maintained independently

**Pros:**
- Clear separation of concerns
- Skills Library can be used for other domains (Ocean, Air, Drayage)

**Cons:**
- Two repos to maintain
- Confusion about which to use

---

### Option 3: Hybrid Approach

**Actions:**
1. Move knowledge extraction templates to rewind-app
2. Keep Skills Library as architectural reference and pattern catalog
3. Rewind-app is production implementation
4. Skills Library is onboarding/training material

**Pros:**
- Best of both worlds
- Clear roles for each repo

**Cons:**
- Still two repos

---

## Recommendations

### Immediate (This Week)

1. **Add Knowledge Extraction to Rewind-App**
   - Copy `skills/_templates/` to `rewind-app/docs/knowledge-extraction/`
   - Update rewind-app README with "How to Add a New Domain" section
   - Reference our 2-day extraction process

2. **Add Test Cases to Rewind-App**
   - Create `rewind-app/tests/playbooks/callback_failure/` directory
   - Add `test_jan22_2026.yaml` with Arpit's 3 tracking IDs
   - Add expected outcomes and validation criteria

3. **Cross-Reference Documentation**
   - Update Skills Library README to reference rewind-app as production implementation
   - Add link to Arpit's UI: http://rewind.fourkites.internal/

### Short Term (Weeks 1-2)

4. **Unified Pattern Format**
   - Adopt Arpit's pattern structure (confirms/rejects)
   - Add our test case format to each pattern
   - Create validation framework that runs test cases against patterns

5. **Knowledge Extraction Session**
   - Use our templates in first SME extraction with Prashant or Surya
   - Validate that templates produce usable playbooks/patterns
   - Refine templates based on feedback

### Medium Term (Weeks 3-4)

6. **Scale to More Domains**
   - Extract Ocean tracking patterns using our templates
   - Extract Drayage patterns using our templates
   - Build pattern library to 50+ patterns

7. **Integration with Cassie**
   - Use our skills_router.py for hierarchical routing
   - Integrate with Cassie's decision engine
   - Deploy to test environment

---

## Key Insights

### What Arpit Built Well

1. **Operational Playbooks** - Step-by-step investigation with branching logic
2. **Pattern Files** - Clean separation, confirms/rejects evidence
3. **Remediation Templates** - Actionable resolution steps with priorities
4. **UI** - Working interface at http://rewind.fourkites.internal/
5. **Production Patterns** - 12 battle-tested patterns from real issues

### What We Built Well

1. **Knowledge Extraction Templates** - 2,850+ lines, 12-section structured process
2. **Test Cases** - Real production issues with expected outcomes
3. **Architectural Framework** - skill_base, skills_router, multi_agent_investigator
4. **Flexibility Emphasis** - YAML-configurable everything
5. **Scaling Process** - Clear path from 1 domain to 10-12 domains

### Perfect Combination

**Arpit's rewind-app + Our knowledge extraction = Complete RCA Platform**

- Arpit has the **implementation** (playbooks, patterns, UI)
- We have the **scaling process** (knowledge extraction, templates, test framework)
- Together: Production-ready system with systematic expansion to 10-12 domains

---

## Next Steps

1. **Share this document with Arpit** - Get his feedback on integration approach
2. **Schedule sync** - Discuss which integration option to pursue
3. **Pilot knowledge extraction** - Run one domain extraction using our templates → produce rewind-app playbook
4. **Measure success** - Did templates accelerate playbook creation?

---

## Appendix: File Comparison

### Playbooks

| Arpit's Rewind-App | Our Skills Library | Notes |
|-------------------|-------------------|-------|
| `callback_failure.yaml` (476 lines) | Embedded in `otr-rca/SKILL.yaml` | Arpit's is more detailed |
| `load_creation_failure.yaml` (292 lines) | Embedded in `otr-rca/SKILL.yaml` | Arpit's is more detailed |

### Patterns

| Arpit's Rewind-App | Our Skills Library | Notes |
|-------------------|-------------------|-------|
| 12 pattern files (~78KB) | Pattern definitions in SKILL.yaml | Arpit's are separate files |
| `eld_not_enabled.yaml` | Pattern category defined | Arpit has full remediation |
| `webhook_5xx.yaml` | Callback pattern defined | Arpit has 3 webhook patterns |

### Knowledge Extraction

| Arpit's Rewind-App | Our Skills Library | Notes |
|-------------------|-------------------|-------|
| ❌ None | ✅ `_templates/` (2,850+ lines) | Our unique contribution |
| ❌ None | ✅ `knowledge_extraction_template.yaml` (800 lines) | 12-section template |
| ❌ None | ✅ 8 supporting docs | README, QUICK_START, VALIDATION_CHECKLIST, etc. |

### Test Cases

| Arpit's Rewind-App | Our Skills Library | Notes |
|-------------------|-------------------|-------|
| ❌ None | ✅ `callback_failure_jan22_2026.yaml` | Real production issue from Arpit |
| ❌ None | ✅ `load_creation_failed_address_validation.yaml` | Real production issue from Arpit |

---

**Conclusion:** Merge efforts. Arpit's rewind-app is the production system. Our Skills Library provides the knowledge extraction toolkit to scale it to 10-12 domains.
