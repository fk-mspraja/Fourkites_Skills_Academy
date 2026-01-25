# Converting Extraction to Skill Definition

**For**: Engineering teams building automated RCA skills
**Input**: Completed and validated `knowledge_extraction_template.yaml`
**Output**: Production-ready skill definition files
**Timeline**: 1-2 days per skill

This guide shows how to transform a validated knowledge extraction into a working RCA skill.

---

## Output Structure

After conversion, your skill directory will look like this:

```
skills/[domain]-rca/
├── skill_definition.yaml          # Main skill definition
├── decision_tree.yaml              # Machine-readable decision logic
├── patterns/                       # Issue pattern library
│   ├── README.md
│   ├── index.yaml
│   ├── pattern_1.yaml
│   ├── pattern_2.yaml
│   └── ...
├── knowledge_base/                 # Original extraction for reference
│   └── [sme_name]_workflow.yaml    # Copy of extraction
├── test_cases/                     # Validated test cases
│   ├── tc_001.yaml
│   ├── tc_002.yaml
│   └── ...
├── api_mappings.yaml               # Data source query examples
├── decision_engine.py              # Reference implementation
└── README.md                       # Skill documentation
```

---

## Step 1: Prepare the Extraction

**Input**: `knowledge_extraction_template.yaml` (fully completed and validated)

Before starting conversion:

- [ ] Extraction has SME sign-off
- [ ] All validation checks passed
- [ ] Test cases are confirmed
- [ ] No blocker issues remain
- [ ] Data sources are verified accessible

**Action**: Copy validated extraction to `skills/[domain]-rca/knowledge_base/[sme_name]_workflow.yaml`

```bash
cp knowledge_extraction_template.yaml \
  skills/otr-rca/knowledge_base/prashant_workflow.yaml
```

---

## Step 2: Create skill_definition.yaml

This is the main configuration file. It describes the skill for the RCA platform.

**Template:**

```yaml
# skills/[domain]-rca/skill_definition.yaml
#
# Generated from: knowledge_base/[sme_name]_workflow.yaml
# SME: [Name]
# Date: YYYY-MM-DD

skill:
  id: "[domain]_rca"
  name: "[Domain] RCA Skill"
  version: "1.0.0"

  owner: "[SME Name]"
  domain: "[Domain]"  # OTR, OCEAN, DRAYAGE, etc.

  status: "poc"  # poc → beta → production
  created: "YYYY-MM-DD"

  description: |
    RCA skill for [domain] support issues.

    Based on support team mental model from [SME name].

    Issue Categories Handled:
    - [Category 1] - X% of tickets
    - [Category 2] - Y% of tickets
    - [Category 3] - Z% of tickets

  # When should the Router invoke this skill?
  triggers:
    keywords:
      # Extract from extraction:mental_model.diagnostic_process
      # and patterns[].symptoms
      - "keyword_1"
      - "keyword_2"
      - "keyword_3"

    issue_categories:
      - "issue_category_1"
      - "issue_category_2"

    conditions:
      # Conditions when this skill is relevant
      - "load.mode == '[MODE]'"
      - "load.shipper == '[SPECIFIC_SHIPPER]'"  # If domain-specific

  # Core capabilities (from extraction.mental_model.primary_checks)
  capabilities:
    - id: "[check_id]"
      name: "[Check Name]"
      description: "[Description]"
      confidence: "[confidence_range]"
      time_estimate: "[estimate]"
      tools:
        - "[tool_1]"
        - "[tool_2]"

  # Data sources used (from extraction.data_sources)
  data_sources:
    [source_id]:
      name: "[Source Name]"
      type: "[Type: API, Database, UI, etc.]"
      endpoint: "${[ENV_VAR]}"
      auth: "[auth_method]"
      credentials: "env:[CREDENTIAL_VAR]"
      purpose: "[What it's used for]"
      data_available:
        - "[field_1]"
        - "[field_2]"

  # Decision tree reference
  decision_tree:
    path: "decision_tree.yaml"
    entry_point: "[step_name]"

  # When to escalate to human (from extraction.human_approval_triggers)
  human_handoff:
    triggers:
      low_confidence:
        threshold: 0.70
        action: "escalate"

      stuck_after_steps:
        max_steps: 5
        action: "escalate"

      critical_decision:
        actions:
          - "[action_1]"
          - "[action_2]"
        action: "request_approval"

  # Metrics baseline (from extraction.metrics)
  metrics:
    baseline:
      time: "[baseline_time]"
      accuracy: [baseline_accuracy]
      tools_used: [avg_tools]

    target:
      time: "[target_time]"
      accuracy: [target_accuracy]
      handoff_rate: [target_handoff]

  # Output format
  output_format:
    type: "investigation_result"
    fields:
      - name: "root_cause"
        type: "string"
        enum: [list from patterns]

      - name: "confidence_score"
        type: "float"
        min: 0.0
        max: 1.0

      - name: "evidence"
        type: "array"

      - name: "recommended_action"
        type: "object"

      - name: "human_approval_required"
        type: "boolean"
```

**How to fill it:**
1. Copy basic info from extraction.skill_metadata
2. Extract triggers from patterns.symptoms and mental_model
3. Map data_sources from extraction.data_sources (1-to-1 mapping)
4. Copy metrics from extraction.metrics
5. Reference decision_tree.yaml (create next)

**Reference**: Look at `/Users/msp.raja/rca-agent-project/skills/ocean_debugging/skill_definition.yaml` for a complete example.

---

## Step 3: Create decision_tree.yaml

Machine-readable flowchart of the diagnostic process.

**Template:**

```yaml
# skills/[domain]-rca/decision_tree.yaml
#
# Generated from: knowledge_base/[sme_name]_workflow.yaml
# SME: [Name]

decision_tree:
  # From extraction.decision_tree.entry_point
  entry_point: "step_1"

  # From extraction.decision_tree.steps
  steps:
    step_1:
      name: "[Step Name]"
      description: "[Description]"
      data_source: "[source_id]"  # Must match data_sources in skill_definition.yaml
      query: "[actual_query]"      # e.g., "GET /loads/{load_number}"

      decisions:
        - condition: "[condition]"  # e.g., "response.status == 404"
          condition_readable: "[Plain English]"
          confidence: 0.95

          # If this is a conclusion:
          next_step: null
          conclusion:
            root_cause: "[PATTERN_ID]"
            explanation: "[Explanation]"
            recommended_action: "[Action]"

        - condition: "[condition]"
          condition_readable: "[Plain English]"
          confidence: 0.80

          # If this branches to another step:
          next_step: "step_2"
          conclusion: null

    step_2:
      # ... more steps ...

  # Pattern index (for reference)
  patterns:
    - pattern_id: "PATTERN_1"
      confidence_min: 0.85
      confidence_max: 0.99

    - pattern_id: "PATTERN_2"
      confidence_min: 0.75
      confidence_max: 0.92
```

**How to fill it:**
1. Convert extraction.decision_tree.steps directly into YAML
2. Use exact condition strings from extraction (copy-paste, don't paraphrase)
3. Include both next_step and conclusion as alternatives
4. Add pattern_index at bottom for lookups

**Validation:**
- [ ] Every step has at least one decision
- [ ] Every decision has either next_step or conclusion (not both)
- [ ] All conditions are specific and testable
- [ ] No circular references
- [ ] All referenced data_sources exist

---

## Step 4: Create Pattern Library

Each pattern becomes a separate YAML file.

**Template** (`skills/[domain]-rca/patterns/[pattern_id].yaml`):

```yaml
# skills/[domain]-rca/patterns/[PATTERN_ID].yaml
#
# Pattern: [Pattern Name]
# Generated from extraction pattern: [extraction_pattern_id]

pattern:
  id: "[PATTERN_ID]"
  name: "[Pattern Name]"
  category: "[Category]"
  version: "1.0.0"

  # Statistics (from extraction.patterns[X])
  stats:
    frequency: "[Frequency]"
    avg_resolution_time: "[Time]"
    cases_resolved: 0  # Update after production use
    last_updated: "YYYY-MM-DD"

  # Symptoms the analyst observes
  symptoms:
    - "[symptom_1]"
    - "[symptom_2]"
    - "[symptom_3]"

  # Evidence needed to confirm pattern
  evidence:
    required:
      - source: "[source_id]"
        field: "[field_name]"
        condition: "[condition]"
        weight: 10  # 10=critical, 5=supporting, 3=nice-to-have

      - source: "[source_id]"
        field: "[field_name]"
        condition: "[condition]"
        weight: 5

    supporting:
      - source: "[source_id]"
        field: "[field_name]"
        condition: "[condition]"
        weight: 3

  # Confidence calculation
  confidence:
    # Formula: sum(matched_evidence.weight) / sum(all_evidence.weight)
    formula: "[formula]"
    min_required: 0.85
    auto_resolve_threshold: 0.90

  # Root cause
  root_cause:
    statement: "[Root cause statement]"
    explanation: |
      [Detailed explanation with template variables]

    impact: |
      - [Impact 1]
      - [Impact 2]
      - [Impact 3]

  # Resolution steps
  resolution:
    automated_steps: false  # true if can be automated
    human_approval_required: true

    steps:
      - step: 1
        action: "[What to do]"
        details: "[How to do it]"
        button: "[UI button label if any]"
        button_url: "[URL or null]"
        time_estimate_minutes: 5

      - step: 2
        action: "[What to do]"
        details: "[How to do it]"
        button: "[UI button label if any]"
        button_url: "[URL or null]"
        time_estimate_minutes: 5

  # Email template if escalation needed
  email_template:
    to: "[recipient]"
    subject: "[subject]"
    body: |
      [Email body with template variables]

  # Related patterns (cross-references)
  related_patterns:
    - "[PATTERN_ID_2]"
    - "[PATTERN_ID_3]"

  # Metadata
  metadata:
    created_by: "[SME Name]"
    created_date: "YYYY-MM-DD"
    last_modified: "YYYY-MM-DD"
    source: "[Original extraction location]"
```

**How to generate:**
1. For each pattern in extraction.patterns[]
2. Create one file per pattern
3. Copy extraction data directly
4. Convert to production format
5. Add related_patterns cross-references

**Create index** (`skills/[domain]-rca/patterns/index.yaml`):

```yaml
pattern_library:
  name: "[Domain] RCA Pattern Library"
  version: "1.0.0"
  total_patterns: [count]
  last_updated: "YYYY-MM-DD"

  categories:
    - name: "[Category Name]"
      code: "[CATEGORY_CODE]"
      pattern_count: [count]
      frequency: "[percentage]"
      avg_resolution: "[time]"

  top_patterns:
    - pattern_id: "[PATTERN_ID]"
      frequency: "[percentage]"
      automation_rate: [percentage]

    - pattern_id: "[PATTERN_ID]"
      frequency: "[percentage]"
      automation_rate: [percentage]
```

---

## Step 5: Create api_mappings.yaml

Document the actual API calls needed.

**Template:**

```yaml
# skills/[domain]-rca/api_mappings.yaml
#
# Actual API query examples from data_sources
# Used by decision_engine for mapping query strings to actual calls

api_mappings:

  # For each data source
  [source_id]:
    base_url: "[Base URL]"
    auth_header: "[Auth type]"
    endpoints:

      - name: "[Endpoint Name]"
        path: "[Endpoint path]"
        method: "GET|POST|etc"
        query_example: "[Example query string]"
        response_example: |
          {
            "field": "value"
          }
        field_mappings:
          api_field: "decision_tree_field"
        error_handling:
          - status_code: 404
            meaning: "[What this means]"
          - status_code: 500
            meaning: "[What this means]"

  [source_id_2]:
    # ... more endpoints ...
```

---

## Step 6: Create test_cases/

Organize test cases from extraction.

**For each test case**, create `test_cases/tc_[case_id].yaml`:

```yaml
# skills/[domain]-rca/test_cases/tc_[CASE_ID].yaml

test_case:
  id: "[CASE_ID]"
  description: "[Description from extraction]"

  # Input (from extraction test case)
  input:
    load_number: "[value]"
    shipper: "[value]"
    carrier: "[value]"
    # ... other relevant fields ...

  # Expected output (from extraction test case)
  expected:
    pattern_matched: true|false
    pattern_id: "[PATTERN_ID]"
    root_cause: "[root cause]"
    confidence_min: 0.85
    confidence_max: 0.95
    recommended_action: "[action]"

  # Real resolution for validation
  actual_resolution: "[What actually happened]"

  # Metadata
  source: "[production ticket ref]"
  date: "YYYY-MM-DD"
  validated: true
```

**Create test runner** (`test_cases/run_tests.py` - reference implementation):

```python
#!/usr/bin/env python3
"""
Test runner for RCA skill test cases.
Validates decision_tree against real examples.
"""

import yaml
import sys
from pathlib import Path

class TestRunner:
    def __init__(self, skill_dir):
        self.skill_dir = Path(skill_dir)
        self.tests = []
        self.results = []

    def load_test_cases(self):
        """Load all test_cases/*.yaml files"""
        test_dir = self.skill_dir / "test_cases"
        for test_file in test_dir.glob("tc_*.yaml"):
            with open(test_file) as f:
                test = yaml.safe_load(f)
                self.tests.append(test)

    def run_tests(self):
        """Run each test case through the decision tree"""
        for test in self.tests:
            result = self._run_test(test)
            self.results.append(result)

            status = "PASS" if result["passed"] else "FAIL"
            print(f"[{status}] {test['test_case']['id']}: "
                  f"{test['test_case']['description']}")

            if not result["passed"]:
                print(f"       Expected: {result['expected']}")
                print(f"       Got: {result['actual']}")

    def _run_test(self, test):
        """Execute a single test case"""
        # TODO: Implement decision_tree execution
        # For now: stub
        return {
            "test_id": test['test_case']['id'],
            "passed": True,
            "expected": test['test_case']['expected'],
            "actual": {}
        }

    def summary(self):
        """Print test summary"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed

        print(f"\n{'='*50}")
        print(f"TEST SUMMARY: {passed}/{total} passed")

        if failed > 0:
            print(f"FAILED: {failed} tests")
            sys.exit(1)
        else:
            print("ALL TESTS PASSED")
            sys.exit(0)

if __name__ == "__main__":
    runner = TestRunner(".")
    runner.load_test_cases()
    runner.run_tests()
    runner.summary()
```

---

## Step 7: Create README.md

Documentation for the skill.

**Template:**

```markdown
# [Domain] RCA Skill

**Status**: [poc/beta/production]
**SME**: [Name]
**Created**: YYYY-MM-DD

## Overview

This skill provides automated Root Cause Analysis for [domain] support issues.

Handles [X]% of support tickets automatically, with [Y]% accuracy.

## Usage

### Input

```yaml
ticket:
  load_number: "..."
  shipper: "..."
  carrier: "..."
  issue_description: "..."
```

### Output

```yaml
result:
  root_cause: "[PATTERN_ID]"
  confidence: 0.92
  evidence: [...]
  recommended_action: "..."
  human_approval_required: false
```

## Architecture

- **Decision Tree**: Flowchart of diagnostic steps
- **Pattern Library**: 50+ issue patterns with detection criteria
- **Data Sources**: Integration with [list systems]

## Performance

| Metric | Baseline | Target | Current |
|--------|----------|--------|---------|
| Time | [time] | [time] | [time] |
| Accuracy | [%] | [%] | [%] |
| Automation | [%] | [%] | [%] |

## Known Limitations

- [Limitation 1]
- [Limitation 2]

## Roadmap

- [ ] Add support for [feature]
- [ ] Improve accuracy on [pattern]
- [ ] Integrate with [system]

## Support

Questions about this skill? Contact [SME name].

## Files

- `skill_definition.yaml` - Main configuration
- `decision_tree.yaml` - Diagnostic logic
- `patterns/` - Pattern library
- `test_cases/` - Validation test cases
- `knowledge_base/` - Original extraction
```

---

## Step 8: Validate Conversion

**Checklist:**

- [ ] skill_definition.yaml is valid YAML
- [ ] decision_tree.yaml references correct data_sources
- [ ] All patterns have unique IDs
- [ ] All test cases pass
- [ ] No broken references between files
- [ ] All API endpoints accessible
- [ ] All conditions are testable
- [ ] Documentation is complete

**Validation Script:**

```bash
#!/bin/bash
# validate_skill.sh

SKILL_DIR=$1

echo "Validating $SKILL_DIR..."

# Check YAML validity
for f in $(find $SKILL_DIR -name "*.yaml"); do
    python3 -c "import yaml; yaml.safe_load(open('$f'))" || exit 1
done

# Check required files
required_files=(
    "skill_definition.yaml"
    "decision_tree.yaml"
    "patterns/index.yaml"
)

for f in "${required_files[@]}"; do
    if [ ! -f "$SKILL_DIR/$f" ]; then
        echo "ERROR: Missing required file: $f"
        exit 1
    fi
done

# Run test cases
python3 test_cases/run_tests.py || exit 1

echo "✓ Validation passed"
```

---

## Step 9: Deploy to Production

1. **Dev Testing**
   - Run against 30-50 historical cases
   - Measure accuracy
   - Collect feedback

2. **Beta Deployment**
   - Deploy to staging environment
   - Monitor for 1-2 weeks
   - Gather support team feedback
   - Tune confidence thresholds if needed

3. **Production Deployment**
   - Final SME review and sign-off
   - Deploy with feature flags
   - Monitor accuracy metrics
   - Document any issues found

4. **Maintenance**
   - Track false positives/negatives
   - Update patterns based on real cases
   - Maintain extraction as knowledge evolves
   - Annual review with SME

---

## Common Issues

### Issue: Decision tree is too broad

**Problem**: Confidence scores too low, everything escalates to human

**Solution**:
1. Review evidence requirements - are they too strict?
2. Add more supporting evidence checks
3. Increase weight on key evidence
4. Work with SME to calibrate confidence thresholds

### Issue: Too many false positives

**Problem**: Skill matches patterns incorrectly

**Solution**:
1. Review evidence conditions - are they too loose?
2. Add more required evidence
3. Increase confidence thresholds
4. Add pattern overlap detection

### Issue: Confidence scores don't match expert judgment

**Problem**: SME says "I'm 95% sure" but calculation shows 0.70

**Solution**:
1. Check evidence weight calibration
2. Add missing evidence checks
3. Review formula - is it correct?
4. Work with SME to recalibrate

### Issue: Decision tree goes to wrong conclusion

**Problem**: Test case expects A, gets B

**Solution**:
1. Review the data - was it wrong?
2. Review the conditions - are they correct?
3. Ask SME why the diagnosis should be A not B
4. Fix conditions and re-test

---

## References

- **Extraction Template**: `skills/_templates/knowledge_extraction_template.yaml`
- **Ocean Example**: `skills/ocean_debugging/skill_definition.yaml`
- **Plan**: `.omc/plans/rca-skills-platform-architecture.md` (Part 4)

---

**Last Updated**: 2026-01-26
**Version**: 1.0.0
