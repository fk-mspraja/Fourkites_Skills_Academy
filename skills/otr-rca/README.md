# OTR RCA Skill - Documentation

**Skill ID:** `otr_rca`
**Name:** OTR Tracking & Operations RCA
**Version:** 1.0.0
**Status:** POC
**Created:** 2026-01-14
**Owner:** MSP Raja, AI R&D Solutions Engineer

---

## Overview

The OTR RCA (Over-The-Road Root Cause Analysis) skill is a specialized investigative module that automates the troubleshooting of ground (OTR) tracking issues. It mirrors the workflow that Prashant (Carrier/OTR Operations) uses to debug real-world tracking problems.

### What This Skill Does

The skill takes a support ticket about an OTR tracking issue and:

1. **Systematically investigates** the issue across multiple data sources
2. **Identifies the root cause** (ELD config, network, carrier API, device, or system issues)
3. **Gathers evidence** to support the diagnosis
4. **Recommends actions** to resolve the issue
5. **Escalates intelligently** when human review is needed

### Why It Matters

Support analysts currently spend **20-30 minutes per ticket** on OTR issues, with **75% of time spent gathering data** from 4-6 different systems. This skill aims to reduce investigation time to **8-12 minutes** by automating data collection and correlation.

---

## Architecture

### File Structure

```
skills/otr-rca/
├── SKILL.yaml                          ← This metadata file (YOU ARE HERE)
├── README.md                           ← Documentation overview
├── decision_trees/
│   └── tracking_issue_classifier.yaml  ← Investigation flow
├── patterns/
│   ├── eld_not_enabled_network.yaml
│   ├── network_relationship_missing.yaml
│   ├── load_not_found.yaml
│   ├── carrier_api_down.yaml
│   ├── gps_null_timestamps.yaml
│   ├── device_config_wrong.yaml
│   ├── carrier_not_configured.yaml
│   ├── late_assignment.yaml
│   ├── stale_location.yaml
│   └── callback_failure.yaml
├── test_cases/                         ← 20 real ticket examples
│   ├── case_eld_offline_1.yaml
│   ├── case_network_missing_1.yaml
│   └── ... (20 total)
└── knowledge_base.md                   ← OTR domain knowledge
```

---

## Key Sections Explained

### 1. Triggers (When to Use This Skill)

The router invokes this skill when it detects:

**Keywords:** "load not tracking", "no GPS", "ELD offline", "network relationship", etc.

**Issue Categories:**
- `tracking_not_working` - Load not showing position
- `eld_offline` - ELD device offline or not responding
- `network_missing` - Carrier-shipper relationship missing
- `gps_failure` - GPS data invalid or stale
- `carrier_api_failure` - Carrier API integration down
- `callback_failure` - Updates not being delivered
- `device_configuration` - Device mapped incorrectly
- `late_assignment` - Load assigned too late

**Load Mode Conditions:**
- `load.mode == 'OTR'` (Over-the-Road)
- `load.mode == 'GROUND'`
- `load.mode == 'LTL'` (Less Than Truckload)
- `load.mode == 'FTL'` (Full Truckload)

### 2. Capabilities (What It Can Check)

The skill has 9 specialized capabilities:

| Capability | Time | Confidence | Purpose |
|-----------|------|-----------|---------|
| **Platform Check** | 2-3 min | High | See customer view, verify load exists |
| **ELD Config Check** | 3-5 min | High | Verify ELD enabled, device online |
| **Network Relationship** | 2-3 min | High | Verify carrier-shipper setup |
| **Carrier API Health** | 3-5 min | High | Check API status and auth |
| **GPS/Location Analysis** | 5-10 min | Medium | Validate GPS data quality |
| **Callback Delivery** | 5-8 min | Medium | Verify webhook delivery |
| **SigNoz Logs** | 10-15 min | Medium | Deep dive into processing logs |
| **Correlate Findings** | 5-10 min | High | Link evidence across sources |

### 3. Data Sources (Where It Looks)

The skill queries these sources in order:

**Platform & APIs:**
- `tracking_api` - Load status, positions, device info
- `company_api` - Network relationships, ELD config
- `data_hub_api` - Quick OTR aggregation
- `cassie` - Carrier lookup, capabilities
- `foursight` - Load patterns, anomalies

**Logs & Database:**
- `signoz` - Processing logs (tracking_worker_global, device_integration_service)
- `redshift` - Load history, relationship status, device events

**Files & Metadata:**
- `s3` - Device logs, ELD data, carrier integrations

### 4. Patterns (Known Issue Signatures)

The skill recognizes 10 common OTR issue patterns:

```yaml
1. eld_not_enabled_network.yaml
   - ELD disabled + no network relationship
   - Symptom: Device sending data but not tracked

2. network_relationship_missing.yaml
   - Carrier-shipper relationship doesn't exist
   - Symptom: Load stuck in "Awaiting Tracking"

3. load_not_found.yaml
   - Load ID doesn't exist in system
   - Symptom: Platform shows "Load not found"

4. carrier_api_down.yaml
   - Carrier API integration failing
   - Symptom: All loads from this carrier not tracking

5. gps_null_timestamps.yaml
   - GPS coordinates exist but timestamps null/stale
   - Symptom: Position shown but marked as old

6. device_config_wrong.yaml
   - Device mapped incorrectly or ELD config incomplete
   - Symptom: Device online but no position updates

7. carrier_not_configured.yaml
   - Carrier exists but not set up for tracking
   - Symptom: Carrier doesn't exist in config

8. late_assignment.yaml
   - Load assigned to carrier hours after creation
   - Symptom: No tracking history before assignment

9. stale_location.yaml
   - Last position update is hours/days old
   - Symptom: Load at warehouse but showing old stop

10. callback_failure.yaml
    - Updates processed but callbacks not delivered
    - Symptom: Platform has data but customer doesn't
```

### 5. Confidence Thresholds

The skill uses **three confidence levels** to determine next steps:

```
Confidence >= 90% (auto_resolve)
├─ Action: Present finding with high confidence
├─ Message: "Root cause identified with 95% confidence"
└─ Next: Recommend specific action

Confidence 80-90% (human_review)
├─ Action: Present finding + recommendation
├─ Message: "Likely cause identified, here's what to do"
└─ Next: Ask human to verify

Confidence < 80% (escalate)
├─ Action: Present evidence gathered so far
├─ Message: "Multiple possible causes, need human review"
└─ Next: Handoff to support analyst
```

### 6. Root Cause Enum (Possible Diagnoses)

The skill can identify 16 specific root causes:

**ELD/Device Issues:**
- `eld_not_enabled` - ELD tracking disabled
- `eld_offline` - ELD device offline
- `device_misconfigured` - Device mapped wrong

**Network/Integration Issues:**
- `network_relationship_missing` - Carrier-shipper relationship doesn't exist
- `network_relationship_inactive` - Relationship exists but disabled
- `carrier_not_configured` - Carrier not in system
- `carrier_api_down` - Carrier API integration failing
- `carrier_api_auth_failed` - API authentication failed

**Data/Processing Issues:**
- `gps_data_invalid` - GPS coordinates are invalid (lat/lon out of range)
- `gps_timestamps_stale` - GPS data too old
- `callback_delivery_failed` - Webhooks not being sent
- `callback_endpoint_unreachable` - Customer endpoint down

**System Issues:**
- `processing_error` - Error in tracking pipeline
- `late_assignment` - Load assigned after delay
- `system_bug` - Unexpected system behavior
- `unknown` - Could not determine

### 7. Human Handoff Triggers

The skill escalates to humans in these scenarios:

**Low Confidence (< 0.7):**
```
"I've gathered data but confidence is low.

Evidence collected:
- Platform check: {result}
- ELD config: {result}
- Network relationship: {result}

What should I check next?"
```

**Stuck After 6 Steps:**
```
"I've checked Platform, ELD, Network, Carrier API, and Logs.
Still couldn't determine root cause definitively.
What else should I investigate?"
```

**Contradictory Data:**
```
"Data sources don't agree:
- Platform shows tracking enabled
- ELD config shows ELD disabled
- Network relationship is {status}

Which source should I trust?"
```

**Critical Decision (Requires Approval):**
```
"Root cause identified: {cause}
Recommended action: {action}

This will {impact}

Should I proceed? [Yes] [No] [Modify]"
```

### 8. Output Format (What You Get Back)

The skill returns a structured investigation result:

```json
{
  "root_cause": "eld_not_enabled",
  "root_cause_category": "configuration_issue",
  "issue_scope": "carrier_wide",
  "confidence_score": 0.94,

  "evidence": [
    {
      "source": "tracking_api",
      "finding": "ELD field is false for all XYZ Carrier devices",
      "confidence": 0.95,
      "timestamp": "2026-01-14T10:30:00Z"
    },
    {
      "source": "signoz_logs",
      "finding": "No device updates received in 48 hours",
      "confidence": 0.90,
      "timestamp": "2026-01-14T10:31:00Z"
    }
  ],

  "recommended_action": {
    "action": "enable_eld",
    "priority": "high",
    "assignee": "carrier_operations",
    "human_approval_required": true
  },

  "time_to_investigate": "PT8M35S",

  "steps_completed": [
    {"step_name": "platform_check", "result": "load_exists", "duration": "PT2M"},
    {"step_name": "eld_config_check", "result": "eld_disabled", "duration": "PT4M"}
  ],

  "escalation": {
    "needed": false,
    "type": null
  },

  "next_steps": [
    "Contact XYZ Carrier to enable ELD tracking",
    "Verify device activation in carrier portal",
    "Wait for 24-48 hours for updates to begin"
  ]
}
```

### 9. Metrics Tracked

The skill tracks performance against baseline and targets:

**Baseline (Current Manual Process):**
- Time: 20-30 minutes
- Tools used: 4-6
- Data gathering: 75% of time
- Analysis: 25% of time

**Target (With Automation):**
- Time: 8-12 minutes (60% reduction)
- Accuracy: 85%
- Human handoff rate: 15-20%
- Automation rate: 60%
- Tools used: 2-3

**Metrics Tracked:**
- Time to complete
- Steps executed
- API calls made
- Log queries executed
- Root cause accuracy
- Human handoffs
- Escalations
- User satisfaction
- False positives
- False negatives

---

## Investigation Flow (Decision Tree)

The skill follows a structured decision tree (in `decision_trees/tracking_issue_classifier.yaml`):

### Entry Point: Step 1 - Platform Check

```
┌─ Check load existence
├─ Is load in system?
│  ├─ NO → End (root_cause: load_not_found)
│  └─ YES → Continue
│
├─ Check tracking enabled?
│  ├─ NO → Goto Step 2 (ELD Config)
│  └─ YES → Continue
│
├─ Check last position update
│  ├─ NULL → Goto Step 2 (ELD Config)
│  ├─ STALE (>24h) → Goto Step 5 (SigNoz Logs)
│  └─ FRESH → Goto Step 2 (ELD Config)
```

### Step 2 - ELD Configuration Check

```
├─ Is ELD enabled?
│  ├─ NO → Check network relationship (Step 3)
│  └─ YES → Check device online (Step 4)
│
├─ Is device online?
│  ├─ NO (offline) → Check last heartbeat
│  │   ├─ >48h ago → root_cause: eld_offline
│  │   └─ Recent → Check carrier API (Step 4)
│  └─ YES → Check carrier API (Step 4)
```

### Step 3 - Network Relationship

```
├─ Does relationship exist?
│  ├─ NO → root_cause: network_relationship_missing
│  └─ YES → Continue
│
├─ Is relationship active?
│  ├─ NO → root_cause: network_relationship_inactive
│  └─ YES → Continue
│
├─ Is tracking enabled?
│  ├─ NO → root_cause: carrier_not_configured
│  └─ YES → Goto Step 4 (Carrier API)
```

### Step 4 - Carrier API Health

```
├─ Is API endpoint configured?
│  ├─ NO → root_cause: carrier_not_configured
│  └─ YES → Continue
│
├─ Is API responding?
│  ├─ NO (timeout/down) → root_cause: carrier_api_down
│  └─ YES → Continue
│
├─ Is auth working?
│  ├─ NO (401/403) → root_cause: carrier_api_auth_failed
│  └─ YES → Goto Step 5 (Logs)
│
├─ Recent updates received?
│  ├─ NO → root_cause: carrier_not_sending_data
│  └─ YES → Goto Step 5 (Logs)
```

### Step 5 - SigNoz Logs Analysis

```
├─ Any processing errors?
│  ├─ YES → Analyze error codes
│  └─ NO → Continue
│
├─ Are GPS coordinates valid?
│  ├─ NO (null/out of range) → root_cause: gps_data_invalid
│  └─ YES → Continue
│
├─ Are timestamps fresh?
│  ├─ NO (stale) → root_cause: gps_timestamps_stale
│  └─ YES → Correlate findings (Step 6)
```

### Step 6 - Correlate Findings

```
├─ Do all sources agree?
│  ├─ YES → Strong confidence, present finding
│  └─ NO → Identify discrepancy
│
├─ Can discrepancy be explained?
│  ├─ YES → Adjust confidence, continue
│  └─ NO → Request human review
│
├─ Is confidence >= 90%?
│  ├─ YES → Present with high confidence
│  └─ NO (70-90%) → Present with recommendation
```

---

## Usage Examples

### Example 1: ELD Not Enabled

**Ticket:** "Load U123 not showing position updates for XYZ Carrier"

**Skill Execution:**

1. **Platform Check** (2 min)
   - Load U123 exists ✓
   - Tracking enabled: YES ✓
   - Last position: 2 days ago (stale)

2. **ELD Config Check** (4 min)
   - ELD enabled: NO ✗
   - Carrier: XYZ Carrier
   - All devices for this carrier: ELD disabled

3. **Confidence: 95%**
   - Root Cause: `eld_not_enabled`
   - Category: `configuration_issue`
   - Scope: `carrier_wide`

4. **Recommendation:**
   - Action: `enable_eld`
   - Assignee: `carrier_operations`
   - Message: "Contact XYZ Carrier to enable ELD integration. Once enabled, position updates should resume within 24 hours."

**Time to Complete:** 6 minutes (vs. 25 minutes manual)

### Example 2: Network Relationship Missing

**Ticket:** "Load stuck in 'Awaiting Tracking' for ABC Freight"

**Skill Execution:**

1. **Platform Check** (3 min)
   - Load U124 exists ✓
   - Current state: AWAITING_TRACKING_INFO
   - No position data

2. **ELD Config Check** (4 min)
   - ELD enabled: YES ✓
   - Device online: YES ✓

3. **Network Relationship Check** (2 min)
   - Relationship exists: NO ✗
   - Carrier: ABC Freight (ID: CARR_456)
   - Shipper: Customer Corp (ID: SHIP_789)

4. **Confidence: 98%**
   - Root Cause: `network_relationship_missing`
   - Category: `configuration_issue`
   - Scope: `single_load` (but likely affects all ABC Freight loads)

5. **Recommendation:**
   - Action: `create_network_relationship`
   - Assignee: `customer_support` (requires human approval)
   - Message: "Network relationship between ABC Freight and Customer Corp doesn't exist. This must be created before tracking can begin. Contact customer to set up integration."

**Time to Complete:** 9 minutes (vs. 28 minutes manual)

### Example 3: Callback Delivery Failure

**Ticket:** "Customer says they're not receiving position updates"

**Skill Execution:**

1. **Platform Check** (2 min)
   - Load U125 exists ✓
   - Tracking enabled: YES ✓
   - Last position: 15 minutes ago (fresh)

2. **ELD Config Check** (3 min)
   - ELD enabled: YES ✓
   - Device online: YES ✓

3. **Network Relationship Check** (2 min)
   - Relationship exists: YES ✓
   - Active: YES ✓

4. **Carrier API Check** (4 min)
   - API responding: YES ✓
   - Recent updates: YES ✓ (5 updates in last hour)

5. **Callback Delivery Check** (6 min)
   - Endpoint configured: YES ✓
   - Endpoint reachable: NO ✗ (HTTP 502)
   - Last successful delivery: 3 days ago

6. **Confidence: 94%**
   - Root Cause: `callback_endpoint_unreachable`
   - Category: `customer_issue`
   - Scope: `single_load`

7. **Recommendation:**
   - Action: `customer_communication_only`
   - Assignee: `customer_success`
   - Message: "We're tracking the load correctly and sending updates, but your webhook endpoint is returning errors (HTTP 502). Please check your server health and verify the endpoint URL is correct."

**Time to Complete:** 8 minutes (vs. 22 minutes manual)

---

## Integration Points

### With Router Agent

The router classifies incoming tickets and invokes this skill:

```python
router.route(
    question="Load U123 not tracking for XYZ Carrier",
    context={
        "load_id": "U123",
        "issue_category": "load_not_tracking",
        "load_mode": "OTR"
    }
)
→ Returns: investigation_result from otr_rca skill
```

### With Other Skills

This skill may coordinate with:

- **`ocean_debugging`** - If load is in intermodal mode (ocean + OTR)
- **`callbacks_analytics`** - For callback-specific deep dives

### With External Systems

**Data Sources:**
- Tracking API (via MCP server)
- Company API (via MCP server)
- SigNoz (via REST or direct ClickHouse)
- Redshift (via SQL)

**Output Destinations:**
- Salesforce (update ticket with findings)
- Slack (alert for critical issues)
- Dashboard (metrics tracking)

---

## Testing

### Test Case Organization

20 test cases organized by category:

**ELD Issues (5 cases):**
- ELD disabled on device
- ELD offline (no heartbeat)
- ELD sync errors
- Device mapping wrong
- Device not configured

**Network Issues (4 cases):**
- Relationship missing
- Relationship inactive
- Carrier not configured
- Tracking disabled on relationship

**Carrier Issues (4 cases):**
- Carrier API down
- Carrier API auth failed
- Carrier not sending updates
- Carrier data wrong format

**GPS Issues (3 cases):**
- GPS coordinates null
- GPS timestamps stale
- GPS coordinates out of range

**Callback Issues (2 cases):**
- Callback endpoint down
- Callback delivery errors

**System Issues (2 cases):**
- Processing pipeline error
- Late load assignment

### Running Tests

```bash
# Run all tests
python -m pytest skills/otr-rca/test_cases/

# Run specific category
python -m pytest skills/otr-rca/test_cases/test_eld_issues.py

# Run with coverage
pytest --cov=skills/otr-rca skills/otr-rca/test_cases/
```

---

## Knowledge Base

The skill references domain knowledge from:

- **PRASHANT_SESSION_PREP.md** - Prashant's workflow and mental model
- **SUPPORT-TEAM-MENTAL-MODEL.md** - Support team processes
- **SUPPORT-SKILLS-AND-TOOLS-CATALOG.md** - Available tools and APIs
- **Confluence Docs:**
  - Carrier OTR Configuration Guide
  - ELD Integration Requirements
  - OTR Troubleshooting Workflows

See `knowledge_base.md` for detailed reference material.

---

## Performance Targets

### Speed

- **Baseline:** 20-30 minutes per ticket
- **Target:** 8-12 minutes per ticket
- **Goal:** 60% reduction

### Accuracy

- **Target Accuracy:** 85%
- **Target Auto-Resolution:** 60% of cases
- **Human Handoff Rate:** 15-20%

### Cost

- **LLM Token Usage:** Optimize to minimize API calls
- **API Calls:** Target 2-3 systems vs. current 4-6
- **Database Queries:** Minimize Redshift load

---

## Roadmap

### Phase 1 (Current - POC)
- ✅ SKILL.yaml definition
- ✅ Triggers and capabilities
- ⏳ Decision tree implementation
- ⏳ Pattern definitions
- ⏳ Test cases

### Phase 2 (Integration)
- ⏳ Router integration
- ⏳ API implementations
- ⏳ Human handoff UI
- ⏳ Metrics collection

### Phase 3 (Enhancement)
- ⏳ Multi-language support
- ⏳ Advanced anomaly detection
- ⏳ Proactive issue detection
- ⏳ Predictive maintenance

---

## Support & Contact

**Skill Owner:** MSP Raja, AI R&D Solutions Engineer

**Questions?**
- Slack: #ai-rca-support
- Email: msps@fourkites.com

**Report Issues:**
- Create GitHub issue: `[OTR-RCA] Issue description`
- Include: Load ID, error logs, expected behavior

**Contribute:**
- Submit patterns: `patterns/new_pattern.yaml`
- Add test cases: `test_cases/case_*.yaml`
- Improve docs: PRs welcome!

---

## File Manifest

| File | Purpose | Status |
|------|---------|--------|
| `SKILL.yaml` | Skill metadata & configuration | ✅ Complete |
| `README.md` | This documentation | ✅ Complete |
| `decision_trees/tracking_issue_classifier.yaml` | Investigation flow | ⏳ TODO |
| `patterns/*.yaml` | Issue signatures (10 files) | ⏳ TODO |
| `test_cases/*.yaml` | Test scenarios (20 files) | ⏳ TODO |
| `knowledge_base.md` | Domain knowledge | ⏳ TODO |

---

**Last Updated:** 2026-01-14
**Status:** POC - Ready for Decision Tree & Pattern Implementation
**Next Steps:** Create decision_trees/tracking_issue_classifier.yaml
