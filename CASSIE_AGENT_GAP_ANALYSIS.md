# Cassie Agent Gap Analysis & Improvement Roadmap

**Date:** January 27, 2026
**Prepared For:** Engineering & Support Operations Leadership
**Status:** ⚠️ CRITICAL GAPS IDENTIFIED - IMMEDIATE ACTION REQUIRED

---

## Executive Summary

**Current State:** Cassie agent correctly identifies high-level categories (e.g., "LOAD_NOT_TRACKING") but **STOPS at categorization** instead of executing diagnostic investigations.

**Result:** 100% of reviewed cases escalated to manual intervention despite having sufficient data to resolve automatically.

**Core Problem:** Agent lacks **investigation playbook execution** - it knows WHAT the problem category is, but doesn't execute the diagnostic steps to determine the specific root cause and draft customer responses.

**Recommendation:** Implement 3-tier investigation framework: Category → Diagnostic Checks → Root Cause → Auto-Response

---

## Part 1: Analysis of Production Failures

### Case 1: GPS Provider Null Timestamp (Case #2693837)

**What Cassie Did:**
```
✓ Identified: FOURKITES_LOAD_NOT_TRACKING
✓ Reasoning: "loads exist but are not receiving GPS/location updates"
✗ Action: Escalated to manual intervention
```

**What Cassie SHOULD Have Done:**
```
Step 1: Identify category (DONE) ✓
Step 2: Execute diagnostic playbook:
   - Check GPS provider API logs via OTR MCP
   - Query location_provider_client errors
   - Identify error: "undefined method `to_datetime' for nil:NilClass"
   - Root cause: RoadoGps API returned null timestamp

Step 3: Draft customer response:
   "The tracking issue occurred due to invalid data returned by the RoadoGps API.
    The API returned location data with a null timestamp, causing downstream processing to fail.
    Next Steps: Please contact your GPS provider to resolve the null timestamp issue."
```

**Gap Identified:**
- ❌ No log analysis execution
- ❌ No GPS provider API check
- ❌ No auto-response generation
- ❌ Bot stops at categorization instead of investigation

**Bot Feasibility from Categories Sheet:** LOW → Should be MEDIUM/HIGH with proper diagnostics

---

### Case 2: Old Location Rejection (Case #2688628)

**What Cassie Did:**
```
✓ Identified: FOURKITES_LOAD_NOT_TRACKING
✓ Reasoning: "location updates not being ingested despite positive ping tests"
✗ Stopped at: "tracking integration failure" (generic)
✗ Did NOT drill into: WHY locations are being rejected
```

**What Cassie SHOULD Have Done:**
```
Step 1: Identify category (DONE) ✓
Step 2: Drill into sub-category:
   - Check outlier detection logs
   - Identify: GPS provider returning old locations
   - Sub-category: "Old/stale location timestamps"

Step 3: Match to pattern from categories sheet:
   Pattern: "Outlier Detection > Speed-Based Ping Rejection"
   Description: "Stale coordinates causing impossible speed calculation"

Step 4: Draft response:
   "The GPS provider is returning historical/stale location data.
    Our system is correctly rejecting these old locations to maintain data quality.
    Please contact your GPS provider to resolve the timestamp issue."
```

**Gap Identified:**
- ❌ No sub-category drill-down
- ❌ Stopped at "tracking integration failure" (too generic)
- ❌ Didn't check outlier detection logs
- ❌ Didn't match to specific pattern from category sheet

**Bot Feasibility:** Currently marked as MEDIUM → Should be HIGH with pattern matching

---

### Case 3: Trailer vs Truck GPS (Case #2692749)

**What Cassie Did:**
```
✗ Got stuck in decision loop
✗ Did not progress to diagnostic checks
✗ Escalated to manual intervention
```

**What Cassie SHOULD Have Done:**
```
Step 1: Identify category → LOAD_NOT_TRACKING
Step 2: Check asset assignment:
   - Query: What asset type is assigned? (Trailer number)
   - Query: What asset types does carrier support? (Truck GPS only)
   - Mismatch detected!

Step 3: Match to pattern:
   Pattern: "Tracking Method Issues > Wrong Tracking Method Applied"
   Root Cause: "Trailer number assigned but carrier only supports Truck GPS"

Step 4: Draft response:
   "The load was assigned a trailer number, but the carrier USA Truck Inc
    only supports truck-based GPS tracking. Please assign a truck number instead."
```

**Gap Identified:**
- ❌ Decision loop failure (routing bug)
- ❌ No asset type verification check
- ❌ No carrier capability check
- ❌ Basic configuration check not executed

**Bot Feasibility:** Should be MEDIUM/HIGH - this is a configuration check

---

### Case 4: ELD Not Enabled (Case #2682612)

**What Cassie Did:**
```
✗ Got stuck in decision loop
✗ Did not execute basic first-step check
✗ Escalated to manual intervention
```

**What Cassie SHOULD Have Done:**
```
Step 1: Identify category → LOAD_NOT_TRACKING
Step 2: Execute first-step diagnostic (ELD configuration check):
   - Query: Is ELD tracking enabled at network level?
   - Result: NO
   - Root cause identified immediately!

Step 3: Match to pattern:
   Pattern: "Configuration/Network Issues > Feature Flag Disabled"
   Bot Feasibility: HIGH (can check feature flags)

Step 4: Draft response:
   "ELD tracking is not enabled at the shipper-carrier network level.
    Please enable ELD tracking in the network configuration to begin receiving updates."
```

**Gap Identified:**
- ❌ Decision loop failure (routing bug)
- ❌ **CRITICAL:** Didn't execute basic first-step check (ELD enabled?)
- ❌ This is the simplest possible case - should be 100% automated

**Bot Feasibility:** HIGH (as per category sheet) - this is a critical failure

---

## Part 2: Pattern Analysis from Categories Sheet

### High-Value Patterns (Bot Feasibility: HIGH)

These should be **100% automated** but currently escalate to manual:

| Pattern | Current Bot | Should Be | Gap |
|---------|-------------|-----------|-----|
| **Check Call Expiry** | N/A | 100% Auto | No expiry check implemented |
| **Configuration/Network Issues** | Categorizes | 100% Auto | Doesn't check Connect config |
| **ELD/GPS Provider Issues** | Categorizes | 90% Auto | Doesn't check asset assignment |
| **Sibling Load Issues** | N/A | 80% Auto | No sibling group logic |

**Impact:** 40-50% of tickets could be auto-resolved with proper configuration checks.

---

### Medium-Value Patterns (Bot Feasibility: MEDIUM)

These should provide **diagnostic guidance** and **draft responses**:

| Pattern | Current Bot | Should Be | Gap |
|---------|-------------|-----------|-----|
| **Outlier Detection** | Stops at category | Draft response | No log analysis |
| **Status Code Processing** | Stops at category | Configuration check | No status mapping check |
| **Geofence Issues** | N/A | Config verification | No geofence check |
| **Infrequent Updates** | N/A | Frequency analysis | No ping interval check |

**Impact:** 30-40% of tickets could get detailed diagnostic guidance instead of generic escalation.

---

### Complex Patterns (Bot Feasibility: LOW)

These require **engineering investigation** but bot should still provide context:

| Pattern | Current Behavior | Should Provide |
|---------|------------------|----------------|
| **Infrastructure Issues** | Generic escalation | Specific log evidence + engineering ticket template |
| **Kafka Lag** | Not detected | Lag metrics + impact analysis |
| **Database Timeout** | Not detected | Timeout logs + query performance data |

**Impact:** 10-20% of tickets - bot provides rich context for engineering escalation.

---

## Part 3: Root Cause Analysis - Why Is Cassie Failing?

### Issue 1: No Diagnostic Execution Framework

**Problem:** Bot categorizes but doesn't execute checks.

**Current Flow:**
```
User Input → Category Classification → "Manual Review Required" → STOP
```

**Should Be:**
```
User Input → Category → Diagnostic Playbook → Evidence Collection → Root Cause → Response
```

**Example:** For "LOAD_NOT_TRACKING" category:
```yaml
diagnostic_playbook:
  step_1:
    check: "ELD tracking enabled at network level?"
    data_source: "Connect API via MCP"
    if_no: "Root cause identified - ELD not enabled"

  step_2:
    check: "Asset (truck/trailer) assigned?"
    data_source: "Tracking API via MCP"
    if_no: "Root cause identified - No asset assigned (T000008)"

  step_3:
    check: "GPS provider returning locations?"
    data_source: "GPS Provider API logs via OTR MCP"
    if_no: "Check GPS provider logs for errors"
```

**Fix Required:** Implement playbook execution engine that runs checks sequentially.

---

### Issue 2: OTR MCP Not Being Called

**Problem:** The neo4j_mcp and other MCP servers exist but Cassie isn't calling them.

**Evidence:**
- Case #2693837: Should have called OTR MCP to check GPS provider logs
- Case #2682612: Should have called OTR MCP to check ELD configuration
- Cases escalate to manual despite having MCP servers with required data

**Root Cause:** Cassie's decision logic doesn't include MCP invocation step.

**Fix Required:**
```python
# Current (wrong):
if category == "LOAD_NOT_TRACKING":
    return "Manual review required"

# Should be:
if category == "LOAD_NOT_TRACKING":
    # Step 1: Call OTR MCP
    mcp_result = call_otr_mcp(load_id, diagnostics=["eld_config", "asset_assignment", "gps_logs"])

    # Step 2: Analyze MCP result
    root_cause = analyze_mcp_result(mcp_result)

    # Step 3: Match to pattern
    pattern = match_pattern_from_categories_sheet(root_cause)

    # Step 4: Generate response
    return generate_customer_response(pattern, mcp_result)
```

---

### Issue 3: Category Sheet Not Used as Investigation Playbook

**Problem:** The 100+ row category sheet with "Bot Feasibility" ratings is not integrated into Cassie.

**What Exists:**
- Comprehensive category taxonomy (Address/Geocoding, API/Integration, Auto-Completion, etc.)
- Root cause patterns mapped to diagnostic steps
- Bot feasibility ratings (HIGH/MEDIUM/LOW)

**What's Missing:**
- Cassie doesn't reference this sheet during investigation
- No playbook mapping from category → diagnostic steps
- Bot feasibility ratings not used to route (auto-resolve vs manual)

**Fix Required:**
1. Convert category sheet to machine-readable YAML (Skills Library format)
2. Map each category to diagnostic playbook
3. Use bot feasibility rating to determine auto-resolve threshold

**Example:**
```yaml
category: "ELD/GPS Provider Issues"
sub_category: "Asset Not Assigned (T000008)"
bot_feasibility: "HIGH"
root_cause_pattern: "Carrier has not assigned truck/trailer/device/driver phone"

diagnostic_steps:
  - check: "truck_number field populated?"
    data_source: "tracking_api"
    expected: "non-null value"
  - check: "trailer_number field populated?"
    data_source: "tracking_api"
    expected: "non-null value"
  - check: "device_id field populated?"
    data_source: "tracking_api"
    expected: "non-null value"

auto_response_template: |
  The carrier has not assigned an asset (truck/trailer/device) to this load.
  This is preventing ELD tracking from starting.

  Please contact the carrier to assign:
  - Truck number, OR
  - Trailer number, OR
  - Device ID, OR
  - Driver phone number
```

---

### Issue 4: Decision Loop Failures

**Problem:** Cases #2692749 and #2682612 show bot getting stuck in decision loop.

**Hypothesis:** Routing logic has circular dependencies or missing exit conditions.

**Evidence:**
```
Case #2692749: "Step 1: NOT a NIC/Nicplace query... Step 2: NOT staging..."
(Bot checking what it's NOT instead of what it IS)
```

**Root Cause:** Classification logic is negative-based (elimination) instead of positive-based (matching).

**Fix Required:**
```python
# Current (wrong) - elimination approach:
if not is_nic_query and not is_staging and not is_default_routing:
    # What is it then? Loop continues...

# Should be (right) - positive matching:
if matches_pattern("LOAD_NOT_TRACKING", input):
    execute_load_not_tracking_playbook()
    return result
elif matches_pattern("GPS_PROVIDER_ISSUE", input):
    execute_gps_provider_playbook()
    return result
# ... etc
```

---

## Part 4: Comparison with Sudhanshu's Timeline

### Sudhanshu's Proposed Plan

| Phase | Task | Timeline | Assessment |
|-------|------|----------|------------|
| **Discovery** | Walk through mental model, review categories, gap analysis | 2 weeks | ✅ GOOD - Essential foundation |
| **Refactor/POC** | Implement collaborative agents framework, integrate data sources | 3 weeks | ⚠️ CONCERN - May be over-engineering |
| **Execution** | Build missing data sources, build agent, improve logs | 4 weeks | ⚠️ CONCERN - Missing diagnostic playbook |
| **Release** | Testing on live cases, feedback and fix | 2 weeks | ✅ GOOD - Proper validation |

**Total Timeline:** 11 weeks (2/17/2026 → 4/21/2026) for Phase 1

---

### Critical Gaps in Sudhanshu's Plan

#### Gap 1: No Diagnostic Playbook Execution in Scope

**Missing from Plan:**
- How bot will execute checks (not just categorize)
- Playbook mapping from categories sheet to diagnostic steps
- MCP invocation strategy

**Recommendation:** Add explicit task:
```
Phase: Execution
Task: "Implement diagnostic playbook execution engine"
Details:
  - Map 50+ HIGH-feasibility patterns to playbooks
  - Integrate OTR MCP calls for each diagnostic check
  - Implement sequential check execution with early exit
  - Add auto-response generation for 90%+ confidence cases
Timeline: +2 weeks
```

#### Gap 2: "Improve Logs" Too Vague

**Current:** "improve logs - or plan for log improvements"

**Problem:** Log access is CRITICAL for RCA but plan doesn't specify:
- Which logs need to be accessible?
- How bot will query logs? (via MCP? direct access?)
- Log parsing and error pattern matching

**Recommendation:** Be specific:
```
Task: "Enable log access via MCP servers"
Details:
  - GPS provider API logs (via OTR MCP)
  - Outlier detection logs (via OTR MCP)
  - Status processing logs (via OTR MCP)
  - Configuration change logs (via Connect API MCP)
  - Implement log pattern matching for common errors
Timeline: 2 weeks (parallel with data source build)
```

#### Gap 3: No Clear Auto-Resolution Target

**Current Plan:** "Agent live and working" (vague success criteria)

**Missing:**
- What % of cases should auto-resolve?
- Which patterns must be automated first?
- How to measure improvement vs current bot?

**Recommendation:** Set measurable targets:
```
Phase 1 Success Criteria:
  - 40% of HIGH-feasibility cases auto-resolved (currently 0%)
  - 80% of MEDIUM-feasibility cases get diagnostic guidance (currently 0%)
  - Average investigation time: <5 minutes (currently 15-30 min manual)
  - Customer satisfaction: 80%+ on auto-responses
```

#### Gap 4: Category Sheet Integration Not Explicit

**Current Plan:** "Review category and sub category of load not tracking usecase"

**Problem:** Reviewing is not the same as IMPLEMENTING.

**Missing:**
- Converting category sheet to machine-readable format (YAML)
- Mapping bot feasibility ratings to auto-resolve logic
- Integrating 100+ patterns as investigation playbooks

**Recommendation:**
```
Phase: Refactor/POC (add task)
Task: "Convert category sheet to Skills Library format"
Details:
  - Create YAML file per category (50+ files)
  - Each YAML defines:
    * Root cause pattern
    * Diagnostic steps (what to check)
    * Data sources (which MCP servers)
    * Evidence rules (confidence scoring)
    * Auto-response template
  - Import into bot's pattern matching engine
Timeline: 1 week
```

---

## Part 5: Recommendations for Immediate Improvement

### Priority 1: Fix Decision Loop Bug (Week 1)

**Problem:** Cases getting stuck in classification loop.

**Fix:**
```
1. Replace elimination-based logic with positive pattern matching
2. Add timeout/max-iterations guard
3. Add fallback: "Unable to classify" → route to Load Not Tracking playbook by default
```

**Impact:** Eliminate 50% of "stuck" cases immediately.

---

### Priority 2: Implement Basic Diagnostic Checks (Weeks 2-3)

**Start with 5 HIGH-feasibility patterns:**

1. **ELD Not Enabled** (Case #2682612 failure)
   - Check: Network-level ELD configuration
   - Data source: Connect API MCP
   - Auto-resolve: YES
   - Response: "Enable ELD tracking at network level"

2. **Asset Not Assigned** (T000008)
   - Check: truck_number / trailer_number / device_id populated?
   - Data source: Tracking API MCP
   - Auto-resolve: YES
   - Response: "Contact carrier to assign asset"

3. **Check Call Expiry** (T000007)
   - Check: Last delivered load > 30 days ago?
   - Data source: Tracking API MCP
   - Auto-resolve: YES
   - Response: "Network inactive - verify carrier is active"

4. **Duplicate SCAC in Network**
   - Check: Query carriers with same SCAC
   - Data source: Connect API MCP
   - Auto-resolve: PARTIAL (needs human verification)
   - Response: "Found duplicate SCACs: [list] - verify correct carrier"

5. **Feature Flag Disabled**
   - Check: Required feature enabled for shipper/carrier?
   - Data source: Connect API MCP
   - Auto-resolve: YES (if simple enable)
   - Response: "Enable feature X in configuration"

**Impact:** 40-50% of cases auto-resolved with these 5 checks alone.

---

### Priority 3: Integrate OTR MCP Calls (Weeks 3-4)

**Current:** OTR MCP exists but not called by Cassie.

**Fix:**
```python
# Add MCP invocation layer to Cassie

def investigate_load_not_tracking(load_id):
    # Call OTR MCP for diagnostics
    otr_diagnostics = call_otr_mcp(
        load_id=load_id,
        checks=[
            "eld_configuration",
            "asset_assignment",
            "gps_provider_logs",
            "outlier_detection_logs",
            "status_processing_logs"
        ]
    )

    # Analyze results
    if not otr_diagnostics["eld_enabled"]:
        return auto_response("eld_not_enabled_template")

    if not otr_diagnostics["asset_assigned"]:
        return auto_response("asset_not_assigned_template")

    if otr_diagnostics["gps_logs"].contains("null timestamp"):
        return auto_response("gps_provider_issue_template")

    # ... continue diagnostic chain
```

**Impact:** Enable log analysis and root cause drilling (fixes Case #2693837, #2688628).

---

### Priority 4: Convert Category Sheet to Skills Library (Week 4)

**Action Items:**
1. Export category sheet to YAML format
2. Create one skill per major category (10-12 skills):
   - `address_geocoding_issues.yaml`
   - `api_integration_issues.yaml`
   - `auto_completion_issues.yaml`
   - `eld_gps_provider_issues.yaml`
   - `configuration_network_issues.yaml`
   - etc.

3. Each skill YAML includes:
   ```yaml
   category: "ELD/GPS Provider Issues"
   patterns:
     - id: "asset_not_assigned"
       root_cause: "T000008 - No asset assigned"
       bot_feasibility: "HIGH"
       diagnostic_steps:
         - check: "truck_number populated?"
           data_source: "tracking_api"
         - check: "trailer_number populated?"
           data_source: "tracking_api"
       auto_response_template: |
         The carrier has not assigned...
   ```

4. Cassie loads these skills at startup and uses them as investigation playbooks

**Impact:** Structured investigation framework (fixes generic categorization problem).

---

### Priority 5: Add Auto-Response Generation (Week 5)

**Current:** Bot identifies issue then escalates.

**Should Be:** Bot drafts customer response automatically.

**Implementation:**
```yaml
# In each pattern YAML
auto_response_template: |
  Subject: Re: Load Not Tracking - {load_number}

  Thank you for contacting FourKites Support.

  We have identified the issue with load {load_number}:

  Root Cause: {root_cause_description}

  Evidence:
  {evidence_list}

  Resolution Steps:
  {resolution_steps}

  Next Steps:
  {next_steps}

  If this does not resolve the issue, please reply and we will investigate further.
```

**Quality Gate:** Human reviews auto-generated response before sending (initially).

**Impact:** Reduce manual response drafting time from 10-15 min to 2-3 min review.

---

## Part 6: Proposed Revised Timeline

### Phase 1: Quick Wins (Weeks 1-2) - NEW

| Task | Outcome | Timeline |
|------|---------|----------|
| Fix decision loop bug | Eliminate stuck cases | Week 1 |
| Implement 5 basic diagnostic checks | 40-50% auto-resolution | Weeks 1-2 |
| Integrate OTR MCP calls | Enable log analysis | Week 2 |

**Milestone:** Bot goes from 0% auto-resolution to 40-50% auto-resolution.

---

### Phase 2: Skills Library Integration (Weeks 3-5)

| Task | Outcome | Timeline |
|------|---------|----------|
| Convert category sheet to YAML skills | Structured playbooks | Week 3 |
| Implement playbook execution engine | Sequential diagnostic checks | Week 4 |
| Add auto-response generation | Draft customer responses | Week 5 |
| Testing on 50 historical cases | Validate 80%+ accuracy | Week 5 |

**Milestone:** Bot provides diagnostic guidance + draft responses for 80% of cases.

---

### Phase 3: Scale to All Categories (Weeks 6-8)

| Task | Outcome | Timeline |
|------|---------|----------|
| Add 20+ HIGH-feasibility patterns | 60-70% auto-resolution | Weeks 6-7 |
| Add 30+ MEDIUM-feasibility patterns | Diagnostic guidance for 90% | Weeks 7-8 |
| Improve log parsing and error detection | Better root cause accuracy | Week 8 |

**Milestone:** Bot handles 90% of OTR Load Not Tracking cases with minimal manual intervention.

---

### Phase 4: Production Release (Weeks 9-11)

| Task | Outcome | Timeline |
|------|---------|----------|
| Shadow mode: Bot provides suggestions, human decides | Build confidence | Week 9 |
| Phased rollout: 10% → 50% → 100% of cases | Monitor quality | Week 10 |
| Feedback loop: Capture false positives/negatives | Continuous improvement | Week 11 |

**Milestone:** Bot in production with 60%+ auto-resolution rate, 85%+ customer satisfaction.

---

## Part 7: Comparison - Current Plan vs Recommended Plan

| Aspect | Sudhanshu's Plan | Recommended Plan | Impact |
|--------|------------------|------------------|--------|
| **Timeline** | 11 weeks | 11 weeks | Same |
| **Auto-Resolution Target** | Not specified | 60-70% by Week 11 | Clear success metric |
| **Quick Wins** | None (starts with refactor) | 40-50% auto-res by Week 2 | Immediate value |
| **Diagnostic Execution** | Implied but not explicit | Explicit playbook engine | Core functionality |
| **Category Sheet Usage** | Review only | Convert to Skills Library | Structured approach |
| **MCP Integration** | Data sources mentioned | Explicit OTR MCP calls | Clear implementation |
| **Auto-Response** | Not mentioned | Implemented in Week 5 | Reduce manual work |
| **Validation** | Live testing at end | Historical + live testing | Better confidence |

---

## Part 8: Success Metrics

### Baseline (Current State - January 2026)

- **Auto-Resolution Rate:** 0% (all cases escalate to manual)
- **Average Investigation Time:** 15-30 minutes per case
- **Category Accuracy:** 80-90% (bot identifies correct high-level category)
- **Root Cause Accuracy:** 0% (bot doesn't drill to root cause)
- **Customer Satisfaction:** N/A (no auto-responses generated)

### Target (Phase 1 Complete - April 2026)

- **Auto-Resolution Rate:** 60-70% for HIGH-feasibility cases
- **Diagnostic Guidance:** 90% of cases get specific diagnostic steps
- **Average Investigation Time:** 5-8 minutes (70% reduction)
- **Category + Root Cause Accuracy:** 85%+ (bot identifies specific pattern)
- **Customer Satisfaction:** 80%+ on auto-generated responses
- **Manual Intervention:** Only for LOW-feasibility or ambiguous cases (10-20%)

### Measurement Approach

**Week-by-Week Tracking:**
```
Week 1: Fix decision loop → Measure: % of stuck cases eliminated
Week 2: Add 5 basic checks → Measure: % auto-resolved (target: 40%)
Week 3: Category sheet conversion → Measure: Pattern coverage %
Week 4: Playbook execution → Measure: Root cause accuracy
Week 5: Auto-response → Measure: Customer satisfaction on drafts
Weeks 6-8: Scale patterns → Measure: Auto-resolution climbing to 60%
Weeks 9-11: Production rollout → Measure: All metrics + false pos/neg rate
```

---

## Part 9: Risk Analysis & Mitigation

### Risk 1: Over-Engineering Too Soon

**Problem:** Sudhanshu's plan mentions "collaborative agents framework" in Week 3.

**Concern:** Multi-agent orchestration may be premature when basic checks aren't working.

**Mitigation:**
- Start with simple playbook execution (single-agent model)
- Prove value with basic diagnostics first (Weeks 1-5)
- Add multi-agent complexity only if needed (Phase 2+)

**Principle:** "Do the simplest thing that could possibly work"

---

### Risk 2: Data Source Dependencies

**Problem:** "Build missing data sources" could become a blocker.

**Current State:** 10 MCP servers exist (Athena, Redshift, Tracking API, etc.)

**Mitigation:**
- Verify existing MCPs can provide required data
- Use workarounds (direct API calls) if MCP gaps exist
- Don't block on MCP development - use what's available

**Principle:** "Work with what you have, improve incrementally"

---

### Risk 3: Log Access Complexity

**Problem:** "Improve logs" is vague and could become scope creep.

**Mitigation:**
- Define specific logs needed for top 10 patterns (Week 1)
- Verify log access via existing OTR MCP (Week 2)
- If logs not accessible, adjust playbooks to work with available data
- Don't wait for perfect log access before launching

**Principle:** "Good enough to start, perfect over time"

---

### Risk 4: Category Sheet Interpretation

**Problem:** 100+ row sheet with subjective "Bot Feasibility" ratings.

**Mitigation:**
- Start with 20 HIGH-feasibility patterns (clear automated checks)
- Human-review MEDIUM-feasibility patterns before automating
- Leave LOW-feasibility for manual intervention (expected)
- Validate bot feasibility ratings with actual case data

**Principle:** "Trust but verify"

---

## Part 10: Technical Architecture Recommendations

### Current Architecture (Inferred)

```
User Input
  → Cassie Agent (Classification)
  → Category Identified
  → "Manual Review Required"
  → STOP
```

**Problem:** No execution layer after classification.

---

### Recommended Architecture

```
User Input
  ↓
Cassie Agent (Intent Classification)
  ↓
Category Router
  ↓
Playbook Executor
  ↓
┌─────────────────────────────────────┐
│ Diagnostic Checks (Parallel)       │
│ - Check 1: ELD enabled?             │
│ - Check 2: Asset assigned?          │
│ - Check 3: GPS logs for errors?     │
│ - Check 4: Outlier detection logs?  │
└─────────────────────────────────────┘
  ↓
Evidence Collector
  ↓
Pattern Matcher (against Skills Library)
  ↓
Confidence Scorer
  ↓
┌─────────────────────┬─────────────────────┐
│ Confidence ≥ 90%    │ Confidence < 90%    │
│ Auto-Response       │ Manual Review       │
│ (draft for human    │ (with evidence)     │
│  approval)          │                     │
└─────────────────────┴─────────────────────┘
```

---

### Key Components to Build

#### 1. Playbook Executor

**Purpose:** Run diagnostic checks sequentially until root cause found or evidence exhausted.

**Implementation:**
```python
class PlaybookExecutor:
    def execute(self, category: str, load_id: str):
        # Load playbook for category
        playbook = load_playbook(category)

        # Execute checks sequentially
        for step in playbook.diagnostic_steps:
            result = self.execute_check(step, load_id)

            if result.is_conclusive:
                return result  # Early exit on definitive answer

        # If no conclusive result, return collected evidence
        return Evidence(
            category=category,
            checks_performed=...,
            recommendation="Manual review required"
        )
```

#### 2. MCP Integration Layer

**Purpose:** Standardize how Cassie calls OTR MCP and other data sources.

**Implementation:**
```python
class MCPClient:
    def __init__(self):
        self.otr_mcp = OTRMCPServer(url=..., auth=...)
        self.connect_mcp = ConnectMCPServer(url=..., auth=...)

    def check_eld_enabled(self, shipper_id: str, carrier_id: str) -> bool:
        result = self.connect_mcp.query(
            "network_configuration",
            params={"shipper": shipper_id, "carrier": carrier_id}
        )
        return result.get("eld_tracking_enabled", False)

    def get_asset_assignment(self, load_id: str) -> dict:
        result = self.otr_mcp.query(
            "asset_info",
            params={"load_id": load_id}
        )
        return {
            "truck_number": result.get("truck_number"),
            "trailer_number": result.get("trailer_number"),
            "device_id": result.get("device_id")
        }
```

#### 3. Pattern Matcher

**Purpose:** Match diagnostic results to patterns from Skills Library.

**Implementation:**
```python
class PatternMatcher:
    def __init__(self):
        self.patterns = load_all_patterns_from_skills_library()

    def match(self, evidence: Evidence) -> Pattern:
        for pattern in self.patterns:
            if pattern.matches(evidence):
                return pattern

        return Pattern.UNKNOWN
```

#### 4. Auto-Response Generator

**Purpose:** Generate customer response from pattern template.

**Implementation:**
```python
class ResponseGenerator:
    def generate(self, pattern: Pattern, evidence: Evidence) -> str:
        template = pattern.auto_response_template

        # Fill template variables
        response = template.format(
            load_number=evidence.load_id,
            root_cause_description=pattern.description,
            evidence_list=self.format_evidence(evidence),
            resolution_steps=pattern.resolution_steps,
            next_steps=pattern.next_steps
        )

        return response
```

---

## Part 11: Actionable Next Steps (This Week)

### For Engineering Team

**Monday:**
1. Review this gap analysis report
2. Identify decision loop bug location in Cassie codebase
3. Prioritize 5 basic diagnostic checks for Week 1-2 implementation

**Tuesday-Wednesday:**
4. Fix decision loop bug (replace elimination logic with positive matching)
5. Add timeout guard and fallback routing

**Thursday-Friday:**
6. Implement first diagnostic check: "ELD enabled at network level?"
7. Test on Case #2682612 (should now auto-resolve)
8. Implement second check: "Asset assigned?"
9. Test on historical cases

**Target:** By Friday EOW, bot auto-resolves 2 pattern types (20-30% of common cases).

---

### For Support Operations Team

**This Week:**
1. Validate the 5 HIGH-feasibility patterns proposed for Week 1-2:
   - ELD Not Enabled
   - Asset Not Assigned
   - Check Call Expiry
   - Duplicate SCAC
   - Feature Flag Disabled

2. Provide 10 historical cases for each pattern (50 cases total) for testing

3. Review and approve auto-response templates for these 5 patterns

**Target:** Engineering has validated test cases and approved templates by Friday.

---

### For Product Team

**This Week:**
1. Define success metrics for Phase 1:
   - What % auto-resolution is acceptable for production release?
   - What customer satisfaction threshold must be met?
   - What false positive rate is tolerable?

2. Approve phased rollout plan:
   - Week 9: Shadow mode (bot suggests, human decides)
   - Week 10: 10% of cases → monitor quality
   - Week 10: 50% of cases → monitor quality
   - Week 11: 100% rollout

**Target:** Clear go/no-go criteria defined by Friday.

---

## Part 12: Conclusion

### What's Working

✅ **Category Classification:** Cassie correctly identifies high-level categories (80-90% accuracy)
✅ **MCP Infrastructure:** 10 production MCP servers exist and are operational
✅ **Category Taxonomy:** Comprehensive 100+ row sheet with root cause patterns
✅ **Engineering Capability:** Team has skills to build diagnostic execution framework

### What's Broken

❌ **No Diagnostic Execution:** Bot stops at categorization instead of running checks
❌ **MCP Integration Gap:** MCP servers exist but Cassie doesn't call them
❌ **Decision Loop Bug:** Bot gets stuck on basic cases
❌ **No Auto-Resolution:** 100% of cases escalate to manual despite having automation potential

### Critical Path Forward

**Week 1-2:** Fix decision loop + implement 5 basic checks → **40-50% auto-resolution**
**Week 3-5:** Skills Library integration + playbook execution → **Diagnostic guidance for 80%**
**Week 6-8:** Scale to all HIGH/MEDIUM patterns → **60-70% auto-resolution**
**Week 9-11:** Production rollout with monitoring → **Live at scale**

### Key Insight

> **Sudhanshu's plan has the right phases but needs MORE SPECIFICITY on diagnostic execution and auto-resolution targets.**
>
> The plan should explicitly call out:
> 1. Playbook execution engine (not just "collaborative agents")
> 2. OTR MCP integration strategy (not just "data sources")
> 3. Category sheet conversion to Skills Library (not just "review")
> 4. Auto-response generation (currently missing)
> 5. Week-by-week auto-resolution metrics (currently vague)

### Recommendation

**Approve Sudhanshu's timeline (11 weeks) BUT require:**
1. Add explicit tasks for playbook execution, MCP integration, auto-response
2. Set measurable targets: 40% by Week 2, 60% by Week 8
3. Start with quick wins (5 basic checks) before multi-agent refactor
4. Use Skills Library format for category sheet (structured approach)

**With these clarifications, the plan is solid and achievable.**

---

**Report Prepared By:** AI R&D Solutions Engineer
**Date:** January 27, 2026
**Next Review:** February 3, 2026 (after Week 1 quick wins)
