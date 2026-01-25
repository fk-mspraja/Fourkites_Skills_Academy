# Knowledge Extraction Validation Checklist

**Status**: Ready for conversion to skill definition
**Date**: [Today's date]
**Domain**: [e.g., OTR, OCEAN, DRAYAGE]
**SME**: [Name]
**Extractor**: [Name]

This checklist ensures the extracted mental model is complete, accurate, and ready for automation.

---

## Section 1: Completeness Review

### Observation Session Documented

- [ ] Shadow session date and duration recorded
- [ ] Number of tickets observed documented
- [ ] All tools/systems used are listed
- [ ] Access patterns for each tool documented
- [ ] Response times captured
- [ ] Tool usage order is clear

**Notes:**
```
[Document any gaps or issues found]
```

### Mental Model Captured

- [ ] Diagnostic philosophy clearly articulated
- [ ] Step-by-step workflow is complete (no missing steps)
- [ ] Success and failure criteria defined for each step
- [ ] Primary "go-to" checks identified
- [ ] Tribal knowledge documented
- [ ] Confidence levels assigned
- [ ] Decision branches are exhaustive (If X then Y, else Z)

**Notes:**
```
[Document any gaps or issues found]
```

### Data Sources Mapped

- [ ] All systems the analyst touches are documented
- [ ] Query patterns are specific (not vague)
- [ ] Response times realistic
- [ ] Field names match actual API/database
- [ ] Authentication methods correct
- [ ] Data freshness accurately described
- [ ] Common issues with each source listed

**Notes:**
```
[Document any gaps or issues found]
```

### Patterns Clearly Defined

- [ ] Each issue type has a unique pattern ID
- [ ] Frequency estimates provided (High/Medium/Low)
- [ ] Symptoms are observable and specific
- [ ] Evidence checks are verifiable
- [ ] Evidence weights are justified (10/5/3)
- [ ] Root cause is explained plainly
- [ ] Resolution steps are concrete
- [ ] Confidence levels are reasonable
- [ ] False positive/negative rates estimated

**Notes:**
```
[Document any gaps or issues found]
```

---

## Section 2: Accuracy Review

### Technical Accuracy

- [ ] All API endpoints are correct (no fictional endpoints)
- [ ] Query syntax matches actual API/SQL dialect
- [ ] Field names match actual system (verify in dev environment)
- [ ] Response examples are real (from actual queries)
- [ ] Confidence thresholds match expert judgment (ask SME to verify)
- [ ] Decision logic matches what analyst actually does

**Test Method**: Run against development environment
**Result**: [ ] PASS [ ] FAIL

**Notes:**
```
[Document any discrepancies found]
```

### SME Validation

- [ ] SME reviewed complete extraction (all 12 sections)
- [ ] SME confirmed mental model is accurate
- [ ] SME agreed with decision tree logic
- [ ] SME confirmed confidence levels
- [ ] SME identified any missing tribal knowledge
- [ ] SME signed off on test cases
- [ ] SME approved edge case handling

**SME Sign-Off**: _________________________ Date: _______

**Notes:**
```
[Document any changes SME requested]
```

### Decision Tree Validation

- [ ] Entry point is clear
- [ ] Each decision has exactly 2 outcomes (true/false or multiple explicit paths)
- [ ] No dead-end paths except conclusions
- [ ] All conclusions have explicit recommendations
- [ ] Confidence scores increase as you gather evidence (generally)
- [ ] Confidence scores are 0.0-1.0 (not percentages)
- [ ] At least one path leads to "escalate to human"

**Test Method**: Walk through 5 test cases manually
**Result**: [ ] PASS [ ] FAIL

**Discrepancies Found**:
```
[Document any logic errors found]
```

---

## Section 3: Test Case Validation

### Test Case Coverage

- [ ] At least 3 test cases included
- [ ] Mix of high, medium, low confidence cases
- [ ] At least one edge case included
- [ ] At least one escalation case included
- [ ] Cases are from REAL production tickets (not hypothetical)
- [ ] Cases use actual data (load numbers, carrier codes, etc.)
- [ ] Expected outcomes are documented

**Count of test cases**: _____

### Test Case Execution

For each test case:

**Case 1: ________________________**
- [ ] Expected pattern matches actual pattern
- [ ] Expected confidence within ±0.10 of actual
- [ ] Expected root cause matches actual
- [ ] Expected recommendation matches actual
- [ ] Resolution matches production resolution

**Case 2: ________________________**
- [ ] Expected pattern matches actual pattern
- [ ] Expected confidence within ±0.10 of actual
- [ ] Expected root cause matches actual
- [ ] Expected recommendation matches actual
- [ ] Resolution matches production resolution

**Case 3: ________________________**
- [ ] Expected pattern matches actual pattern
- [ ] Expected confidence within ±0.10 of actual
- [ ] Expected root cause matches actual
- [ ] Expected recommendation matches actual
- [ ] Resolution matches production resolution

**Case 4: ________________________**
- [ ] Expected pattern matches actual pattern
- [ ] Expected confidence within ±0.10 of actual
- [ ] Expected root cause matches actual
- [ ] Expected recommendation matches actual
- [ ] Resolution matches production resolution

**Case 5: ________________________**
- [ ] Expected pattern matches actual pattern
- [ ] Expected confidence within ±0.10 of actual
- [ ] Expected root cause matches actual
- [ ] Expected recommendation matches actual
- [ ] Resolution matches production resolution

**Overall Result**: [ ] ALL PASS [ ] SOME FAIL

**Failures Found**:
```
[Document any test case failures and root cause]
```

---

## Section 4: Data Source Validation

### API/System Access Verification

For each data source documented:

**Source 1: ________________________**
- [ ] Endpoint/location is correct and accessible
- [ ] Authentication method works
- [ ] Response format matches documentation
- [ ] Required fields are present
- [ ] Response times reasonable
- [ ] Data freshness matches claim

**Source 2: ________________________**
- [ ] Endpoint/location is correct and accessible
- [ ] Authentication method works
- [ ] Response format matches documentation
- [ ] Required fields are present
- [ ] Response times reasonable
- [ ] Data freshness matches claim

**Source 3: ________________________**
- [ ] Endpoint/location is correct and accessible
- [ ] Authentication method works
- [ ] Response format matches documentation
- [ ] Required fields are present
- [ ] Response times reasonable
- [ ] Data freshness matches claim

**Overall Result**: [ ] ALL ACCESSIBLE [ ] SOME INACCESSIBLE

**Access Issues Found**:
```
[Document any endpoints that are down or different than expected]
```

---

## Section 5: Pattern Correctness

### Pattern Detection Accuracy

For each major pattern:

**Pattern 1: ________________________**
- [ ] Pattern ID is unique
- [ ] Symptoms are distinctive
- [ ] Evidence checks are specific
- [ ] No overlap with other patterns (ask: could this be mistaken for pattern X?)
- [ ] Confidence thresholds are calibrated
- [ ] False positive rate is acceptable
- [ ] False negative rate is acceptable

**Pattern 2: ________________________**
- [ ] Pattern ID is unique
- [ ] Symptoms are distinctive
- [ ] Evidence checks are specific
- [ ] No overlap with other patterns
- [ ] Confidence thresholds are calibrated
- [ ] False positive rate is acceptable
- [ ] False negative rate is acceptable

**Pattern 3: ________________________**
- [ ] Pattern ID is unique
- [ ] Symptoms are distinctive
- [ ] Evidence checks are specific
- [ ] No overlap with other patterns
- [ ] Confidence thresholds are calibrated
- [ ] False positive rate is acceptable
- [ ] False negative rate is acceptable

**Overlaps Found**:
```
[Document any patterns that could be confused with each other]
```

---

## Section 6: Edge Case Validation

### Edge Case Coverage

- [ ] At least 2 edge cases documented
- [ ] Each edge case has clear detection criteria
- [ ] Analyst's handling approach is documented
- [ ] Escalation path is clear
- [ ] Edge cases don't break the main decision tree

**Edge Cases Identified**: _____ (list below)
```
[List each edge case documented]
```

### Edge Case Testing

- [ ] Can the decision tree handle edge cases? (Or do they escalate?)
- [ ] Are edge cases clearly distinguished from normal patterns?
- [ ] Would a new analyst know when they've encountered an edge case?

**Result**: [ ] GOOD [ ] NEEDS WORK

**Issues Found**:
```
[Document any edge case handling issues]
```

---

## Section 7: Tribal Knowledge Validation

### Documented Shortcuts

- [ ] All shortcuts the analyst mentioned are captured
- [ ] Each shortcut has a "when it applies" condition
- [ ] Sources are documented (where did they learn this?)
- [ ] Confidence levels are realistic
- [ ] Shortcuts don't contradict the main workflow

**Count of tribal knowledge items**: _____

### Verification with SME

- [ ] SME confirmed each shortcut is accurate
- [ ] SME verified "when it applies" conditions
- [ ] SME rated confidence for each shortcut
- [ ] No critical shortcuts were missed

**SME Feedback**:
```
[Document any tribal knowledge the SME wanted to add]
```

---

## Section 8: Dependencies & Escalations

### External Dependencies Documented

- [ ] All required approvals are listed
- [ ] All escalation paths are defined
- [ ] Escalation criteria are clear
- [ ] Typical turnaround times are realistic
- [ ] Contact information is complete

**Count of dependencies**: _____

### Escalation Paths Clear

- [ ] When to escalate to engineering
- [ ] When to escalate to carrier
- [ ] When to escalate to operations
- [ ] When to escalate to other teams
- [ ] What information to include in escalation
- [ ] Expected response time for each escalation type

**Result**: [ ] CLEAR [ ] NEEDS CLARIFICATION

**Issues Found**:
```
[Document any escalation path ambiguities]
```

---

## Section 9: Assumptions & Limitations

### Documented Assumptions

- [ ] All assumptions are explicitly listed
- [ ] Impact of each assumption is clear
- [ ] How to validate each assumption is documented
- [ ] No critical assumptions are missing

**Count of assumptions**: _____

### Documented Limitations

- [ ] All known limitations are listed
- [ ] Impact of each limitation is clear
- [ ] Workarounds are documented
- [ ] Future improvements are identified

**Count of limitations**: _____

### Reality Check

- [ ] Are assumptions realistic for production?
- [ ] Will limitations cause problems in automation?
- [ ] Are there workarounds that should be in the skill?

**Result**: [ ] ACCEPTABLE [ ] CONCERNING

**Concerns**:
```
[Document any assumptions/limitations that could cause problems]
```

---

## Section 10: Confidence Calibration

### Confidence Level Review

- [ ] Confidence scores are realistic (not all 0.9+)
- [ ] Confidence increases as evidence accumulates
- [ ] Low-confidence cases escalate to human
- [ ] High-confidence cases can auto-resolve
- [ ] Confidence thresholds match business requirements

**Overall Calibration**: [ ] GOOD [ ] NEEDS TUNING

**Tuning Needed**:
```
[Document any patterns where confidence seems miscalibrated]
```

### Test Against Business Requirements

- [ ] Business wants auto-resolution confidence >= 85%?
  - [ ] Patterns with >= 85% are clear and correct
  - [ ] False positive rate is acceptable

- [ ] Business wants human review for confidence 60-84%?
  - [ ] These cases are escalated appropriately
  - [ ] Human can make good decisions with the evidence provided

- [ ] Business wants escalation for < 60%?
  - [ ] These cases are truly ambiguous
  - [ ] Not being used as "dump everything unclear" bucket

**Result**: [ ] MEETS REQUIREMENTS [ ] NEEDS ADJUSTMENT

**Adjustments Needed**:
```
[Document any confidence threshold changes needed]
```

---

## Section 11: Performance Metrics

### Baseline Metrics Documented

- [ ] Current time per ticket documented
- [ ] Current resolution rate documented
- [ ] Tool usage patterns documented
- [ ] Escalation rate documented

**Baseline Time**: _____ minutes
**Baseline Accuracy**: _____ %
**Current Escalation Rate**: _____ %

### Target Metrics Reasonable

- [ ] Target time is ambitious but achievable
- [ ] Target accuracy is realistic (not 100%)
- [ ] Target handoff rate accounts for complex cases
- [ ] Metrics are measurable

**Target Time**: _____ minutes (_____ % improvement)
**Target Accuracy**: _____ %
**Target Handoff Rate**: _____ %

**Assessment**: [ ] REALISTIC [ ] TOO AGGRESSIVE [ ] TOO CONSERVATIVE

---

## Section 12: Documentation Quality

### Writing Quality

- [ ] All sections use clear, concise language
- [ ] Technical details are specific (not vague)
- [ ] Examples are provided where helpful
- [ ] No jargon without explanation
- [ ] Consistent terminology throughout

**Quality**: [ ] GOOD [ ] NEEDS POLISH

**Issues Found**:
```
[Document any clarity issues]
```

### Completeness

- [ ] No obvious sections are blank
- [ ] All important information is captured
- [ ] Nothing critical is missing
- [ ] Sources are documented
- [ ] References are provided

**Completeness**: [ ] COMPLETE [ ] MISSING SECTIONS

**Missing Content**:
```
[Document any gaps in documentation]
```

---

## Final Sign-Off

### Pre-Conversion Checklist

- [ ] All completeness checks passed
- [ ] All accuracy checks passed
- [ ] All test cases passed
- [ ] SME validation completed
- [ ] No blocker issues remain
- [ ] Knowledge extraction is production-ready

### Sign-Off

**Extractor Name**: _________________________ Date: _______

**SME Name**: _________________________ Date: _______

**Technical Review**: _________________________ Date: _______

### Issues to Fix Before Conversion

Priority: BLOCKER (must fix before skill creation)
```
[List any blocker issues that prevent skill conversion]
```

Priority: IMPORTANT (should fix soon)
```
[List any important issues to address in next iteration]
```

Priority: NICE-TO-HAVE (can fix later)
```
[List any nice-to-have improvements]
```

---

## Post-Validation Next Steps

Once validation is complete:

1. **Generate Skill Definition** (using validated extraction)
   - [ ] skill_definition.yaml created
   - [ ] decision_tree.yaml created
   - [ ] test_cases.yaml created

2. **Deploy to Dev Environment**
   - [ ] Skill deployed to dev
   - [ ] All APIs working
   - [ ] Test cases passing

3. **Begin Integration Testing**
   - [ ] Test against historical cases
   - [ ] Measure accuracy
   - [ ] Measure speed
   - [ ] Gather team feedback

4. **Iterate and Improve**
   - [ ] Fix any failed test cases
   - [ ] Tune confidence thresholds
   - [ ] Add missing patterns
   - [ ] Refine based on initial testing

5. **Promote to Production**
   - [ ] Final SME sign-off
   - [ ] Deploy to production
   - [ ] Monitor accuracy
   - [ ] Maintain over time

---

## Document History

| Date | Version | Status | Changes |
|------|---------|--------|---------|
| | 1.0 | Draft | Initial extraction |
| | 1.1 | Review | SME review and changes |
| | 1.2 | Validated | Validation checklist passed |
| | 2.0 | Converted | Converted to skill definition |

---

**Generated**: [Date]
**Template Version**: 1.0.0
**Validation Framework**: RCA Skills Platform v1.0
