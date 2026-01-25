# RCA Agent POC - Project Structure
**Date:** January 13, 2026
**Timeline:** 1 week POC → February in-person demo
**Participants:** MSP Raja, Arpit, Surya (ocean), Prashant (carrier/OTR)

---

## Executive Summary

**Problem:** Support analysts spend 45-50 minutes per ticket navigating multiple fragmented tools with no structured decision tree.

**Solution:** Skills-based agent architecture with router directing queries to specialized sub-agents, each containing specific APIs, decision trees, and domain logic.

**POC Scope:** Two use cases - Surya's ocean debugging workflow + Prashant's carrier/OTR operations.

**Success Criteria:** Agent completes investigation faster than manual, analyst trusts and would use on real tickets.

---

## Architecture

### High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Salesforce Ticket / Natural Language Query                 │
│  "Load U110123982 showing wrong departure date"             │
└────────────────────┬────────────────────────────────────────┘
                     ↓
         ┌───────────────────────┐
         │   Router Agent        │ ← Classifies issue type
         │   (Supervisor)        │ ← Selects appropriate skill
         └───────────┬───────────┘
                     ↓
    ┌────────────────┴────────────────┐
    │                                  │
    ↓                                  ↓
┌──────────────────┐        ┌──────────────────┐
│ Ocean Debugging  │        │ Carrier/OTR Ops  │
│ Skill            │        │ Skill            │
│ (Surya's flow)   │        │ (Prashant's flow)│
└────────┬─────────┘        └────────┬─────────┘
         ↓                           ↓
┌────────────────────────────────────────────────┐
│         State Machine                          │
│ ■ Step 1: Check network relationship           │
│ ■ Step 2: Check carrier files                  │
│ □ Step 3: Check file matching ← [CURRENT]      │
│ □ Step 4: Check SigNoz logs                    │
└────────────────────┬───────────────────────────┘
                     ↓
         ┌───────────────────────┐
         │ Stuck? Confidence low?│
         └───────────┬───────────┘
                     ↓
              ┌──────┴──────┐
              │   Human     │
              │ In-the-Loop │
              │             │
              │ "Found X,   │
              │  What should│
              │  I check    │
              │  next?"     │
              └─────────────┘
```

### Components

#### 1. Router Agent (Supervisor)
**File:** `router_agent.py`

**Purpose:** Classify incoming question and route to appropriate skill

**Logic:**
```python
def route(question: str, context: dict) -> str:
    # Pattern matching
    if "not tracking" in question.lower():
        return "ocean_debugging"
    if "carrier file" in question.lower():
        return "carrier_otr_operations"

    # LLM classification if patterns don't match
    classification = llm.classify(question, available_skills)
    return classification.skill_name
```

**Inputs:**
- Natural language question
- Load metadata (ID, mode, carrier, status)
- Ticket context (Salesforce)

**Outputs:**
- Skill to invoke
- Initial parameters for skill

#### 2. Skills (Sub-Agents)
**Structure:**
```
skills/
├── ocean_debugging/
│   ├── skill_definition.yaml
│   ├── decision_tree.yaml
│   ├── api_mappings.yaml
│   └── knowledge_base.md
└── carrier_otr_operations/
    └── [same structure]
```

**Skill Definition Example:**
```yaml
# skills/ocean_debugging/skill_definition.yaml
skill:
  name: "ocean_debugging"
  version: "1.0"
  description: "Debug ocean shipment tracking issues"
  owner: "Surya (support team)"

  triggers:
    patterns:
      - "not tracking"
      - "awaiting tracking info"
      - "vessel departure wrong"
    issue_categories:
      - "load_not_tracking"
      - "eta_issues"

  capabilities:
    - "Check network relationships"
    - "Verify carrier file reception"
    - "Analyze file matching"
    - "Query SigNoz logs"

  data_sources:
    - type: "redshift"
      tables: ["company_relationships", "fact_carrier_file_logs", "fact_carrier_record_logs"]
    - type: "clickhouse"
      service: "signoz"
    - type: "api"
      endpoint: "JustTransform API"

  decision_tree: "decision_tree.yaml"

  human_handoff_triggers:
    - confidence_threshold: 0.7
    - stuck_after_steps: 4
    - unexpected_data: true
```

#### 3. State Machine
**File:** `state_manager.py`

**Purpose:** Track investigation progress across non-linear paths

**State Structure:**
```python
{
  "session_id": "uuid",
  "ticket_id": "SF-12345",
  "load_id": "U110123982",
  "skill": "ocean_debugging",
  "current_step": "step_2_carrier_files",
  "steps_completed": [
    {
      "step": "step_1_network_relationship",
      "result": "relationship_ok",
      "data": {...},
      "timestamp": "2026-01-13T10:30:00Z"
    }
  ],
  "pending_steps": ["step_3_file_matching"],
  "confidence": 0.85,
  "requires_human": false,
  "evidence_collected": [...]
}
```

**Key Operations:**
- `advance(step_result)` - Move to next step based on decision
- `backtrack(step_name)` - Go back if wrong path
- `parallel(steps)` - Fork into multiple investigation paths
- `merge(results)` - Combine parallel results
- `handoff_to_human(reason)` - Pause and ask for help

#### 4. Human-in-the-Loop Interface
**File:** `human_handoff.py`

**When to trigger:**
- Confidence score < 0.7
- Stuck after N steps without conclusion
- Unexpected data (contradictions)
- Critical decision point (create relationship, escalate, etc.)

**Handoff Format:**
```json
{
  "status": "needs_human_input",
  "reason": "Unexpected: Files exist but no matches found",
  "context": {
    "steps_completed": 3,
    "evidence": [
      "Network relationship: ACTIVE",
      "Carrier files received: 15 in last 7 days",
      "File matching: 0 matches found"
    ],
    "current_hypothesis": "Identifier mismatch - load identifiers don't match file"
  },
  "question_to_human": "Should I download most recent file to inspect identifiers?",
  "suggested_actions": [
    {"label": "Download file", "confidence": 0.6},
    {"label": "Check load creation", "confidence": 0.4},
    {"label": "Escalate to engineering", "confidence": 0.2}
  ],
  "resume_state": "saved_state_id_xyz"
}
```

---

## POC Use Cases

### Use Case 1: Ocean Debugging (Surya's Workflow)
**Documentation:** `SUPPORT-TEAM-MENTAL-MODEL.md` (already exists)

**Issue Type:** "Load not tracking - Awaiting Tracking Info"

**Decision Tree:** 3 steps
1. Check network relationship
2. Check carrier files
3. Check file matching

**Expected Time Savings:** 40 min → 20 min (50% reduction)

**Test Cases:**
- Known ticket: Network relationship missing
- Known ticket: Carrier not sending files
- Known ticket: Identifier mismatch

### Use Case 2: Carrier/OTR Operations (Prashant's Workflow)
**Documentation:** To be created from tomorrow's session

**Issue Type:** TBD (from Prashant)

**Decision Tree:** TBD

**Expected Time Savings:** TBD

---

## APIs & Data Sources

### Authentication Flows
**To be mapped:**
- [ ] Redshift credentials (which account? read-only access?)
- [ ] ClickHouse/SigNoz (how to authenticate?)
- [ ] JustTransform API (get credentials from Surya)
- [ ] Tracking API (Super API - get Postman collection)
- [ ] Salesforce API (for ticket integration)

### API Inventory
| API | Purpose | Auth | Owner | POC Required? |
|-----|---------|------|-------|---------------|
| Redshift | Load metadata, files, relationships | IAM | Data Platform | ✅ Yes |
| SigNoz | Log analysis | TBD | Platform | ✅ Yes |
| JustTransform | Web scraping data | Shared creds | External | ✅ Yes |
| Super API | Tracking config | API key | Internal | ⚠️ Maybe |
| Data Hub API | Ocean checklist | User login | Internal | ⚠️ Maybe |

---

## Critical Success Factors

### What Makes This POC Succeed?

1. **Speed:** Agent faster than manual (even if only by 10 minutes)
2. **Trust:** Shows its work, doesn't black-box
3. **Graceful failure:** When stuck, hands off cleanly
4. **Real ticket validation:** Works on last week's actual tickets
5. **Champion adoption:** Surya says "I'd use this"

### What Makes This POC Fail?

1. ❌ **Takes longer than manual** - Won't get adopted
2. ❌ **Too many false positives** - Loses trust
3. ❌ **Opaque reasoning** - "How did you get this answer?"
4. ❌ **Can't handle edge cases** - 80% coverage not good enough
5. ❌ **Another tool to learn** - Already tool-fatigued

### How to Avoid Failure

**Learn from previous RCA bot "low usage despite claims":**
- Why didn't people use it? Ask Surya, Prashant directly
- What was wrong with it? Too slow? Too rigid? Not integrated?
- What would make this different?

**Design for adoption:**
- Show all SQL queries run (copy-pasteable)
- Display all data fetched (verifiable)
- Let analyst override any decision
- Work in Salesforce (where they already are)

---

## Timeline

### Week 1 (Jan 13-19): POC Development
**Day 1 (Today):** Structure defined, prep for Prashant session
**Day 2 (Tomorrow):** Prashant session - document carrier/OTR workflow
**Day 3-4:** Build router + ocean debugging skill
**Day 5:** Test on known tickets
**Day 6-7:** Refine based on test results

### Week 2 (Jan 20-26): Internal Demo
**Demo to:** Arpit, Surya, Prashant
**Format:** Live demonstration on real ticket
**Outcome:** Go/no-go decision

### February: In-Person Demo (Chennai)
**With:** Surya (live debugging session)
**Validate:** Works in real support environment
**Outcome:** Production readiness assessment

---

## Documentation Strategy

### Markdown Optimized for AI Consumption

**Format:**
```markdown
# Skill: Ocean Debugging

## When to use this skill
- Issue category: Load not tracking
- Keywords: "awaiting tracking info", "no updates"

## Step 1: Check Network Relationship
Query: SELECT ... FROM company_relationships WHERE ...
Decision:
  - If NO relationship → ACTION: Create relationship
  - If INACTIVE → ACTION: Activate relationship
  - If ACTIVE → NEXT: Step 2

## Step 2: Check Carrier Files
...
```

**Why this format:**
- LLM can parse easily
- Human readable
- Version controllable (Git)
- Easy to update as workflows change

---

## Open Questions

**Technical:**
- [ ] Which LLM? (Claude, GPT-4, local model?)
- [ ] State persistence? (Redis, DB, in-memory?)
- [ ] Deployment? (Docker, K8s, serverless?)
- [ ] Logging framework? (OpenTelemetry, custom?)

**Organizational:**
- [ ] Who reviews PRs? (Arpit? Surya?)
- [ ] Who approves production deployment? (Need security review?)
- [ ] What happens if POC fails? (Pivot or pause?)
- [ ] Budget for LLM API costs? (Track usage)

**Integration:**
- [ ] Salesforce API access? (Need admin approval?)
- [ ] Production DB access? (Read-only sufficient?)
- [ ] JustTransform credentials? (Get from Surya)

---

## Next Steps

**For MSP Raja:**
- [x] Create POC_STRUCTURE.md (this document)
- [ ] Attend Prashant session tomorrow
- [ ] Create SKILLS_FRAMEWORK.md (architecture patterns)
- [ ] Build router prototype
- [ ] Test on known tickets

**For Arpit:**
- [ ] Review POC structure
- [ ] Provide feedback on architecture decisions
- [ ] Share rewind-app codebase access
- [ ] Get API credentials

**For Surya:**
- [ ] Share JustTransform API credentials
- [ ] Share Postman collections (Super API, Data Hub)
- [ ] Provide 5 real tickets for POC testing
- [ ] Review decision tree accuracy

**For Prashant:**
- [ ] Tomorrow's debugging session
- [ ] Document carrier/OTR workflow
- [ ] Share custom tools/queries used

---

## Metrics for POC

### Measure These:

**Time Savings:**
- Manual process: ___ minutes
- Agent process: ___ minutes
- Savings: ___ minutes (___%)

**Accuracy:**
- Correct root cause: ___/10 tickets
- False positives: ___/10 tickets
- Had to handoff to human: ___/10 tickets

**Usability:**
- Surya would use on real ticket: Yes/No
- Prashant would use on real ticket: Yes/No
- Identified pain points: [list]

**Technical:**
- Average API calls per investigation: ___
- Average LLM tokens used: ___
- Error rate: ___

---

**Status:** ✅ POC structure defined
**Next:** Prashant session tomorrow, then build router
**Owner:** MSP Raja
**Last Updated:** 2026-01-13
