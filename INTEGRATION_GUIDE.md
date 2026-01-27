# Integration Guide: Skills Library → Rewind-App

**How to use MSP's knowledge extraction templates to create Arpit's playbooks and patterns**

---

## Overview

This guide shows how to use the **Skills Library knowledge extraction templates** to systematically create **rewind-app playbooks and patterns** for new domains.

**Process:**
```
Knowledge Extraction (2-4 days)
  → Use skills/_templates/knowledge_extraction_template.yaml
  → Shadow SME, capture mental model
  ↓
Playbook Creation (1 day)
  → Convert investigation flow to playbook YAML
  → Define steps, outcomes, branching logic
  ↓
Pattern Creation (1-2 days)
  → Convert diagnostic rules to pattern YAML files
  → Define evidence rules, root causes, remediation
  ↓
Test Case Creation (0.5 days)
  → Convert test scenarios to test case YAML files
  → Define expected outcomes, validation criteria
  ↓
Validation (0.5 days)
  → Run test cases against playbook/patterns
  → Verify accuracy, refine weights
```

**Total:** 5-8 days from zero knowledge to production-ready playbook

---

## Step 1: Knowledge Extraction (2-4 days)

### Setup

1. **Schedule shadow session** with SME (Prashant for OTR, Surya for Ocean, etc.)
2. **Open template:** `skills/_templates/knowledge_extraction_template.yaml`
3. **Prepare:** Read `skills/_templates/QUICK_START.md` (5 minutes)

### During Shadow Session

Use the 12-section template to capture:

```yaml
# Section 1: Observation Session
domain: "otr"
issue_category: "CALLBACK_FAILURE"
sme_name: "Prashant Kumar"
observer: "MSP Raja"
date: "2026-01-27"
duration: "2 hours"
tickets_reviewed: ["SF-12345", "SF-67890", "SF-11223"]

# Section 3: Investigation Flow
mental_model:
  initial_hypothesis: "What does the SME check first?"
  primary_data_source: "Which tool/query do they use?"
  decision_points:
    - condition: "If X is true..."
      action: "Then check Y..."
      confidence: "How confident are they?"

# Section 5: Diagnostic Patterns
patterns:
  - pattern_id: "webhook_5xx_persistent"
    trigger_conditions:
      - "ext_request_status >= 500"
      - "failure_count > 10"
      - "hours_since_success > 4"
    evidence_collection:
      - source: "Athena callbacks_v2"
        query: "SELECT * FROM callbacks_v2 WHERE tracking_id = ? AND error_msg IS NOT NULL"
        confidence_weight: 0.85
    resolution_steps:
      1. "Contact customer about endpoint failures"
      2. "Verify endpoint is accessible"
      3. "Review error response body"
```

**Deliverable:** Completed `knowledge_extraction_otr_callbacks.yaml` (500-800 lines)

---

## Step 2: Convert to Rewind-App Playbook (1 day)

### Mapping: Extraction → Playbook

| Extraction Section | Playbook Field | Notes |
|-------------------|---------------|-------|
| `issue_category` | `playbook_id`, `triggers.categories` | Use consistent naming |
| `trigger_keywords` | `triggers.keywords` | Copy directly |
| `initial_hypothesis` | `steps[0]` | First investigation step |
| `decision_points` | `steps[].outcomes` | Branch conditions |
| `data_sources` | `steps[].action`, `steps[].table` | Query definitions |
| `confidence_indicators` | `outcomes[].confidence` | Per-outcome confidence |

### Example: Creating callback_failure.yaml

From extraction:
```yaml
# Section 3: Investigation Flow
step_1:
  action: "Verify load exists in system"
  data_source: "Tracking API"
  endpoint: "/v2/shipments/{tracking_id}"
  outcomes:
    - condition: "200 OK"
      next_step: "check_callbacks"
    - condition: "404 Not Found"
      conclusion: "Load doesn't exist - cannot investigate callbacks"
      confidence: 0.95
```

Becomes playbook:
```yaml
steps:
  - step: 1
    id: "check_load_exists"
    name: "Verify Load Exists"
    description: "Confirm load exists in Tracking API"
    action: "api_call"
    uses_schema: "common.schemas.tracking_api"
    endpoint: "search_load"
    params:
      tracking_id: "{identifier}"
    outcomes:
      - condition: "status == 200"
        result: "LOAD_FOUND"
        message: "Load found: tracking_id={response.tracking_id}"
        action: "CONTINUE"
        next_step: 2
      - condition: "status == 404"
        result: "LOAD_NOT_FOUND"
        message: "Load not found - cannot investigate callbacks"
        action: "STOP"
        confidence: 0.95
```

### Template Structure

```yaml
playbook_id: "{domain}_{issue_category}"
name: "{Human-Readable Name}"
version: "1.0.0"
domain: "{otr|ocean|drayage|air}"

triggers:
  categories: ["{CATEGORY}"]
  keywords: ["{keyword1}", "{keyword2}"]

identifier_rules:
  primary_identifier: "{tracking_id|load_number}"
  fallback_identifiers: ["{alt1}", "{alt2}"]

steps:
  - step: 1
    id: "{step_id}"
    name: "{Step Name}"
    description: "{What this step does}"
    action: "{api_call|query|analyze}"
    # ... step details ...
    outcomes:
      - condition: "{boolean expression}"
        result: "{RESULT_CODE}"
        message: "{user-facing message}"
        action: "{CONTINUE|STOP|REPORT}"
        next_step: {2|null}
        confidence: {0.0-1.0}

output_template:
  summary: |
    ## Investigation Summary: {Playbook Name}
    **Load:** {identifier}
    **Result:** {final_result}
    **Confidence:** {confidence}%
    # ... template ...

metadata:
  author: "extracted-by-{observer}"
  created: "{date}"
  source: "knowledge_extraction_{file}"
```

**Deliverable:** `rewind-app/backend/app/domains/{domain}/playbooks/{issue}.yaml` (300-500 lines)

---

## Step 3: Convert to Rewind-App Patterns (1-2 days)

### Mapping: Extraction → Pattern

| Extraction Section | Pattern Field | Notes |
|-------------------|--------------|-------|
| `pattern_id` | `pattern_id` | Use consistent naming convention |
| `trigger_conditions` | `evidence_rules.confirms` | Positive evidence |
| `exclusion_criteria` | `evidence_rules.rejects` | Negative evidence |
| `confidence_weight` | `evidence_rules.*.weight` | Per-evidence weight |
| `root_cause` | `root_causes[]` | Multiple causes possible |
| `resolution_steps` | `remediation[]` | Prioritized actions |

### Example: Creating webhook_5xx.yaml

From extraction:
```yaml
patterns:
  - pattern_id: "webhook_5xx_persistent"
    description: "Customer endpoint returning 5xx server errors"
    trigger_conditions:
      - field: "ext_request_status"
        operator: ">="
        value: 500
        weight: 0.8
      - field: "failure_count"
        operator: ">"
        value: 5
        weight: 0.5
    exclusion_criteria:
      - field: "hours_since_last_success"
        operator: "<"
        value: 1
        weight: 0.8
        reason: "Recent success means likely transient"
    root_cause: "Customer endpoint experiencing internal errors"
    resolution:
      1. "Contact customer about endpoint failures"
      2. "Check customer status page for known issues"
      3. "Monitor for recovery (15-30 min)"
```

Becomes pattern:
```yaml
pattern_id: "H_WEBHOOK_5XX"
domain: "otr"
category: "CALLBACK_WEBHOOK_FAILURE"
name: "Webhook 5xx Server Error"
description: "Callback webhooks are returning 5xx server errors indicating issues with the customer's endpoint"

investigation_steps:
  - skill: "analyze_callbacks"
    purpose: "Analyze callback history and identify 5xx server error patterns"

evidence_rules:
  confirms:
    - condition: "ext_request_status >= 500 AND ext_request_status < 600"
      weight: 0.8
      message: "Callbacks are returning HTTP {ext_request_status} server error"

    - condition: "failure_count > 5 AND ext_request_status >= 500"
      weight: 0.5
      message: "{failure_count} callbacks failed with {ext_request_status} server errors"

  rejects:
    - condition: "hours_since_last_success < 1"
      weight: 0.8
      message: "Callback delivered successfully {minutes_since_last_success} minutes ago"

root_causes:
  - cause: "Customer endpoint is experiencing internal errors"
    likelihood: "high"
    conditions: ["ext_request_status = 500"]
    indicators:
      - "HTTP 500 Internal Server Error"
      - "Customer application may have bugs"

remediation:
  - action: "Notify customer of endpoint failures"
    owner: "Support"
    priority: 1
    template: |
      Your webhook endpoint is returning server errors.
      HTTP Status: {ext_request_status}
      Please investigate your endpoint...
```

### Pattern Template

```yaml
pattern_id: "{PREFIX}_{PATTERN_NAME}"
domain: "{domain}"
category: "{CATEGORY}"
name: "{Human-Readable Name}"
description: "{What this pattern identifies}"

investigation_steps:
  - skill: "{skill_name}"
    purpose: "{Why run this skill}"

evidence_rules:
  confirms:
    - condition: "{boolean expression}"
      weight: {0.0-1.0}
      message: "{explanation}"

  rejects:
    - condition: "{boolean expression}"
      weight: {0.0-1.0}
      message: "{why this rejects the pattern}"

root_causes:
  - cause: "{root cause description}"
    likelihood: "{high|medium|low}"
    conditions: ["{condition1}", "{condition2}"]
    indicators: ["{indicator1}", "{indicator2}"]

remediation:
  - action: "{what to do}"
    owner: "{who does it}"
    priority: {1|2|3|4}
    condition: "{when to do this}" # optional
    template: |
      {action template with {variables}}

runbook_link: "https://confluence.fourkites.com/display/SUPPORT/{Runbook}"
troubleshooting_guide: "troubleshooting_guide.md#{anchor}"
```

**Deliverable:** `rewind-app/backend/app/domains/{domain}/patterns/{pattern}.yaml` per pattern (150-250 lines each)

---

## Step 4: Create Test Cases (0.5 days)

### Mapping: Extraction → Test Case

| Extraction Section | Test Case Field | Notes |
|-------------------|----------------|-------|
| `validation_scenarios` | `test_case_id`, `description` | One test case per scenario |
| `test_data` | `input`, `investigation_queries` | Real or synthetic data |
| `expected_pattern` | `expected_root_cause` | Pattern ID to match |
| `expected_confidence` | `expected_confidence` | Target confidence score |
| `expected_resolution` | `expected_resolution` | Expected actions |

### Example: Creating test case

From extraction:
```yaml
validation_scenarios:
  - scenario: "Persistent 5xx errors from customer endpoint"
    test_data:
      tracking_id: 626717801
      date_range: "2026-01-22 to 2026-01-23"
    expected_evidence:
      - "ext_request_status = 503"
      - "failure_count = 47"
      - "hours_since_last_success = 8.5"
    expected_pattern: "webhook_5xx_persistent"
    expected_confidence: 0.90
    expected_resolution:
      - "Contact customer about endpoint failures"
      - "HTTP 503 Service Unavailable"
```

Becomes test case:
```yaml
test_case_id: "TC-WEBHOOK-5XX-001"
date_reported: "2026-01-22"
reported_by: "Arpit Garg"
category: "callback_issues"
severity: "high"
source: "Production"

description: |
  Callbacks failing with HTTP 503 Service Unavailable errors.
  Customer endpoint is down or overloaded.

input:
  ticket_description: "Callbacks not sent for load, receiving 503 errors"
  tracking_id: 626717801
  date_range:
    start: "2026-01-22"
    end: "2026-01-23"

investigation_queries:
  athena_query: |
    SELECT
      tracking_id,
      message_type,
      error_msg,
      ext_request_status,
      attempt_count,
      created_at
    FROM raw_data_db.callbacks_v2
    WHERE tracking_id = 626717801
      AND error_msg IS NOT NULL
      AND datestr BETWEEN '2026-01-22' AND '2026-01-23'

expected_evidence:
  - source: "Athena callbacks_v2"
    finding: "ext_request_status = 503"
    confidence_weight: 0.80

  - source: "Athena callbacks_v2"
    finding: "failure_count = 47"
    confidence_weight: 0.50

  - source: "Error pattern"
    finding: "hours_since_last_success > 4"
    confidence_weight: 0.60

expected_root_cause: "webhook_5xx_persistent"
expected_confidence: 0.90

expected_resolution:
  category: "customer_endpoint_issue"
  responsible_party: "customer"
  steps:
    - "Notify customer of endpoint failures"
    - "HTTP 503 Service Unavailable - endpoint is down/overloaded"
    - "Monitor for recovery (15-30 minutes)"
    - "Callbacks will be automatically retried"

validation_criteria:
  - "Correctly identifies tracking_id"
  - "Queries callbacks_v2 table"
  - "Recognizes 5xx error pattern"
  - "Confidence score >= 0.85"
  - "Identifies customer responsibility (not FourKites)"
```

**Deliverable:** `rewind-app/tests/playbooks/{playbook_id}/test_{id}.yaml` per scenario (80-120 lines each)

---

## Step 5: Validation (0.5 days)

### Run Test Cases

```bash
cd rewind-app
pytest tests/playbooks/callback_failure/test_webhook_5xx_001.yaml
```

### Validation Checklist

From `skills/_templates/VALIDATION_CHECKLIST.md`:

- [ ] **Pattern Triggers:** Test case triggers correct pattern
- [ ] **Evidence Collection:** All expected evidence is collected
- [ ] **Confidence Scoring:** Confidence score matches expected ± 0.05
- [ ] **Root Cause:** Correct root cause identified
- [ ] **Resolution Steps:** Correct remediation actions suggested
- [ ] **False Positives:** Pattern doesn't trigger on unrelated issues
- [ ] **False Negatives:** Pattern triggers on all relevant test cases

### Refinement

If validation fails:
1. **Adjust evidence weights** in pattern YAML
2. **Add missing evidence rules** (confirms/rejects)
3. **Refine conditions** in playbook outcomes
4. **Re-run test cases**

Target: **90% accuracy** on test cases before production deployment

---

## Real Example: Arpit's Production Issues

### Issue 1: Callback Failures (Jan 22, 2026)

**Knowledge Extracted:**
- 3 tracking IDs: 626717801, 623705749, 625342806
- Error patterns: event_not_subscribed, DNS lookup failure, HTTP 503
- Investigation: Athena callbacks_v2 query
- Confidence: 85-90%

**Created Playbooks:**
✅ `callback_failure.yaml` (Arpit already has this - 476 lines)

**Created Patterns:**
✅ `webhook_5xx.yaml` (Arpit already has - 232 lines)
🔨 `event_not_subscribed.yaml` (NEEDS TO BE CREATED)
🔨 `dns_lookup_failure.yaml` (NEEDS TO BE CREATED)

**Created Test Case:**
✅ `skills/otr-rca/test_cases/callback_failure_jan22_2026.yaml` (90 lines)

**Next Step:** Create missing patterns `event_not_subscribed` and `dns_lookup_failure`

---

### Issue 2: Load Creation Failure (Jan 23, 2026)

**Knowledge Extracted:**
- Load S20251111-0041
- Error: Address validation failed
- Missing: address_line_1 OR (city + state + country) OR (lat + long)
- Investigation: Redshift load_validation_data_mart query
- Confidence: 95%

**Created Playbooks:**
✅ `load_creation_failure.yaml` (Arpit already has - 292 lines)

**Created Patterns:**
✅ `validation_error.yaml` (Arpit already has - 6,093 bytes)
🔨 `address_validation_failed.yaml` (NEEDS TO BE CREATED - more specific)

**Created Test Case:**
✅ `skills/otr-rca/test_cases/load_creation_failed_address_validation.yaml` (136 lines)

**Next Step:** Create specific `address_validation_failed` pattern from general `validation_error`

---

## Integration Workflow

### Week 1: Setup

1. **Copy knowledge extraction templates** to rewind-app
   ```bash
   cp -r skills/_templates/ rewind-app/docs/knowledge-extraction/
   ```

2. **Add test framework** to rewind-app
   ```bash
   mkdir -p rewind-app/tests/playbooks/
   cp skills/otr-rca/test_cases/*.yaml rewind-app/tests/playbooks/callback_failure/
   ```

3. **Update rewind-app README**
   - Add "How to Add a New Domain" section
   - Reference knowledge extraction process
   - Link to templates

### Week 2-3: First Domain Extraction

4. **Schedule SME session** (Prashant for OTR callback deep dive)
   - 2-hour shadow session
   - Review 5-10 historical tickets
   - Use `knowledge_extraction_template.yaml`

5. **Create playbook/patterns** from extraction
   - Follow this integration guide
   - Target: 1 new playbook, 3-5 new patterns

6. **Create test cases** from real production issues
   - Use historical tickets
   - Define expected outcomes
   - Validate accuracy

### Week 4: Validation & Refinement

7. **Run test cases** against playbook/patterns
   - Measure accuracy (target: 90%+)
   - Refine evidence weights
   - Adjust confidence thresholds

8. **Deploy to test environment**
   - Integrate with Arpit's UI
   - Test with live tickets
   - Monitor accuracy

### Month 2-3: Scale to More Domains

9. **Extract Ocean domain** (Surya)
10. **Extract Drayage domain**
11. **Extract Air domain**
12. **Target: 50+ patterns across 4-5 domains**

---

## Success Metrics

### Knowledge Extraction

- **Time to extract:** 2-4 days per domain (target)
- **Completeness:** 12 sections filled out with 80%+ detail
- **Usability:** Non-technical SME can use templates (target)

### Playbook/Pattern Creation

- **Conversion time:** 1-2 days from extraction to YAML (target)
- **Accuracy:** 90%+ on test cases
- **Coverage:** 10+ patterns per domain

### Production Impact

- **Investigation time:** 20-30 min → 8-12 min (60% reduction)
- **Automation rate:** 60% of L1 tickets auto-investigated
- **Confidence:** 85%+ for auto-resolution

---

## Tools & Resources

### Knowledge Extraction

- Template: `skills/_templates/knowledge_extraction_template.yaml` (800 lines)
- Quick Start: `skills/_templates/QUICK_START.md`
- Validation: `skills/_templates/VALIDATION_CHECKLIST.md`
- Conversion: `skills/_templates/EXTRACTION_TO_SKILL.md`

### Playbook/Pattern Examples

- Arpit's Playbooks: `rewind-app/backend/app/domains/otr/playbooks/*.yaml`
- Arpit's Patterns: `rewind-app/backend/app/domains/otr/patterns/*.yaml`
- Our Test Cases: `skills/otr-rca/test_cases/*.yaml`

### UI

- Rewind UI: http://rewind.fourkites.internal/
- Pattern Editor: (to be built - allows editing YAML via UI)

---

## FAQ

**Q: Which repo should be the source of truth?**
A: **Rewind-app** for production playbooks/patterns. **Skills Library** for knowledge extraction templates.

**Q: Can I create patterns without knowledge extraction?**
A: Yes, but extraction ensures completeness and captures SME mental model systematically.

**Q: How do I update an existing pattern?**
A: Edit the pattern YAML file directly, or re-run knowledge extraction to capture new learnings.

**Q: What if test cases fail?**
A: Adjust evidence weights, add missing evidence rules, or refine playbook conditions.

**Q: How do I add a new domain?**
A: Follow this guide:
1. Extract knowledge (2-4 days)
2. Create playbook (1 day)
3. Create patterns (1-2 days)
4. Create test cases (0.5 days)
5. Validate (0.5 days)

---

**Next:** Share this with Arpit and schedule integration sync.
