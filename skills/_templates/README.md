# RCA Skills Templates

This directory contains templates for extracting and documenting support team mental models into machine-readable RCA skills.

## Overview

The RCA Skills Platform transforms expert knowledge from support analysts into automated diagnostic workflows. These templates guide the knowledge extraction process from shadowing sessions to production-ready skills.

## Available Templates

### knowledge_extraction_template.yaml

The primary template for capturing SME (Subject Matter Expert) mental models during support analyst shadowing sessions.

**Use this template when:**
- You're about to shadow a support analyst (Prashant for OTR, Surya for Ocean, etc.)
- You want to capture their diagnostic workflows
- You need to extract their decision trees and tribal knowledge
- You're building a new RCA skill for a domain

**Timeline:**
- **Day 1 (4 hours)**: Shadow session - observe analyst handling 5-10 real tickets, fill sections 1-4
- **Day 2 (4 hours)**: Documentation - complete sections 5-12, validate with analyst

## How to Use the Template

### Step 1: Prepare (Before the Session)

1. Print or copy `knowledge_extraction_template.yaml`
2. Read through all sections to understand what you'll be documenting
3. Set up screen recording if possible
4. Prepare sample tickets to analyze

### Step 2: Day 1 - Shadow Session (4 hours)

During the analyst's workday, observe them handling real support tickets:

**Hour 1-2: Initial Observations**
- Watch them handle 2-3 tickets
- Fill in `observation_session` (Section 1)
- Note all tools they access in order
- Ask: "Why did you check that first?"

**Hour 2-3: Dig Deeper**
- Ask about their decision logic
- Document mental model patterns (Section 2)
- Identify the 2-3 most common issues
- Ask: "What's your first instinct when you see this?"

**Hour 3-4: Complete the Picture**
- Watch 2-3 more tickets
- Capture data source patterns (Section 3)
- Note patterns and edge cases (Section 4)
- Ask: "Have you ever seen something weird that breaks the rules?"

**Example Questions to Ask:**
- "Walk me through your typical 'load not tracking' workflow"
- "What do you always check first?"
- "How do you decide if it's a network issue vs an ELD issue?"
- "What's the hardest part to diagnose?"
- "Have you seen cases that confused you?"
- "What data source is most reliable?"
- "When do you know to escalate?"

### Step 3: Day 2 - Documentation & Validation (4 hours)

After the shadow session, convert your observations into a complete extraction:

**Hour 1-2: Create Decision Tree**
- Structure your observations as a flowchart
- Define each decision point clearly
- Add confidence levels to each branch
- Fill in Section 5

**Hour 2-3: Add Test Cases**
- Use the tickets you observed as test cases
- Create 3-5 representative examples
- Include both common and edge cases
- Fill in Section 6

**Hour 3-4: Validate with Analyst**
- Review the extraction with the analyst
- Fix any misunderstandings
- Add missing tribal knowledge
- Get their sign-off

## Template Sections Explained

| Section | Purpose | Filled When |
|---------|---------|------------|
| 1. Observation Session | Basic facts about the shadow | Day 1 (during session) |
| 2. Mental Model | How the analyst thinks about diagnosis | Day 1 (during session) |
| 3. Data Sources | Systems they query and how | Day 1 (during session) |
| 4. Patterns | Issue types they encounter and identify | Day 1 (during session) |
| 5. Decision Tree | Machine-readable flowchart | Day 2 (after session) |
| 6. Test Cases | Real examples for validation | Day 2 (after session) |
| 7. Edge Cases | Weird situations and workarounds | Day 1-2 (both) |
| 8. Metrics | Performance targets | Day 2 (after session) |
| 9. Dependencies | External systems/approvals needed | Day 1-2 (both) |
| 10. Knowledge Sources | Where the knowledge comes from | Day 2 (after session) |
| 11. Assumptions | Things assumed to be true | Day 2 (after session) |
| 12. Next Steps | Validation and conversion plan | Day 2 (after session) |

## Key Concepts

### Mental Model
The analyst's overall approach to diagnosis - their philosophy and first instincts. Think: "What would this person do with incomplete information?"

### Confidence Levels
How certain are they at each decision point? Use 0.0-1.0 scale:
- 1.0 = Absolutely certain
- 0.85+ = High confidence (can auto-resolve)
- 0.60-0.84 = Medium confidence (may need human review)
- <0.60 = Low confidence (escalate immediately)

### Evidence Weight
How important is each piece of evidence?
- 10 = Critical (single piece can determine outcome)
- 5 = Supporting (helps confirm diagnosis)
- 3 = Nice-to-have (helpful but not essential)

### Tribal Knowledge
Experience-based shortcuts that aren't documented anywhere:
- "CR England always sends ref number instead of load ID"
- "Pepsi loads sometimes have no carrier"
- "Check network FIRST - 40% of cases solved there"

## Example: OTR "Load Not Tracking" Extraction

The plan document includes a complete example (Part 3.3) showing how Prashant's OTR workflow would be extracted:

```yaml
session:
  analyst_name: "Prashant"
  analyst_role: "OTR Support Lead"
  domain: "OTR"

mental_model:
  diagnostic_philosophy: |
    Start with the simplest check (load exists?) and escalate to deeper queries.
    Network relationship is the #1 cause - check that before ELD.

decision_tree:
  entry_point: "check_load_exists"
  steps:
    check_load_exists:
      condition: "Load in system?"
      decisions:
        - condition: "404 Not Found"
          confidence: 0.98
          conclusion: "LOAD_NOT_FOUND"
        - condition: "200 OK"
          confidence: 0.80
          next_step: "check_network_relationship"
```

See `/Users/msp.raja/rca-agent-project/.omc/plans/rca-skills-platform-architecture.md` sections 3.3 and 4.1 for complete examples.

## Output: Skill Definition

Once completed, the extracted knowledge becomes a production skill:

```
skills/[domain]-rca/
├── skill_definition.yaml        # Generated from extraction
├── decision_tree.yaml            # Machine-readable flowchart
├── patterns/
│   ├── pattern_1.yaml
│   ├── pattern_2.yaml
│   └── ...
├── test_cases/
│   ├── case_1.yaml
│   └── ...
└── knowledge_base/
    └── [sme_name]_workflow.yaml  # This extraction document
```

## Validation Checklist

Before converting to a skill, verify:

- [ ] **Analyst review**: SME confirmed all details are accurate
- [ ] **Decision tree completeness**: All branches have clear outcomes
- [ ] **Test cases pass**: All test cases return expected patterns
- [ ] **Data sources validated**: Confirmed all APIs/databases work
- [ ] **Confidence scores reasonable**: Thresholds match expert judgment
- [ ] **Edge cases documented**: Unusual situations are covered
- [ ] **Dependencies clear**: Know what needs human approval

## Tips for Success

### During the Shadow Session

1. **Ask "Why?" often** - The reason matters as much as the action
2. **Record real cases** - Use actual customer issues, not hypotheticals
3. **Pay attention to order** - Which tool they check first matters
4. **Notice hesitation** - When they pause, they're making an uncertain decision
5. **Ask for shortcuts** - "What's your quick heuristic?"
6. **Understand the data** - "What does that field mean?" "Why is it null?"

### In the Write-Up

1. **Be specific** - "Check load exists" is vague; "GET /loads/{load_number} and check status code" is precise
2. **Use real conditions** - Copy actual API responses, field names, SQL queries
3. **Document confidence** - Don't assume 100% certainty
4. **Include both paths** - "If true then X, if false then Y" for every decision
5. **Test with examples** - Use cases they showed you to validate your extraction

### Common Mistakes to Avoid

- **Too vague**: "Check the system" (which system? how?)
- **Skipping tribal knowledge**: The shortcuts matter - they're why experts are fast
- **Wrong confidence levels**: Don't assume anything is 100% certain
- **Missing edge cases**: "What happens when...?" is a good question
- **Not asking why**: Understanding reasoning matters for validation

## Converting to Skill Definition

After completing the extraction, use it to create a production skill:

```bash
# The extracted YAML becomes the foundation for:
# 1. skills/[domain]-rca/skill_definition.yaml
# 2. skills/[domain]-rca/decision_tree.yaml
# 3. skills/[domain]-rca/test_cases.yaml
```

Reference: `knowledge_extraction_template.yaml` Section 12 for the conversion plan.

## Questions?

Use this template as an interview guide. It's designed to be filled collaboratively with the analyst - you're documenting their knowledge, not making assumptions about it.

**Key principle**: If you can't explain why the analyst does something, you don't understand the model yet.

---

**Last Updated**: 2026-01-26
**Template Version**: 1.0.0
**Purpose**: Guide knowledge extraction for RCA skill development
