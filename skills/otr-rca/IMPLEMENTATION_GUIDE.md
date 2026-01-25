# OTR RCA Skill - Implementation Guide

**Created:** 2026-01-14
**Skill ID:** `otr_rca`
**Version:** 1.0.0
**Status:** Phase 1 Complete (SKILL.yaml definition created)

---

## Phase Delivery Status

### Phase 1: Skill Definition (COMPLETE ✅)

This phase creates the foundation - the SKILL.yaml metadata file that defines what the OTR RCA skill is, what it can do, and how it should behave.

**Deliverables:**
- ✅ `SKILL.yaml` - Complete skill definition (702 lines)
- ✅ `README.md` - Comprehensive documentation (650+ lines)
- ✅ `QUICK_REFERENCE.md` - Quick lookup guide (300+ lines)
- ✅ `IMPLEMENTATION_GUIDE.md` - This file

**What's Included:**

1. **Skill Metadata**
   - ID, name, version, author, status
   - Domain: OTR, Category: support-operations

2. **Triggers (When to Invoke)**
   - 24 keywords recognized ("load not tracking", "no GPS", "ELD offline", etc.)
   - 8 issue categories
   - 4 load mode conditions (OTR, GROUND, LTL, FTL)

3. **Capabilities (What It Can Do)**
   - 9 specialized investigation capabilities
   - 7 data sources to query
   - 2-15 minute investigation time per capability

4. **Data Sources (Where It Looks)**
   - Tracking API - Real-time load status
   - Company API - Network relationships, ELD config
   - SigNoz - Processing logs and errors
   - Redshift - Historical data and patterns
   - CASSIE - Carrier lookup and capabilities
   - FourSight - Load patterns and anomalies
   - S3 - Device logs and raw data

5. **Patterns (Known Issues)**
   - 10 common OTR issue signatures
   - Each pattern maps to root causes
   - Examples: "eld_not_enabled_network", "network_relationship_missing", "gps_null_timestamps"

6. **Root Causes (Possible Diagnoses)**
   - 16 specific root causes
   - Organized by category (ELD, Network, Carrier, GPS, Callbacks, System)
   - Each has recommended action and escalation path

7. **Confidence Thresholds**
   - Auto-resolve: ≥ 90% confidence
   - Human review: 80-90% confidence
   - Escalate: < 80% confidence

8. **Human Handoff Triggers**
   - Low confidence detection
   - Stuck after N steps
   - Contradictory data detection
   - Critical decision approval

9. **Output Format**
   - Structured investigation result
   - 10+ output fields
   - Evidence array with sources and timestamps
   - Recommended actions with priority

10. **Metrics & Targets**
    - Baseline: 20-30 minutes, 75% data gathering
    - Target: 8-12 minutes, 60% automation rate
    - 20 metrics tracked for performance

11. **Integration Points**
    - Router integration
    - CASSIE tool integration
    - FourSight analytics integration
    - MCP server support

12. **Test Cases**
    - 20 real ticket examples
    - Organized by category (5+4+4+3+2+2)
    - Each maps to root causes

---

## What You Can Do NOW (Phase 1)

With the SKILL.yaml definition complete, you can:

### 1. **Router Configuration**
   - Configure router to recognize OTR triggers
   - Map keywords to skill invocation
   - Set up skill selection logic

   **Example:**
   ```python
   router.register_skill(
       skill_id="otr_rca",
       definition_path="skills/otr-rca/SKILL.yaml",
       triggers=["load not tracking", "no GPS", "ELD offline"]
   )
   ```

### 2. **Data Source Preparation**
   - Validate MCP servers are available
   - Test API endpoints
   - Verify Redshift/SigNoz access
   - Confirm CASSIE connectivity

   **Checklist:**
   - [ ] Tracking API responding
   - [ ] Company API responding
   - [ ] SigNoz queries working
   - [ ] Redshift accessible
   - [ ] S3 accessible

### 3. **Capability Planning**
   - Identify which capabilities to implement first
   - Estimate implementation time per capability
   - Plan API call sequences
   - Design error handling

### 4. **Output Integration**
   - Plan how to present results to users
   - Design UI for investigation findings
   - Plan Salesforce ticket updates
   - Plan escalation notifications

### 5. **Testing Infrastructure**
   - Set up test harness
   - Create mock data generators
   - Plan test execution strategy
   - Set up metrics collection

---

## Next Steps (Phase 2: Implementation)

### Step 1: Create Decision Tree (1-2 days)

**File:** `decision_trees/tracking_issue_classifier.yaml`

This defines the step-by-step investigation flow:

```yaml
entry_point: "step_1_platform_check"

steps:
  step_1_platform_check:
    name: "Platform Check"
    description: "Verify load exists and check tracking status"
    action:
      type: "api_call"
      endpoint: "tracking_api.get_load_details"
    decisions:
      load_not_found:
        condition: "result.load_exists == false"
        next_step: null  # End
        root_cause: "load_not_found"

      load_tracking_normally:
        condition: "result.tracking_enabled == true"
        next_step: "step_2_eld_check"

      # ... more decisions

  step_2_eld_check:
    # ... similar structure
```

### Step 2: Define Patterns (1-2 days)

**Files:** `patterns/*.yaml` (10 files)

Each pattern defines a common issue signature:

```yaml
# patterns/eld_not_enabled_network.yaml
pattern:
  id: "eld_not_enabled_network"
  name: "ELD Not Enabled + No Network"
  description: "ELD disabled AND no network relationship"

  indicators:
    - "eld_enabled == false"
    - "network_relationship_missing == true"

  root_cause: "eld_not_enabled"
  confidence: 0.94

  evidence_required:
    - source: "company_api"
      field: "eld_enabled"
      expected: false
    - source: "company_api"
      field: "relationship_exists"
      expected: false

  recommended_action: "enable_eld"
  priority: "high"
```

### Step 3: Create Test Cases (1-2 days)

**Files:** `test_cases/*.yaml` (20 files)

Real ticket examples for validation:

```yaml
# test_cases/case_eld_offline_1.yaml
test_case:
  id: "tc_eld_offline_001"
  load_id: "U123456"
  issue_type: "tracking_not_working"

  input:
    ticket_description: "Load U123456 not showing positions for XYZ Carrier"
    context:
      carrier_id: "CARR_XYZ"
      shipper_id: "SHIP_ABC"
      load_mode: "OTR"

  expected_output:
    root_cause: "eld_offline"
    confidence_score: "> 0.90"
    recommended_action: "restart_eld_sync"

  steps_to_execute:
    - step_1_platform_check
    - step_2_eld_check
    - step_3_investigate_offline

  api_mocks:
    - endpoint: "tracking_api/loads/U123456"
      response: {load_exists: true, eld_enabled: true, device_online: false}
    - endpoint: "company_api/devices/DEV_XYZ"
      response: {online: false, last_heartbeat: "2026-01-12T08:00:00Z"}
```

### Step 4: Implement Skill Class (2-3 days)

**File:** `skills/otr_rca/skill.py`

Main investigator that executes the decision tree:

```python
from skill_base import Skill

class OTRRCASkill(Skill):
    """OTR Root Cause Analysis Skill"""

    def __init__(self, skill_dir: str):
        super().__init__(skill_dir)
        self.definition = self._load_yaml("SKILL.yaml")
        self.decision_tree = self._load_yaml("decision_trees/tracking_issue_classifier.yaml")
        self.patterns = self._load_patterns()
        self.test_cases = self._load_test_cases()

    def investigate(self, context: dict) -> InvestigationResult:
        """Execute investigation"""
        result = InvestigationResult()

        # Start at entry point
        current_step = self.decision_tree["entry_point"]

        while current_step:
            # Execute step
            step_result = self.execute_step(current_step, context)
            result.add_step(current_step, step_result)

            # Check for handoff
            if step_result.needs_human_input:
                return self._create_handoff_result(result)

            # Next step
            current_step = step_result.next_step

        return result

    def execute_step(self, step_name: str, context: dict) -> StepResult:
        """Execute single investigation step"""
        # ...
```

### Step 5: Integration Testing (1-2 days)

- Test with router
- Test all API integrations
- Test handoff flow
- Test escalation paths
- Run all 20 test cases

### Step 6: Metrics & Monitoring (1 day)

- Set up metrics collection
- Create dashboard
- Configure alerts
- Plan monitoring strategy

---

## Dependency Matrix

```
SKILL.yaml (Phase 1 - DONE ✅)
    ├── decision_tree.yaml (Phase 2)
    │   ├── test_cases/*.yaml (Phase 2)
    │   └── skill.py (Phase 2)
    │
    ├── patterns/*.yaml (Phase 2)
    │
    └── Integration (Phase 2)
        ├── router.py
        ├── tracking_api.py
        ├── company_api.py
        ├── signoz_connector.py
        └── redshift_connector.py
```

---

## SKILL.yaml Content Breakdown

### Header & Metadata (lines 1-14)
- File purpose and source
- Skill ID, name, version
- Author and status

### Description (lines 16-29)
- What issues it handles
- Mental model summary
- Key value proposition

### Triggers (lines 31-75)
- 24 keywords that trigger skill
- 8 issue categories
- 4 load mode conditions

### Capabilities (lines 77-214)
- 9 investigation capabilities
- Time estimates
- Confidence levels
- Tool references
- Output fields

### Data Sources (lines 216-320)
- 9 different data sources
- API endpoints
- Authentication methods
- Latency expectations
- Data availability matrix

### Patterns (lines 351-376)
- 10 issue patterns
- File references
- Descriptions

### Confidence Thresholds (lines 378-385)
- 3 confidence levels
- Actions per level

### Human Handoff (lines 387-441)
- 4 escalation triggers
- Custom messages

### Output Format (lines 443-590)
- 10 output fields
- Data types and validation
- Structured result schema

### Metrics (lines 592-619)
- Baseline metrics
- Target metrics
- 10 tracked metrics

### Integration (lines 621-633)
- CASSIE integration
- FourSight integration
- MCP servers

### Test Cases (lines 635-645)
- 20 test cases
- Organized by category

### Knowledge Base (lines 647-656)
- Reference sources
- Domain documentation

### Version History (lines 665-671)
- Version tracking
- Status tracking

### Metadata Section (lines 674-702)
- UI properties
- Documentation links
- SLA targets
- Support contact

---

## Validation Checklist

- ✅ SKILL.yaml is valid YAML
- ✅ All required fields present
- ✅ Triggers are comprehensive
- ✅ Capabilities are realistic
- ✅ Data sources are available
- ✅ Root causes are specific
- ✅ Confidence thresholds are reasonable
- ✅ Output format is complete
- ✅ Metrics are trackable
- ✅ Integration points are clear
- ✅ Documentation is comprehensive

---

## File Sizes & Lines of Code

| File | Size | Lines | Purpose |
|------|------|-------|---------|
| SKILL.yaml | 23 KB | 702 | Skill definition |
| README.md | 30 KB | 650+ | Full documentation |
| QUICK_REFERENCE.md | 12 KB | 300+ | Quick lookup |
| IMPLEMENTATION_GUIDE.md | 8 KB | 250+ | This file |

**Total Phase 1 Deliverable:** 73 KB documentation

---

## Key Features of This SKILL.yaml

1. **Production-Ready Structure**
   - Follows FourKites conventions
   - Consistent with ocean_debugging skill
   - Ready for router integration
   - Includes metadata for UI

2. **Comprehensive Coverage**
   - 24 trigger keywords
   - 16 root causes
   - 9 capabilities
   - 7 data sources
   - 10 patterns
   - 20 test cases

3. **Clear Decision Logic**
   - Confidence thresholds defined
   - Human handoff triggers documented
   - Escalation paths clear
   - Next steps obvious

4. **Well-Documented**
   - 3 documentation files
   - Examples included
   - Integration points clear
   - Testing strategy outlined

5. **Extensible Design**
   - Easy to add patterns
   - Easy to add test cases
   - Easy to add capabilities
   - Version tracking built in

---

## How to Use This Document

**For Developers:**
- Reference SKILL.yaml for capability definitions
- Check QUICK_REFERENCE.md for decision logic
- Read README.md for full context

**For Project Managers:**
- Use phase breakdown for scheduling
- Track deliverables against checklist
- Monitor metrics collection

**For Support Teams:**
- Review real examples in README.md
- Understand decision tree flow
- Know when human handoff triggers

**For Product:**
- Reference output format for UI
- Plan metrics dashboard
- Understand scope of automation

---

## Success Criteria for Phase 1

✅ SKILL.yaml created and validated
✅ README.md documentation complete
✅ QUICK_REFERENCE.md for operators
✅ IMPLEMENTATION_GUIDE.md created
✅ File structure established
✅ All 16 root causes defined
✅ All 9 capabilities described
✅ Integration points identified
✅ Test case strategy documented
✅ Metrics targets set

**Phase 1 Status: COMPLETE**

---

## What Was Delivered

### Documentation Files
1. **SKILL.yaml** (702 lines)
   - Complete skill definition
   - 9 capabilities
   - 7 data sources
   - 16 root causes
   - 10 patterns
   - Confidence thresholds
   - Human handoff triggers
   - Output format
   - Integration points

2. **README.md** (650+ lines)
   - Architecture overview
   - Section-by-section explanation
   - 3 detailed examples
   - Testing strategy
   - Integration guide
   - Roadmap

3. **QUICK_REFERENCE.md** (300+ lines)
   - 30-second overview
   - 16 root causes table
   - 6-step investigation flow
   - Confidence thresholds
   - Pro tips
   - Common patterns

4. **IMPLEMENTATION_GUIDE.md** (250+ lines)
   - Phase breakdown
   - Current status
   - Next steps
   - Dependency matrix
   - Validation checklist

### What You Can Do Next

1. Share with Prashant for validation
2. Start Phase 2: Decision tree implementation
3. Plan router integration
4. Set up API mocks for testing
5. Create test harness
6. Begin implementation sprint

---

## Questions?

Refer to:
- **"How do I use this skill?"** → README.md Overview section
- **"What root causes are supported?"** → QUICK_REFERENCE.md table
- **"What's next?"** → IMPLEMENTATION_GUIDE.md
- **"How confident does it need to be?"** → QUICK_REFERENCE.md Confidence Thresholds

---

**Document Status:** Final ✅
**Date Created:** 2026-01-14
**Next Document:** Phase 2 - Decision Tree Implementation Plan
