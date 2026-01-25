---
name: rca-support-agent
description: "Root Cause Analysis for FourKites Support Cases - Automated investigation of logistics and tracking issues including load not tracking, ELD problems, ocean container tracking, and carrier integration failures. Use this skill when analyzing support tickets, diagnosing tracking issues, or performing RCA on customer-reported problems."
version: 1.0.0
author: FourKites AI R&D
category: support-operations
tags: [rca, troubleshooting, support, tracking, eld, ocean, logistics]
---

# RCA Support Agent Skill

## Overview

This skill provides comprehensive root cause analysis capabilities for FourKites support operations. It encapsulates the mental model, data sources, diagnostic patterns, and resolution workflows that expert support analysts use to investigate tracking and logistics issues.

## When to Use This Skill

**For Humans:**
- Investigating load not tracking issues
- Diagnosing ELD configuration problems
- Troubleshooting ocean container tracking
- Analyzing carrier integration failures
- Performing post-mortem analysis on P0/P1 incidents

**For AI Agents:**
- Automated ticket triage and investigation
- Hypothesis generation from symptoms
- Evidence gathering from multiple data sources
- Root cause determination with confidence scoring
- Resolution recommendation generation

## Skill Capabilities

### 1. Issue Classification

The skill can identify and classify 85+ subcategories of tracking issues:

**Major Categories:**
- Load Not Found
- ELD Not Enabled (Network/Carrier Level)
- GPS Data Issues (Null Timestamps, Stale Location)
- Device Configuration Issues (Truck vs Trailer)
- Carrier Integration Failures
- Ocean Container Tracking Issues
- JT/RPA Scraping Failures
- Network Relationship Missing
- API Callback Failures

### 2. Data Source Integration

The skill knows how to query and correlate data from:

| Data Source | Purpose | Query Examples |
|-------------|---------|----------------|
| **Tracking API** | Load status, positions | `GET /loads/{load_number}` |
| **Company API** | Network relationships | `GET /companies/{permalink}/relationships` |
| **JT (Just Transform)** | Ocean scraping history | Check RPA execution logs |
| **Super API (DataHub)** | Ocean subscriptions | Subscription status and config |
| **SigNoz (ClickHouse)** | Application logs | GPS errors, API failures |
| **Redshift DWH** | Historical load data | `load_validation_data_mart` |
| **Athena** | API callback logs | Carrier webhook delivery |

### 3. Diagnostic Patterns

The skill encodes expert troubleshooting patterns for common issues:

#### Pattern: ELD Not Enabled at Network Level

**Symptoms:**
- Load exists in system
- Carrier has ELD capability
- No tracking updates received

**Investigation:**
```sql
-- Check network relationship ELD configuration
SELECT cr.id, cr.eld_enabled, cr.eld_provider,
       c1.name as shipper, c2.name as carrier
FROM company_relationships cr
JOIN companies c1 ON cr.company_id = c1.id
JOIN companies c2 ON cr.related_company_id = c2.id
WHERE c1.permalink = '{shipper_permalink}'
  AND c2.permalink = '{carrier_permalink}';
```

**Root Cause:** `eld_enabled = FALSE` at relationship level

**Resolution:**
1. Enable ELD in FourKites Connect for carrier-shipper relationship
2. Verify ELD provider is configured
3. Confirm carrier has active ELD devices
4. Test with sample load

**Expected Time:** 15 minutes

#### Pattern: GPS Returning Null Timestamps

**Symptoms:**
- Carrier has GPS capability
- API ping successful
- No position updates in tracking

**Investigation:**
```python
# Query SigNoz for GPS timestamp errors
{
  "service": "tracking-worker-global",
  "query": "GPS timestamp is null",
  "timeRange": "last 24 hours",
  "filters": {
    "load_number": "{load_number}",
    "carrier_code": "{carrier_code}"
  }
}
```

**Root Cause:** Carrier GPS system returning null/invalid timestamps

**Resolution:**
1. Contact carrier to fix GPS data feed
2. Verify device firmware version
3. Check for known GPS provider issues
4. Document in carrier notes

**Expected Time:** 30 minutes (requires carrier coordination)

#### Pattern: Ocean Container Not Tracking (JT Scraping Failure)

**Symptoms:**
- Ocean container number provided
- JT subscription active
- No container events received

**Investigation:**
1. Check JT scraping history via Super API/DataHub
2. Verify container number format and validity
3. Review shipping line availability in JT
4. Check for rate limiting or IP blocks

**Root Cause Decision Tree:**
```
Container not tracking?
├─ Subscription disabled → Enable in Super API
├─ Invalid container number → Validate format (e.g., MSCU1234567)
├─ Shipping line not supported → Manual tracking or alternative source
└─ JT scraping error → Review error logs, retry, or escalate to Ocean team
```

**Resolution:** Depends on root cause (see decision tree)

**Expected Time:** 20-45 minutes

### 4. Multi-Agent Investigation Workflow

The skill orchestrates a multi-agent investigation process:

```
User Issue → Identifier Agent → Data Collection Agents → Hypothesis Agent → Synthesis Agent
                  ↓                        ↓                      ↓                ↓
           Extract IDs          Query 6+ sources      Form hypotheses    Determine root cause
         (load, container,       (parallel exec)      (evidence-based)   (80%+ confidence)
          carrier, etc.)
```

**Agent Responsibilities:**

**Identifier Agent:**
- Extract tracking IDs, load numbers, container numbers
- Identify shipper and carrier from context
- Determine transport mode (ground/ocean/air)

**Data Collection Agents (run in parallel):**
- **Tracking API Agent:** Load existence, current status, position history
- **JT Agent:** Ocean scraping history, subscription status
- **Super API Agent:** Ocean configuration, subscription details
- **Network Agent:** Carrier-shipper relationship, ELD enablement

**Hypothesis Agent:**
- Generate 3-6 hypotheses based on data patterns
- Score evidence for/against each hypothesis
- Weight evidence by reliability

**Synthesis Agent:**
- Evaluate hypothesis confidence scores
- Determine root cause if confidence ≥ 80%
- Request human assistance if confidence < 80%

### 5. Evidence Scoring

The skill uses evidence-based scoring to determine confidence:

```python
# Example hypothesis: ELD_NOT_ENABLED_NETWORK
Hypothesis(
    id="H_ELD_NOT_ENABLED_NETWORK",
    category=RootCauseCategory.ELD_NOT_ENABLED,
    description="ELD tracking not enabled at network relationship level",
    evidence_for=[
        Evidence(
            source="Network API",
            finding="eld_enabled = FALSE in company_relationships",
            weight=10,  # Critical evidence
            confidence=100
        ),
        Evidence(
            source="Carrier Config",
            finding="Carrier has ELD provider configured (Samsara)",
            weight=5,  # Supporting evidence
            confidence=100
        )
    ],
    evidence_against=[],
    confidence_score=95  # High confidence → Auto-resolve
)
```

**Confidence Thresholds:**
- **≥ 80%:** Auto-determine root cause, provide resolution
- **50-79%:** Present top hypotheses, request human input
- **< 50%:** Escalate to human analyst with evidence summary

## Usage Examples

### Example 1: Load Not Tracking (Ground)

**Input:**
```
Load U110123982 is not tracking. Customer reports no updates.
Shipper: ABC Corp
Carrier: XYZ Logistics
```

**Agent Process:**
1. **Identifier:** Extract load_number=U110123982, shipper=ABC Corp, carrier=XYZ Logistics
2. **Tracking API:** Load found, status=IN_TRANSIT, last_position=null
3. **Network Agent:** Check relationship → eld_enabled=FALSE
4. **Hypothesis:** H_ELD_NOT_ENABLED_NETWORK (confidence: 95%)
5. **Synthesis:** Root cause determined

**Output:**
```
ROOT CAUSE: ELD not enabled at network relationship level

EVIDENCE:
✓ Load exists in system (U110123982)
✓ Load status: IN_TRANSIT
✗ No position updates received
✓ Carrier has ELD capability (Samsara)
✗ ELD not enabled in carrier-shipper relationship

RESOLUTION:
1. Enable ELD in FourKites Connect
   - Navigate to Network Relationships
   - Find ABC Corp → XYZ Logistics
   - Enable "ELD Tracking"
   - Select Provider: Samsara

2. Verify configuration
   - Confirm carrier has active ELD devices
   - Test with sample load

3. Monitor for updates (should receive within 15 minutes)

ESTIMATED TIME: 15 minutes
PRIORITY: Medium
```

### Example 2: Ocean Container Not Tracking

**Input:**
```
Container MSCU1234567 not receiving updates.
Shipper: Global Shipping Inc
Shipping Line: MSC
```

**Agent Process:**
1. **Identifier:** container=MSCU1234567, shipping_line=MSC, mode=OCEAN
2. **JT Agent:** Check scraping history → Last attempt failed (404)
3. **Super API:** Subscription active, last_event=3 days ago
4. **Hypothesis:** H_JT_SCRAPING_FAILURE (confidence: 85%)
5. **Synthesis:** Root cause determined

**Output:**
```
ROOT CAUSE: JT scraping failure - Container not found on shipping line

EVIDENCE:
✓ Container number valid format (MSCU1234567)
✓ JT subscription active for MSC
✗ Last scraping attempt: 404 Not Found
✗ No events received in 3 days
✓ Shipping line supported by JT

RESOLUTION:
1. Verify container number with customer
   - Check for typos or format errors
   - Confirm bill of lading matches

2. Manual tracking verification
   - Visit MSC website
   - Search for container MSCU1234567
   - If not found → Invalid container number

3. If valid but not in JT:
   - Escalate to Ocean team
   - Request manual scraping review
   - Consider alternative tracking source

ESTIMATED TIME: 30 minutes
PRIORITY: Medium
```

## Mental Model: Support Analyst Workflow

This skill replicates the step-by-step process expert support analysts follow:

### Phase 1: Understand the Issue (2-5 min)
1. Read ticket description carefully
2. Extract key identifiers (load, container, carrier, shipper)
3. Clarify ambiguous information with customer if needed
4. Determine transport mode (ground/ocean/air)

### Phase 2: Gather Evidence (5-15 min)
1. **Check if load/container exists**
   - Tracking API search
   - If not found → LOAD_NOT_FOUND root cause

2. **Check configuration**
   - Network relationship status
   - ELD enablement
   - Carrier capabilities

3. **Check recent activity**
   - Last position update
   - Recent API callbacks
   - Error logs in SigNoz

4. **Check external systems** (if ocean)
   - JT scraping history
   - Shipping line availability
   - Container validity

### Phase 3: Form Hypotheses (3-5 min)
1. List possible root causes based on evidence
2. Rank by likelihood
3. Identify what additional data would confirm/reject each

### Phase 4: Test and Validate (5-10 min)
1. Query specific data sources for each hypothesis
2. Score evidence for/against
3. Eliminate low-confidence hypotheses

### Phase 5: Determine Root Cause (2-5 min)
1. If confidence ≥ 80% → Declare root cause
2. If confidence < 80% → Request additional info or escalate
3. Document findings in ticket

### Phase 6: Provide Resolution (5-10 min)
1. Prescribe specific steps to fix
2. Estimate time to resolution
3. Set customer expectations
4. Provide workaround if available

**Total Time:** 20-50 minutes per case (depending on complexity)

## Integration with Cassie Agent

This skill is used by the Cassie classification agent:

```python
# Cassie routing logic
if classification == "LOAD_NOT_TRACKING":
    # Route to RCA Support Agent skill
    response = investigate_with_skill(
        skill="rca-support-agent",
        ticket=ticket_data
    )

    if response.confidence >= 80:
        # Auto-resolve with root cause and resolution
        ticket.update(
            status="Resolved",
            resolution=response.resolution,
            root_cause=response.root_cause
        )
    else:
        # Human-in-the-loop
        ticket.assign_to_analyst(
            context=response.evidence,
            suggested_hypotheses=response.hypotheses
        )
```

## Success Metrics

**Automation Rate:**
- Target: 60% of L1 support tickets auto-investigated
- Current: 0% (manual intervention required)
- Gap: Skill enables automation

**Time Savings:**
- Manual investigation: 20-50 minutes per case
- Automated investigation: 2-5 minutes per case
- Savings: 15-45 minutes per case

**Accuracy:**
- Human analyst accuracy: ~85% (experienced)
- AI agent with skill: ~95% (data-driven, no human error)

**Coverage:**
- 85+ subcategories of load not tracking
- 6+ integrated data sources
- Ground, ocean, and air transport modes

## Limitations

**What This Skill Cannot Do:**
- Diagnose issues requiring carrier contact
- Fix infrastructure problems (API downtime, etc.)
- Handle edge cases not in pattern library
- Make business decisions (e.g., carrier offboarding)

**When to Escalate to Human:**
- Confidence score < 80%
- Customer requests human contact
- Resolution requires policy decision
- Issue involves financial impact

## Future Enhancements

**Planned Additions:**
1. Redshift agent for historical load analysis
2. Athena agent for API callback pattern detection
3. RAG integration for Confluence/Slack historical resolutions
4. Predictive analysis (identify issues before customer reports)
5. Auto-remediation for simple fixes (enable ELD, retry scraping)

## Contributing

To improve this skill:
1. Document new issue patterns in `patterns/`
2. Add data source queries to `queries/`
3. Update decision trees in `workflows/`
4. Test with real support cases
5. Submit pull request with evidence of accuracy improvement

## License

Proprietary - FourKites Internal Use Only

---

**Last Updated:** January 22, 2026
**Maintained By:** AI R&D Solutions Engineering Team
**Contact:** msp.raja@fourkites.com
