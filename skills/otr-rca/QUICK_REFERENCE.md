# OTR RCA Skill - Quick Reference

**Skill:** OTR Tracking & Operations RCA | **ID:** `otr_rca` | **Version:** 1.0.0

---

## When to Use This Skill

Invoke when ticket mentions:
- **Keywords:** "not tracking", "no GPS", "no ELD", "network relationship", "callback failure", etc.
- **Load Mode:** OTR, GROUND, LTL, FTL
- **Issue Type:** Tracking issue, device config, carrier integration

---

## What It Does (In 30 Seconds)

1. **Checks Platform** - Verifies load exists and tracking status
2. **Checks ELD Config** - Confirms ELD enabled and device online
3. **Checks Network** - Verifies carrier-shipper relationship
4. **Checks Carrier API** - Tests carrier integration health
5. **Analyzes Logs** - Dives into SigNoz for processing errors
6. **Correlates** - Combines findings into root cause

**Result:** Root cause identified with confidence score + recommended action

**Time:** 8-12 minutes (vs. 20-30 manual)

---

## 16 Root Causes It Can Identify

| Category | Root Causes |
|----------|------------|
| **ELD/Device** | eld_not_enabled, eld_offline, device_misconfigured |
| **Network** | network_relationship_missing, network_relationship_inactive, carrier_not_configured |
| **Carrier API** | carrier_api_down, carrier_api_auth_failed |
| **GPS Data** | gps_data_invalid, gps_timestamps_stale |
| **Callbacks** | callback_delivery_failed, callback_endpoint_unreachable |
| **System** | processing_error, late_assignment, system_bug, unknown |

---

## Investigation Steps

### Step 1: Platform Check (2-3 min)
```
✓ Load exists?
✓ Tracking enabled?
✓ Last position time?
→ Decision: Proceed or diagnose immediately
```

### Step 2: ELD Config (3-5 min)
```
✓ ELD enabled?
✓ Device online?
✓ Last heartbeat?
→ Decision: ELD issue or check network
```

### Step 3: Network Relationship (2-3 min)
```
✓ Relationship exists?
✓ Relationship active?
✓ Tracking enabled?
→ Decision: Network issue or check carrier API
```

### Step 4: Carrier API Health (3-5 min)
```
✓ Endpoint configured?
✓ API responding?
✓ Auth working?
✓ Recent updates?
→ Decision: API issue or check logs
```

### Step 5: SigNoz Logs (10-15 min)
```
✓ Processing errors?
✓ GPS coordinates valid?
✓ Timestamps fresh?
→ Decision: Identify data issue
```

### Step 6: Correlate Findings (5-10 min)
```
✓ All sources agree?
✓ Confidence >= 90%?
→ Decision: Present finding or ask human
```

---

## Confidence Thresholds

| Score | Action | Message |
|-------|--------|---------|
| **≥ 90%** | Auto-resolve | "Root cause identified with 94% confidence" |
| **80-90%** | Review | "Likely cause found, recommended action:" |
| **< 80%** | Escalate | "Need human review, multiple possibilities" |

---

## Recommended Actions (12 Options)

- `enable_eld` - Enable ELD tracking on device
- `restart_device` - Restart tracking device
- `restart_eld_sync` - Restart ELD sync service
- `create_network_relationship` - Create carrier-shipper relationship
- `activate_network_relationship` - Reactivate inactive relationship
- `configure_carrier` - Add carrier to system
- `contact_carrier` - Reach out to carrier
- `update_device_config` - Fix device mapping
- `reprocess_load` - Retry load processing
- `escalate_to_carrier` - Create carrier escalation ticket
- `escalate_to_engineering` - Create engineering ticket
- `customer_communication_only` - Explain issue to customer

---

## Data Sources Used

| Source | Time | Confidence |
|--------|------|-----------|
| Tracking API | 1-2 min | High |
| Company API | 2-3 min | High |
| SigNoz Logs | 10-15 min | Medium |
| Redshift DB | 3-5 min | Medium |
| CASSIE Tool | 1-2 min | High |

---

## Output Example

```json
{
  "root_cause": "eld_not_enabled",
  "root_cause_category": "configuration_issue",
  "issue_scope": "carrier_wide",
  "confidence_score": 0.94,

  "evidence": [
    {
      "source": "company_api",
      "finding": "ELD disabled for all XYZ Carrier devices",
      "confidence": 0.95
    },
    {
      "source": "signoz_logs",
      "finding": "No device updates in 48 hours",
      "confidence": 0.90
    }
  ],

  "recommended_action": {
    "action": "enable_eld",
    "priority": "high",
    "assignee": "carrier_operations",
    "human_approval_required": true
  },

  "time_to_investigate": "PT8M35S",

  "next_steps": [
    "Contact XYZ Carrier to enable ELD",
    "Verify device activation",
    "Wait 24-48 hours for updates"
  ]
}
```

---

## Common Patterns Recognized

1. **ELD Not Enabled + No Network** → Root cause: ELD disabled
2. **No Relationship + Awaiting Tracking** → Root cause: Network missing
3. **Load Not Found** → Root cause: Load ID wrong
4. **All Carrier Loads Down** → Root cause: Carrier API down
5. **GPS Null + Recent Logs** → Root cause: GPS data invalid
6. **Device Mapped Wrong** → Root cause: Device config error
7. **Carrier Exists But Not Configured** → Root cause: Carrier not set up
8. **Load Assigned Late** → Root cause: Late assignment
9. **Position 24h Old** → Root cause: Stale location
10. **Updates in Platform But Not Customer** → Root cause: Callback failure

---

## When It Asks for Human Help

The skill escalates when:

```
1. Confidence drops below 70%
   → "I've gathered data but need your input"

2. After checking 6 steps without clear cause
   → "Tried everything, what else should I check?"

3. Data sources contradict each other
   → "Platform shows X but logs show Y, which is right?"

4. Action requires critical change
   → "Need to create relationship, approve? [Yes/No]"
```

---

## Performance Metrics

### Baseline (Manual)
- Time: 20-30 minutes
- Tools: 4-6 systems
- Data gathering: 75% of effort
- Accuracy: Variable

### Target (With Skill)
- Time: 8-12 minutes (60% faster)
- Tools: 2-3 systems
- Data gathering: 40% of effort
- Accuracy: 85%
- Automation: 60%

---

## Integration Checklist

- [ ] Router configured to recognize OTR triggers
- [ ] Tracking API MCP server available
- [ ] Company API MCP server available
- [ ] SigNoz credentials configured
- [ ] Redshift access granted
- [ ] Test cases passing
- [ ] Decision tree implemented
- [ ] Patterns defined
- [ ] Escalation templates created
- [ ] Metrics dashboard configured

---

## Files in This Skill

| File | Purpose |
|------|---------|
| `SKILL.yaml` | Metadata, triggers, capabilities, data sources |
| `README.md` | Full documentation with examples |
| `QUICK_REFERENCE.md` | This file - quick lookup |
| `decision_trees/` | Investigation workflow |
| `patterns/` | 10 known issue signatures |
| `test_cases/` | 20 real ticket examples |
| `knowledge_base.md` | Domain knowledge references |

---

## Pro Tips

1. **Start with Platform Check** - Fastest way to eliminate "load not found"
2. **ELD Config is 30% of OTR issues** - Check early if load is recent
3. **Network Relationship is #1 cause** - Like ocean's company_relationships table
4. **Carrier API status matters** - Affects entire carrier's loads
5. **SigNoz logs take time** - Parallelize other checks while waiting
6. **Confidence thresholds are strict** - Better to escalate than guess wrong
7. **Callback failures are customer issue** - Communicate clearly about endpoint

---

## Contact & Support

**Owner:** MSP Raja (msps@fourkites.com)
**Slack:** #ai-rca-support
**Issues:** Create GitHub issue with `[OTR-RCA]` prefix

---

**Last Updated:** 2026-01-14 | **Status:** POC | **Version:** 1.0.0
